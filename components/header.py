import streamlit as st
from style import LOGO_PATH, LOGO_BG_COLOR, TEXT_COLOR

# Cabeçalho superior com logo e título
def render_header():
    col1, col2 = st.columns([1, 5])
    with col1:
        st.image(str(LOGO_PATH), width=80)
    with col2:
        st.markdown(
            f"<h2 style='color:{TEXT_COLOR}; margin-top: 20px;'>Dashboard de Performance Comercial</h2>",
            unsafe_allow_html=True
        )

# Bloco de filtros estilizado
def render_filtros(filtro_comercial, filtro_mes, filtro_botao_limpar):
    with st.container():
        st.markdown(
            f"""
            <div style='background-color:{LOGO_BG_COLOR}; padding: 15px; border-radius: 10px; color: {TEXT_COLOR};'>
                <h4 style='margin-bottom: 10px;'>Filtros</h4>
            """,
            unsafe_allow_html=True
        )

        col1, col2, col3 = st.columns([3, 2, 1])
        with col1:
            filtro_comercial()
        with col2:
            filtro_mes()
        with col3:
            filtro_botao_limpar()

        st.markdown("</div>", unsafe_allow_html=True)
