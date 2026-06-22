import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests

# 1. Configuración de la página (Wide mode)
st.set_page_config(
    page_title="Dashboard Comercio Ilícito de Licores FND-Datexco", 
    layout="wide", 
    page_icon="📊"
)

# --- CSS AGRESIVO PARA DISEÑO PREMIUM ---
hide_st_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {visibility: hidden;} 
            
            /* Ocultar elementos inyectados por Streamlit Cloud */
            .stDeployButton {display: none !important;}
            [data-testid="stToolbar"] {display: none !important;}
            [data-testid="manage-app-button"] {display: none !important;}
            .viewerBadge_container__1QSob {display: none !important;}
            #stDecoration {display: none !important;}
            
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
            
            h1 {margin-bottom: 0px !important; padding-bottom: 5px !important; color: #1e293b; font-size: 2.2rem !important; font-weight: 800;}
            
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

# 5. Colores
colores_invamer = {
    "Zona 1": "#8FBC8B", "Zona 2": "#E4B56C", "Zona 3": "#192055",
    "Zona 4": "#C9D8C5", "Zona 5": "#528797", "Zona 6": "#CBE0EE",
    "Otras Zonas": "#E5E7EB"
}

widget_title_style = "font-size: 12px; color: #64748B; font-weight: 700; text-transform: uppercase; letter-spacing: 0.8px; margin-bottom: 6px;"

# --- TÍTULO PRINCIPAL ---
st.markdown("<h1>Comercio Ilícito de Licores FND-Datexco 2025</h1>", unsafe_allow_html=True)

# --- CREACIÓN DE PESTAÑAS ---
pag1, pag2, pag3 = st.tabs(["🗺️ Mapa y Zonas", "🏆 Tops de Ilícitos", "📊 Comparativa por Departamento"])

# ==============================================================================
# PÁGINA 1: MAPA Y ANÁLISIS GEOESPACIAL 
# ==============================================================================
with pag1:
    col_filtro1, _ = st.columns([1, 4]) 
    with col_filtro1:
        zona_seleccionada = st.selectbox(
            "📍 Seleccione la Zona:",
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
            marker=dict(size=18, color="#000000", opacity=0.8, line=dict(width=1, color="white")),
            textposition="middle center", hoverinfo="skip", showlegend=False
        ))

    fig.update_geos(visible=False, fitbounds="locations")
    # Aumentamos la altura del mapa para que sea más imponente
    fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0}, showlegend=False, height=500, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)') 

    # --- NUEVA PROPORCIÓN: El mapa (1.4) tiene mucho más espacio frente a las cajitas (1.6) ---
    col_mapa, col_datos = st.columns([1.4, 1.6]) 
    with col_mapa:
        st.plotly_chart(fig, use_container_width=True)

    with col_datos:
        if zona_seleccionada != "Todas las Zonas":
            st.markdown(f"<div style='{widget_title_style} margin-top: 5px;'>Detalle interactivo: {zona_seleccionada}</div>", unsafe_allow_html=True)
            color_borde = colores_invamer[zona_seleccionada]
            
            cajitas_cols = st.columns(2)
            
            # SOLUCIÓN DEL APILAMIENTO: Usamos enumerate para que se asigne exactamente 1 izquierda, 1 derecha.
            for seq_i, (index, row) in enumerate(df_zona.iterrows()):
                depto_nombre = row["Departamento"]
                num = row["Numero"]
                adul_text = f"{row['Adulteración (%)']:.2f}%" if pd.notna(row['Adulteración (%)']) else "N/A"
                contra_text = f"{row['Contrabando (%)']:.2f}%" if pd.notna(row['Contrabando (%)']) else "N/A"
                falsi_text = f"{row['Falsificación (%)']:.2f}%" if pd.notna(row['Falsificación (%)']) else "N/A"
                
                # Tarjeta miniatura: text-size muy compacto
                html_card = f"""<div style="border: 1px solid #E5E7EB; border-left: 4px solid {color_borde}; border-radius: 4px; padding: 4px 8px; margin-bottom: 6px; background-color: white; box-shadow: 1px 1px 2px rgba(0,0,0,0.05);">
<h4 style="margin: 0 0 2px 0; color: #1e293b; font-family: sans-serif; font-size: 11px; display: flex; align-items: center; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">
<span style="background-color: {color_borde}; color: white; border-radius: 50%; min-width: 14px; height: 14px; display: inline-block; text-align: center; line-height: 14px; margin-right: 5px; font-size: 8px; font-weight: bold;">{num}</span>{depto_nombre}</h4>
<div style="display: flex; justify-content: space-between; margin-bottom: 0px;"><span style="color: #64748b; font-size: 10px;">Adulteración:</span><span style="color: #b91c1c; font-weight: bold; font-size: 10px;">{adul_text}</span></div>
<div style="display: flex; justify-content: space-between; margin-bottom: 0px;"><span style="color: #64748b; font-size: 10px;">Contrabando:</span><span style="color: #d97706; font-weight: bold; font-size: 10px;">{contra_text}</span></div>
<div style="display: flex; justify-content: space-between;"><span style="color: #64748b; font-size: 10px;">Falsificación:</span><span style="color: #475569; font-weight: bold; font-size: 10px;">{falsi_text}</span></div></div>"""
                
                # seq_i es secuencial (0, 1, 2, 3...) asegurando un balance perfecto
                with cajitas_cols[seq_i % 2]:
                    st.markdown(html_card, unsafe_allow_html=True)
        else:
            st.markdown(f"<div style='{widget_title_style} margin-top: 5px;'>Promedios por Zonas FND</div>", unsafe_allow_html=True)
            html_table = "<style>.styled-table { border-collapse: collapse; margin: 0; font-size: 12px; font-family: sans-serif; width: 100%; box-shadow: 0 2px 8px rgba(0,0,0,0.05); border-radius: 6px 6px 0 0; overflow: hidden; }.styled-table thead tr { background-color: #192055; color: #ffffff; text-align: left; }.styled-table th, .styled-table td { padding: 8px 10px; border-bottom: 1px solid #f1f5f9;}.styled-table tbody tr { background-color: #ffffff; }.styled-table tbody tr:nth-of-type(even) { background-color: #f8fafc; }</style>"
            html_table += "<table class='styled-table'><thead><tr><th>Zonas FND</th><th style='text-align: right;'>Adulteración</th><th style='text-align: right;'>Contrabando</th><th style='text-align: right;'>Falsificación</th></tr></thead><tbody>"
            for index, row in df_promedios.iterrows():
                zona = row["Zona"]
                color_zona = colores_invamer.get(zona, "#000000")
                adul_text = f"{row['Adulteración (%)']:.2f}%" if pd.notna(row['Adulteración (%)']) else "N/A"
                contra_text = f"{row['Contrabando (%)']:.2f}%" if pd.notna(row['Contrabando (%)']) else "N/A"
                falsi_text = f"{row['Falsificación (%)']:.2f}%" if pd.notna(row['Falsificación (%)']) else "N/A"
                html_table += f"<tr><td style='font-weight: bold; color: #1e293b; display: flex; align-items: center;'><span style='background-color: {color_zona}; width: 10px; height: 10px; border-radius: 50%; display: inline-block; margin-right: 6px; border: 1px solid #cbd5e1;'></span>{zona}</td><td style='text-align: right; color: #b91c1c; font-weight: bold;'>{adul_text}</td><td style='text-align: right; color: #d97706; font-weight: bold;'>{contra_text}</td><td style='text-align: right; color: #475569; font-weight: bold;'>{falsi_text}</td></tr>"
            html_table += "</tbody></table>"
            st.markdown(html_table, unsafe_allow_html=True)

