
import pandas as pd
import streamlit as st
import plotly.express as px

from datetime import datetime

try:
    from padrao_visual import (
        CORES_FAROL, aviso, barra_filtros, cabecalho, cartao, faixa_farol,
        grafico_duracao, grafico_evolucao, grafico_farol, secao, tabela_detalhada,
        tema_ativo, titulo_card, PLOTLY_CONFIG,
    )
except ModuleNotFoundError:  # quando as páginas são importadas como pacote (paginas.xxx)
    from paginas.padrao_visual import (
        CORES_FAROL, aviso, barra_filtros, cabecalho, cartao, faixa_farol,
        grafico_duracao, grafico_evolucao, grafico_farol, secao, tabela_detalhada,
        tema_ativo, titulo_card, PLOTLY_CONFIG,
    )

# ============================================================
# CONFIGURAÇÕES
# ============================================================

COLUNA_INICIO = "Data Presença Carga"
COLUNA_FIM = "Data Coleta Carga"

FAROIS = [
    "DENTRO DO PRAZO",
    "ATENÇÃO",
    "ALERTA",
    "ATRASO",
    "SEM DATA",
    "REVISAR REGRA",
]


# ============================================================
# CÁLCULO DE DIAS
# ============================================================

def calcular_dias_armazenagem(df):
    """
    Simulação:
    - Data Presença Carga é o início da contagem.
    - Como a base fictícia não possui Data Coleta Carga,
      todos os processos com presença são considerados
      ainda sem coleta.
    - Calcula dias completos até o momento atual.
    """

    dados = df.copy()

    dados[COLUNA_INICIO] = pd.to_datetime(
        dados[COLUNA_INICIO],
        errors="coerce"
    )

    agora = pd.Timestamp.now(tz="America/Sao_Paulo").tz_localize(None)

    # Coluna criada apenas para viabilizar a estrutura da tabela.
    # Não representa um campo existente na base fictícia.
    dados[COLUNA_FIM] = pd.NaT

    dados["Dias"] = pd.NA

    validos = dados[COLUNA_INICIO].notna()

    diferenca = (
        agora - dados.loc[validos, COLUNA_INICIO]
    ).dt.days

    dados.loc[validos, "Dias"] = diferenca

    dados["Dias"] = pd.to_numeric(
        dados["Dias"],
        errors="coerce"
    )

    return dados


# ============================================================
# CLASSIFICAÇÃO DO FAROL
# ============================================================

def classificar_farol(linha):

    modal = str(linha.get("Modal", "")).strip().upper()

    estufagem = str(
        linha.get("Estufagem", "")
    ).strip().upper()

    dias = linha.get("Dias")

    if pd.isna(dias):
        return "SEM DATA"

    dias = int(dias)

    if dias < 0:
        return "REVISAR REGRA"

    # --------------------------------------------------------
    # MARÍTIMO FCL
    # --------------------------------------------------------

    if modal == "MARÍTIMO" and estufagem == "FCL":

        if dias < 7:
            return "DENTRO DO PRAZO"

        elif dias < 10:
            return "ATENÇÃO"

        elif dias <= 15:
            return "ALERTA"

        else:
            return "ATRASO"

    # --------------------------------------------------------
    # MARÍTIMO LCL
    # --------------------------------------------------------

    elif modal == "MARÍTIMO" and estufagem == "LCL":

        if dias <= 7:
            return "DENTRO DO PRAZO"

        elif dias < 10:
            return "ATENÇÃO"

        elif dias <= 14:
            return "ALERTA"

        else:
            return "ATRASO"

    # --------------------------------------------------------
    # AÉREO
    # --------------------------------------------------------

    elif modal == "AÉREO":

        if dias < 6:
            return "DENTRO DO PRAZO"

        elif dias < 8:
            return "ATENÇÃO"

        elif dias <= 10:
            return "ALERTA"

        else:
            return "ATRASO"

    # --------------------------------------------------------
    # RODOVIÁRIO
    # --------------------------------------------------------

    elif modal == "RODOVIÁRIO":

        if dias <= 3:
            return "DENTRO DO PRAZO"

        elif dias <= 6:
            return "ATENÇÃO"

        elif dias <= 9:
            return "ALERTA"

        else:
            return "ATRASO"

    return "REVISAR REGRA"


# ============================================================
# PREPARAÇÃO DOS DADOS
# ============================================================

def preparar_dados_armazenagem(df):

    dados = df.copy()

    if COLUNA_INICIO not in dados.columns:
        st.error(
            f"A coluna obrigatória '{COLUNA_INICIO}' "
            "não foi encontrada na base."
        )
        return pd.DataFrame()

    if "Modal" not in dados.columns:
        st.error("A coluna 'Modal' não foi encontrada na base.")
        return pd.DataFrame()

    if "Estufagem" not in dados.columns:
        st.error("A coluna 'Estufagem' não foi encontrada na base.")
        return pd.DataFrame()

    dados = calcular_dias_armazenagem(dados)

    dados["Farol da etapa"] = dados.apply(
        classificar_farol,
        axis=1
    )

    dados["Situação da etapa"] = dados[COLUNA_INICIO].apply(
        lambda x: "Em andamento" if pd.notna(x) else "Concluída"
    )

    # Processos sem data de presença não entram no controle.
    dados = dados[dados[COLUNA_INICIO].notna()].copy()

    return dados


# ============================================================
# PÁGINA PRINCIPAL
# ============================================================

