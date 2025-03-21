# frontend.py
import streamlit as st
import requests
import base64
import numpy as np
import json
import plotly.express as px
import plotly.graph_objects as go
from streamlit_folium import st_folium
import folium
import pandas as pd

# -----------------------------------------------------------------------------
# CONFIGURACIÓN
# -----------------------------------------------------------------------------
API_URL = "http://34.70.250.5"  # <--- Ajusta a tu URL, por ejemplo: "https://fca1-194-209-94-51.ngrok-free.app"

st.title("🌍 Dashboard con FastAPI (Backend) + Streamlit (Frontend)")

# -----------------------------------------------------------------------------
# FUNCIONES PARA CONSUMIR EL BACKEND
# -----------------------------------------------------------------------------
def get_geojson(endpoint: str) -> dict:
    """Llama a un endpoint del backend que retorna un GeoJSON dict."""
    url = f"{API_URL}{endpoint}"
    try:
        resp = requests.get(url)
        if resp.status_code == 200:
            data = resp.json()
            return data
        else:
            st.error(f"Error {resp.status_code} al llamar {url}: {resp.text}")
            return {}
    except Exception as e:
        st.error(f"No se pudo conectar con {url}: {e}")
        return {}

def get_raster(endpoint: str, params: dict = None):
    """
    Llama a un endpoint que retorna un dict con:
     - 'base64_data': string,
     - 'shape': [rows, cols],
     - 'metadata': {...}
    Devuelve (numpy_array, metadata) o (None, None) si falla.
    """
    url = f"{API_URL}{endpoint}"
    try:
        resp = requests.get(url, params=params, timeout=20)
        if resp.status_code == 200:
            result = resp.json()
            if "error" in result:
                st.warning(result["error"])
                return None, None

            # Decodificar base64
            shape = result["shape"]  # [rows, cols]
            data_b64 = result["base64_data"]
            metadata = result["metadata"]

            # Convertir base64 a bytes
            data_bytes = base64.b64decode(data_b64)
            # Inferir dtype del raster
            dtype_str = metadata.get("dtype", "int16")  
            arr = np.frombuffer(data_bytes, dtype=dtype_str)
            arr = arr.reshape(shape)  # (rows, cols)

            return arr, metadata
        else:
            st.error(f"Error {resp.status_code} al llamar {url}: {resp.text}")
            return None, None
    except Exception as e:
        st.error(f"No se pudo conectar con {url}: {e}")
        return None, None

def plot_raster_and_hist(data: np.ndarray, title_map: str, title_hist: str, color_label: str):
    """
    Genera figuras Plotly (Heatmap y Histograma) para un array 2D.
    Retorna (fig_map, fig_hist).
    """
    # 1) Heatmap
    fig_map = go.Figure(data=go.Heatmap(
        z=data[::-1],  # invertimos eje Y
        colorscale="Viridis",
        colorbar=dict(title=color_label)
    ))
    fig_map.update_layout(
        title=title_map,
        xaxis=dict(title="X"),
        yaxis=dict(title="Y")
    )

    # 2) Histograma
    flat_data = data.flatten()
    fig_hist = px.histogram(
        x=flat_data,
        nbins=50,
        title=title_hist,
        labels={"x": color_label}
    )
    fig_hist.update_layout(bargap=0.1)

    return fig_map, fig_hist

# -----------------------------------------------------------------------------
# CREACIÓN DE PESTAÑAS
# -----------------------------------------------------------------------------
tabs = st.tabs([
    "Capas Vectoriales",
    "Cobertura de Tierra",
    "Productividad Primaria (GPP)",
    "Precipitación",
    "Densidad Poblacional",
    "Información Distritos"
])

# -----------------------------------------------------------------------------
# 1) CAPAS VECTORIALES
# -----------------------------------------------------------------------------
with tabs[0]:
    st.subheader("Capas vectoriales (distritos, región, carreteras, ríos)")

    st.write("Selecciona las capas que deseas ver en el mapa:")
    show_districts = st.checkbox("Distritos Assaba", value=True)
    show_region = st.checkbox("Región Assaba", value=False)
    show_roads = st.checkbox("Carreteras", value=False)
    show_water = st.checkbox("Cuerpos de Agua", value=False)

    # Crear mapa base Folium
    m = folium.Map(location=[17.0, -11.0], zoom_start=7)

    # Distritos
    if show_districts:
        data_geo = get_geojson("/admin/districts")
        if data_geo and "features" in data_geo:
            folium.GeoJson(data_geo, name="Distritos").add_to(m)

    # Región
    if show_region:
        data_geo = get_geojson("/admin/region")
        if data_geo and "features" in data_geo:
            folium.GeoJson(data_geo, name="Región Assaba",
                           style_function=lambda x: {
                               "fillColor": "#ffaf00",
                               "color": "black",
                               "weight": 2,
                               "fillOpacity": 0.2
                           }).add_to(m)

    # Carreteras
    if show_roads:
        data_geo = get_geojson("/roads")
        if data_geo and "features" in data_geo:
            folium.GeoJson(data_geo, name="Carreteras").add_to(m)

    # Ríos
    if show_water:
        data_geo = get_geojson("/water")
        if data_geo and "features" in data_geo:
            folium.GeoJson(data_geo, name="Cuerpos de Agua").add_to(m)

    folium.LayerControl().add_to(m)
    st_folium(m, width=700, height=500)

