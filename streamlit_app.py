import streamlit as st
import pandas as pd
import plotly.express as px
import requests

# 1. Configuración de la página
st.set_page_config(page_title="Dashboard Licores FND", layout="wide", page_icon="📊")

st.title("📊 Dashboard FND: Mercado Ilícito de Licores 2025")
st.markdown("Análisis geoespacial interactivo. *Nota: San Andrés ha sido reubicado visualmente para facilitar su lectura en el mapa nacional.*")

# 2. Cargar el mapa GeoJSON de Colombia y ACERCAR SAN ANDRÉS
@st.cache_data
def load_and_fix_geojson():
    url = "https://gist.githubusercontent.com/john-guerra/43c7656821069d00dcbc/raw/be6a6e239cd5b5b803c6e7c2ec405b793a9064dd/Colombia.geo.json"
    geojson = requests.get(url).json()
    
    # TRUCO CARTOGRÁFICO: Función recursiva para mover coordenadas
    def shift_coords(coords, lon_shift, lat_shift):
        if isinstance(coords[0], (int, float)):
            return [coords[0] + lon_shift, coords[1] + lat_shift]
        else:
            return [shift_coords(c, lon_shift, lat_shift) for c in coords]
            
    # Buscar San Andrés y moverlo más cerca de la costa continental
    for feature in geojson['features']:
        if feature['properties']['NOMBRE_DPT'] == 'ARCHIPIELAGO DE SAN ANDRES PROVIDENCIA Y SANTA CATALINA':
            # Sumamos +5.5 grados a la longitud (Este) y restamos -1.0 a la latitud (Sur)
            feature['geometry']['coordinates'] = shift_coords(feature['geometry']['coordinates'], 5.5, -1.0)
            
    return geojson

colombia_geojson = load_and_fix_geojson()

# 3. Cargar y procesar los datos desde tu archivo Excel
@st.cache_data
def load_data():
    df = pd.read_excel("Base_Datos_Licores_Zonas.xlsx")
    
    # Convertir a porcentaje (0 - 100)
    df["Adulteración (%)"] = df["Adulteración"] * 100
    df["Contrabando (%)"] = df["Contrabando"] * 100
    
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
df_promedios = df.groupby("Zona")[["Adulteración (%)", "Contrabando (%)"]].mean().reset_index()
df_mapa = pd.merge(df[["Departamento", "DPT_GEOJSON", "Zona"]], df_promedios, on="Zona", how="left")

# 5. Menú lateral (Sidebar) interactivo
st.sidebar.header("Configuración del Mapa")
metrica_seleccionada = st.sidebar.radio(
    "Selecciona el indicador:",
    ["Adulteración (%)", "Contrabando (%)"]
)

escala_color = "YlOrRd" if metrica_seleccionada == "Adulteración (%)" else "YlGnBu"

# 6. CREAR EL MAPA ÚNICO (Con San Andrés ya acercado)
fig = px.choropleth(
    df_mapa,
    geojson=colombia_geojson,
    featureidkey="properties.NOMBRE_DPT",
    locations="DPT_GEOJSON",
    color=metrica_seleccionada,
    color_continuous_scale=escala_color,
    range_color=(0, df_promedios[metrica_seleccionada].max() + 2),
    hover_name="Zona",
    hover_data={"DPT_GEOJSON": False, "Departamento": True, metrica_seleccionada: ':.2f'}
)

# Ocultar el mapa base del mundo y auto-encuadrar
fig.update_geos(visible=False, fitbounds="locations")
fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})

# 7. Disposición visual en la pantalla
col1, col2 = st.columns([2.5, 1])

with col1:
    st.markdown(f"### Mapa de Calor Promedio: {metrica_seleccionada}")
    # Al graficar, Plotly automáticamente hará zoom y San Andrés aparecerá grande al lado de la costa
    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.markdown("### Promedios por Zona")
    st.dataframe(df_promedios.style.format({
        "Adulteración (%)": "{:.2f}%",
        "Contrabando (%)": "{:.2f}%"
    }), hide_index=True, use_container_width=True)
    
st.markdown("---")
st.markdown("### Base de Datos Detallada")
st.dataframe(df.drop(columns=["DPT_GEOJSON"]).style.format({
    "Adulteración": "{:.2%}",
    "Contrabando": "{:.2%}",
    "Adulteración (%)": "{:.2f}%",
    "Contrabando (%)": "{:.2f}%"
}), use_container_width=True)
