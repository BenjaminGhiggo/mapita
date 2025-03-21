import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import time

# --------------------------------------------------------------------------------
# EJEMPLOS DE LLAMADAS A APIS Y DATOS OPEN SOURCE (placeholder)
# Nota: Estas funciones usan endpoints ficticios o reales de ejemplo.
#       Ajusta las URLs y la lógica según tus credenciales y endpoints disponibles.
# --------------------------------------------------------------------------------

def get_nasa_land_cover(year=2021):
    """
    Ejemplo de función para "simular" la obtención de datos de cobertura
    de tierra desde NASA EarthData o GEE. Aquí se usa un placeholder.
    """
    # EJEMPLO de solicitud GET (URL ficticia):
    # url = f"https://api.nasa.gov/earth/landcover/{year}?api_key=TU_API_KEY"
    # r = requests.get(url)
    # data_json = r.json()
    # En este placeholder simulamos un DataFrame
    time.sleep(1)  # Simula latencia
    df_placeholder = pd.DataFrame({
        "lat": [14.5, 14.6, 14.7],
        "lon": [-10.2, -10.3, -10.4],
        "land_cover_class": [1, 2, 2],
        "valor": [0.6, 0.8, 0.75]
    })
    return df_placeholder

def get_openweather_forecast(lat=14.5, lon=-10.2):
    """
    Ejemplo de función para "simular" la obtención de pronóstico climático.
    Placeholder con datos ficticios usando API de OpenWeatherMap.
    """
    # url = f"http://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&appid=TU_API_KEY"
    # r = requests.get(url)
    # data_json = r.json()
    # ...
    time.sleep(1)  # Simula latencia
    df_placeholder = pd.DataFrame({
        "fecha": pd.date_range("2025-01-01", periods=5, freq="D"),
        "temp_c": [35, 36, 34, 37, 35],
        "precip_mm": [2, 0, 5, 0, 10],
    })
    return df_placeholder

def get_fao_data_soil():
    """
    Ejemplo de función para "simular" la obtención de datos de suelos
    desde la FAO. Placeholder con datos ficticios.
    """
    # url = "https://data.apps.fao.org/api/v1/soildata"
    # r = requests.get(url)
    # data_json = r.json()
    time.sleep(1)
    df_placeholder = pd.DataFrame({
        "region": ["Assaba", "Brakna", "Gorgol"],
        "soil_quality_index": [0.72, 0.66, 0.8]
    })
    return df_placeholder

def get_population_data():
    """
    Ejemplo de función para "simular" la obtención de datos de población
    usando un endpoint de ONU, WorldPop, etc. Placeholder.
    """
    # url = "http://worldpop.org/api/some_endpoint"
    # r = requests.get(url)
    # data_json = r.json()
    time.sleep(1)
    df_placeholder = pd.DataFrame({
        "year": [2020, 2025, 2030],
        "population_estimate": [1200000, 1400000, 1600000]
    })
    return df_placeholder


# --------------------------------------------------------------------------------
# MÓDULOS
# --------------------------------------------------------------------------------

def modulo_monitoreo_inteligente():
    st.subheader("1️⃣ Módulo de Monitoreo Inteligente y Predicción Climática")
    st.write("Cargando datos de NASA (placeholder)...")
    df_lc = get_nasa_land_cover(year=2021)
    st.write("Ejemplo de datos de coberturas de tierra:")
    st.dataframe(df_lc)

    st.write("Cargando pronóstico del tiempo (placeholder)...")
    df_forecast = get_openweather_forecast()
    st.write("Ejemplo de datos de pronóstico climático:")
    st.dataframe(df_forecast)

    st.write("Visualización simple de temperatura vs. fecha:")
    fig = px.line(df_forecast, x="fecha", y="temp_c", title="Temperatura Pronosticada (°C)")
    st.plotly_chart(fig, use_container_width=True)


def modulo_accion_comunitaria():
    st.subheader("2️⃣ Módulo de Acción Comunitaria y Gamificación")
    st.write("Ejemplo de lógicas de 'Misiones de Restauración' e incentivos (placeholder).")
    st.markdown("""- Misiones semanales (plantar árboles, mejorar retención de agua).
- Sistema de puntos y recompensas.
- Leaderboards para comunidades.""")

    st.write("Simulación: Tabla de 'Puntos' por usuario:")
    df_points = pd.DataFrame({
        "Usuario": ["Aicha", "Moussa", "Fatima", "Amadou"],
        "Árboles Plantados": [20, 5, 15, 10],
        "Puntos": [200, 50, 150, 100]
    })
    st.dataframe(df_points)

    fig = px.bar(df_points, x="Usuario", y="Puntos", title="Puntos de Gamificación")
    st.plotly_chart(fig, use_container_width=True)


def modulo_capacitacion():
    st.subheader("3️⃣ Módulo de Capacitación y Conocimiento Comunitario")
    st.write("Ejemplo de acceso a datos de FAO (placeholder).")
    df_soil = get_fao_data_soil()
    st.write("Calidad de suelos (índice) en distintas regiones:")
    st.dataframe(df_soil)

    fig = px.bar(df_soil, x="region", y="soil_quality_index",
                 title="Índice de Calidad de Suelos (Ejemplo)")
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("""### Ejemplo de plataforma de aprendizaje
- Asistente de voz (WhatsApp o SMS).
- Videos educativos offline.
- Mentores locales con experiencia práctica.
""")


def modulo_economia_circular():
    st.subheader("4️⃣ Módulo de Economía Circular y Monetización Verde")
    st.write("Ejemplo: usando datos de población (placeholder) para estimar mercados.")
    df_pop = get_population_data()
    st.dataframe(df_pop)

    fig = px.line(df_pop, x="year", y="population_estimate", title="Proyección de Población")
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("""
    - Créditos y préstamos verdes verificados con datos satelitales.
    - Tokenización de impacto ambiental.
    - Conexión con mercados globales (productos ecológicos).
    """)


# --------------------------------------------------------------------------------
# MAIN
# --------------------------------------------------------------------------------

def main():
    st.title("Implementación de Módulos con APIs y Datos Open Source (Placeholder)")

    st.markdown("""
    Este panel demuestra una **implementación** básica de los 4 módulos
    para el Sahel, utilizando llamadas a APIs y datos abiertos (simulados).
    Usa las pestañas de abajo para navegar.
    """)

    tabs = st.tabs([
        "Módulo 1: Monitoreo Inteligente",
        "Módulo 2: Acción Comunitaria",
        "Módulo 3: Capacitación",
        "Módulo 4: Economía Circular"
    ])

    with tabs[0]:
        modulo_monitoreo_inteligente()

    with tabs[1]:
        modulo_accion_comunitaria()

    with tabs[2]:
        modulo_capacitacion()

    with tabs[3]:
        modulo_economia_circular()

if __name__ == "__main__":
    main()
