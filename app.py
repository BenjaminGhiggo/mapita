import streamlit as st
import os
import geopandas as gpd
import pandas as pd
import rasterio
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import folium
from streamlit_folium import st_folium
import logging

# ----------------------------------------------------------------------------
# CONFIGURACIÓN DEL LOGGING
# ----------------------------------------------------------------------------
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s"
)
logger = logging.getLogger(__name__)

# ----------------------------------------------------------------------------
# FUNCIONES DE CARGA DE DATOS
# ----------------------------------------------------------------------------
def load_shapefile(filepath: str) -> gpd.GeoDataFrame:
    """
    Carga un shapefile con GeoPandas.
    Convierte columnas datetime a string para evitar errores de serialización.
    Retorna None si falla.
    """
    try:
        logger.info(f"Cargando shapefile: {filepath}")
        gdf = gpd.read_file(filepath)
        # Convertir columnas datetime en string, de ser necesario
        for col in gdf.columns:
            if pd.api.types.is_datetime64_any_dtype(gdf[col]):
                gdf[col] = gdf[col].dt.strftime('%Y-%m-%d %H:%M:%S')
        return gdf
    except Exception as e:
        logger.error(f"Error al cargar shapefile '{filepath}': {e}", exc_info=True)
        return None

def load_raster(filepath: str):
    """
    Carga un archivo ráster (TIF) con rasterio.
    Retorna (data, profile) o (None, None) si falla.
    """
    try:
        logger.info(f"Cargando ráster: {filepath}")
        with rasterio.open(filepath) as src:
            data = src.read(1)
            profile = src.profile
        return data, profile
    except Exception as e:
        logger.error(f"Error al cargar ráster '{filepath}': {e}", exc_info=True)
        return None, None

def plot_raster_and_hist(
    data: np.ndarray,
    title_map: str,
    title_hist: str,
    colorbar_label: str = "Valor",
    bins: int = 50
):
    """
    Crea dos gráficos con Plotly:
    - Mapa (Heatmap) a partir de un array 2D.
    - Histograma de distribución de valores.
    Retorna (fig_map, fig_hist).
    """
    # 1) Mapa tipo Heatmap (invertimos en eje Y para apariencia “normal”)
    fig_map = go.Figure(
        data=go.Heatmap(
            z=data[::-1],  
            colorscale="Viridis",
            colorbar=dict(title=colorbar_label),
            zauto=True
        )
    )
    fig_map.update_layout(
        title=title_map,
        xaxis=dict(title="Eje X (columnas)"),
        yaxis=dict(title="Eje Y (filas)")
    )

    # 2) Histograma
    # Convertimos data en un DataFrame para usar px.histogram
    flat_data = data.flatten()
    df = pd.DataFrame({colorbar_label: flat_data})

    fig_hist = px.histogram(
        df,
        x=colorbar_label,
        nbins=bins,
        title=title_hist
    )
    fig_hist.update_layout(bargap=0.1)

    return fig_map, fig_hist