# -----------------------------------------------------------------------------
# 2) COBERTURA DE TIERRA
# -----------------------------------------------------------------------------
with tabs[1]:
    st.subheader("Cobertura de Tierra (MODIS)")

    year_lc = st.selectbox("Selecciona año:", list(range(2010,2024)), index=0)
    data_lc, meta_lc = get_raster("/rasters/landcover", params={"year": year_lc})

    if data_lc is not None:
        fig_map, fig_hist = plot_raster_and_hist(
            data_lc,
            title_map=f"Land Cover {year_lc}",
            title_hist=f"Histograma Land Cover {year_lc}",
            color_label="Land Cover"
        )
        col1, col2 = st.columns([1.5, 1])
        with col1:
            st.plotly_chart(fig_map, use_container_width=True)
        with col2:
            st.plotly_chart(fig_hist, use_container_width=True)

        st.write("**Metadatos:**")
        st.json(meta_lc)

# -----------------------------------------------------------------------------
# 3) PRODUCTIVIDAD PRIMARIA (GPP)
# -----------------------------------------------------------------------------
with tabs[2]:
    st.subheader("Productividad Primaria (GPP)")

    year_gpp = st.selectbox("Selecciona año (GPP):", list(range(2010,2024)), index=0)
    data_gpp, meta_gpp = get_raster("/rasters/gpp", params={"year": year_gpp})

    if data_gpp is not None:
        fig_map, fig_hist = plot_raster_and_hist(
            data_gpp,
            title_map=f"GPP {year_gpp}",
            title_hist=f"Histograma GPP {year_gpp}",
            color_label="GPP"
        )
        col1, col2 = st.columns([1.5, 1])
        with col1:
            st.plotly_chart(fig_map, use_container_width=True)
        with col2:
            st.plotly_chart(fig_hist, use_container_width=True)

        st.write("**Metadatos:**")
        st.json(meta_gpp)

# -----------------------------------------------------------------------------
# 4) PRECIPITACIÓN
# -----------------------------------------------------------------------------
with tabs[3]:
    st.subheader("Precipitación (CHIRPS / Climate Data)")

    year_prec = st.selectbox("Selecciona año (Precip):", list(range(2010,2024)), index=0)
    data_prec, meta_prec = get_raster("/rasters/precip", params={"year": year_prec})

    if data_prec is not None:
        fig_map_prec, fig_hist_prec = plot_raster_and_hist(
            data_prec,
            title_map=f"Precipitación {year_prec}",
            title_hist=f"Histograma Precip {year_prec}",
            color_label="mm/año"
        )
        col1, col2 = st.columns([1.5, 1])
        with col1:
            st.plotly_chart(fig_map_prec, use_container_width=True)
        with col2:
            st.plotly_chart(fig_hist_prec, use_container_width=True)

        st.write("**Metadatos:**")
        st.json(meta_prec)

# -----------------------------------------------------------------------------
# 5) DENSIDAD POBLACIONAL
# -----------------------------------------------------------------------------
with tabs[4]:
    st.subheader("Densidad Poblacional")

    years_pop = [2000, 2005, 2010, 2015, 2020]
    year_pop = st.selectbox("Selecciona año (Pop):", years_pop, index=2)
    data_pop, meta_pop = get_raster("/rasters/pop", params={"year": year_pop})

    if data_pop is not None:
        fig_map_pop, fig_hist_pop = plot_raster_and_hist(
            data_pop,
            title_map=f"Densidad Poblacional {year_pop}",
            title_hist=f"Histograma Población {year_pop}",
            color_label="Pob/km2"
        )
        col1, col2 = st.columns([1.5, 1])
        with col1:
            st.plotly_chart(fig_map_pop, use_container_width=True)
        with col2:
            st.plotly_chart(fig_hist_pop, use_container_width=True)

        st.write("**Metadatos:**")
        st.json(meta_pop)

# -----------------------------------------------------------------------------
# 6) INFORMACIÓN DE DISTRITOS
# -----------------------------------------------------------------------------
with tabs[5]:
    st.subheader("Información de Distritos (Tabla de Atributos)")
    st.write(""" 
    Aquí se muestra la información detallada que llega desde el endpoint 
    `/admin/districts`. Este endpoint retorna un GeoJSON con las \textbf{properties} 
    de cada distrito, así como su geometría. 
    """)

    geo_data = get_geojson("/admin/districts")
    if geo_data and "features" in geo_data:
        features = geo_data["features"]
        if len(features) > 0:
            # Construir un DataFrame a partir de 'properties'
            props_list = []
            for feat in features:
                # feat: { "type": "Feature", "properties": {...}, "geometry": {...} }
                props_list.append(feat.get("properties", {}))
            df_districts = pd.DataFrame(props_list)

            st.write("**Vista de la tabla de atributos**")
            st.dataframe(df_districts)

            st.write("**Cantidad de distritos:**", len(df_districts))

            # Opcional: Mostrar la columna "ADM3_EN" si existe
            if "ADM3_EN" in df_districts.columns:
                st.write("**Nombres de los distritos:**")
                st.write(", ".join(df_districts["ADM3_EN"].unique()))
        else:
            st.warning("No se encontró ninguna feature en /admin/districts.")
    else:
        st.warning("No se pudo obtener la información de distritos.")
