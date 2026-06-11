import streamlit as st
import pandas as pd
import plotly.express as px
import requests

# 1. Configuración de la página
st.set_page_config(page_title="Dashboard Licores FND", layout="wide", page_icon="📊")

st.title("📊 Dashboard FND: Mercado Ilícito de Licores 2025")
st.markdown("Análisis geoespacial interactivo basado en los promedios por zonas de la Federación Nacional de Departamentos.")

# 2. Cargar el mapa GeoJSON de Colombia
@st.cache_data
def load_geojson():
    url = "https://gist.githubusercontent.com/john-guerra/43c7656821069d00dcbc/raw/be6a6e239cd5b5b803c6e7c2ec405b793a9064dd/Colombia.geo.json"
    return requests.get(url).json()

colombia_geojson = load_geojson()

# 3. Cargar y procesar los datos desde tu archivo Excel
@st.cache_data
def load_data():
    # Leer el Excel que está en tu repositorio GitHub
    df = pd.read_excel("Base_Datos_Licores_Zonas.xlsx")
    
    # Convertir las métricas a porcentaje (0 - 100) para mejor visualización
    df["Adulteración (%)"] = df["Adulteración"] * 100
    df["Contrabando (%)"] = df["Contrabando"] * 100
    
    # Diccionario para homologar los nombres de tu Excel con las fronteras del GeoJSON
    mapeo_nombres = {
        "Antioquia": "ANTIOQUIA", "Atlántico": "ATLANTICO", "Bogotá D.C.": "SANTAFE DE BOGOTA D.C",
        "Bolívar": "BOLIVAR", "Boyacá": "BOYACA", "Caldas": "CALDAS", "Caquetá": "CAQUETA",
        "Cauca": "CAUCA", "Cesar": "CESAR", "Córdoba": "CORDOBA", "Cundinamarca": "CUNDINAMARCA",
        "Chocó": "CHOCO", "Huila": "HUILA", "La Guajira": "LA GUAJIRA", "Magdalena": "MAGDALENA",
        "Meta": "META", "Nariño": "NARIÑO", "Nte. Santander": "NORTE DE SANTANDER", 
        "Quindío": "QUINDIO", "Risaralda": "RISARALDA", "Santander": "SANTANDER", 
        "Sucre": "SUCRE", "Tolima": "TOLIMA", "Valle del Cauca": "VALLE DEL CAUCA",
        "Arauca": "ARAUCA", "Casanare": "CASANARE", "Putumayo": "PUTUMAYO",
        "San Andrés": "ARCHIPIELAGO DE SAN ANDRES PROVIDENCIA Y SANTA CATALINA",
        "Amazonas": "AMAZONAS", "Guainía": "GUAINIA", "Guaviare": "GUAVIARE",
        "Vaupés": "VAUPES", "Vichada": "VICHADA"
    }
    df["DPT_GEOJSON"] = df["Departamento"].map(mapeo_nombres)
    return df

df = load_data()

# 4. Calcular el promedio por ZONA
# Esto es vital para que todos los departamentos de una zona se pinten del mismo color
df_promedios = df.groupby("Zona")[["Adulteración (%)", "Contrabando (%)"]].mean().reset_index()

# Unimos los promedios calculados con los departamentos para graficarlos
df_mapa = pd.merge(df[["Departamento", "DPT_GEOJSON", "Zona"]], df_promedios, on="Zona", how="left")

# 5. Menú lateral (Sidebar) interactivo
st.sidebar.image("https://upload.wikimedia.org/wikipedia/commons/thumb/c/c5/Escudo_de_Colombia.svg/120px-Escudo_de_Colombia.svg.png", width=80)
st.sidebar.header("Configuración")
metrica_seleccionada = st.sidebar.radio(
    "Selecciona el indicador a visualizar:",
    ["Adulteración (%)", "Contrabando (%)"]
)

# Definir la escala de colores (Rojo/Amarillo para Adulteración, Azul/Amarillo para Contrabando)
escala_color = "YlOrRd" if metrica_seleccionada == "Adulteración (%)" else "YlGnBu"

# 6. Crear el mapa interactivo con Plotly
fig = px.choropleth_mapbox(
    df_mapa,
    geojson=colombia_geojson,
    featureidkey="properties.NOMBRE_DPT",
    locations="DPT_GEOJSON",
    color=metrica_seleccionada,
    color_continuous_scale=escala_color,
    range_color=(0, df_promedios[metrica_seleccionada].max() + 2), # Ajuste automático del rango
    mapbox_style="carto-positron",
    zoom=4.5,
    center={"lat": 4.5709, "lon": -74.2973},
    opacity=0.85,
    hover_name="Zona",
    hover_data={"DPT_GEOJSON": False, "Departamento": True, metrica_seleccionada: ':.2f'}
)

fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})

# 7. Disposición en la pantalla (Columnas)
col1, col2 = st.columns([2.5, 1])

with col1:
    st.markdown(f"### Mapa de Calor Promedio: {metrica_seleccionada}")
    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.markdown("### Promedios por Zona")
    st.dataframe(df_promedios.style.format({
        "Adulteración (%)": "{:.2f}%",
        "Contrabando (%)": "{:.2f}%"
    }), hide_index=True, use_container_width=True)
    
    st.info("💡 **Nota interactiva:** Al pasar el ratón por el mapa, verás a qué departamento y zona pertenece cada región.")

st.markdown("---")
st.markdown("### Base de Datos Detallada (Extraída del Excel)")
st.dataframe(df.drop(columns=["DPT_GEOJSON"]).style.format({
    "Adulteración": "{:.2%}",
    "Contrabando": "{:.2%}",
    "Adulteración (%)": "{:.2f}%",
    "Contrabando (%)": "{:.2f}%"
}), use_container_width=True)