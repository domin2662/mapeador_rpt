import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import io

# Configuración de la página
st.set_page_config(
    page_title="Filtrador de Funcionarios",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personalizado
st.markdown("""
<style>
.main-header {
    font-size: 2.5rem;
    color: #1f4e79;
    text-align: center;
    margin-bottom: 2rem;
}
.metric-card {
    background-color: #f0f2f6;
    padding: 1rem;
    border-radius: 0.5rem;
    border-left: 4px solid #1f4e79;
}
.filter-section {
    background-color: #ffffff;
    padding: 1rem;
    border-radius: 0.5rem;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    margin-bottom: 1rem;
}
</style>
""", unsafe_allow_html=True)

# Logo y título principal
col_logo, col_title = st.columns([1, 4])
with col_logo:
    try:
        st.image("img/logo_eco.png", width=120)
    except:
        pass  # Si no se encuentra el logo, continuar sin él

with col_title:
    st.markdown('<h1 class="main-header">🏛️ Filtrador - RPT - Funcionarios Públicos</h1>', unsafe_allow_html=True)

st.markdown("---")

# Función para cargar datos
@st.cache_data
def load_data(uploaded_file):
    """Carga y procesa el archivo Excel"""
    try:
        # Leer el archivo Excel saltando las primeras 3 filas de metadatos
        df = pd.read_excel(uploaded_file, skiprows=3)
        
        # Definir los nombres de columnas correctos basados en la estructura mostrada
        expected_columns = [
            'Minis.', 'Denominación Ministerio', 'C.Dir', 'Denominación C.Dir',
            'Unidad', 'Denominación Unidad', 'País U.', 'Denominación País U.',
            'Provincia U.', 'Denominación Provincia U.', 'Localidad U.', 'Denominación Localidad U.',
            'Puesto', 'Denominación corta', 'Denominación Larga', 'Nivel',
            'C.Específ.', 'T.Pto.', 'Provis.', 'Ad.Pu', 'Gr/Sb', 'Agr.cuer/cuer',
            'Tit.Académica', 'For.Espec.', 'País', 'Denominación País',
            'Provincia', 'Denominación Provincia', 'Localidad', 'Denominación Localidad',
            'Observaciones', 'Estado'
        ]
        
        
        # Asignar nombres de columnas si el número coincide
        if len(df.columns) == len(expected_columns):
            df.columns = expected_columns
        
        # Limpiar y convertir datos
        # Convertir columnas numéricas
        numeric_columns = ['Nivel', 'C.Específ.']
        for col in numeric_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', '.'), errors='coerce')
        
        # Limpiar espacios en blanco
        string_columns = df.select_dtypes(include=['object']).columns
        for col in string_columns:
            df[col] = df[col].astype(str).str.strip()
            df[col] = df[col].replace('nan', '')
        
        return df
    except Exception as e:
        st.error(f"Error al cargar el archivo: {str(e)}")
        return None

# Función para aplicar filtros
def apply_filters(df, filters):
    """Aplica todos los filtros seleccionados al dataframe"""
    filtered_df = df.copy()
    
    # Filtro por búsqueda de texto
    if filters['search_text']:
        search_cols = ['Denominación Ministerio', 'Denominación C.Dir', 'Denominación Unidad',
                      'Denominación corta', 'Denominación Larga', 'Denominación País U.',
                      'Denominación Provincia U.', 'Denominación Localidad U.']
        
        search_mask = pd.Series([False] * len(filtered_df))
        for col in search_cols:
            if col in filtered_df.columns:
                search_mask |= filtered_df[col].str.contains(filters['search_text'], case=False, na=False)
        
        filtered_df = filtered_df[search_mask]
    
    # Filtro por ministerio
    if filters['ministerios']:
        filtered_df = filtered_df[filtered_df['Denominación Ministerio'].isin(filters['ministerios'])]
    
    # Filtro por provincia
    if filters['provincias']:
        filtered_df = filtered_df[filtered_df['Denominación Provincia U.'].isin(filters['provincias'])]
    
    # Filtro por denominación corta
    if filters['denominaciones_cortas']:
        filtered_df = filtered_df[filtered_df['Denominación corta'].isin(filters['denominaciones_cortas'])]
    
    # Filtro por denominación C.Dir
    if filters['denominaciones_cdir']:
        filtered_df = filtered_df[filtered_df['Denominación C.Dir'].isin(filters['denominaciones_cdir'])]
    
    # Filtro por denominación unidad
    if filters['denominaciones_unidad']:
        filtered_df = filtered_df[filtered_df['Denominación Unidad'].isin(filters['denominaciones_unidad'])]
    
    # Filtro por localidad
    if filters['localidades']:
        filtered_df = filtered_df[filtered_df['Denominación Localidad U.'].isin(filters['localidades'])]
    
    # Filtro por nivel
    if filters['nivel_min'] is not None and filters['nivel_max'] is not None:
        filtered_df = filtered_df[
            (filtered_df['Nivel'] >= filters['nivel_min']) & 
            (filtered_df['Nivel'] <= filters['nivel_max'])
        ]
    
    # Filtro por complemento específico
    if filters['comp_min'] is not None and filters['comp_max'] is not None:
        filtered_df = filtered_df[
            (filtered_df['C.Específ.'] >= filters['comp_min']) & 
            (filtered_df['C.Específ.'] <= filters['comp_max'])
        ]
    
    # Filtro por tipo de puesto
    if filters['tipo_puesto']:
        filtered_df = filtered_df[filtered_df['T.Pto.'].isin(filters['tipo_puesto'])]
    
    # Filtro por Gr/Sb
    if filters['gr_sb']:
        filtered_df = filtered_df[filtered_df['Gr/Sb'].isin(filters['gr_sb'])]
    
    # Filtro por estado
    if filters['estados']:
        filtered_df = filtered_df[filtered_df['Estado'].isin(filters['estados'])]
    
    return filtered_df

# Función para mostrar métricas
def show_metrics(df):
    """Muestra métricas principales del dataset"""
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Funcionarios", f"{len(df):,}")
    
    with col2:
        ministerios_count = df['Denominación Ministerio'].nunique()
        st.metric("Ministerios", ministerios_count)
    
    with col3:
        provincias_count = df['Denominación Provincia U.'].nunique()
        st.metric("Provincias", provincias_count)
    
    with col4:
        if 'Nivel' in df.columns:
            nivel_promedio = df['Nivel'].mean()
            st.metric("Nivel Promedio", f"{nivel_promedio:.1f}")

# Función principal
def main():
    # Logo en el sidebar
    try:
        st.sidebar.image("img/logo_eco.png", use_container_width=True)
    except:
        pass  # Si no se encuentra el logo, continuar sin él
    
    # Sidebar para carga de archivo
    st.sidebar.header("📁 Cargar Datos")
    uploaded_file = st.sidebar.file_uploader(
        "Selecciona el archivo Excel de funcionarios",
        type=['xlsx', 'xls'],
        help="Sube el archivo 250601_Tablaconjunta.xlsx"
    )
    
    if uploaded_file is not None:
        # Cargar datos
        with st.spinner("Cargando datos..."):
            df = load_data(uploaded_file)
        
        if df is not None:
            st.success(f"✅ Archivo cargado correctamente: {len(df):,} registros")
            
            # Mostrar métricas principales
            show_metrics(df)
            st.markdown("---")
            
            # Sidebar para filtros
            st.sidebar.header("🔍 Filtros")
            
            # Inicializar filtros
            filters = {}
            
            # Búsqueda por texto
            filters['search_text'] = st.sidebar.text_input(
                "🔎 Búsqueda por texto",
                placeholder="Buscar en denominaciones..."
            )
            
            # Filtro por ministerio
            ministerios_disponibles = sorted(df['Denominación Ministerio'].dropna().unique())
            filters['ministerios'] = st.sidebar.multiselect(
                "🏛️ Ministerios",
                options=ministerios_disponibles
            )
            
            # Filtro por provincia (ya permite múltiples selecciones)
            provincias_disponibles = sorted(df['Denominación Provincia U.'].dropna().unique())
            filters['provincias'] = st.sidebar.multiselect(
                "🗺️ Provincias",
                options=provincias_disponibles
            )
            
            # Filtro por denominación corta
            if 'Denominación corta' in df.columns:
                denominaciones_cortas = sorted(df['Denominación corta'].dropna().unique())
                filters['denominaciones_cortas'] = st.sidebar.multiselect(
                    "📝 Denominación Corta",
                    options=denominaciones_cortas
                )
            else:
                filters['denominaciones_cortas'] = []
            
            # Filtro por denominación C.Dir
            if 'Denominación C.Dir' in df.columns:
                denominaciones_cdir = sorted(df['Denominación C.Dir'].dropna().unique())
                filters['denominaciones_cdir'] = st.sidebar.multiselect(
                    "🏢 Denominación C.Dir",
                    options=denominaciones_cdir
                )
            else:
                filters['denominaciones_cdir'] = []
            
            # Filtro por denominación unidad
            if 'Denominación Unidad' in df.columns:
                denominaciones_unidad = sorted(df['Denominación Unidad'].dropna().unique())
                filters['denominaciones_unidad'] = st.sidebar.multiselect(
                    "🏛️ Denominación Unidad",
                    options=denominaciones_unidad
                )
            else:
                filters['denominaciones_unidad'] = []
            
            # Filtro por localidad (solo si se ha seleccionado provincia)
            if filters['provincias']:
                df_filtered_prov = df[df['Denominación Provincia U.'].isin(filters['provincias'])]
                localidades_disponibles = sorted(df_filtered_prov['Denominación Localidad U.'].dropna().unique())
                filters['localidades'] = st.sidebar.multiselect(
                    "🏙️ Localidades",
                    options=localidades_disponibles
                )
            else:
                filters['localidades'] = []
            
            # Filtro por nivel
            if 'Nivel' in df.columns:
                nivel_min, nivel_max = int(df['Nivel'].min()), int(df['Nivel'].max())
                nivel_range = st.sidebar.slider(
                    "📊 Rango de Nivel",
                    min_value=nivel_min,
                    max_value=nivel_max,
                    value=(nivel_min, nivel_max)
                )
                filters['nivel_min'], filters['nivel_max'] = nivel_range
            else:
                filters['nivel_min'], filters['nivel_max'] = None, None
            
            # Filtro por complemento específico
            if 'C.Específ.' in df.columns:
                comp_min, comp_max = float(df['C.Específ.'].min()), float(df['C.Específ.'].max())
                comp_range = st.sidebar.slider(
                    "💰 Rango Complemento Específico",
                    min_value=comp_min,
                    max_value=comp_max,
                    value=(comp_min, comp_max),
                    step=100.0
                )
                filters['comp_min'], filters['comp_max'] = comp_range
            else:
                filters['comp_min'], filters['comp_max'] = None, None
            
            # Filtro por tipo de puesto
            tipos_puesto = sorted(df['T.Pto.'].dropna().unique())
            filters['tipo_puesto'] = st.sidebar.multiselect(
                "💼 Tipo de Puesto",
                options=tipos_puesto
            )
            
            # Filtro por Gr/Sb
            if 'Gr/Sb' in df.columns:
                gr_sb_disponibles = sorted(df['Gr/Sb'].dropna().unique())
                filters['gr_sb'] = st.sidebar.multiselect(
                    "👥 Gr/Sb",
                    options=gr_sb_disponibles
                )
            else:
                filters['gr_sb'] = []
            
            # Filtro por estado
            estados_disponibles = sorted(df['Estado'].dropna().unique())
            filters['estados'] = st.sidebar.multiselect(
                "📋 Estado",
                options=estados_disponibles
            )
            
            # Aplicar filtros
            df_filtered = apply_filters(df, filters)
            
            # Mostrar resultados filtrados
            st.header(f"📊 Resultados Filtrados: {len(df_filtered):,} registros")
            
            if len(df_filtered) > 0:
                # Tabs para diferentes vistas
                tab1, tab2, tab3 = st.tabs(["📋 Tabla de Datos", "📈 Gráficos", "📊 Estadísticas"])
                
                with tab1:
                    # Selector de columnas a mostrar
                    st.subheader("Seleccionar columnas a mostrar")
                    all_columns = df_filtered.columns.tolist()
                    default_columns = [
                        'Denominación Ministerio', 'Denominación C.Dir', 'Denominación Unidad',
                        'Denominación corta', 'Nivel', 'C.Específ.', 'Denominación Provincia U.',
                        'Denominación Localidad U.', 'Estado'
                    ]
                    
                    # Filtrar columnas por defecto que existen en el dataframe
                    default_columns = [col for col in default_columns if col in all_columns]
                    
                    selected_columns = st.multiselect(
                        "Columnas a mostrar:",
                        options=all_columns,
                        default=default_columns
                    )
                    
                    if selected_columns:
                        # Mostrar tabla
                        st.dataframe(
                            df_filtered[selected_columns],
                            use_container_width=True,
                            height=400
                        )
                        
                        # Botón de descarga
                        csv = df_filtered[selected_columns].to_csv(index=False)
                        st.download_button(
                            label="📥 Descargar datos filtrados (CSV)",
                            data=csv,
                            file_name=f"funcionarios_filtrados_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv",
                            mime="text/csv"
                        )
                
                with tab2:
                    # Gráficos
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        # Gráfico por ministerio
                        if 'Denominación Ministerio' in df_filtered.columns:
                            ministerio_counts = df_filtered['Denominación Ministerio'].value_counts().head(10)
                            fig_ministerio = px.bar(
                                x=ministerio_counts.values,
                                y=ministerio_counts.index,
                                orientation='h',
                                title="Top 10 Ministerios por Número de Funcionarios",
                                labels={'x': 'Número de Funcionarios', 'y': 'Ministerio'}
                            )
                            fig_ministerio.update_layout(height=400)
                            st.plotly_chart(fig_ministerio, use_container_width=True)
                    
                    with col2:
                        # Gráfico por provincia
                        if 'Denominación Provincia U.' in df_filtered.columns:
                            provincia_counts = df_filtered['Denominación Provincia U.'].value_counts().head(10)
                            fig_provincia = px.pie(
                                values=provincia_counts.values,
                                names=provincia_counts.index,
                                title="Top 10 Provincias por Número de Funcionarios"
                            )
                            fig_provincia.update_layout(height=400)
                            st.plotly_chart(fig_provincia, use_container_width=True)
                    
                    # Histograma de niveles
                    if 'Nivel' in df_filtered.columns:
                        fig_nivel = px.histogram(
                            df_filtered,
                            x='Nivel',
                            title="Distribución de Niveles",
                            nbins=20
                        )
                        st.plotly_chart(fig_nivel, use_container_width=True)
                    
                    # Gráfico de complemento específico por nivel
                    if 'Nivel' in df_filtered.columns and 'C.Específ.' in df_filtered.columns:
                        fig_scatter = px.scatter(
                            df_filtered,
                            x='Nivel',
                            y='C.Específ.',
                            title="Relación entre Nivel y Complemento Específico",
                            opacity=0.6
                        )
                        st.plotly_chart(fig_scatter, use_container_width=True)
                
                with tab3:
                    # Estadísticas descriptivas
                    st.subheader("📊 Estadísticas Descriptivas")
                    
                    # Estadísticas numéricas
                    numeric_cols = df_filtered.select_dtypes(include=[np.number]).columns
                    if len(numeric_cols) > 0:
                        st.write("**Variables Numéricas:**")
                        st.dataframe(df_filtered[numeric_cols].describe())
                    
                    # Conteos por categorías principales
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        if 'T.Pto.' in df_filtered.columns:
                            st.write("**Distribución por Tipo de Puesto:**")
                            tipo_puesto_counts = df_filtered['T.Pto.'].value_counts()
                            st.dataframe(tipo_puesto_counts.to_frame('Cantidad'))
                    
                    with col2:
                        if 'Estado' in df_filtered.columns:
                            st.write("**Distribución por Estado:**")
                            estado_counts = df_filtered['Estado'].value_counts()
                            st.dataframe(estado_counts.to_frame('Cantidad'))
            
            else:
                st.warning("⚠️ No se encontraron registros con los filtros aplicados.")
    
    else:
        st.info("👆 Por favor, sube el archivo Excel para comenzar el análisis.")
        
        # Mostrar información sobre el formato esperado
        st.markdown("""
        ### 📋 Formato de Archivo Esperado
        
        El archivo debe ser un Excel (.xlsx) con la siguiente estructura:
        - **Fila 1-3**: Metadatos (se omitirán automáticamente)
        - **Fila 4**: Cabeceras de columnas
        - **Columnas esperadas**: Minis., Denominación Ministerio, C.Dir, Denominación C.Dir, etc.
        
        ### 🔍 Funcionalidades Disponibles
        
        - **Búsqueda por texto**: Busca en todas las denominaciones
        - **Filtros múltiples**: Por ministerio, provincia, localidad, nivel, etc.
        - **Visualizaciones**: Gráficos interactivos de distribución
        - **Exportación**: Descarga los datos filtrados en CSV
        - **Estadísticas**: Análisis descriptivo de los datos
        """)

if __name__ == "__main__":
    main()