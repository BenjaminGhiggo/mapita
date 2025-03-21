# backend.py

import os
import base64
import logging
import json

import geopandas as gpd
import rasterio
import numpy as np
import pandas as pd

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from typing import Any, Dict, Union

app = FastAPI()

# -----------------------------------------------------------------------------
# CONFIGURACIÓN DE LOGGING
# -----------------------------------------------------------------------------
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# -----------------------------------------------------------------------------
# CONFIGURACIÓN DE CORS (Permitir todas las conexiones)
# -----------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=[""],       # Acepta cualquier origen
    allow_credentials=True,
    allow_methods=[""],       # Acepta cualquier método
    allow_headers=["*"],
)


# -----------------------------------------------------------------------------
# FUNCIONES AUXILIARES
# -----------------------------------------------------------------------------
def load_shapefile_as_geojson(filepath: str) -> Dict[str, Any]:
    """
    Carga un shapefile con GeoPandas, re-proyecta a EPSG:4326 (si fuera necesario)
    y lo convierte a GeoJSON (dict). Esto garantiza que tanto la geometría como
    las propiedades aparezcan correctamente en la respuesta.
    """
    logger.info(f"Cargando shapefile: {filepath}")
    gdf = gpd.read_file(filepath)
    if gdf.empty:
        logger.warning(f"El shapefile '{filepath}' no contiene geometrías o está vacío.")
    
    # Si el shapefile no tiene crs definido o si es distinto de EPSG:4326,
    # lo forzamos/convertimos a EPSG:4326 para que se muestre correctamente en clientes web.
    if gdf.crs is None:
        logger.warning(f"El shapefile '{filepath}' no define un CRS. Se asume EPSG:4326.")
        gdf.crs = "EPSG:4326"
    else:
        try:
            gdf = gdf.to_crs(epsg=4326)
        except Exception as e:
            logger.error(f"No se pudo reproyectar '{filepath}' a EPSG:4326: {e}")

    # Convertir columnas datetime a string, si existen
    for col in gdf.columns:
        if pd.api.types.is_datetime64_any_dtype(gdf[col]):
            gdf[col] = gdf[col].dt.strftime('%Y-%m-%d %H:%M:%S')

    # Convierte a GeoJSON (string) y luego a diccionario
    geojson_str = gdf.to_json()
    geojson_dict = json.loads(geojson_str)
    return geojson_dict


def load_raster_as_base64(filepath: str) -> Dict[str, Union[str, tuple, dict]]:
    """
    Carga un ráster .tif con rasterio, y devuelve:
      - 'base64_data': codificación base64 de la primera banda (array numpy),
      - 'shape': (alto, ancho),
      - 'metadata': metadatos relevantes (crs, transform, dtype, etc.).
    """
    logger.info(f"Cargando ráster: {filepath}")
    with rasterio.open(filepath) as src:
        data = src.read(1)  # Leer solo la primera banda
        profile = src.profile

    # Convertir la matriz (numpy) a bytes
    data_bytes = data.tobytes()
    # Codificar en base64
    base64_string = base64.b64encode(data_bytes).decode('utf-8')

    shape = data.shape  # (rows, cols)

    # Convertir metadatos a un dict JSON-friendly
    meta = {
        "crs": str(profile.get("crs")),
        "transform": tuple(profile.get("transform")) if profile.get("transform") else None,
        "dtype": profile.get("dtype"),
        "nodata": profile.get("nodata"),
        "driver": profile.get("driver"),
        "count": profile.get("count"),
        "width": profile.get("width"),
        "height": profile.get("height")
    }

    return {
        "base64_data": base64_string,
        "shape": shape,
        "metadata": meta
    }

# -----------------------------------------------------------------------------
# ENDPOINTS
# -----------------------------------------------------------------------------
@app.get("/")
def read_root():
    """
    Retorna un mensaje de bienvenida para verificar que la API está activa.
    """
    return {"message": "Hola desde el Backend (FastAPI)!"}