# ==============================================================================
# PÁGINA 2: TOPS DE ILÍCITOS 
# ==============================================================================
with pag2:
    col_filtro2, _ = st.columns([1, 4])
    with col_filtro2:
        ilicito_elegido = st.selectbox(
            "📊 Métrica:",
            ["Falsificación (%)", "Contrabando (%)", "Adulteración (%)"],
            label_visibility="collapsed"
        )
    
    st.markdown("<br>", unsafe_allow_html=True)
    col_mapa2, col_cuadros2 = st.columns([1.2, 1])
    
    with col_mapa2:
        st.markdown(f"<div style='{widget_title_style}'>🗺️ Mapa de Calor ({ilicito_elegido.split()[0]})</div>", unsafe_allow_html=True)
        if "Adul" in ilicito_elegido:
            escala_calor = "Reds"
        elif "Contra" in ilicito_elegido:
            escala_calor = "Oranges"
        else:
            escala_calor = "Blues"
            
        fig_heat = px.choropleth(
            df, geojson=colombia_geojson, featureidkey="properties.NOMBRE_DPT", locations="DPT_GEOJSON",
            color=ilicito_elegido, color_continuous_scale=escala_calor, hover_name="Departamento",
            hover_data={"DPT_GEOJSON": False, "Zona": True, ilicito_elegido: ':.1f'}
        )
        fig_heat.update_geos(visible=False, fitbounds="locations")
        fig_heat.update_layout(margin={"r":0,"t":0,"l":0,"b":0}, height=550, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', coloraxis_colorbar=dict(title="", thicknessmode="pixels", thickness=12))
        st.plotly_chart(fig_heat, use_container_width=True)

    with col_cuadros2:
        st.markdown(f"<div style='{widget_title_style}'>🏆 Ranking de Departamentos</div>", unsafe_allow_html=True)
        df_dept_sorted = df[df[ilicito_elegido].notna()][["Departamento", ilicito_elegido]].sort_values(by=ilicito_elegido, ascending=False)
        df_dept_sorted.reset_index(drop=True, inplace=True)
        df_dept_sorted.index += 1 
        
        st.dataframe(
            df_dept_sorted.style.format({ilicito_elegido: "{:.2f}%"}),
            use_container_width=True,
            height=300 
        )
        
        st.markdown(f"<div style='{widget_title_style} margin-top: 10px;'>📊 Promedios de Zonas FND</div>", unsafe_allow_html=True)
        df_zona_sorted = df_promedios[df_promedios[ilicito_elegido].notna()].sort_values(by=ilicito_elegido, ascending=True)
        fig_zona_bar = px.bar(
            df_zona_sorted, x=ilicito_elegido, y="Zona", orientation='h',
            text=ilicito_elegido,
            color="Zona", color_discrete_map=colores_invamer
        )
        fig_zona_bar.update_traces(texttemplate='%{text:.1f}%', textposition='outside', textfont_size=11)
        fig_zona_bar.update_layout(height=230, margin={"l": 60, "r": 30, "t": 0, "b": 0}, showlegend=False, xaxis_title=None, yaxis_title=None, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig_zona_bar, use_container_width=True)

# ==============================================================================
# PÁGINA 3: COMPARATIVA INTELIGENTE 
# ==============================================================================
with pag3:
    col_filtro3, _ = st.columns([1, 4])
    with col_filtro3:
        depto_seleccionado = st.selectbox(
            "📍 Departamento:",
            sorted(df["Departamento"].unique()),
            label_visibility="collapsed"
        )
    
    fila_depto = df[df["Departamento"] == depto_seleccionado].iloc[0]
    zona_del_depto = fila_depto["Zona"]
    promedios_nacionales = df[["Adulteración (%)", "Contrabando (%)", "Falsificación (%)"]].mean()
    promedios_zona = df_promedios[df_promedios["Zona"] == zona_del_depto].iloc[0]
    
    st.markdown(f"<div style='{widget_title_style} margin-top: 15px; font-size: 15px;'>Ficha Técnica: {depto_seleccionado} ({zona_del_depto})</div>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    metricas = [("Adulteración (%)", col1), ("Contrabando (%)", col2), ("Falsificación (%)", col3)]
    
    for met, col in metricas:
        v_depto = fila_depto[met]
        v_zona = promedios_zona[met]
        v_nac = promedios_nacionales[met]
        nombre_metrica = met.replace(" (%)", "")
        
        with col:
            if pd.notna(v_depto):
                delta_zona = v_depto - v_zona
                delta_nac = v_depto - v_nac
                
                color_d_zona = "#b91c1c" if delta_zona > 0 else "#15803d"
                color_d_nac = "#b91c1c" if delta_nac > 0 else "#15803d"
                
                html_card = f"""<div style="border: 1px solid #E5E7EB; border-top: 4px solid #192055; border-radius: 8px; padding: 18px; background-color: white; box-shadow: 0 4px 6px rgba(0,0,0,0.05);">
<h4 style="margin: 0; color: #64748b; font-size: 14px; text-transform: uppercase; letter-spacing: 0.5px;">{nombre_metrica}</h4>
<h2 style="margin: 5px 0 15px 0; color: #0f172a; font-size: 32px; font-weight: 800;">{v_depto:.2f}%</h2>
<div style="background-color: #f8fafc; padding: 10px; border-radius: 6px;">
<div style="display: flex; justify-content: space-between; font-size: 13px; margin-bottom: 8px; border-bottom: 1px solid #e2e8f0; padding-bottom: 8px;">
<span style="color: #475569;">Promedio {zona_del_depto}: <strong style="color:#0f172a;">{v_zona:.2f}%</strong></span>
<span style="font-weight: bold; color: {color_d_zona};">{delta_zona:+.2f}%</span>
</div>
<div style="display: flex; justify-content: space-between; font-size: 13px;">
<span style="color: #475569;">Nacional: <strong style="color:#0f172a;">{v_nac:.2f}%</strong></span>
<span style="font-weight: bold; color: {color_d_nac};">{delta_nac:+.2f}%</span>
</div>
</div>
</div>"""
                st.markdown(html_card, unsafe_allow_html=True)
            else:
                st.info(f"Sin datos registrados para {nombre_metrica}.")