def pagina_armazenagem(df):

    cabecalho(
        titulo="Armazenagem",
        subtitulo="Acompanhamento dos prazos de armazenagem.",
        chave="armazenagem",
    )

    dados = preparar_dados_armazenagem(df)

    if dados.empty:
        aviso(
            "Não existem processos com Data Presença Carga "
            "preenchida para análise.",
            tipo="atencao"
        )
        return

    aviso(
        "SIMULAÇÃO: a base fictícia não possui o campo "
        "'Data Coleta Carga'. Portanto, todos os processos "
        "com Data Presença Carga preenchida são considerados "
        "sem coleta. Os dias são calculados até o momento atual.",
        tipo="atencao"
    )

    # ========================================================
    # FILTROS
    # ========================================================

    secao(
        "Filtros",
        "Utilize os filtros para localizar processos específicos."
    )

    filtrado = barra_filtros(
        dados,
        COLUNA_INICIO,
        "armazenagem"
    )

    if filtrado.empty:
        aviso(
            "Nenhum processo encontrado com os filtros selecionados.",
            tipo="info"
        )
        return

    # ========================================================
    # INDICADORES
    # ========================================================

    secao(
        "Indicadores de armazenagem",
        "Resumo dos processos em acompanhamento."
    )

    total = len(filtrado)

    dentro = (
        filtrado["Farol da etapa"] == "DENTRO DO PRAZO"
    ).sum()

    atencao = (
        filtrado["Farol da etapa"] == "ATENÇÃO"
    ).sum()

    alerta = (
        filtrado["Farol da etapa"] == "ALERTA"
    ).sum()

    atraso = (
        filtrado["Farol da etapa"] == "ATRASO"
    ).sum()

    media_dias = filtrado["Dias"].mean()

    c1, c2, c3, c4, c5 = st.columns(5)

    with c1:
        cartao(
            "Total de processos",
            f"{total}",
            "Processos em acompanhamento",
            "#1F6FB2"
        )

    with c2:
        cartao(
            "Dentro do prazo",
            f"{dentro}",
            f"{dentro / total:.1%} do total",
            CORES_FAROL["DENTRO DO PRAZO"]
        )

    with c3:
        cartao(
            "Atenção",
            f"{atencao}",
            f"{atencao / total:.1%} do total",
            CORES_FAROL["ATENÇÃO"]
        )

    with c4:
        cartao(
            "Alerta",
            f"{alerta}",
            f"{alerta / total:.1%} do total",
            CORES_FAROL["ALERTA"]
        )

    with c5:
        cartao(
            "Atrasados",
            f"{atraso}",
            f"{atraso / total:.1%} do total",
            CORES_FAROL["ATRASO"]
        )

    st.write("")

    c6, c7 = st.columns(2)

    with c6:
        cartao(
            "Média de dias",
            f"{media_dias:.1f}" if pd.notna(media_dias) else "—",
            "Dias completos desde a presença da carga",
            "#1F6FB2"
        )

    with c7:
        cartao(
            "Sem classificação",
            str(
                filtrado["Farol da etapa"].isin(
                    ["SEM DATA", "REVISAR REGRA"]
                ).sum()
            ),
            "Processos sem regra aplicável",
            CORES_FAROL["REVISAR REGRA"]
        )

    # ========================================================
    # DISTRIBUIÇÃO DOS FARÓIS
    # ========================================================

    secao(
        "Distribuição dos faróis",
        "Distribuição dos processos conforme os limites de armazenagem."
    )

    contagem = (
        filtrado["Farol da etapa"]
        .value_counts()
        .reindex(FAROIS, fill_value=0)
    )

    faixa_farol(contagem, total)

    col1, col2 = st.columns([1, 1])

    with col1:
        grafico_farol(
            filtrado,
            "armazenagem"
        )

    with col2:

        resumo = (
            filtrado["Farol da etapa"]
            .value_counts()
            .reindex(FAROIS, fill_value=0)
            .reset_index()
        )

        resumo.columns = ["Farol", "Processos"]

        resumo = resumo[resumo["Processos"] > 0]

        fig = px.bar(
            resumo,
            x="Farol",
            y="Processos",
            color="Farol",
            color_discrete_map=CORES_FAROL,
            text="Processos",
            category_orders={"Farol": FAROIS}
        )

        fig.update_traces(
            textposition="outside",
            cliponaxis=False
        )

        fig.update_layout(
            xaxis_title="Classificação",
            yaxis_title="Quantidade de processos",
            showlegend=False
        )


        st.plotly_chart(
            fig,
            use_container_width=True,
            config=PLOTLY_CONFIG,
            key="grafico_barras_armazenagem"
        )

    # ========================================================
    # DISTRIBUIÇÃO POR MODAL
    # ========================================================

    secao(
        "Análise por modal",
        "Comparativo dos processos conforme a modalidade de transporte."
    )

    resumo_modal = (
        filtrado.groupby(
            ["Modal", "Farol da etapa"]
        )
        .size()
        .reset_index(name="Processos")
    )

    fig_modal = px.bar(
        resumo_modal,
        x="Modal",
        y="Processos",
        color="Farol da etapa",
        color_discrete_map=CORES_FAROL,
        barmode="stack",
        category_orders={
            "Farol da etapa": FAROIS
        },
        text_auto=True
    )

    fig_modal.update_layout(
        xaxis_title="Modal",
        yaxis_title="Quantidade de processos",
        legend_title="Farol"
    )

    st.plotly_chart(
        fig_modal,
        use_container_width=True,
        config=PLOTLY_CONFIG,
        key="grafico_modal_armazenagem"
    )

    # ========================================================
    # TABELA DETALHADA
    # ========================================================

    secao(
        "Detalhamento dos processos",
        "Consulte os processos, seus respectivos dias de armazenagem "
        "e a classificação atual."
    )

    tabela_detalhada(
        filtrado,
        COLUNA_INICIO,
        COLUNA_FIM,
        "armazenagem",
        "controle_armazenagem.csv"
    )
