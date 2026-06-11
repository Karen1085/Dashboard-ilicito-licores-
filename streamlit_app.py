import streamlit as st
import pandas as pd
import plotly.express as px
import requests

# 1. Configuración de la página
st.set_page_config(page_title="Dashboard Licores FND", layout="wide", page_icon="📊")

st.title("📊 Dashboard FND: Mercado Ilícito de Licores 2025")
st.markdown("Análisis geoespacial interactivo enfocado exclusivamente en el territorio colombiano.")

# 2. Cargar el mapa GeoJSON de Colombia
@st.cache_data
def load_geojson():
    url = "https://gist.githubusercontent.com/john-guerra/43c7656821069d00dcbc/raw/be6a6e239cd5b5b803c6e7c2ec405b793a9064dd/Colombia.geo.json"
    return requests.get(url).json()

colombia_geojson = load_geojson()

# 3. Cargar y procesar los datos
@st.cache_data
def load_data():
    df = pd.read_excel("Base_Datos_Licores_Zonas.xlsx")
    
    # Convertir a porcentaje
    df["Adulteración (%)"] = df["Adulteración"] * 100
    df["Contrabando (%)"] = df["Contrabando"] * 100
    
    # Homologación exacta
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

# 4. Calcular promedios por Zona
df_promedios = df.groupby("Zona")[["Adulteración (%)", "Contrabando (%)"]].mean().reset_index()
df_mapa = pd.merge(df[["Departamento", "DPT_GEOJSON", "Zona"]], df_promedios, on="Zona", how="left")

# --- TRUCO: SEPARAR CONTINENTE Y SAN ANDRÉS ---
df_continente = df_mapa[df_mapa["Departamento"] != "San Andrés"]
df_san_andres = df_mapa[df_mapa["Departamento"] == "San Andrés"]

# 5. Menú lateral (Sidebar)
st.sidebar.header("Filtros del Mapa")
metrica_seleccionada = st.sidebar.radio(
    "Selecciona el indicador:",
    ["Adulteración (%)", "Contrabando (%)"]
)

escala_color = "YlOrRd" if metrica_seleccionada == "Adulteración (%)" else "YlGnBu"
rango_colores = (0, df_promedios[metrica_seleccionada].max() + 2)

# 6. CREACIÓN DEL MAPA PRINCIPAL (CONTINENTE)
fig_main = px.choropleth(
    df_continente,
    geojson=colombia_geojson,
    featureidkey="properties.NOMBRE_DPT",
    locations="DPT_GEOJSON",
    color=metrica_seleccionada,
    color_continuous_scale=escala_color,
    range_color=rango_colores,
    hover_name="Zona",
    hover_data={"DPT_GEOJSON": False, "Departamento": True, metrica_seleccionada: ':.2f'}
)
fig_main.update_geos(visible=False, fitbounds="locations")
fig_main.update_layout(margin={"r":0,"t":0,"l":0,"b":0})

# 7. CREACIÓN DEL MAPA LUPA (SAN ANDRÉS)
fig_sa = px.choropleth(
    df_san_andres,
    geojson=colombia_geojson,
    featureidkey="properties.NOMBRE_DPT",
    locations="DPT_GEOJSON",
    color=metrica_seleccionada,
    color_continuous_scale=escala_color,
    range_color=rango_colores,
    hover_name="Zona",
    hover_data={"DPT_GEOJSON": False, "Departamento": True, metrica_seleccionada: ':.2f'}
)
fig_sa.update_geos(visible=False, fitbounds="locations")
# Ocultamos la leyenda en la lupa para ahorrar espacio
fig_sa.update_layout(margin={"r":0,"t":0,"l":0,"b":0}, coloraxis_showscale=False, height=250)

# 8. Disposición en la pantalla
col1, col2 = st.columns([2.5, 1])

with col1:
    st.markdown(f"### Mapa por Zonas: {metrica_seleccionada}")
    st.plotly_chart(fig_main, use_container_width=True)

with col2:
    # Mostramos la lupa de San Andrés justo arriba de los datos
    st.markdown("### 🏝️ Lupa: San Andrés")
    st.plotly_chart(fig_sa, use_container_width=True)
    
    st.markdown("### Promedios por Zona")
    st.dataframe(df_promedios.style.format({
        "Adulteración (%)": "{:.2f}%",
        "Contrabando (%)": "{:.2f}%"
    }), hide_index=True, use_container_width=True)

st.markdown("---")
st.markdown("### Base de Datos Completa")
st.dataframe(df.drop(columns=["DPT_GEOJSON"]).style.format({
    "Adulteración": "{:.2%}",
    "Contrabando": "{:.2%}",
    "Adulteración (%)": "{:.2f}%",
    "Contrabando (%)": "{:.2f}%"
}), use_container_width=True)
