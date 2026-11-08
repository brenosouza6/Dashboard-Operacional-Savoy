
import streamlit as st
import pandas as pd
from pathlib import Path

# ==================================================
# IMPORTAÇÃO DAS PÁGINAS
# ==================================================
from paginas.home import pagina_home
from paginas.padrao_visual import aplicar_tema
from paginas.visao_geral import pagina_visao_geral
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
# MENU DE NAVEGAÇÃO
# ==================================================

st.sidebar.title("Dashboard Operacional - Savoy")

pagina = st.sidebar.radio(
    "Etapas",
    [
        "Home",
        "Visão Geral",
        "Prontidão",
        "Pré-Alerta",
        "Trânsito Internacional",
        "Numerários",
        "Controle da Desova",
        "Armazenagem",
        "Gestão Aduaneira",
        "Entrega de Carga",
        "Conclusão"
    ]
)

aplicar_tema()

# ==================================================
# EXIBIÇÃO DAS PÁGINAS
# ==================================================

# ==================================================
# EXIBIÇÃO DAS PÁGINAS
# ==================================================

if pagina == "Home":

    pagina_home()

elif pagina == "Visão Geral":
    pagina_visao_geral(dados)

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