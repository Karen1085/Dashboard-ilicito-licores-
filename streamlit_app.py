import streamlit as st
import pandas as pd
import plotly.express as px
import requests

# 1. Configuración de la página
st.set_page_config(page_title="Dashboard Licores FND", layout="wide", page_icon="📊")

st.title("📊 Dashboard FND: Mercado Ilícito de Licores 2025")
st.markdown("Análisis geoespacial interactivo. Seleccione una Zona para ver el detalle departamental.")

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

# 4. PALETA DE COLORES DE INVAMER
colores_invamer = {
    "Zona 1": "#8FBC8B", # Verde
    "Zona 2": "#E4B56C", # Mostaza
    "Zona 3": "#192055", # Azul Oscuro
    "Zona 4": "#C9D8C5", # Verde Claro
    "Zona 5": "#528797", # Azul Petróleo
    "Zona 6": "#CBE0EE", # Celeste
    "Otras Zonas": "#E5E7EB" # Gris claro suave
}

# 5. MENÚ LATERAL INTERACTIVO
st.sidebar.header("Filtros del Dashboard")
zona_seleccionada = st.sidebar.selectbox(
    "Selecciona la Zona a visualizar:",
    ["Todas las Zonas", "Zona 1", "Zona 2", "Zona 3", "Zona 4", "Zona 5", "Zona 6"]
)

# 6. LÓGICA DE FILTRADO (Efecto Gris)
if zona_seleccionada != "Todas las Zonas":
    df["Visual_Zona"] = df["Zona"].apply(lambda x: x if x == zona_seleccionada else "Otras Zonas")
else:
    df["Visual_Zona"] = df["Zona"]

# 7. CREAR EL MAPA
fig = px.choropleth(
    df,
    geojson=colombia_geojson,
    featureidkey="properties.NOMBRE_DPT",
    locations="DPT_GEOJSON",
    color="Visual_Zona",
    color_discrete_map=colores_invamer,
    hover_name="Departamento",
    hover_data={
        "DPT_GEOJSON": False, 
        "Visual_Zona": False, 
        "Zona": True, 
        "Adulteración (%)": ':.2f', 
        "Contrabando (%)": ':.2f'
    }
)

fig.update_geos(visible=False, fitbounds="locations")
fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0}, showlegend=False, height=500) 

# 8. DISPOSICIÓN VISUAL (MAPA ARRIBA, CAJITAS ABAJO)
st.plotly_chart(fig, use_container_width=True)

# 9. GENERACIÓN DE "CAJITAS" (Tarjetas de información por departamento)
if zona_seleccionada != "Todas las Zonas":
    st.markdown(f"### Detalle Departamental: {zona_seleccionada}")
    
    # Filtrar solo los departamentos de la zona seleccionada
    df_zona = df[df["Zona"] == zona_seleccionada].sort_values(by="Departamento")
    
    # Obtener el color de la zona para pintar el borde de las cajitas
    color_borde = colores_invamer[zona_seleccionada]
    
    # Crear un grid de columnas (4 columnas por fila queda muy elegante)
    cols = st.columns(4)
    
    # Iterar sobre los departamentos y crear una cajita HTML/CSS para cada uno
    for index, row in enumerate(df_zona.itertuples()):
        with cols[index % 4]: # Reparte las cajitas equitativamente en las 4 columnas
            st.markdown(f"""
            <div style="
                border: 2px solid {color_borde}; 
                border-top: 8px solid {color_borde};
                border-radius: 8px; 
                padding: 15px; 
                margin-bottom: 20px; 
                background-color: white; 
                box-shadow: 2px 4px 10px rgba(0,0,0,0.1);">
                <h4 style="margin-top: 0; color: #192055; text-align: center; font-family: sans-serif;">{row.Departamento}</h4>
                <hr style="margin: 10px 0; border: 1px solid #E5E7EB;">
                <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
                    <span style="color: #4B5563; font-weight: bold; font-size: 14px;">Adulteración:</span>
                    <span style="color: #B91C1C; font-weight: bold; font-size: 14px;">{row._4:.2f}%</span>
                </div>
                <div style="display: flex; justify-content: space-between;">
                    <span style="color: #4B5563; font-weight: bold; font-size: 14px;">Contrabando:</span>
                    <span style="color: #D97706; font-weight: bold; font-size: 14px;">{row._5:.2f}%</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
else:
    # Si "Todas las Zonas" está seleccionado, mostramos una tabla resumen general
    st.info("👆 Selecciona una zona específica en el menú izquierdo para ver las tarjetas informativas de cada departamento.")
