#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Aplicación interactiva utilizando Google Earth Engine, geemap y Streamlit

Descripción General:
--------------------
Esta aplicación te permite:
  - **Definir una Región de Interés (ROI):** Usa el mapa interactivo para dibujar el área que deseas analizar.
  - **Analizar series de tiempo:** Visualiza la evolución de variables ambientales (GPP, NDVI o Precipitación) en la ROI seleccionada.
  - **Comparar períodos:** Compara dos intervalos de tiempo para identificar cambios o tendencias en las variables.

Cada sección tiene un propósito específico:
  - **Mapa Interactivo:** Permite dibujar la ROI y descargar el mapa en HTML.
  - **Análisis de Datos (Serie de Tiempo):** Genera un gráfico de serie de tiempo que muestra la evolución temporal de la variable seleccionada.  
    *El gráfico de serie de tiempo sirve para visualizar tendencias y patrones en los datos a lo largo del tiempo.*
  - **Comparativa de Períodos:** Compara los datos de dos intervalos de tiempo mediante gráficos comparativos.  
    *El gráfico comparativo facilita identificar diferencias y cambios significativos entre dos períodos distintos.*

Para ejecutar la aplicación, guarda este código en un archivo (por ejemplo, `app.py`) y ejecuta:
    streamlit run app.py
"""

import os
import sys
import types
import logging
from datetime import datetime

import ee
import streamlit as st
import geemap.foliumap as geemap  # Usamos geemap basado en folium para la visualización del mapa
import pandas as pd
import matplotlib.pyplot as plt

# Configuración de logging:
# Se configuran mensajes de log para la consola y un archivo (app.log)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("app.log")
    ]
)
logging.info("Iniciando la aplicación...")

# Parche para compatibilidad con Python 3 (módulos que esperan StringIO de Python 2)
if sys.version_info.major >= 3:
    import io
    sys.modules["StringIO"] = io

# Parche para módulos específicos de Unix en Windows
if os.name == 'nt':
    try:
        # Se crea un módulo ficticio para fcntl
        fcntl = types.ModuleType("fcntl")
        fcntl.ioctl = lambda fd, op, arg: None
        sys.modules["fcntl"] = fcntl

        # Se crea un módulo ficticio para termios
        termios = types.ModuleType("termios")
        termios.TIOCGWINSZ = 0  # Valor dummy
        sys.modules["termios"] = termios
        logging.info("Parche de módulos Unix aplicado en Windows.")
    except Exception as e:
        logging.exception("Error al aplicar parches para módulos Unix en Windows: %s", e)

# Función para inicializar la API de Google Earth Engine.
@st.cache_resource(show_spinner=False)
def init_ee():
    try:
        logging.info("Autenticando con Earth Engine...")
        ee.Authenticate()  # Se abrirá una URL para autenticarse
        ee.Initialize(project='ivanti-453315')
        logging.info("Autenticación e inicialización completadas.")
    except Exception as e:
        logging.exception("Error durante la autenticación/inicialización: %s", e)
        st.error("Error al autenticar/inicializar Earth Engine. Revisa los logs.")
        raise e

# Inicializar Earth Engine
init_ee()

# Título principal y descripción para la vista web
st.title("Aplicación Interactiva: Análisis Espacial con Earth Engine")
st.write("""
Esta aplicación te permite:
- **Definir una Región de Interés (ROI):** Utiliza el mapa interactivo para dibujar el área que deseas analizar.
- **Analizar variables ambientales:** Visualiza series de tiempo de GPP, NDVI o Precipitación en la ROI seleccionada.
- **Comparar períodos:** Observa la evolución de las variables en dos intervalos de tiempo distintos.

