import streamlit as st
import pandas as pd
from db import get_connection
from utils import calcular_percentual, calcular_variacao

st.set_page_config("Performance Comercial", layout="wide")
st.title("📈 Performance Comercial")

conn = get_connection()

# Filtro de Representante
df_nomes = pd.read_sql("""
    SELECT DISTINCT nome_comercial
    FROM vw_cadastro_metas
    ORDER BY nome_comercial
""", conn)
nome_comercial = st.selectbox("Selecione o Representante", df_nomes['nome_comercial'])

# Filtro de mês
df_meses = pd.read_sql("""
    SELECT DISTINCT TO_CHAR(competencia, 'YYYY-MM') as mes
    FROM vw_cadastro_metas
    ORDER BY mes DESC
""", conn)
mes_selecionado = st.selectbox("Selecione o Mês", df_meses['mes'])

# Query principal: JOIN das duas views
query = """
SELECT
    cm.nome_comercial,
    cm.descricao_meta AS categoria,
    TO_CHAR(cm.competencia, 'YYYY-MM') as mes,
    cm.valor_meta AS meta,
    COALESCE(rm.resultado, 0) AS resultado
FROM vw_cadastro_metas cm
LEFT JOIN vw_resultado_metas rm
    ON cm.id_meta = rm.id_meta
   AND cm.id_comercial = rm.id_comercial
   AND cm.competencia = rm.competencia
WHERE cm.nome_comercial = %s
"""
df = pd.read_sql(query, conn, params=[nome_comercial])

# Divide entre mês atual e anterior
df_atual = df[df['mes'] == mes_selecionado]
ano, mes = mes_selecionado.split("-")
mes_anterior = pd.to_datetime(f"{ano}-{mes}-01") - pd.DateOffset(months=1)
mes_anterior_str = mes_anterior.strftime("%Y-%m")
df_anterior = df[df['mes'] == mes_anterior_str]

# KPIs
st.subheader(f"📌 KPIs - {mes_selecionado}")
colunas = st.columns(4)
categorias = ["Visitas", "Cotações", "Propostas", "Conversão"]

for i, cat in enumerate(categorias):
    atual = df_atual[df_atual['categoria'].str.lower() == cat.lower()]
    anterior = df_anterior[df_anterior['categoria'].str.lower() == cat.lower()]

    meta = atual['meta'].sum()
    resultado = atual['resultado'].sum()
    resultado_ant = anterior['resultado'].sum()

    perc = calcular_percentual(meta, resultado)
    variacao, cor = calcular_variacao(resultado, resultado_ant)

    with colunas[i]:
        st.metric(
            label=cat,
            value=f"{perc}%",
            delta=variacao,
            delta_color="normal"
        )
        st.markdown(
            f"<span style='color:{cor}; font-size: 16px;'>{'↑' if '+' in variacao else '↓'} {variacao}</span>",
            unsafe_allow_html=True
        )
