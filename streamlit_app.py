import streamlit as st
import pandas as pd
import plotly.express as px
import requests

# 1. Configuración de la página
st.set_page_config(page_title="Dashboard Licores FND", layout="wide", page_icon="📊")

st.title("📊 Dashboard FND: Mercado Ilícito de Licores 2025")
st.markdown("Análisis geoespacial interactivo. *Nota: El Archipiélago de San Andrés y Providencia ha sido agrupado, escalado (5x) y reubicado visualmente.*")

# 2. Cargar el mapa GeoJSON, ACERCAR, AGRANDAR Y AGRUPAR LAS ISLAS
@st.cache_data
def load_and_fix_geojson():
    url = "https://gist.githubusercontent.com/john-guerra/43c7656821069d00dcbc/raw/be6a6e239cd5b5b803c6e7c2ec405b793a9064dd/Colombia.geo.json"
    geojson = requests.get(url).json()
    
    def transform_coords(coords):
        if isinstance(coords[0], (int, float)):
            lon, lat = coords[0], coords[1]
            if lat > 13.0: # Providencia
                lon_c, lat_c = -81.37, 13.35
                lon_c_new, lat_c_new = -81.60, 12.85 
            else: # San Andrés
                lon_c, lat_c = -81.70, 12.55
                lon_c_new, lat_c_new = -81.70, 12.55
            
            scale_factor = 5.0
            lon_scaled = lon_c_new + (lon - lon_c) * scale_factor
            lat_scaled = lat_c_new + (lat - lat_c) * scale_factor
            
            lon_final = lon_scaled + 5.5
            lat_final = lat_scaled - 1.0
            return [lon_final, lat_final]
        else:
            return [transform_coords(c) for c in coords]
            
    for feature in geojson['features']:
        if feature['properties']['NOMBRE_DPT'] == 'ARCHIPIELAGO DE SAN ANDRES PROVIDENCIA Y SANTA CATALINA':
            feature['geometry']['coordinates'] = transform_coords(feature['geometry']['coordinates'])
            
    return geojson

colombia_geojson = load_and_fix_geojson()

# 3. Cargar y procesar los datos
@st.cache_data
def load_data():
    df = pd.read_excel("Base_Datos_Licores_Zonas.xlsx")
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

# Calcular el promedio por ZONA
df_promedios = df.groupby("Zona")[["Adulteración (%)", "Contrabando (%)"]].mean().reset_index()
df_mapa = pd.merge(df[["Departamento", "DPT_GEOJSON", "Zona"]], df_promedios, on="Zona", how="left")

# 4. PALETA DE COLORES DE INVAMER
colores_invamer = {
    "Zona 1": "#8FBC8B", # Verde
    "Zona 2": "#E4B56C", # Mostaza / Naranja claro
    "Zona 3": "#192055", # Azul Oscuro
    "Zona 4": "#C9D8C5", # Verde Claro
    "Zona 5": "#528797", # Azul Petróleo / Teal
    "Zona 6": "#CBE0EE", # Celeste / Azul Claro
    "Otras Zonas": "#D3D3D3" # Gris (Para las zonas no seleccionadas)
}

# 5. MENÚ LATERAL INTERACTIVO
st.sidebar.header("Filtros del Dashboard")
zona_seleccionada = st.sidebar.selectbox(
    "Selecciona la Zona a visualizar:",
    ["Todas las Zonas", "Zona 1", "Zona 2", "Zona 3", "Zona 4", "Zona 5", "Zona 6"]
)

# 6. LÓGICA DE FILTRADO (Efecto Gris)
# Creamos una columna temporal "Visual_Zona". 
# Si filtramos, los departamentos que no son de esa zona pasan a llamarse "Otras Zonas" (que se pinta de gris)
if zona_seleccionada != "Todas las Zonas":
    df_mapa["Visual_Zona"] = df_mapa["Zona"].apply(lambda x: x if x == zona_seleccionada else "Otras Zonas")
else:
    df_mapa["Visual_Zona"] = df_mapa["Zona"]

# 7. CREAR EL MAPA DE COLOR DISCRETO
fig = px.choropleth(
    df_mapa,
    geojson=colombia_geojson,
    featureidkey="properties.NOMBRE_DPT",
    locations="DPT_GEOJSON",
    color="Visual_Zona",                   # Colorear por la nueva columna temporal
    color_discrete_map=colores_invamer,    # Usar el diccionario de colores fijos
    hover_name="Departamento",
    hover_data={
        "DPT_GEOJSON": False, 
        "Visual_Zona": False, 
        "Zona": True, 
        "Adulteración (%)": ':.2f', 
        "Contrabando (%)": ':.2f'
    }
)

# Ocultar el mapa base del mundo y auto-encuadrar
fig.update_geos(visible=False, fitbounds="locations")
# Ajustamos márgenes y ocultamos la leyenda de colores porque es intuitiva
fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0}, showlegend=False) 

# 8. DISPOSICIÓN VISUAL
col1, col2 = st.columns([2.5, 1])

with col1:
    st.markdown(f"### Mapa: {zona_seleccionada}")
    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.markdown(f"### Datos de {zona_seleccionada}")
    
    # Si se selecciona una sola zona, mostramos los promedios específicos de esa zona en tarjetas grandes
    if zona_seleccionada != "Todas las Zonas":
        datos_zona = df_promedios[df_promedios["Zona"] == zona_seleccionada].iloc[0]
        st.metric("Adulteración Promedio", f"{datos_zona['Adulteración (%)']:.2f}%")
        st.metric("Contrabando Promedio", f"{datos_zona['Contrabando (%)']:.2f}%")
        
        st.markdown(f"**Departamentos en la {zona_seleccionada}:**")
        deptos_zona = df[df["Zona"] == zona_seleccionada]["Departamento"].tolist()
        st.write(", ".join(deptos_zona))
    else:
        # Si están todas, mostramos la tabla general
        st.dataframe(df_promedios.style.format({
            "Adulteración (%)": "{:.2f}%",
            "Contrabando (%)": "{:.2f}%"
        }), hide_index=True, use_container_width=True)
    
st.markdown("---")
st.markdown("### Base de Datos Detallada")
# Filtramos la tabla de abajo si hay una zona seleccionada
df_mostrar = df if zona_seleccionada == "Todas las Zonas" else df[df["Zona"] == zona_seleccionada]

st.dataframe(df_mostrar.drop(columns=["DPT_GEOJSON"]).style.format({
    "Adulteración": "{:.2%}",
    "Contrabando": "{:.2%}",
    "Adulteración (%)": "{:.2f}%",
    "Contrabando (%)": "{:.2f}%"
}), use_container_width=True)
