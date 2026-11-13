
import streamlit as st
import pandas as pd
from pathlib import Path

# ==================================================
# IMPORTAÇÃO DAS PÁGINAS
# ==================================================
from paginas.home import pagina_home
from paginas.padrao_visual import aplicar_tema
from paginas.prontidao import pagina_prontidao
from paginas.pre_alerta import pagina_pre_alerta
from paginas.transito_internacional import pagina_transito_internacional
from paginas.numerarios import pagina_numerarios
from paginas.controle_da_desova import pagina_controle_da_desova
from paginas.armazenagem import pagina_armazenagem
from paginas.gestao_aduaneira import pagina_gestao_aduaneira
from paginas.entrega_da_carga import pagina_entrega_da_carga
from paginas.conclusao import pagina_conclusao


# ==================================================
# CONFIGURAÇÃO DA PÁGINA
# ==================================================

st.set_page_config(
    page_title="Dashboard Operacional - Savoy",
    layout="wide"
)


# ==================================================
# CARREGAMENTO DA BASE DE DADOS
# ==================================================

@st.cache_data
def carregar_dados():

    pasta_projeto = Path(__file__).parent

    arquivos = list(pasta_projeto.glob("*.xlsx"))

    if not arquivos:
        st.error(
            "Não encontrei nenhum arquivo Excel na pasta do projeto."
        )
        st.stop()

    arquivo = arquivos[0]

    dados = pd.read_excel(
        arquivo,
        sheet_name="Base_Operacional"
    )

    return dados


dados = carregar_dados()


# ==================================================
# IDENTIDADE VISUAL E MENU DE NAVEGAÇÃO
# ==================================================

st.markdown("""
<style>
[data-testid="stSidebar"] {
    border-right: 1px solid rgba(150, 150, 150, 0.18);
}

.sidebar-brand {
    padding: 12px 8px 20px 8px;
    text-align: center;
}

.sidebar-brand-title {
    font-size: 21px;
    font-weight: 700;
    letter-spacing: 3px;
    margin-top: 10px;
}

.sidebar-brand-subtitle {
    font-size: 10px;
    letter-spacing: 2px;
    opacity: 0.65;
    margin-top: 4px;
}

.sidebar-divider {
    border: none;
    border-top: 1px solid rgba(150, 150, 150, 0.22);
    margin: 8px 0 18px 0;
}
</style>
""", unsafe_allow_html=True)

pasta_logos = Path(__file__).resolve().parent / "Arquivos png"

logo_savoy = None

if pasta_logos.exists():
    imagens = [
        arquivo for arquivo in pasta_logos.iterdir()
        if arquivo.suffix.lower() in [".png", ".jpg", ".jpeg", ".webp"]
    ]

    logo_savoy = next(
        (arquivo for arquivo in imagens
         if "savoy" in arquivo.stem.lower()),
        None
    )

with st.sidebar:
    if logo_savoy:
        st.image(str(logo_savoy), use_container_width=True)

    st.markdown("""
        <div class="sidebar-brand">
            <div class="sidebar-brand-title">SAVOY</div>
            <div class="sidebar-brand-subtitle">
                DASHBOARD OPERACIONAL
            </div>
        </div>
        <hr class="sidebar-divider">
    """, unsafe_allow_html=True)

    pagina = st.radio(
        "NAVEGAÇÃO",
        [
            "Home",
            "Prontidão",
            "Pré-Alerta",
            "Trânsito Internacional",
            "Numerários",
            "Controle da Desova",
            "Armazenagem",
            "Gestão Aduaneira",
            "Entrega de Carga",
            "Conclusão"
        ],
        key="menu_navegacao"
    )

# ==================================================
# EXIBIÇÃO DAS PÁGINAS
# ==================================================

if pagina == "Home":

    pagina_home()

elif pagina == "Prontidão":
    pagina_prontidao(dados)

elif pagina == "Pré-Alerta":
    pagina_pre_alerta(dados)

elif pagina == "Trânsito Internacional":
    pagina_transito_internacional(dados)

elif pagina == "Numerários":
    pagina_numerarios(dados)

elif pagina == "Controle da Desova":
    pagina_controle_da_desova(dados)

elif pagina == "Armazenagem":
    pagina_armazenagem(dados)

elif pagina == "Gestão Aduaneira":
    pagina_gestao_aduaneira(dados)

elif pagina == "Entrega de Carga":
    pagina_entrega_da_carga(dados)

elif pagina == "Conclusão":
    pagina_conclusao(dados)