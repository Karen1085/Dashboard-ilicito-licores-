import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests

# 1. Configuración de la página
st.set_page_config(page_title="Dashboard Licores FND", layout="wide", page_icon="📊")

st.title("📊 Dashboard FND: Mercado Ilícito de Licores 2025")
st.markdown("Análisis geoespacial interactivo. Seleccione una Zona en el menú izquierdo para ver el detalle en el panel derecho.")

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

# 3. Diccionario de coordenadas para poner los NÚMEROS sobre el mapa
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
    "San Andrés": {"lat": 11.55, "lon": -76.2}, "Santander": {"lat": 6.5, "lon": -73.0},
    "Sucre": {"lat": 9.0, "lon": -75.0}, "Tolima": {"lat": 4.0, "lon": -75.0},
    "Valle del Cauca": {"lat": 3.5, "lon": -76.5}, "Vaupés": {"lat": 0.5, "lon": -70.5},
    "Vichada": {"lat": 4.5, "lon": -69.5}
}

# 4. Cargar y procesar los datos
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

# 5. PALETA DE COLORES DE INVAMER
colores_invamer = {
    "Zona 1": "#8FBC8B", "Zona 2": "#E4B56C", "Zona 3": "#192055",
    "Zona 4": "#C9D8C5", "Zona 5": "#528797", "Zona 6": "#CBE0EE",
    "Otras Zonas": "#E5E7EB"
}

# 6. MENÚ LATERAL INTERACTIVO
st.sidebar.header("Filtros del Dashboard")
zona_seleccionada = st.sidebar.selectbox(
    "Selecciona la Zona a visualizar:",
    ["Todas las Zonas", "Zona 1", "Zona 2", "Zona 3", "Zona 4", "Zona 5", "Zona 6"]
)

# 7. LÓGICA DE FILTRADO Y ENUMERACIÓN
if zona_seleccionada != "Todas las Zonas":
    df["Visual_Zona"] = df["Zona"].apply(lambda x: x if x == zona_seleccionada else "Otras Zonas")
    # Aislar departamentos de la zona para numerarlos del 1 al N
    df_zona = df[df["Zona"] == zona_seleccionada].sort_values(by="Departamento").copy()
    df_zona["Numero"] = range(1, len(df_zona) + 1)
    df_zona["lat"] = df_zona["Departamento"].apply(lambda x: coords_dptos.get(x, {}).get("lat", 0))
    df_zona["lon"] = df_zona["Departamento"].apply(lambda x: coords_dptos.get(x, {}).get("lon", 0))
else:
    df["Visual_Zona"] = df["Zona"]
    df_zona = pd.DataFrame() # Vacío si no hay zona seleccionada

# 8. CREAR EL MAPA BASE
fig = px.choropleth(
    df,
    geojson=colombia_geojson,
    featureidkey="properties.NOMBRE_DPT",
    locations="DPT_GEOJSON",
    color="Visual_Zona",
    color_discrete_map=colores_invamer,
    hover_name="Departamento",
    hover_data={"DPT_GEOJSON": False, "Visual_Zona": False, "Zona": True, "Adulteración (%)": ':.2f', "Contrabando (%)": ':.2f'}
)

# 9. AGREGAR LOS PINES NUMÉRICOS AL MAPA (Solo si hay zona seleccionada)
if not df_zona.empty:
    fig.add_trace(go.Scattergeo(
        lon=df_zona["lon"],
        lat=df_zona["lat"],
        text=df_zona["Numero"].astype(str),
        mode="markers+text",
        textfont=dict(color="white", size=14, family="sans-serif", weight="bold"),
        marker=dict(size=26, color="#000000", opacity=0.75, line=dict(width=2, color="white")),
        textposition="middle center",
        hoverinfo="skip",
        showlegend=False
    ))

fig.update_geos(visible=False, fitbounds="locations")
fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0}, showlegend=False, height=600) 

# 10. DISPOSICIÓN VISUAL (Columnas: Izquierda Mapa, Derecha Cajitas)
col1, col2 = st.columns([1.8, 1.2]) # Columna 1 más ancha para el mapa

with col1:
    st.plotly_chart(fig, use_container_width=True)

with col2:
    if zona_seleccionada != "Todas las Zonas":
        st.markdown(f"<h3 style='color: {colores_invamer[zona_seleccionada]}; margin-bottom: 20px;'>Detalle: {zona_seleccionada}</h3>", unsafe_allow_html=True)
        color_borde = colores_invamer[zona_seleccionada]
        
        # En el panel derecho creamos 2 columnas internas para que las cajitas no queden tan grandes
        cajitas_cols = st.columns(2)
        
        for i, row in df_zona.iterrows():
            depto_nombre = row["Departamento"]
            adul_val = row["Adulteración (%)"]
            contra_val = row["Contrabando (%)"]
            num = row["Numero"]
            
            # Dibujar la cajita con el número
            with cajitas_cols[i % 2]:
                st.markdown(f"""
                <div style="
                    border: 1px solid #E5E7EB; 
                    border-top: 6px solid {color_borde};
                    border-radius: 6px; 
                    padding: 12px; 
                    margin-bottom: 15px; 
                    background-color: white; 
                    box-shadow: 1px 2px 8px rgba(0,0,0,0.05);">
                    <h4 style="margin-top: 0; margin-bottom: 10px; color: #192055; font-family: sans-serif; font-size: 15px; display: flex; align-items: center;">
                        <span style="background-color: {color_borde}; color: white; border-radius: 50%; width: 22px; height: 22px; display: inline-block; text-align: center; line-height: 22px; margin-right: 8px; font-size: 13px;">{num}</span>
                        {depto_nombre}
                    </h4>
                    <div style="display: flex; justify-content: space-between; margin-bottom: 4px;">
                        <span style="color: #6B7280; font-size: 13px;">Adulteración:</span>
                        <span style="color: #B91C1C; font-weight: bold; font-size: 13px;">{adul_val:.2f}%</span>
                    </div>
                    <div style="display: flex; justify-content: space-between;">
                        <span style="color: #6B7280; font-size: 13px;">Contrabando:</span>
                        <span style="color: #D97706; font-weight: bold; font-size: 13px;">{contra_val:.2f}%</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
    else:
        st.info("👆 Selecciona una zona en el menú izquierdo para ver el desglose de los departamentos en este panel.")

st.markdown("---")
st.markdown("### Base de Datos General")
st.dataframe(df.drop(columns=["DPT_GEOJSON", "Visual_Zona"], errors='ignore').style.format({
    "Adulteración": "{:.2%}", "Contrabando": "{:.2%}", "Adulteración (%)": "{:.2f}%", "Contrabando (%)": "{:.2f}%"
}), use_container_width=True)
