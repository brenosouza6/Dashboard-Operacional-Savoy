
from pathlib import Path
import streamlit as st


def pagina_home():

    caminho_capa = (
        Path(__file__).resolve().parent.parent / "capa_dashboard.png"
    )

    st.markdown(
        """
        <style>
            [data-testid="stMainBlockContainer"] {
                max-width: 100% !important;
                padding: 0 !important;
                margin: 0 !important;
            }

            [data-testid="stImage"] {
                width: 100%;
            }

            [data-testid="stImage"] img {
                width: 100%;
                height: auto;
                display: block;
            }
        </style>
        """,
        unsafe_allow_html=True
    )

    if caminho_capa.exists():
        st.image(
            str(caminho_capa),
            use_container_width=True
        )
    else:
        st.error(
            f"Imagem da capa não encontrada: {caminho_capa}"
        )
