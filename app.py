import streamlit as st
import pandas as pd
from db import get_connection
from utils import calcular_percentual
import plotly.graph_objects as go
from io import BytesIO
from style import *

# Configuração da página
st.set_page_config(page_title="Painel Comercial FFH", layout="wide")

# Estilo customizado
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');
        @import url('https://fonts.googleapis.com/css2?family=Garamond');

        * {
            transition: all ease-in-out;
        } 
        
        html, body, [class*="css"] {
            font-family: 'Inter', sans-serif;
            background-color: #F1F5FA;
        }

        .main-title {
            text-align: center;
            font-size: 36px;
            font-weight: bold;
            background: linear-gradient(90deg, #295148, #C1FBAD);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            padding-bottom: 1rem;
            font-family: 'Garamond', serif;
        }

        .kpi-box {
            background: linear-gradient(135deg, #CBCCBC, #F1F5FA);
            border-left: 6px solid #192B23;
            border-radius: 15px;
            padding: 20px;
            box-shadow: 2px 4px 10px rgba(0,0,0,0.05);
            transition: all 0.3s ease-in-out;
        }

        .kpi-box:hover {
            transform: scale(1.01);
        }

        .kpi-title {
            font-size: 18px;
            font-weight: bold;
            color: #192B23;
            margin-bottom: 8px;
        }

        .kpi-meta, .kpi-resultado {
            font-size: 16px;
            font-weight: 600;
        }

        .progress-highlight {
            text-align:center;
            font-size: 16px;
            font-weight: bold;
            color: #295148;
            margin-top: 5px;
        }

        .export-button button {
            background-color: #295148;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 8px;
            font-weight: bold;
        }

        .export-button button:hover {
            background-color: #192B23;
            color: #C1FBAD;
        }

        progress {
            accent-color: #295148;
        }
    </style>
""", unsafe_allow_html=True)

# Conexão
conn = get_connection()

# Filtros
df_filtros = pd.read_sql("""
    SELECT DISTINCT 
        nome_comercial, 
        EXTRACT(YEAR FROM competencia) AS ano,
        TO_CHAR(competencia, 'Month') AS mes,
        descricao_meta
    FROM vw_cadastro_metas
""", conn)

# Inicializar estado dos filtros
if 'filtros' not in st.session_state:
    st.session_state.filtros = {
        'nome_comercial': 'Todos',
        'ano': 'Todos',
        'mes': 'Todos',
        'descricao_meta': 'Todos'
    }

# Query principal
df_raw = pd.read_sql("""
    SELECT
        cm.nome_comercial,
        cm.descricao_meta AS categoria,
        TO_CHAR(cm.competencia, 'TMMonth') AS mes,
        TO_CHAR(cm.competencia, 'YYYY-MM') AS mes_ano,
        EXTRACT(YEAR FROM cm.competencia) AS ano,
        cm.valor_meta AS meta,
        COALESCE(rm.resultado, 0) AS resultado
    FROM vw_cadastro_metas cm
    LEFT JOIN vw_resultado_metas rm
        ON cm.id_meta = rm.id_meta
       AND cm.id_comercial = rm.id_comercial
       AND cm.competencia = rm.competencia
""", conn)

# Aplicar filtros salvos
filtros = st.session_state.filtros

df = df_raw.copy()
if filtros['nome_comercial'] != "Todos":
    df = df[df['nome_comercial'] == filtros['nome_comercial']]
if filtros['ano'] != "Todos":
    df = df[df['ano'] == int(filtros['ano'])]
if filtros['mes'] != "Todos":
    df = df[df['mes'].str.strip() == filtros['mes'].strip()]
if filtros['descricao_meta'] != "Todos":
    df = df[df['categoria'] == filtros['descricao_meta']]

# Sidebar com logo, filtros e exportação
with st.sidebar:
    
    st.image(LOGO_PATH, width=120)


    st.markdown("### Filtros")
    nome_comercial = st.selectbox("Nome Comercial", ["Todos"] + sorted(df_filtros['nome_comercial'].dropna().unique().tolist()), index=0)
    ano = st.selectbox("Ano", ["Todos"] + sorted(df_filtros['ano'].dropna().unique().astype(int).tolist(), reverse=True), index=0)
    mes = st.selectbox("Mês", ["Todos"] + sorted(df_filtros['mes'].dropna().str.strip().unique().tolist()), index=0)
    descricao_meta = st.selectbox("Categoria da Meta", ["Todos"] + sorted(df_filtros['descricao_meta'].dropna().unique().tolist()), index=0)

    st.session_state.filtros = {
        'nome_comercial': nome_comercial,
        'ano': ano,
        'mes': mes,
        'descricao_meta': descricao_meta
    }

    st.markdown("<hr style='margin-top:30px;margin-bottom:10px;'>", unsafe_allow_html=True)
    st.markdown("### Exportar Relatório")
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Relatorio')
    st.download_button(
        label="📁 Exportar XLSX",
        data=output.getvalue(),
        file_name="relatorio_metas.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

# Título
st.markdown("<div class='main-title'>Painel de Performance Comercial</div>", unsafe_allow_html=True)

# Exibição dos KPIs e gráficos
if not df.empty:
    st.markdown("### Indicadores por Categoria")
    col_kpis = st.columns(min(len(df['categoria'].unique()), 4))

    for i, cat in enumerate(df['categoria'].unique()):
        linha = df[df['categoria'] == cat]
        meta = linha['meta'].sum()
        resultado = linha['resultado'].sum()
        perc = calcular_percentual(meta, resultado)

        with col_kpis[i % 4]:
            st.markdown(f"""
                <div class='kpi-box'>
                    <div class='kpi-title'>{cat}</div>
                    <div class='kpi-meta'>Meta: {meta:.0f}</div>
                    <div class='kpi-resultado'>Resultado: {resultado:.0f}</div>
                    <progress value='{perc}' max='100' style='width:100%; height: 18px;'></progress>
                    <div class='progress-highlight'>{perc:.1f}% da meta</div>
                </div>
            """, unsafe_allow_html=True)

    df_comparativo = df.groupby('nome_comercial', as_index=False).agg(meta=('meta', 'sum'), resultado=('resultado', 'sum'))
    df_comparativo['perc_atingido'] = df_comparativo.apply(lambda row: calcular_percentual(row['meta'], row['resultado']), axis=1)

    fig2 = go.Figure()
    for _, row in df_comparativo.iterrows():
        fig2.add_trace(go.Bar(
            x=[row['nome_comercial']],
            y=[row['perc_atingido']],
            marker=dict(color='#295148'),
            text=f"{row['perc_atingido']:.1f}%",
            textposition='outside'
        ))
    fig2.update_layout(title="Ranking por Comercial", yaxis=dict(range=[0, 120], ticksuffix='%'))

    df_linha = (
        df.groupby(['mes_ano', 'mes'], as_index=False)
        .agg(meta=('meta', 'sum'), resultado=('resultado', 'sum'))
        .sort_values('mes_ano')
    )
    df_linha['perc'] = df_linha.apply(lambda row: calcular_percentual(row['meta'], row['resultado']), axis=1)
    melhor_mes = df_linha.loc[df_linha['perc'].idxmax()]

    fig3 = go.Figure()
    fig3.add_trace(go.Scatter(x=df_linha['mes'], y=df_linha['meta'], name='Meta', fill='tozeroy', line=dict(color='#C1FBAD')))
    fig3.add_trace(go.Scatter(x=df_linha['mes'], y=df_linha['resultado'], name='Resultado', fill='tozeroy', line=dict(color='#295148')))
    fig3.add_vline(x=melhor_mes['mes'], line_dash="dash", line_color="#192B23")
    fig3.update_layout(title="Evolução Mensal", hovermode='x unified')

    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(fig2, use_container_width=True)
    with col2:
        st.plotly_chart(fig3, use_container_width=True)
        st.markdown(f"<div style='text-align:center; font-size:14px;'>Melhor mês: <b>{melhor_mes['mes']}</b> com <b>{melhor_mes['perc']:.1f}%</b></div>", unsafe_allow_html=True)
else:
    st.warning("Aplique algum filtro ou verifique se há dados disponíveis para os critérios selecionados.")
