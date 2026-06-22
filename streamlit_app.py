import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests

# 1. Configuración de la página
st.set_page_config(
    page_title="Dashboard Comercio Ilícito de Licores FND-Datexco", 
    layout="wide"
)

# --- CSS AGRESIVO PARA DISEÑO PREMIUM Y OCULTAR MARCAS DE AGUA ---
hide_st_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {visibility: hidden;} 
            
            /* Ocultar elementos de Streamlit Cloud (Botones) */
            .stDeployButton {display: none !important;}
            [data-testid="stToolbar"] {display: none !important;}
            [data-testid="manage-app-button"] {display: none !important;}
            #stDecoration {display: none !important;}
            
            /* ESCUDO ANTI-MARCA DE AGUA (Creator Badge) */
            .viewerBadge_container__1QSob {display: none !important;}
            .viewerBadge_link__1S137 {display: none !important;}
            [class*="viewerBadge"] {display: none !important;}
            [class*="CreatorBadge"] {display: none !important;}
            [class*="creatorBadge"] {display: none !important;}
            [class^="styles_viewerBadge"] {display: none !important;}
            [class^="styles_creatorBadge"] {display: none !important;}
            [id^="viewerBadge"] {display: none !important;}
            a[href*="streamlit.io/cloud"] {display: none !important;}
            a[target="_blank"][href*="streamlit"] {display: none !important;}
            
            /* Ajuste de márgenes del lienzo */
            .block-container {
                padding-top: 1.5rem !important; 
                padding-bottom: 0rem !important; 
                padding-left: 2rem !important;
                padding-right: 2rem !important;
                max-width: 100% !important;
            }
            
            .stTabs [data-baseweb="tab-list"] {margin-bottom: 0px;}
            .stTabs [data-baseweb="tab-panel"] {padding-top: 15px;}
            
            h1 {margin-bottom: 0px !important; padding-bottom: 5px !important; color: #192055; font-size: 2.2rem !important; font-weight: 800;}
            h3, h4 {color: #192055 !important;}
            
            .stSelectbox {margin-bottom: 0px !important;}
            div[data-testid="stVerticalBlock"] {gap: 0.5rem !important;}
            </style>
            """
st.markdown(hide_st_style, unsafe_allow_html=True)

# 2. Cargar el mapa GeoJSON
@st.cache_data
def load_and_fix_geojson():
    url = "https://gist.githubusercontent.com/john-guerra/43c7656821069d00dcbc/raw/be6a6e239cd5b5b803c6e7c2ec405b793a9064dd/Colombia.geo.json"
    geojson = requests.get(url).json()
    
    def transform_coords(coords):
        if isinstance(coords[0], (int, float)):
            lon, lat = coords[0], coords[1]
            if lat > 13.0: 
                lon_c, lat_c = -81.37, 13.35
                lon_c_new, lat_c_new = -81.60, 12.85 
            else: 
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

# 3. Diccionario de coordenadas para pines
coords_dptos = {
    "Amazonas": {"lat": -1.0, "lon": -71.5}, "Antioquia": {"lat": 6.5, "lon": -75.3},
    "Arauca": {"lat": 6.5, "lon": -71.0}, "Atlántico": {"lat": 10.6, "lon": -75.0},
    "Bogotá D.C.": {"lat": 4.3, "lon": -74.1}, "Bolívar": {"lat": 9.0, "lon": -74.3},
    "Boyacá": {"lat": 5.5, "lon": -72.5}, "Caldas": {"lat": 5.3, "lon": -75.3},
    "Caquetá": {"lat": 1.0, "lon": -74.0}, "Casanare": {"lat": 5.5, "lon": -71.5},
    "Cauca": {"lat": 2.5, "lon": -76.5}, "Cesar": {"lat": 9.5, "lon": -73.5},
    "Chocó": {"lat": 5.5, "lon": -76.8}, "Córdoba": {"lat": 8.0, "lon": -75.8},
    "Cundinamarca": {"lat": 5.0, "lon": -74.0}, "Guainía": {"lat": 2.5, "lon": -69.0},
    "Guaviare": {"lat": 2.0, "lon": -71.5}, "Huila": {"lat": 2.5, "lon": -75.5},
    "La Guajira": {"lat": 11.5, "lon": -72.5}, "Magdalena": {"lat": 10.0, "lon": -74.0},
    "Meta": {"lat": 3.5, "lon": -73.0}, "Nariño": {"lat": 1.5, "lon": -77.5},
    "Nte. Santander": {"lat": 8.0, "lon": -73.0}, "Putumayo": {"lat": 0.5, "lon": -76.0},
    "Quindío": {"lat": 4.5, "lon": -75.6}, "Risaralda": {"lat": 5.0, "lon": -76.0},
    "San Andrés": {"lat": 12.2, "lon": -76.8}, "Santander": {"lat": 6.5, "lon": -73.0},
    "Sucre": {"lat": 9.0, "lon": -75.0}, "Tolima": {"lat": 4.0, "lon": -75.0},
    "Valle del Cauca": {"lat": 3.5, "lon": -76.5}, "Vaupés": {"lat": 0.5, "lon": -70.5},
    "Vichada": {"lat": 4.5, "lon": -69.5}
}

# 4. Cargar y procesar datos
@st.cache_data
def load_data():
    df = pd.read_excel("Base_Datos_Licores_Zonas.xlsx")
    df.columns = df.columns.str.strip() 
    df["Departamento"] = df["Departamento"].astype(str).str.strip() 
    
    df["Departamento"] = df["Departamento"].replace({
        "Norte de Santander": "Nte. Santander", 
        "Bogotá": "Bogotá D.C.",
        "Archipiélago de San Andrés, Providencia y Santa Catalina": "San Andrés"
    })
    
    df["Adulteración (%)"] = df["Adulteración"] * 100
    df["Contrabando (%)"] = df["Contrabando"] * 100
    df["Falsificación (%)"] = df["Falsificación"] * 100 
    
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

# 5. DICCIONARIOS MAESTROS DE IDENTIDAD VISUAL
colores_invamer = {
    "Zona 1": "#8FBC8B", "Zona 2": "#E4B56C", "Zona 3": "#192055",
    "Zona 4": "#C9D8C5", "Zona 5": "#528797", "Zona 6": "#CBE0EE",
    "Otras Zonas": "#E5E7EB"
}

colores_metricas = {
    "Adulteración": "#b91c1c",  
    "Contrabando": "#d97706",   
    "Falsificación": "#192055"  
}

widget_title_style = "font-size: 12px; color: #64748B; font-weight: 700; text-transform: uppercase; letter-spacing: 0.8px; margin-bottom: 6px;"

# --- TÍTULO PRINCIPAL ---
st.markdown("<h1>Comercio Ilícito de Licores FND-Datexco 2025</h1>", unsafe_allow_html=True)

# --- CREACIÓN DE PESTAÑAS ---
pag1, pag2, pag3 = st.tabs(["Mapa y Zonas", "Ranking y Promedios", "Análisis Departamental"])

# ==============================================================================
# PÁGINA 1: MAPA Y ANÁLISIS GEOESPACIAL
# ==============================================================================
with pag1:
    col_filtro1, _ = st.columns([1, 4]) 
    with col_filtro1:
        zona_seleccionada = st.selectbox(
            "Seleccione la Zona:",
            ["Todas las Zonas", "Zona 1", "Zona 2", "Zona 3", "Zona 4", "Zona 5", "Zona 6"],
            label_visibility="collapsed"
        )
    
    df_promedios = df.groupby("Zona")[["Adulteración (%)", "Contrabando (%)", "Falsificación (%)"]].mean().reset_index()

    if zona_seleccionada != "Todas las Zonas":
        df["Visual_Zona"] = df["Zona"].apply(lambda x: x if x == zona_seleccionada else "Otras Zonas")
        df_zona = df[df["Zona"] == zona_seleccionada].sort_values(by="Departamento").copy()
        df_zona["Numero"] = range(1, len(df_zona) + 1)
        df_zona["lat"] = df_zona["Departamento"].apply(lambda x: coords_dptos.get(x, {}).get("lat", None))
        df_zona["lon"] = df_zona["Departamento"].apply(lambda x: coords_dptos.get(x, {}).get("lon", None))
    else:
        df["Visual_Zona"] = df["Zona"]
        df_zona = pd.DataFrame() 

    fig = px.choropleth(
        df, geojson=colombia_geojson, featureidkey="properties.NOMBRE_DPT", locations="DPT_GEOJSON",
        color="Visual_Zona", color_discrete_map=colores_invamer, hover_name="Departamento",
        hover_data={"DPT_GEOJSON": False, "Visual_Zona": False, "Zona": True, "Adulteración (%)": ':.2f', "Contrabando (%)": ':.2f', "Falsificación (%)": ':.2f'}
    )

    if not df_zona.empty:
        fig.add_trace(go.Scattergeo(
            lon=df_zona["lon"], lat=df_zona["lat"], text=df_zona["Numero"].astype(str),
            mode="markers+text", textfont=dict(color="white", size=11, family="sans-serif", weight="bold"),
            marker=dict(size=18, color="#000000", opacity=0.8, line=dict(width=1
