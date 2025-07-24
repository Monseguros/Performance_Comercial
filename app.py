import streamlit as st
import pandas as pd
from db import get_connection
from utils import calcular_percentual
import plotly.graph_objects as go
import plotly.express as px
from io import BytesIO

# Cores suaves e estilo
st.set_page_config(layout="wide")
st.markdown("""
    <style>
        body {
            background-color: #F5F8FA;
        }
        .kpi-box {
            background-color: #ffffff;
            border-radius: 15px;
            padding: 20px;
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.05);
            margin: 10px 0;
            transition: all 0.3s ease-in-out;
        }
        .kpi-box:hover {
            transform: scale(1.01);
        }
        .kpi-title {
            font-size: 18px;
            font-weight: 600;
            color: #333;
            margin-bottom: 8px;
        }
        .kpi-meta {
            font-size: 16px;
            color: #2C3E50;
            font-weight: bold;
        }
        .kpi-resultado {
            font-size: 16px;
            color: #16a085;
            font-weight: bold;
            margin-bottom: 8px;
        }
        .export-button button {
            background-color: #ffffff;
            color: #333;
            border: 1px solid #ccc;
            padding: 0.5rem 1rem;
            border-radius: 10px;
            font-weight: bold;
            transition: all 0.2s ease-in-out;
        }
        .export-button button:hover {
            background-color: #16a085;
            color: white;
            border-color: #16a085;
        }
        .container-box {
            background-color: #fff;
            padding: 30px;
            border-radius: 20px;
            box-shadow: 0 0 20px rgba(0,0,0,0.05);
            margin-bottom: 20px;
        }
    </style>
""", unsafe_allow_html=True)

st.markdown("""
    <div class='container-box'>
""", unsafe_allow_html=True)

st.title("\U0001F680 Painel de Performance Comercial")

conn = get_connection()

# Filtros separados com "Todos"
df_filtros = pd.read_sql("""
    SELECT DISTINCT 
        nome_comercial, 
        EXTRACT(YEAR FROM competencia) AS ano,
        TO_CHAR(competencia, 'Month') AS mes,
        descricao_meta
    FROM vw_cadastro_metas
""", conn)

with st.container():
    with st.expander("\U0001F9BC️ Filtros", expanded=True):
        col1, col2, col3, col4 = st.columns(4)
        nome_comercial = col1.selectbox("\U0001F464 Nome Comercial", ["Todos"] + sorted(df_filtros['nome_comercial'].dropna().unique().tolist()))
        ano = col2.selectbox("\U0001F4C5 Ano", ["Todos"] + sorted(df_filtros['ano'].dropna().unique().astype(int).tolist(), reverse=True))
        mes = col3.selectbox("\U0001F5D3️ Mês", ["Todos"] + sorted(df_filtros['mes'].dropna().str.strip().unique().tolist()))
        descricao_meta = col4.selectbox("\U0001F3F7️ Categoria da Meta", ["Todos"] + sorted(df_filtros['descricao_meta'].dropna().unique().tolist()))

        if st.button("\U0001F9F9", help="Limpar Filtros"):
            st.session_state.clear()
            st.rerun()

