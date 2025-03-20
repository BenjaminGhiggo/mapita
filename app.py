import streamlit as st
import geopandas as gpd
import rasterio
import numpy as np
import folium
from streamlit_folium import st_folium
import matplotlib.pyplot as plt
import logging
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go  # <-- Para el mapa de cobertura de tierra

# ============================================================================
# CONFIGURACIÓN DEL LOGGING
# ============================================================================
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s"
)
logger = logging.getLogger(__name__)

# ============================================================================
# FUNCIONES DE CARGA DE DATOS
# ============================================================================
def load_shapefile(filepath: str):
    try:
        logger.info(f"Intentando cargar shapefile: {filepath}")
        gdf = gpd.read_file(filepath)
        logger.debug(f"Shapefile '{filepath}' cargado correctamente con {len(gdf)} registros.")
        # Convertir datetime a string (si existiera)
        for col in gdf.columns:
            if pd.api.types.is_datetime64_any_dtype(gdf[col]):
                gdf[col] = gdf[col].dt.strftime('%Y-%m-%d %H:%M:%S')
        return gdf
    except Exception as e:
        logger.error(f"Error al cargar shapefile '{filepath}': {e}", exc_info=True)
        return None

def load_raster(filepath: str):
    try:
        logger.info(f"Intentando cargar raster: {filepath}")
        with rasterio.open(filepath) as src:
            data = src.read(1)
            profile = src.profile
            transform = src.transform  # Información de georreferenciación
        logger.debug(f"Raster '{filepath}' cargado. Dimensiones: {data.shape}.")
        return data, profile, transform
    except Exception as e:
        logger.error(f"Error al cargar raster '{filepath}': {e}", exc_info=True)
        return None, None, None

# ============================================================================
# LÓGICA PRINCIPAL DE STREAMLIT
# ============================================================================
def main():
    st.title("🌍 Dashboard de Cobertura de Tierra con Plotly")

    try:
        # --------------------------------------------------------------------
        # 1. SELECCIÓN DE CAPAS VECTORIALES (Shapefile)
        # --------------------------------------------------------------------
        st.sidebar.header("Capas Vectoriales")
        show_shapefile = st.sidebar.checkbox("Mostrar Distritos de Assaba", value=True)

        if show_shapefile:
            shp_path = "Admin_layers/Assaba_Districts_layer.shp"
            assaba_districts = load_shapefile(shp_path)

            if assaba_districts is not None:
                st.subheader("📍 Shapefile: Distritos de Assaba")
                st.write(assaba_districts.head())

                try:
                    m = folium.Map(location=[17.0, -11.0], zoom_start=7)
                    folium.GeoJson(assaba_districts).add_to(m)
                    st_folium(m, width=700, height=450)
                except Exception as e:
                    logger.error("Error al renderizar el mapa folium:", exc_info=True)
                    st.error(f"Error al renderizar el mapa: {e}")
            else:
                st.error(f"No se pudo cargar el archivo shapefile: {shp_path}")

        # --------------------------------------------------------------------
        # 2. SELECCIÓN Y VISUALIZACIÓN DE RASTERS (MODIS LAND COVER)
        # --------------------------------------------------------------------
        st.sidebar.header("Datos Ráster (MODIS Land Cover)")
        years = list(range(2010, 2024))  # Ajusta si difiere
        selected_year = st.sidebar.selectbox("📅 Selecciona el año:", years, index=0)

        tif_path = f"Modis_Land_Cover_Data/{selected_year}LCT.tif"
        data, profile, transform = load_raster(tif_path)

        if data is not None:
            st.subheader(f"🗺️ Mapa de Cobertura de Tierra - {selected_year}")
            st.write("📄 **Metadatos del ráster:**")
            st.write(profile)

            try:
                # --------------------------------------------------------------------
                # 2.1 MAPA DE COBERTURA DE TIERRA CON PLOTLY
                # --------------------------------------------------------------------
                fig_map = go.Figure(data=go.Heatmap(
                    z=data[::-1],  # Invertimos para que se vea bien en la visualización
                    colorscale="Viridis",  # Cambia el colormap si quieres
                    colorbar=dict(title="Land Cover")
                ))

                fig_map.update_layout(
                    title=f"Mapa de Cobertura de Tierra - {selected_year}",
                    xaxis=dict(title="X Coordenada (columna)"),
                    yaxis=dict(title="Y Coordenada (fila)")
                )

                st.plotly_chart(fig_map, use_container_width=True)

                # --------------------------------------------------------------------
                # 2.2 HISTOGRAMA DE LAND COVER CON PLOTLY
                # --------------------------------------------------------------------
                logger.debug("Generando histograma con Plotly...")
                df_lc = pd.DataFrame({"land_cover": data.flatten()})

                fig_hist = px.histogram(
                    df_lc,
                    x="land_cover",
                    nbins=50,  # Ajusta la cantidad de bins
                    title=f"📊 Histograma de valores de Land Cover {selected_year}",
                    labels={"land_cover": "Tipo de Cobertura"}
                )

                fig_hist.update_layout(bargap=0.1)
                st.plotly_chart(fig_hist, use_container_width=True)
                logger.debug("Histograma mostrado en Streamlit con éxito usando Plotly.")

            except Exception as e:
                logger.error("Error al generar gráficos con Plotly:", exc_info=True)
                st.error(f"Error al generar los gráficos: {e}")
        else:
            st.warning(f"No se pudo cargar el archivo ráster: {tif_path}")

    except Exception as e:
        logger.critical("Error general en la aplicación Streamlit:", exc_info=True)
        st.error(f"Ocurrió un error inesperado en la aplicación: {e}")

if __name__ == "__main__":
    main()