@app.get("/admin/districts")
def get_districts():
    """
    Retorna los distritos de Assaba en formato GeoJSON (dict),
    con todas las propiedades y geometrías correctamente proyectadas a EPSG:4326.
    """
    shp_path = os.path.join("Admin_layers", "Assaba_Districts_layer.shp")
    if not os.path.exists(shp_path):
        return {"error": f"No se encontró {shp_path}"}

    geojson_dict = load_shapefile_as_geojson(shp_path)
    return geojson_dict

@app.get("/admin/region")
def get_region():
    """
    Retorna la región de Assaba en formato GeoJSON (dict).
    """
    shp_path = os.path.join("Admin_layers", "Assaba_Region_layer.shp")
    if not os.path.exists(shp_path):
        return {"error": f"No se encontró {shp_path}"}

    geojson_dict = load_shapefile_as_geojson(shp_path)
    return geojson_dict

@app.get("/roads")
def get_roads():
    """
    Retorna las carreteras en formato GeoJSON (dict).
    """
    shp_path = os.path.join("Streamwater_Line_Road_Network", "Main_Road.shp")
    if not os.path.exists(shp_path):
        return {"error": f"No se encontró {shp_path}"}

    geojson_dict = load_shapefile_as_geojson(shp_path)
    return geojson_dict

@app.get("/water")
def get_streams():
    """
    Retorna ríos/cuerpos de agua en formato GeoJSON (dict).
    """
    shp_path = os.path.join("Streamwater_Line_Road_Network", "Streamwater.shp")
    if not os.path.exists(shp_path):
        return {"error": f"No se encontró {shp_path}"}

    geojson_dict = load_shapefile_as_geojson(shp_path)
    return geojson_dict

@app.get("/rasters/landcover")
def get_landcover(year: int = 2010):
    """
    Retorna la Cobertura de Tierra (MODIS) para un año dado.
    Devuelve la matriz en base64, la forma (shape) y metadatos.
    Ejemplo: /rasters/landcover?year=2015
    """
    tif_path = os.path.join("Modis_Land_Cover_Data", f"{year}LCT.tif")
    if not os.path.exists(tif_path):
        return {"error": f"No se encontró {tif_path}"}

    result = load_raster_as_base64(tif_path)
    return result

@app.get("/rasters/gpp")
def get_gpp(year: int = 2010):
    """
    Retorna la Productividad Primaria Bruta (GPP) para un año dado.
    Ejemplo: /rasters/gpp?year=2020
    """
    tif_path = os.path.join("MODIS_Gross_Primary_Production_GPP", f"{year}_GP.tif")
    if not os.path.exists(tif_path):
        return {"error": f"No se encontró {tif_path}"}

    result = load_raster_as_base64(tif_path)
    return result

@app.get("/rasters/precip")
def get_precip(year: int = 2010):
    """
    Retorna los datos de precipitación (CHIRPS) para un año dado (por ej, 2010R.tif).
    Ejemplo: /rasters/precip?year=2015
    """
    tif_path = os.path.join("Climate_Precipitation_Data", f"{year}R.tif")
    if not os.path.exists(tif_path):
        return {"error": f"No se encontró {tif_path}"}

    result = load_raster_as_base64(tif_path)
    return result

@app.get("/rasters/pop")
def get_population(year: int = 2010):
    """
    Retorna la densidad poblacional para un año dado (2000, 2005, 2010, 2015, 2020),
    usando archivos con nomenclatura 'mrt_pd_{year}_1km.tif'.
    Ejemplo: /rasters/pop?year=2015
    """
    tif_path = os.path.join("Gridded_Population_Density_Data", f"mrt_pd_{year}_1km.tif")
    if not os.path.exists(tif_path):
        return {"error": f"No se encontró {tif_path}"}

    result = load_raster_as_base64(tif_path)
    return result