# Query principal
df = pd.read_sql("""
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

# Aplicar filtros
if nome_comercial != "Todos":
    df = df[df['nome_comercial'] == nome_comercial]
if ano != "Todos":
    df = df[df['ano'] == int(ano)]
if mes != "Todos":
    df = df[df['mes'].str.strip() == mes.strip()]
if descricao_meta != "Todos":
    df = df[df['categoria'] == descricao_meta]

if not df.empty:
    st.subheader("\U0001F4CA Indicadores por Categoria")
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
                    <div style='text-align:center; font-size:14px; margin-top:5px;'>{perc:.1f}% da meta</div>
                </div>
            """, unsafe_allow_html=True)

    st.markdown("---")

    df_comparativo = (
        df.groupby('nome_comercial', as_index=False)
          .agg(meta=('meta', 'sum'), resultado=('resultado', 'sum'))
    )

    def calc_perc(row):
        try:
            return (row['resultado'] / row['meta'] * 100) if row['meta'] > 0 else 0
        except ZeroDivisionError:
            return 0

    df_comparativo['perc_atingido'] = df_comparativo.apply(calc_perc, axis=1)
    df_comparativo = df_comparativo.sort_values('perc_atingido', ascending=False).reset_index(drop=True)

    cor_padrao = 'rgba(58, 134, 255, 0.8)'

    fig2 = go.Figure()

    for _, row in df_comparativo.iterrows():
        fig2.add_trace(go.Bar(
            x=[row['nome_comercial']],
            y=[row['perc_atingido']],
            marker=dict(color=cor_padrao),
            text=f"{row['perc_atingido']:.1f}%",
            textposition='outside',
            textfont=dict(size=14, color='black', family='Arial'),
            hovertemplate=(
                f"<b>{row['nome_comercial']}</b><br>"
                f"Meta: {row['meta']:.0f}<br>"
                f"Resultado: {row['resultado']:.0f}<br>"
                f"% da Meta: {row['perc_atingido']:.1f}%<extra></extra>"
            ),
            width=0.5
        ))

    fig2.update_layout(
        barmode='group',
        yaxis=dict(range=[0, 120], ticksuffix='%', showgrid=False, title=''),
        xaxis=dict(title='', tickangle=0),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color="#333", size=13),
        showlegend=False,
        margin=dict(t=40, b=100)
    )

    # Gráfico de linha com preenchimento e mês por nome
    df_linha = (
        df.groupby(['mes_ano', 'mes'], as_index=False)
        .agg(meta=('meta', 'sum'), resultado=('resultado', 'sum'))
        .sort_values('mes_ano')
    )
    df_linha['perc'] = df_linha.apply(lambda row: calcular_percentual(row['meta'], row['resultado']), axis=1)
    melhor_mes = df_linha.loc[df_linha['perc'].idxmax()]

    fig3 = go.Figure()
    fig3.add_trace(go.Scatter(
        x=df_linha['mes'],
        y=df_linha['meta'],
        mode='lines+markers',
        name='Meta',
        line=dict(color='rgba(239, 71, 111, 1)', width=3),
        fill='tozeroy',
        fillcolor='rgba(239, 71, 111, 0.1)'
    ))
    fig3.add_trace(go.Scatter(
        x=df_linha['mes'],
        y=df_linha['resultado'],
        mode='lines+markers',
        name='Resultado',
        line=dict(color='rgba(0, 206, 201, 1)', width=3),
        fill='tozeroy',
        fillcolor='rgba(0, 206, 201, 0.1)'
    ))
    fig3.add_vline(x=melhor_mes['mes'], line_width=2, line_dash="dash", line_color="green")
    fig3.update_layout(
        title="\U0001F4C8 Evolução Mensal - Meta x Resultado",
        xaxis_title="Mês",
        yaxis_title="Valor",
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color="#333", size=13),
        hovermode='x unified'
    )

    col_left, col_right = st.columns([1, 1])

    with col_left:
        st.markdown("""
            <div class='kpi-box'>
                <div class='kpi-title'>\U0001F465 Ranking dos Comerciais por % da Meta Atingida</div>
        """, unsafe_allow_html=True)
        st.plotly_chart(fig2, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with col_right:
        st.markdown("""
            <div class='kpi-box'>
                <div class='kpi-title'>\U0001F4C8 Análise Mensal</div>
        """, unsafe_allow_html=True)
        st.plotly_chart(fig3, use_container_width=True)
        st.markdown(f"<div style='text-align:center; font-size:14px;'>\U0001F389 Melhor desempenho: <b>{melhor_mes['mes']}</b> com <b>{melhor_mes['perc']:.1f}%</b> da meta atingida</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div class='export-button'>", unsafe_allow_html=True)
    output = BytesIO()
    df_export = df.copy()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df_export.to_excel(writer, index=False, sheet_name='Relatorio')
    st.download_button(
        label="\U0001F4BE Exportar Relatório XLSX",
        data=output.getvalue(),
        file_name="relatorio_metas.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    st.markdown("</div>", unsafe_allow_html=True)

else:
    st.info("Aplique algum filtro ou verifique se existem dados para os filtros selecionados.")

st.markdown("</div>", unsafe_allow_html=True)
