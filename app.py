import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import datetime
import os

# --- CONFIGURACIÓN DE SEGURIDAD (Cámbialo cuando quieras) ---
USUARIO_ACCESO = "mvp"
CLAVE_ACCESO = "scouting26"

# --- CONFIGURACIÓN Y ESTÉTICA ---
st.set_page_config(page_title="MVP Scouting Lab", page_icon="⚽", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');
    .stApp { background-color: #f8fafc; font-family: 'Inter', sans-serif; }
    
    .stTabs [data-baseweb="tab"] {
        background-color: #f1f5f9; border-radius: 8px 8px 0 0;
        padding: 10px 20px; font-weight: 700; color: #475569;
    }
    .stTabs [aria-selected="true"] {
        background-color: #0f172a !important; color: #fbbf24 !important;
        border-bottom: 4px solid #fbbf24 !important;
    }
    @media (prefers-color-scheme: dark) {
        .stApp { background-color: #0f172a; }
        .stTabs [data-baseweb="tab"] { background-color: #1e293b; color: #94a3b8; }
    }
    </style>
""", unsafe_allow_html=True)

# --- SISTEMA DE LOGIN Y REGISTRO ---
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

def registrar_acceso(usuario, exito):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    estado = "EXITO" if exito else "FALLIDO"
    with open("registro_accesos.txt", "a") as f:
        f.write(f"[{timestamp}] Intento: {usuario} | Estado: {estado}\n")

if not st.session_state['logged_in']:
    st.markdown("""
        <div style="background: linear-gradient(135deg, #0f172a 0%, #022c22 100%);
                    padding: 40px; border-radius: 15px; margin-bottom: 25px; text-align: center;">
            <h1 style="color: #ffffff; font-size: 2.5rem; font-weight: 800;">MVP SCOUTING LAB</h1>
            <p style="color: #fbbf24; font-size: 1.2rem;">Acceso Restringido</p>
        </div>
    """, unsafe_allow_html=True)
    
    c1, c2, c3 = st.columns([1,2,1])
    with c2:
        st.info("Introduce tus credenciales para acceder a la plataforma.")
        user_input = st.text_input("👤 Usuario")
        pass_input = st.text_input("🔑 Contraseña", type="password")
        
        if st.button("Entrar al Sistema", use_container_width=True):
            if user_input == USUARIO_ACCESO and pass_input == CLAVE_ACCESO:
                st.session_state['logged_in'] = True
                registrar_acceso(user_input, True)
                st.rerun()
            else:
                registrar_acceso(user_input, False)
                st.error("Credenciales incorrectas. Acceso denegado.")
    st.stop() # Detiene la ejecución si no está logueado

# --- CABECERA (Solo visible si está logueado) ---
st.markdown("""
    <div style="background: linear-gradient(135deg, #064e3b 0%, #022c22 100%);
                padding: 40px; border-radius: 15px; margin-bottom: 25px;
                box-shadow: 0 10px 20px rgba(0,0,0,0.2); border-bottom: 5px solid #fbbf24; text-align: center;">
        <h1 style="color: #ffffff; font-size: 3rem; margin: 0; font-weight: 800;">MVP SCOUTING LAB</h1>
        <p style="color: #fbbf24; font-size: 1.2rem; margin: 5px 0 0 0;">PLATAFORMA DE INTELIGENCIA DE DATOS APLICADA AL FÚTBOL</p>
    </div>
""", unsafe_allow_html=True)

# Panel de Administrador (Oculto en el sidebar)
with st.sidebar.expander("🛡️ Panel de Administrador (Logs)", expanded=False):
    if os.path.exists("registro_accesos.txt"):
        with open("registro_accesos.txt", "r") as f:
            logs = f.read()
        st.text_area("Registro Histórico de Accesos:", logs, height=150)
        if st.button("Borrar Logs"):
            os.remove("registro_accesos.txt")
            st.rerun()
    else:
        st.write("No hay accesos registrados aún.")
    if st.button("Cerrar Sesión"):
        st.session_state['logged_in'] = False
        st.rerun()

# --- PROCESAMIENTO ETL Y LIMPIEZA EXTREMA ---
@st.cache_data
def process_data(df):
    df.columns = df.columns.str.strip()
    target_col = next((c for c in ['Player', 'Jugador', 'Name', 'Nombre'] if c in df.columns), None)
    if not target_col:
        text_cols = df.select_dtypes(include=['object']).columns.tolist()
        target_col = text_cols[0] if text_cols else 'ID'
    
    df = df.rename(columns={target_col: 'Player'})
    
    cols_to_int = ['Age', 'Edad', 'Min', 'Minutos', 'Minutos jugados', 'Matches', 'Partidos', 'Partidos jugados', 'MP']
    for c in cols_to_int:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c].astype(str).str.replace(',', '.'), errors='coerce').fillna(0).round().astype(int)
            
    return df.fillna(0)

# --- CARGA DE ARCHIVOS ---
st.sidebar.header("📁 DATA CENTER")
uploaded_files = st.sidebar.file_uploader("Sube archivos CSV/Excel", type=['csv', 'xlsx', 'xls'], accept_multiple_files=True)

df_raw = pd.DataFrame()
try:
    if uploaded_files:
        df_list = [pd.read_csv(f, sep=None, engine='python') if f.name.endswith('.csv') else pd.read_excel(f) for f in uploaded_files]
        df_raw = pd.concat(df_list, ignore_index=True)
    else:
        df_raw = pd.read_csv("FBREF_players_2223.csv", sep=";", encoding="utf-8")
except:
    if not uploaded_files:
        st.sidebar.info("Esperando carga de archivos...")
        st.stop()

df = process_data(df_raw)
num_cols = [c for c in df.select_dtypes(include=[np.number]).columns if c not in ['Age', 'Edad', 'Born', 'Matches', 'Min', 'Minutos jugados', 'ID', 'Partidos jugados', 'MP']]

# --- FILTROS COMPLETOS (RECUPERADOS) ---
st.sidebar.markdown("---")
st.sidebar.header("🔍 FILTROS")
mask = pd.Series(True, index=df.index)

# 1. Filtro Competición
if 'Competition' in df.columns:
    ligas = st.sidebar.multiselect("Competición", sorted(df['Competition'].unique()), default=[])
    if ligas: mask &= df['Competition'].isin(ligas)

# 2. Filtro Posición
col_pos_valida = 'Pos' if 'Pos' in df.columns else ('Posición específica' if 'Posición específica' in df.columns else None)
if col_pos_valida:
    posiciones = st.sidebar.multiselect("Posición", sorted(df[col_pos_valida].unique()), default=[])
    if posiciones: mask &= df[col_pos_valida].isin(posiciones)

# 3. Filtro Edad
col_edad = 'Age' if 'Age' in df.columns else ('Edad' if 'Edad' in df.columns else None)
if col_edad:
    min_e, max_e = int(df[col_edad].min()), int(df[col_edad].max())
    rango_edad = st.sidebar.slider("Edad", min_e, max_e, (min_e, max_e))
    mask &= df[col_edad].between(rango_edad[0], rango_edad[1])

# 4. Filtro Minutos Jugados
col_min = 'Min' if 'Min' in df.columns else ('Minutos jugados' if 'Minutos jugados' in df.columns else None)
if col_min:
    min_m, max_m = int(df[col_min].min()), int(df[col_min].max())
    rango_min = st.sidebar.slider("Minutos Jugados", min_m, max_m, (min_m, max_m))
    mask &= df[col_min].between(rango_min[0], rango_min[1])

df_f = df[mask].copy()

# --- CLASIFICACIÓN POSICIONAL PARA EL ALGORITMO ---
def get_pos_group(p):
    p = str(p).upper()
    if any(k in p for k in ['GK', 'PORTERO']): return 'GK'
    elif any(k in p for k in ['DF', 'CB', 'FB', 'LB', 'RB', 'CENTRAL', 'LATERAL']): return 'DF'
    elif any(k in p for k in ['FW', 'ST', 'RW', 'LW', 'DELANTERO', 'EXTREMO', 'CF']): return 'FW'
    else: return 'MF' 

if col_pos_valida:
    df_f['Grupo_Pos'] = df_f[col_pos_valida].apply(get_pos_group)
else:
    df_f['Grupo_Pos'] = 'MF'

# --- NUEVO MOTOR DE PONDERACIÓN POR POSICIÓN ---
st.sidebar.markdown("---")
st.sidebar.header("🧠 PONDERACIÓN POR LÍNEA")
st.sidebar.info("Define métricas y pesos específicos para cada posición.")

config_pos = {}
lineas_def = [
    ("GK", "Portería", 0, 1, 2),
    ("DF", "Defensa", 0, 1, 2),
    ("MF", "Medio", 0, 1, 2),
    ("FW", "Ataque", 0, 1, 2)
]

for key, name, i1, i2, i3 in lineas_def:
    with st.sidebar.expander(f"⚙️ Configurar {name} ({key})", expanded=False):
        m1 = st.selectbox(f"Métrica 1", num_cols, index=min(i1, len(num_cols)-1), key=f"m1_{key}")
        m2 = st.selectbox(f"Métrica 2", num_cols, index=min(i2, len(num_cols)-1), key=f"m2_{key}")
        m3 = st.selectbox(f"Métrica 3", num_cols, index=min(i3, len(num_cols)-1), key=f"m3_{key}")
        
        c1, c2, c3 = st.columns(3)
        w1 = c1.number_input(f"P1 %", 0, 100, 34, key=f"w1_{key}")
        w2 = c2.number_input(f"P2 %", 0, 100, 33, key=f"w2_{key}")
        w3 = c3.number_input(f"P3 %", 0, 100, 33, key=f"w3_{key}")
        
        if (w1 + w2 + w3) != 100:
            st.error(f"Suma = {w1+w2+w3}%. Debe ser 100.")
            st.stop()
            
        config_pos[key] = {'metrics': [m1, m2, m3], 'weights': [w1, w2, w3]}

# --- CÁLCULO DEL SCORE DINÁMICO ---
if not df_f.empty:
    def calc_score(row):
        g = row['Grupo_Pos']
        mets = config_pos[g]['metrics']
        wgts = config_pos[g]['weights']
        s = 0
        for m, w in zip(mets, wgts):
            mx = df[m].max() if df[m].max() > 0 else 1
            s += ((row[m] / mx) * 100) * (w / 100)
        return s
        
    df_f['Score'] = df_f.apply(calc_score, axis=1)
    df_f = df_f.sort_values('Score', ascending=False).reset_index(drop=True)
    df_f.index += 1

col_config = {
    "Age": st.column_config.NumberColumn("Edad", format="%d"),
    "Edad": st.column_config.NumberColumn("Edad", format="%d"),
    "Min": st.column_config.NumberColumn("Minutos", format="%d"),
    "Minutos jugados": st.column_config.NumberColumn("Minutos", format="%d"),
    "Matches": st.column_config.NumberColumn("PJ", format="%d"),
    "Partidos jugados": st.column_config.NumberColumn("PJ", format="%d"),
    "MP": st.column_config.NumberColumn("PJ", format="%d"),
    "Score": st.column_config.NumberColumn("MVP Score", format="%.2f")
}

# --- PESTAÑAS PRINCIPALES ---
t1, t2, t3, t4 = st.tabs(["🏆 RANKING", "📊 COMPARADOR", "👤 FICHA SCOUTING", "🧩 ONCE IDEAL"])

# --- TAB 1: RANKING ---
with t1:
    base_cols = [c for c in ['Player', 'Squad', 'Equipo', 'Competition', 'Age', 'Edad', 'Pos', 'Posición específica', 'Min', 'Minutos jugados'] if c in df_f.columns] + ['Grupo_Pos', 'Score']
    st.dataframe(df_f[base_cols].head(100), column_config=col_config, use_container_width=True)
    
    st.markdown("---")
    st.markdown("### 📈 Gráfico de Dispersión (Scatter Plot)")
    c_x, c_y = st.columns(2)
    eje_x = c_x.selectbox("Métrica Eje X", num_cols, index=0)
    eje_y = c_y.selectbox("Métrica Eje Y", num_cols, index=min(1, len(num_cols)-1))
    
    if not df_f.empty:
        fig_scatter = px.scatter(df_f.head(100), x=eje_x, y=eje_y, hover_name='Player', size='Score', size_max=15, color='Grupo_Pos', color_discrete_sequence=px.colors.qualitative.Set2)
        fig_scatter.update_layout(height=500, plot_bgcolor="rgba(0,0,0,0.05)")
        st.plotly_chart(fig_scatter, use_container_width=True)

# --- TAB 2: COMPARATIVA ---
with t2:
    players = df_f['Player'].tolist() if not df_f.empty else []
    if len(players) >= 2:
        c1, c2 = st.columns(2)
        p1 = c1.selectbox("Jugador 1 (Verde)", players, 0)
        p2 = c2.selectbox("Jugador 2 (Dorado)", players, 1)
        
        rad_mets_comp = st.multiselect("Selecciona las métricas a comparar:", num_cols, default=num_cols[:3])
        
        if rad_mets_comp:
            fig = go.Figure()
            colors = ['#064e3b', '#fbbf24']
            for i, p in enumerate([p1, p2]):
                vals = (df[df['Player'] == p][rad_mets_comp].iloc[0] / df[rad_mets_comp].max().replace(0,1) * 100).values
                fig.add_trace(go.Scatterpolar(r=vals, theta=rad_mets_comp, fill='toself', name=p, line_color=colors[i], line_width=3))
            fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 100])), height=550)
            st.plotly_chart(fig, use_container_width=True)

# --- TAB 3: FICHA DE JUGADOR ---
with t3:
    if players:
        sel_p = st.selectbox("Seleccionar Jugador para el Informe:", players)
        d = df_f[df_f['Player'] == sel_p].iloc[0]
        g_pos = d['Grupo_Pos']
        mets_jugador = config_pos[g_pos]['metrics'] 
        
        st.markdown(f'''
            <div style="background: #0f172a; padding: 25px; border-radius: 12px; border-left: 8px solid #fbbf24; margin-bottom: 20px; display:flex; justify-content: space-between;">
                <div><h1 style="color: white; margin:0;">{d['Player']}</h1><h4 style="color: #94a3b8; margin:0;">{d.get('Squad', d.get('Equipo','-'))} | {g_pos}</h4></div>
                <div style="text-align:right;"><h3 style="color:#fbbf24; margin:0;">MVP SCORE</h3><h1 style="color:white; margin:0;">{d['Score']:.2f}</h1></div>
            </div>
        ''', unsafe_allow_html=True)
        
        c1, c2, c3 = st.columns([1, 1, 2])
        
        edad_str = str(int(d['Age'])) if 'Age' in d else (str(int(d['Edad'])) if 'Edad' in d else '-')
        min_str = str(int(d['Min'])) if 'Min' in d else (str(int(d['Minutos jugados'])) if 'Minutos jugados' in d else '-')
        pos_str = d.get('Pos', d.get('Posición específica', '-'))
        
        c1.markdown(f"**Edad:** {edad_str}<br>**Minutos:** {min_str}<br>**Posición Original:** {pos_str}", unsafe_allow_html=True)
        
        c2.metric(mets_jugador[0], f"{d[mets_jugador[0]]:.2f}")
        c2.metric(mets_jugador[1], f"{d[mets_jugador[1]]:.2f}")
        c2.metric(mets_jugador[2], f"{d[mets_jugador[2]]:.2f}")
        
        with c3:
            rad_mets_ficha = st.multiselect("Métricas del Radar (Ficha):", num_cols, default=mets_jugador)
            if rad_mets_ficha:
                vals_ficha = (d[rad_mets_ficha] / df[rad_mets_ficha].max().replace(0,1) * 100).values
                fig_ind = go.Figure(go.Scatterpolar(r=vals_ficha, theta=rad_mets_ficha, fill='toself', line_color='#fbbf24'))
                fig_ind.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 100])), height=350, margin=dict(t=20, b=20))
                st.plotly_chart(fig_ind, use_container_width=True)

        st.markdown("---")
        with st.expander("📊 Ver todas las métricas del jugador"):
            st.dataframe(pd.DataFrame(d).T, hide_index=True)
            
        csv_data = pd.DataFrame(d).T.to_csv(index=False).encode('utf-8')
        st.download_button(label="📥 Descargar Informe Completo (CSV)", data=csv_data, file_name=f"Informe_{d['Player']}.csv", mime='text/csv')

# --- TAB 4: ONCE IDEAL ---
with t4:
    if not df_f.empty:
        c_sis, _ = st.columns([1, 2])
        sistema = c_sis.selectbox("Sistema de Juego", ["1-4-3-3", "1-4-4-2", "1-3-5-2", "1-5-3-2", "1-4-1-4-1", "1-3-2-3-2"])
        
        coords = {
            "1-4-3-3": {"GK": [(50, 12)], "DF": [(15,28),(38,24),(62,24),(85,28)], "MF": [(25,52),(50,48),(75,52)], "FW": [(20,82),(50,88),(80,82)]},
            "1-4-4-2": {"GK": [(50, 12)], "DF": [(15,28),(38,24),(62,24),(85,28)], "MF": [(15,52),(38,48),(62,48),(85,52)], "FW": [(35,82),(65,82)]},
            "1-3-5-2": {"GK": [(50, 12)], "DF": [(25,24),(50,24),(75,24)], "MF": [(10,52),(30,48),(50,45),(70,48),(90,52)], "FW": [(35,82),(65,82)]},
            "1-5-3-2": {"GK": [(50, 12)], "DF": [(10,30),(30,24),(50,24),(70,24),(90,30)], "MF": [(25,52),(50,48),(75,52)], "FW": [(35,82),(65,82)]},
            "1-4-1-4-1": {"GK": [(50, 12)], "DF": [(15,28),(38,24),(62,24),(85,28)], "MF": [(50,40),(15,60),(35,55),(65,55),(85,60)], "FW": [(50,85)]},
            "1-3-2-3-2": {"GK": [(50, 12)], "DF": [(25,24),(50,24),(75,24)], "MF": [(35,40),(65,40),(20,60),(50,60),(80,60)], "FW": [(35,85),(65,85)]}
        }

        lineas = {
            "GK": df_f[df_f['Grupo_Pos'] == 'GK'].head(len(coords[sistema]["GK"])),
            "DF": df_f[df_f['Grupo_Pos'] == 'DF'].head(len(coords[sistema]["DF"])),
            "MF": df_f[df_f['Grupo_Pos'] == 'MF'].head(len(coords[sistema]["MF"])),
            "FW": df_f[df_f['Grupo_Pos'] == 'FW'].head(len(coords[sistema]["FW"]))
        }

        c_list, c_pitch = st.columns([1, 1])
        
        with c_list:
            cols_show = ['Player', 'Score']
            st.markdown("#### 🧤 Portería")
            st.dataframe(lineas["GK"][cols_show] if not lineas["GK"].empty else pd.DataFrame(), hide_index=True, column_config=col_config, use_container_width=True)
            st.markdown("#### 🛡️ Defensa")
            st.dataframe(lineas["DF"][cols_show], hide_index=True, column_config=col_config, use_container_width=True)
            st.markdown("#### 🧠 Medio")
            st.dataframe(lineas["MF"][cols_show], hide_index=True, column_config=col_config, use_container_width=True)
            st.markdown("#### 🔥 Ataque")
            st.dataframe(lineas["FW"][cols_show], hide_index=True, column_config=col_config, use_container_width=True)

        with c_pitch:
            pitch_data = []
            number_counter = 1
            for linea, players in lineas.items():
                pos_list = coords[sistema][linea]
                for i, row in enumerate(players.itertuples()):
                    if i < len(pos_list):
                        x, y = pos_list[i]
                        hover = f"<b>{row.Player}</b><br>Score: {row.Score:.2f}"
                        pitch_data.append({"x": x, "y": y, "Name": row.Player, "Number": str(number_counter), "Hover": hover})
                        number_counter += 1
            
            if pitch_data:
                df_pitch = pd.DataFrame(pitch_data)
                fig = go.Figure()
                fig.add_shape(type="rect", x0=0, y0=0, x1=100, y1=100, fillcolor="#1b5e20", line=dict(color="white", width=2))
                fig.add_shape(type="line", x0=0, y0=50, x1=100, y1=50, line=dict(color="white", width=2))
                fig.add_shape(type="circle", x0=40, y0=40, x1=60, y1=60, line=dict(color="white", width=2))
                fig.add_shape(type="rect", x0=20, y0=0, x1=80, y1=15, line=dict(color="white", width=2))
                fig.add_shape(type="rect", x0=20, y0=100, x1=80, y1=85, line=dict(color="white", width=2))

                fig.add_trace(go.Scatter(
                    x=df_pitch['x'], y=df_pitch['y'], mode="markers+text",
                    marker=dict(symbol="circle", size=32, color="#fbbf24", line=dict(width=2, color="#ffffff")),
                    text=df_pitch['Number'], textposition="middle center",
                    textfont=dict(color="#0f172a", size=16, weight="bold"),
                    hovertemplate="%{customdata}<extra></extra>", customdata=df_pitch['Hover']
                ))
                
                for _, row in df_pitch.iterrows():
                    fig.add_annotation(
                        x=row['x'], y=row['y']-7, 
                        text=f"<b>{row['Name'].split(' ')[-1]}</b>",
                        showarrow=False,
                        font=dict(color="white", size=11, family="Inter"),
                        bgcolor="#0f172a", bordercolor="#fbbf24",
                        borderwidth=1, borderpad=3, opacity=0.95
                    )
                
                fig.update_layout(xaxis=dict(visible=False, range=[-5, 105]), 
                                  yaxis=dict(visible=False, range=[-8, 105]),
                                  height=700, margin=dict(l=10,r=10,t=10,b=10), 
                                  paper_bgcolor="rgba(0,0,0,0)", showlegend=False)
                st.plotly_chart(fig, use_container_width=True)