# ----------------------------------------------------------------------------
# LÓGICA PRINCIPAL DE STREAMLIT
# ----------------------------------------------------------------------------
def main():
    st.title("🌍 SahelSense")

    # Breve descripción general
    st.markdown("""
    **Descripción General**  
    En este dashboard mostramos diversos datasets para la región del Sahel,
    con el objetivo de entender la dinámica de la tierra: cobertura,
    precipitación, población, productividad primaria, y la infraestructura
    (carreteras, cursos de agua, etc.). Cada pestaña incluye una breve
    descripción del *dataset* y una visualización en forma de mapa e histograma.
    """)

    # ------------------------------------------------------------------------
    # PESTAÑAS PRINCIPALES
    # ------------------------------------------------------------------------
    tabs = st.tabs([
        "Capas Administrativas y Redes",
        "Cobertura de Tierra (MODIS)",
        "Productividad Primaria (MODIS GPP)",
        "Precipitación",
        "Densidad Poblacional"
    ])

    # ========================================================================
    # 1. TAB: Capas Administrativas (Distritos/Regiones) y Red (Carreteras/Ríos)
    # ========================================================================
    with tabs[0]:
        st.markdown("### Capas Administrativas y Red de Carreteras/Agua")
        st.write("""
        En esta sección se muestran las **capas vectoriales** correspondientes a:
        - **Distritos** de Assaba
        - **Región** de Assaba
        - **Carreteras** principales
        - **Ríos/cuerpos de agua**

        Cada una puede visualizarse en un mapa interactivo para entender
        la división administrativa y la infraestructura existente.
        """)

        # Opciones de visualización
        show_districts = st.checkbox("Mostrar Distritos de Assaba", value=True)
        show_region = st.checkbox("Mostrar Región de Assaba", value=False)
        show_roads = st.checkbox("Mostrar Carreteras Principales", value=False)
        show_streams = st.checkbox("Mostrar Cuerpos de Agua", value=False)

        # Creamos un mapa base Folium
        m = folium.Map(location=[17.0, -11.0], zoom_start=7)

        if show_districts:
            shp_path = os.path.join("Admin_layers", "Assaba_Districts_layer.shp")
            gdf_districts = load_shapefile(shp_path)
            if gdf_districts is not None:
                folium.GeoJson(gdf_districts, name="Distritos Assaba").add_to(m)

        if show_region:
            shp_path = os.path.join("Admin_layers", "Assaba_Region_layer.shp")
            gdf_region = load_shapefile(shp_path)
            if gdf_region is not None:
                folium.GeoJson(gdf_region, name="Región Assaba", 
                               style_function=lambda x: {
                                    "fillColor": "#ffaf00",
                                    "color": "black",
                                    "weight": 2,
                                    "fillOpacity": 0.2
                               }
                ).add_to(m)

        if show_roads:
            shp_path = os.path.join("Streamwater_Line_Road_Network", "Main_Road.shp")
            gdf_roads = load_shapefile(shp_path)
            if gdf_roads is not None:
                folium.GeoJson(gdf_roads, name="Carreteras").add_to(m)

        if show_streams:
            shp_path = os.path.join("Streamwater_Line_Road_Network", "Streamwater.shp")
            gdf_streams = load_shapefile(shp_path)
            if gdf_streams is not None:
                folium.GeoJson(gdf_streams, name="Ríos").add_to(m)

        folium.LayerControl().add_to(m)
        st_folium(m, width=700, height=500)

    # ========================================================================
    # 2. TAB: Cobertura de Tierra (MODIS Land Cover)
    # ========================================================================
    with tabs[1]:
        st.markdown("### Cobertura de Tierra (MODIS Land Cover)")
        st.write("""
        Este dataset muestra la clasificación de la superficie terrestre según
        diversos tipos de cobertura (bosques, pastizales, zonas urbanas, etc.).
        Permite analizar cambios en el uso de la tierra y la evolución de las
        áreas vegetadas o urbanizadas a lo largo del tiempo.
        """)

        # Selección de año
        years_lc = list(range(2010, 2024))  # 2010 a 2023
        year_lc = st.selectbox("Selecciona año para Cobertura de Tierra:", years_lc, index=0)

        # Cargamos el ráster
        lc_path = os.path.join("Modis_Land_Cover_Data", f"{year_lc}LCT.tif")
        data_lc, profile_lc = load_raster(lc_path)

        if data_lc is not None:
            # Mostramos el mapa e histograma
            fig_map, fig_hist = plot_raster_and_hist(
                data_lc,
                title_map=f"Mapa de Cobertura de Tierra - {year_lc}",
                title_hist=f"Histograma de valores (Land Cover {year_lc})",
                colorbar_label="Land Cover"
            )

            # Dos columnas
            col1, col2 = st.columns([1.5, 1])
            with col1:
                st.plotly_chart(fig_map, use_container_width=True)
            with col2:
                st.plotly_chart(fig_hist, use_container_width=True)

            st.write("**Metadatos del ráster**")
            st.write(profile_lc)
        else:
            st.warning("No se pudo cargar el ráster de Cobertura de Tierra.")

    # ========================================================================
    # 3. TAB: Productividad Primaria (MODIS GPP)
    # ========================================================================
    with tabs[2]:
        st.markdown("### Productividad Primaria Bruta (GPP - MODIS)")
        st.write("""
        Los datos de **Gross Primary Production (GPP)** indican la tasa total a la
        cual las plantas acumulan carbono mediante la fotosíntesis. Sirve para
        entender la **salud de la vegetación** y su capacidad de absorber CO2.
        """)

        # Selección de año
        years_gpp = list(range(2010, 2024))
        year_gpp = st.selectbox("Selecciona año para GPP:", years_gpp, index=0)

        # Carga de ráster GPP
        gpp_path = os.path.join("MODIS_Gross_Primary_Production_GPP", f"{year_gpp}_GP.tif")
        data_gpp, profile_gpp = load_raster(gpp_path)

        if data_gpp is not None:
            fig_map_gpp, fig_hist_gpp = plot_raster_and_hist(
                data_gpp,
                title_map=f"Mapa GPP - {year_gpp}",
                title_hist=f"Histograma de GPP {year_gpp}",
                colorbar_label="GPP",
                bins=50
            )
            col1, col2 = st.columns([1.5, 1])
            with col1:
                st.plotly_chart(fig_map_gpp, use_container_width=True)
            with col2:
                st.plotly_chart(fig_hist_gpp, use_container_width=True)

            st.write("**Metadatos del ráster**")
            st.write(profile_gpp)
        else:
            st.warning(f"No se pudo cargar el ráster de GPP para {year_gpp}.")

    # ========================================================================
    # 4. TAB: Precipitación (Climate_Precipitation_Data)
    # ========================================================================
    with tabs[3]:
        st.markdown("### Precipitación (CHIRPS / Climate Data)")
        st.write("""
        El régimen de precipitaciones es crucial para la agricultura,
        la disponibilidad de agua y la dinámica de la vegetación en el Sahel.
        Aquí puedes visualizar datos de lluvia anual estimada para distintos años.
        """)

        years_prec = list(range(2010, 2024))
        year_prec = st.selectbox("Selecciona año para Precipitación:", years_prec, index=0)

        # Carga de ráster de precipitación
        prec_path = os.path.join("Climate_Precipitation_Data", f"{year_prec}R.tif")
        data_prec, profile_prec = load_raster(prec_path)

        if data_prec is not None:
            fig_map_prec, fig_hist_prec = plot_raster_and_hist(
                data_prec,
                title_map=f"Mapa de Precipitación - {year_prec}",
                title_hist=f"Histograma de Precipitación {year_prec}",
                colorbar_label="Precipitación",
                bins=50
            )
            col1, col2 = st.columns([1.5, 1])
            with col1:
                st.plotly_chart(fig_map_prec, use_container_width=True)
            with col2:
                st.plotly_chart(fig_hist_prec, use_container_width=True)

            st.write("**Metadatos del ráster**")
            st.write(profile_prec)
        else:
            st.warning(f"No se pudo cargar el ráster de precipitación para {year_prec}.")

    # ========================================================================
    # 5. TAB: Densidad Poblacional (Gridded_Population_Density_Data)
    # ========================================================================
    with tabs[4]:
        st.markdown("### Densidad de Población")
        st.write("""
        Esta capa muestra estimaciones de densidad poblacional en celdas de 1km.
        Permite analizar la presión demográfica sobre la tierra y los recursos.
        """)

        # Según los TIF existentes, hay años 2000, 2005, 2010, 2015, 2020
        years_pop = [2000, 2005, 2010, 2015, 2020]
        year_pop = st.selectbox("Selecciona año para Densidad Poblacional:", years_pop, index=2)

        # Nombre de archivo (por ejemplo: "mrt_pd_2010_1km.tif" segun tu estructura)
        pop_filename = f"mrt_pd_{year_pop}_1km.tif"
        pop_path = os.path.join("Gridded_Population_Density_Data", pop_filename)

        data_pop, profile_pop = load_raster(pop_path)

        if data_pop is not None:
            fig_map_pop, fig_hist_pop = plot_raster_and_hist(
                data_pop,
                title_map=f"Mapa de Densidad de Población - {year_pop}",
                title_hist=f"Histograma de Densidad {year_pop}",
                colorbar_label="Población (personas/km²)",
                bins=50
            )
            col1, col2 = st.columns([1.5, 1])
            with col1:
                st.plotly_chart(fig_map_pop, use_container_width=True)
            with col2:
                st.plotly_chart(fig_hist_pop, use_container_width=True)

            st.write("**Metadatos del ráster**")
            st.write(profile_pop)
        else:
            st.warning(f"No se pudo cargar el ráster de población para {year_pop}.")

# ----------------------------------------------------------------------------
# EJECUCIÓN
# ----------------------------------------------------------------------------
if __name__ == "__main__":
    main()