**Descripción de los gráficos:**
- **Serie de Tiempo:** Muestra cómo evoluciona la variable seleccionada a lo largo del tiempo. Es útil para identificar tendencias, patrones y anomalías.
- **Gráfico Comparativo:** Permite contrastar dos períodos de tiempo para detectar cambios significativos o diferencias en el comportamiento de la variable.
""")

# Sidebar para la navegación entre secciones
opcion = st.sidebar.selectbox("Selecciona una sección", ["Mapa Interactivo", "Análisis de Datos", "Comparativa de Períodos"])

# Variable para almacenar las coordenadas de la ROI en session_state
if 'roi_coords' not in st.session_state:
    st.session_state['roi_coords'] = None

def get_drawn_roi():
    """
    Obtiene la geometría de la ROI dibujada en el mapa.
    Retorna un objeto ee.Geometry.Polygon basado en las coordenadas guardadas.
    Si no se ha definido ninguna ROI, retorna None.
    """
    if st.session_state['roi_coords'] is not None:
        coords = st.session_state['roi_coords']
        try:
            roi = ee.Geometry.Polygon(coords)
            return roi
        except Exception as ex:
            st.error("Error al crear la ROI con las coordenadas.")
            logging.exception("Error al crear ROI: %s", ex)
    return None

# -----------------------------------------------------------------------------
# Sección 1: Mapa Interactivo
# -----------------------------------------------------------------------------
if opcion == "Mapa Interactivo":
    st.header("Mapa Interactivo: Dibuja tu Región de Interés (ROI)")
    st.write("""
    En esta sección, puedes usar la herramienta de dibujo para definir el área que deseas analizar.
    Una vez dibujada, presiona **Guardar ROI** para que las demás secciones utilicen esta región en sus análisis.
    """)
    try:
        # Crear y mostrar el mapa interactivo
        Map = geemap.Map()
        Map.setCenter(19, 33, 5)
        Map.add_basemap("HYBRID")
        Map.add_draw_control()  # Herramienta para dibujar la ROI
        Map.to_streamlit(height=500)
        
        # Botón para guardar la ROI
        if st.button("Guardar ROI"):
            drawn_features = Map.get_drawn_features()
            if drawn_features:
                # Se asume que el primer polígono es la ROI
                coords = drawn_features[0]['geometry']['coordinates']
                st.session_state['roi_coords'] = coords
                st.success("ROI guardada correctamente.")
                logging.info("ROI guardada: %s", coords)
            else:
                st.warning("No se detectó ninguna ROI. Dibuja un polígono en el mapa.")
        
        # Opción para descargar el mapa en formato HTML
        try:
            map_html = Map.to_html()
            st.download_button(
                label="Descargar Mapa (HTML)",
                data=map_html,
                file_name="mapa_interactivo.html",
                mime="text/html"
            )
            logging.info("Botón para descargar el mapa HTML agregado.")
        except Exception as e:
            logging.exception("Error al generar HTML del mapa: %s", e)
            st.error("No se pudo generar el HTML del mapa para descarga.")
    except Exception as e:
        logging.exception("Error en el mapa interactivo: %s", e)
        st.error("Error al mostrar el mapa interactivo.")

# -----------------------------------------------------------------------------
# Sección 2: Análisis de Datos (Serie de Tiempo)
# -----------------------------------------------------------------------------
elif opcion == "Análisis de Datos":
    st.header("Análisis de Datos: Serie de Tiempo")
    st.write("""
    En esta sección podrás analizar la evolución temporal de una variable ambiental.
    
    **Pasos:**
    1. Selecciona el rango de fechas.
    2. Escoge la variable que deseas analizar (GPP, NDVI o Precipitación).
    3. Ejecuta el análisis para visualizar una **Serie de Tiempo** que muestra cómo varía la variable en la ROI.
    
    **¿Para qué sirve este gráfico?**
    - El gráfico de serie de tiempo te ayuda a identificar tendencias, patrones estacionales y anomalías en los datos.
    - Es fundamental para entender cómo se comporta una variable ambiental a lo largo de los años.
    """)
    
    # Selección de fechas y variable
    start_date = st.date_input("Fecha de inicio", datetime(2010, 1, 1))
    end_date = st.date_input("Fecha de fin", datetime(2020, 12, 31))
    if start_date > end_date:
        st.error("La fecha de inicio debe ser anterior a la fecha de fin.")
    
    variable = st.selectbox("Selecciona variable", ["GPP (MODIS)", "NDVI (MODIS)", "Precipitación (CHIRPS)"])
    
    if st.button("Ejecutar Análisis"):
        st.info("Procesando datos...")
        start_str = start_date.strftime('%Y-%m-%d')
        end_str = end_date.strftime('%Y-%m-%d')
        
        # Se obtiene la ROI definida por el usuario o se usa una ROI por defecto
        roi = get_drawn_roi()
        if roi is None:
            st.warning("No se ha definido una ROI. Se usará una región por defecto.")
            roi = ee.Geometry.Rectangle([-16.0, 16.0, -14.0, 18.0])
        
        try:
            features = None
            if variable == "GPP (MODIS)":
                collection = ee.ImageCollection('MODIS/006/MOD17A2H').filterDate(start_str, end_str).filterBounds(roi)
                def compute_mean_gpp(image):
                    mean_dict = image.reduceRegion(
                        reducer=ee.Reducer.mean(),
                        geometry=roi,
                        scale=500,
                        maxPixels=1e9
                    )
                    mean_gpp = mean_dict.get('Gpp')
                    date = image.get('system:time_start')
                    return ee.Feature(None, {'date': date, 'value': mean_gpp})
                features = collection.map(compute_mean_gpp).filter(ee.Filter.notNull(['value']))
            elif variable == "NDVI (MODIS)":
                collection = ee.ImageCollection("MODIS/006/MOD13A2").filterDate(start_str, end_str).filterBounds(roi)
                def compute_mean_ndvi(image):
                    mean_dict = image.reduceRegion(
                        reducer=ee.Reducer.mean(),
                        geometry=roi,
                        scale=500,
                        maxPixels=1e9
                    )
                    mean_ndvi = mean_dict.get('NDVI')
                    date = image.get('system:time_start')
                    return ee.Feature(None, {'date': date, 'value': mean_ndvi})
                features = collection.map(compute_mean_ndvi).filter(ee.Filter.notNull(['value']))
            elif variable == "Precipitación (CHIRPS)":
                collection = ee.ImageCollection("UCSB-CHG/CHIRPS/DAILY").filterDate(start_str, end_str).filterBounds(roi)
                def compute_mean_precip(image):
                    mean_dict = image.reduceRegion(
                        reducer=ee.Reducer.mean(),
                        geometry=roi,
                        scale=5000,
                        maxPixels=1e9
                    )
                    mean_precip = mean_dict.get('precipitation')
                    date = image.get('system:time_start')
                    return ee.Feature(None, {'date': date, 'value': mean_precip})
                features = collection.map(compute_mean_precip).filter(ee.Filter.notNull(['value']))
            
            # Procesamiento de los datos obtenidos
            features_info = features.getInfo()
            features_list = features_info.get('features', [])
            if not features_list:
                st.warning("No se encontraron datos para el rango de fechas y la ROI seleccionada.")
            else:
                dates = []
                values = []
                for f in features_list:
                    props = f['properties']
                    timestamp = props['date']
                    date_dt = pd.to_datetime(timestamp, unit='ms')
                    dates.append(date_dt)
                    values.append(props['value'])
                df = pd.DataFrame({'Fecha': dates, 'Valor': values})
                df.sort_values('Fecha', inplace=True)
                st.subheader(f"Serie de Tiempo - {variable}")
                st.dataframe(df)
                
                # Gráfico de Serie de Tiempo
                fig, ax = plt.subplots(figsize=(10, 6))
                ax.plot(df['Fecha'], df['Valor'], marker='o', linestyle='-')
                ax.set_xlabel('Fecha')
                ax.set_ylabel(variable)
                ax.set_title(f'Serie de Tiempo: {variable}')
                ax.grid(True)
                st.pyplot(fig)
                
                # Botón para descargar los datos en CSV
                csv = df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="Descargar CSV",
                    data=csv,
                    file_name=f"{variable.replace(' ', '_')}_timeseries.csv",
                    mime='text/csv'
                )
                st.success("Análisis completado.")
        except Exception as e:
            logging.exception("Error en el análisis de datos: %s", e)
            st.error("Error en el análisis. Revisa los logs.")

# -----------------------------------------------------------------------------
# Sección 3: Comparativa de Períodos
# -----------------------------------------------------------------------------
elif opcion == "Comparativa de Períodos":
    st.header("Comparativa de Períodos: Análisis Comparativo")
    st.write("""
    En esta sección podrás comparar la evolución de las variables ambientales en dos intervalos de tiempo distintos.
    
    **Pasos:**
    1. Define dos períodos (Período 1 y Período 2) mediante la selección de fechas.
    2. Selecciona las variables que deseas comparar.
    3. Ejecuta el análisis para visualizar gráficos comparativos que muestren cómo varió la variable en ambos períodos.
    
    **¿Para qué sirve el gráfico comparativo?**
    - Este gráfico te permite contrastar visualmente las tendencias entre dos intervalos, ayudándote a detectar cambios significativos o patrones diferenciales.
    """)
    
    # Definir dos períodos
    st.subheader("Período 1")
    start_date1 = st.date_input("Fecha de inicio (Período 1)", datetime(2010, 1, 1), key="start1")
    end_date1   = st.date_input("Fecha de fin (Período 1)", datetime(2015, 12, 31), key="end1")
    
    st.subheader("Período 2")
    start_date2 = st.date_input("Fecha de inicio (Período 2)", datetime(2016, 1, 1), key="start2")
    end_date2   = st.date_input("Fecha de fin (Período 2)", datetime(2020, 12, 31), key="end2")
    
    # Selección de variables para comparar
    variables = st.multiselect("Selecciona variables para comparar", ["GPP (MODIS)", "NDVI (MODIS)"], default=["GPP (MODIS)", "NDVI (MODIS)"])
    
    if st.button("Comparar Períodos"):
        st.info("Procesando comparación...")
        start_str1 = start_date1.strftime('%Y-%m-%d')
        end_str1   = end_date1.strftime('%Y-%m-%d')
        start_str2 = start_date2.strftime('%Y-%m-%d')
        end_str2   = end_date2.strftime('%Y-%m-%d')
        
        roi = get_drawn_roi()
        if roi is None:
            st.warning("No se ha definido una ROI. Se usará una región por defecto.")
            roi = ee.Geometry.Rectangle([-16.0, 16.0, -14.0, 18.0])
        
        results = {}
        for var in variables:
            if var == "GPP (MODIS)":
                collection1 = ee.ImageCollection('MODIS/006/MOD17A2H').filterDate(start_str1, end_str1).filterBounds(roi)
                collection2 = ee.ImageCollection('MODIS/006/MOD17A2H').filterDate(start_str2, end_str2).filterBounds(roi)
                def compute_mean(image):
                    mean_dict = image.reduceRegion(
                        reducer=ee.Reducer.mean(),
                        geometry=roi,
                        scale=500,
                        maxPixels=1e9
                    )
                    value = mean_dict.get('Gpp')
                    date = image.get('system:time_start')
                    return ee.Feature(None, {'date': date, 'value': value})
                features1 = collection1.map(compute_mean).filter(ee.Filter.notNull(['value']))
                features2 = collection2.map(compute_mean).filter(ee.Filter.notNull(['value']))
            elif var == "NDVI (MODIS)":
                collection1 = ee.ImageCollection("MODIS/006/MOD13A2").filterDate(start_str1, end_str1).filterBounds(roi)
                collection2 = ee.ImageCollection("MODIS/006/MOD13A2").filterDate(start_str2, end_str2).filterBounds(roi)
                def compute_mean(image):
                    mean_dict = image.reduceRegion(
                        reducer=ee.Reducer.mean(),
                        geometry=roi,
                        scale=500,
                        maxPixels=1e9
                    )
                    value = mean_dict.get('NDVI')
                    date = image.get('system:time_start')
                    return ee.Feature(None, {'date': date, 'value': value})
                features1 = collection1.map(compute_mean).filter(ee.Filter.notNull(['value']))
                features2 = collection2.map(compute_mean).filter(ee.Filter.notNull(['value']))
            
            # Extraer y procesar los datos para cada período
            features_info1 = features1.getInfo()
            features_info2 = features2.getInfo()
            features_list1 = features_info1.get('features', [])
            features_list2 = features_info2.get('features', [])
            
            df1, df2 = None, None
            if features_list1:
                dates1 = []
                values1 = []
                for f in features_list1:
                    props = f['properties']
                    timestamp = props['date']
                    date_dt = pd.to_datetime(timestamp, unit='ms')
                    dates1.append(date_dt)
                    values1.append(props['value'])
                df1 = pd.DataFrame({'Fecha': dates1, var: values1})
                df1.sort_values('Fecha', inplace=True)
            if features_list2:
                dates2 = []
                values2 = []
                for f in features_list2:
                    props = f['properties']
                    timestamp = props['date']
                    date_dt = pd.to_datetime(timestamp, unit='ms')
                    dates2.append(date_dt)
                    values2.append(props['value'])
                df2 = pd.DataFrame({'Fecha': dates2, var: values2})
                df2.sort_values('Fecha', inplace=True)
            results[var] = (df1, df2)
        
        # Mostrar resultados y graficar la comparación para cada variable
        for var, (df1, df2) in results.items():
            st.subheader(f"Comparación: {var}")
            if df1 is not None and df2 is not None:
                st.write("**Período 1:**")
                st.dataframe(df1)
                st.write("**Período 2:**")
                st.dataframe(df2)
                
                # Gráfico Comparativo: Muestra las tendencias en ambos períodos para la variable seleccionada.
                fig, ax = plt.subplots(figsize=(10, 6))
                if df1 is not None:
                    ax.plot(df1['Fecha'], df1[var], marker='o', linestyle='-', label='Período 1')
                if df2 is not None:
                    ax.plot(df2['Fecha'], df2[var], marker='s', linestyle='--', label='Período 2')
                ax.set_xlabel('Fecha')
                ax.set_ylabel(var)
                ax.set_title(f'Comparación de {var} entre Períodos')
                ax.legend()
                ax.grid(True)
                st.pyplot(fig)
            else:
                st.warning(f"No se encontraron datos para {var}.")
        
        st.success("Comparación completada.")
