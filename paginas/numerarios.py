
import hashlib
from datetime import date, timedelta

import pandas as pd
import streamlit as st

from paginas.padrao_visual import (
    cabecalho,
    secao,
    cartao,
    aviso,
    faixa_farol,
    CORES_FAROL,
    PLOTLY_CONFIG,
)

try:
    import plotly.express as px
    PLOTLY_DISPONIVEL = True
except ImportError:
    PLOTLY_DISPONIVEL = False


# ============================================================
# CONFIGURAÇÕES
# ============================================================

FAROL_ORDEM = [
    "DENTRO DO PRAZO",
    "ATENÇÃO",
    "ALERTA",
    "ATRASO",
]

CORES = {
    "DENTRO DO PRAZO": "#16A36A",
    "ATENÇÃO": "#E5A000",
    "ALERTA": "#E87524",
    "ATRASO": "#D64545",
}

HOJE = pd.Timestamp.today().normalize()


# ============================================================
# FUNÇÕES AUXILIARES
# ============================================================

def _localizar_coluna(df, alternativas):
    """Localiza uma coluna considerando possíveis variações do nome."""
    for coluna in alternativas:
        if coluna in df.columns:
            return coluna
    return None


def _texto(valor):
    if pd.isna(valor):
        return ""
    return str(valor).strip()


def _data(valor):
    return pd.to_datetime(valor, errors="coerce", dayfirst=True)


def _simular_data(referencia, deslocamento):
    """
    Cria uma data sintética determinística a partir da referência.
    Não altera a base original.
    """
    if pd.isna(referencia):
        return pd.NaT

    return pd.Timestamp(referencia).normalize() + timedelta(
        days=int(deslocamento)
    )


def _dias_uteis_nao():
    """Calcula dias corridos entre a data inicial e hoje."""
    return None


def _classificar_farol(dias):
    if pd.isna(dias):
        return "SEM DATA"

    dias = max(0, int(dias))

    if dias <= 1:
        return "DENTRO DO PRAZO"
    elif dias == 2:
        return "ATENÇÃO"
    elif dias == 3:
        return "ALERTA"

    return "ATRASO"


def _preparar_base(df):
    """
    Trabalha sempre sobre uma cópia.
    Campos inexistentes recebem valores sintéticos identificados.
    """
    dados = df.copy()

    obrigatorias = [
        "Status",
        "Ref.Cliente",
        "Nº Processo",
        "Responsável",
        "Categoria",
        "Exportador",
        "Modal",
    ]

    for coluna in obrigatorias:
        if coluna not in dados.columns:
            dados[coluna] = ""

    # Normalização de datas disponíveis
    for coluna in dados.columns:
        if "Data " in str(coluna):
            dados[coluna] = pd.to_datetime(
                dados[coluna],
                errors="coerce",
                dayfirst=True,
            )

    # Identificador para simulações determinísticas
    dados["_chave_simulacao"] = dados["Nº Processo"].astype(str)

    return dados


def _criar_data_sintetica(dados, coluna_origem, coluna_destino, minimo=0, maximo=5):
    """
    Cria uma data de demonstração a partir de outra data existente.
    O deslocamento é determinístico para cada processo.
    """
    if coluna_destino in dados.columns:
        dados[coluna_destino] = pd.to_datetime(
            dados[coluna_destino], errors="coerce"
        )
        return

    origem = (
        dados[coluna_origem]
        if coluna_origem in dados.columns
        else pd.Series(pd.NaT, index=dados.index)
    )

    valores = []

    for idx, referencia in origem.items():
        if pd.isna(referencia):
            valores.append(pd.NaT)
            continue

        chave = str(dados.at[idx, "_chave_simulacao"])
        digest = hashlib.md5(chave.encode("utf-8")).hexdigest()
        deslocamento = minimo + (
            int(digest[:8], 16) % (maximo - minimo + 1)
        )

        valores.append(_simular_data(referencia, deslocamento))

    dados[coluna_destino] = valores


def _criar_dias_farol(dados, coluna_inicio, coluna_fim=None):
    inicio = pd.to_datetime(dados[coluna_inicio], errors="coerce")

    if coluna_fim and coluna_fim in dados.columns:
        fim = pd.to_datetime(dados[coluna_fim], errors="coerce")
        referencia = fim.fillna(HOJE)
    else:
        referencia = pd.Series(HOJE, index=dados.index)

    dias = (referencia - inicio).dt.days
    dias = dias.where(inicio.notna())

    dados["Dias"] = dias.clip(lower=0)
    dados["Farol"] = dados["Dias"].apply(_classificar_farol)

    return dados


def _filtros(dados, chave):
    st.markdown("")

    col1, col2 = st.columns(2)

    with col1:
        referencias = sorted(
            dados["Ref.Cliente"]
            .dropna()
            .astype(str)
            .unique()
            .tolist()
        )

        referencia = st.selectbox(
            "Referência do Cliente",
            ["Todas"] + referencias,
            key=f"{chave}_ref_cliente",
        )

    with col2:
        processos = sorted(
            dados["Nº Processo"]
            .dropna()
            .astype(str)
            .unique()
            .tolist()
        )

        processo = st.selectbox(
            "Nº Processo",
            ["Todos"] + processos,
            key=f"{chave}_processo",
        )

    filtrado = dados.copy()

    if referencia != "Todas":
        filtrado = filtrado[
            filtrado["Ref.Cliente"].astype(str) == referencia
        ]

    if processo != "Todos":
        filtrado = filtrado[
            filtrado["Nº Processo"].astype(str) == processo
        ]

    return filtrado


def _indicadores_farol(dados, chave):
    total = len(dados)

    contagem = (
        dados["Farol"]
        .value_counts()
        .reindex(FAROL_ORDEM, fill_value=0)
    )

    st.markdown("")

    colunas = st.columns(4)

    for coluna, farol in zip(colunas, FAROL_ORDEM):
        quantidade = int(contagem[farol])
        percentual = quantidade / total * 100 if total else 0

        with coluna:
            cartao(
                farol.title(),
                quantidade,
                f"{percentual:.1f}% dos processos",
                CORES[farol],
            )

    if total:
        faixa_farol(contagem.to_dict(), total)


def _tabela(dados, colunas, chave):
    disponiveis = [c for c in colunas if c in dados.columns]

    if dados.empty:
        st.info("Nenhum processo encontrado com os filtros selecionados.")
        return

    tabela = dados[disponiveis].copy()

    for coluna in tabela.columns:
        if pd.api.types.is_datetime64_any_dtype(tabela[coluna]):
            tabela[coluna] = tabela[coluna].dt.strftime("%d/%m/%Y")
            tabela[coluna] = tabela[coluna].fillna("")

    if "Farol" in tabela.columns:
        tabela["Farol"] = tabela["Farol"].replace({
            "DENTRO DO PRAZO": "🟢 Dentro do Prazo",
            "ATENÇÃO": "🟡 Atenção",
            "ALERTA": "🟠 Alerta",
            "ATRASO": "🔴 Atraso",
            "SEM DATA": "⚪ Sem Data",
        })

    st.dataframe(
        tabela,
        use_container_width=True,
        hide_index=True,
        height=420,
        key=f"tabela_{chave}",
    )

    csv = tabela.to_csv(index=False, sep=";", encoding="utf-8-sig")

    st.download_button(
        "⬇️ Exportar tabela CSV",
        data=csv,
        file_name=f"{chave}.csv",
        mime="text/csv",
        key=f"download_{chave}",
    )


def _grafico_farol(dados, chave):
    if not PLOTLY_DISPONIVEL or dados.empty:
        return

    resumo = (
        dados["Farol"]
        .value_counts()
        .reindex(FAROL_ORDEM, fill_value=0)
        .reset_index()
    )

    resumo.columns = ["Farol", "Quantidade"]
    resumo = resumo[resumo["Quantidade"] > 0]

    if resumo.empty:
        return

    fig = px.bar(
        resumo,
        x="Farol",
        y="Quantidade",
        color="Farol",
        color_discrete_map=CORES,
        category_orders={"Farol": FAROL_ORDEM},
        text="Quantidade",
    )

    fig.update_layout(
        showlegend=False,
        height=280,
        margin=dict(l=10, r=10, t=20, b=10),
        xaxis_title="",
        yaxis_title="Quantidade de processos",
    )

    fig.update_traces(textposition="outside")

    st.plotly_chart(
        fig,
        use_container_width=True,
        key=f"grafico_farol_{chave}",
        config=PLOTLY_CONFIG,
    )


# ============================================================
# PREPARAÇÃO DOS TRÊS CONTROLES
# ============================================================

def _controle_pre_adm(base):
    dados = base.copy()

    # Campo de referência para a etapa pré-administrativa.
    # A data de instrução não existe na base fictícia.
    _criar_data_sintetica(
        dados,
        "Data Envio Instrução Desembaraço",
        "Data Instrução Despacho",
        0,
        2,
    )

    _criar_data_sintetica(
        dados,
        "Data Instrução Despacho",
        "Data Envio Numerário",
        0,
        5,
    )

    if "Solicita Numerário" not in dados.columns:
        dados["Solicita Numerário"] = "Sim (simulado)"

    dados = _criar_dias_farol(
        dados,
        "Data Instrução Despacho",
        "Data Envio Numerário",
    )

    return dados


def _controle_adm_cliente(base):
    dados = base.copy()

    # O campo de envio não existe com esse nome na base.
    # A data é criada somente para demonstração.
    _criar_data_sintetica(
        dados,
        "Data Envio Instrução Desembaraço",
        "Data Envio Numerário",
        0,
        5,
    )

    dados = _criar_dias_farol(
        dados,
        "Data Envio Numerário",
        None,
    )

    return dados


def _controle_pagamento(base):
    dados = base.copy()

    if "Ref.Pibernat" not in dados.columns:
        dados["Ref.Pibernat"] = dados["Nº Processo"].astype(str)

    if "Data Solicitação Numerário Cliente" not in dados.columns:
        dados["Data Solicitação Numerário Cliente"] = pd.NaT

    # A coluna Data Recebimento Numerário existe na base fictícia.
    # Mantemos seu valor original, sem presumir que equivale
    # ao campo do BI "Data Recebimento Numerário Cliente".
    if "Data Recebimento Numerário Cliente" not in dados.columns:
        dados["Data Recebimento Numerário Cliente"] = pd.NaT

    # Para demonstração, usamos a data de solicitação existente
    # como ponto de partida. Não substituímos datas reais.
    origem = "Data Solicitação Numerário Cliente"

    if dados[origem].isna().all():
        _criar_data_sintetica(
            dados,
            "Data Solicitação Numerário Cliente",
            "_Data Solicitação Simulada",
            0,
            0,
        )

        # Fallback: a data de recebimento existente é mantida
        # apenas como referência de demonstração.
        if "Data Recebimento Numerário" in dados.columns:
            dados["_Data Solicitação Simulada"] = (
                dados["Data Recebimento Numerário"]
                .apply(
                    lambda x: (
                        pd.Timestamp(x) - pd.Timedelta(days=1)
                        if pd.notna(x)
                        else pd.NaT
                    )
                )
            )

        origem = "_Data Solicitação Simulada"

    dados = _criar_dias_farol(
        dados,
        origem,
        "Data Recebimento Numerário Cliente",
    )

    return dados


# ============================================================
# PÁGINA PRINCIPAL
# ============================================================

def pagina_numerarios(df):

    cabecalho(
        "Controle de Numerários",
        "Acompanhamento das solicitações e pagamentos de numerários.",
        chave="numerarios",
    )

    if df is None or df.empty:
        aviso(
            "A base de dados está vazia. Verifique a importação da planilha.",
            "atencao",
        )
        return

    base = _preparar_base(df)

    st.caption(
        "Os campos inexistentes na planilha de demonstração são "
        "simulados nesta página. Eles não alteram a base original."
    )

    aba_pre, aba_adm, aba_pag = st.tabs([
        "1. Solicitação de Numerário — Pré-adm",
        "2. Solicitação de Numerário — Adm / Cliente",
        "3. Controle de Pagamento",
    ])

    # --------------------------------------------------------
    # ABA 1 — PRÉ-ADM
    # --------------------------------------------------------

    with aba_pre:

        dados = _controle_pre_adm(base)

        secao(
            "Controle de Solicitação de Numerário (pré-adm)",
            "Acompanhamento entre a instrução do despacho e o envio do numerário.",
        )

        aviso(
            "Dados de demonstração: as datas de instrução e envio "
            "são simuladas quando não existem na planilha.",
        )

        st.markdown("**Regra de medição**")
        st.caption(
            "0 a 1 dia: Dentro do Prazo | 2 dias: Atenção | "
            "3 dias: Alerta | Acima de 3 dias: Atraso."
        )

        filtrado = _filtros(dados, "pre_adm")

        _indicadores_farol(filtrado, "pre_adm")
        _grafico_farol(filtrado, "pre_adm")

        _tabela(
            filtrado,
            [
                "Status",
                "Ref.Cliente",
                "Nº Processo",
                "Responsável",
                "Categoria",
                "Exportador",
                "Modal",
                "Solicita Numerário",
                "Data Instrução Despacho",
                "Data Envio Numerário",
                "Dias",
                "Farol",
            ],
            "numerarios_pre_adm",
        )

    # --------------------------------------------------------
    # ABA 2 — ADM / CLIENTE
    # --------------------------------------------------------

    with aba_adm:

        dados = _controle_adm_cliente(base)

        secao(
            "Controle de Solicitação de Numerário (adm - cliente)",
            "Acompanhamento do envio da solicitação ao cliente.",
        )

        aviso(
            "A data de envio é simulada para demonstração quando "
            "não existe um campo equivalente na planilha.",
        )

        st.markdown("**Regra de medição**")
        st.caption(
            "0 a 1 dia: Dentro do Prazo | 2 dias: Atenção | "
            "3 dias: Alerta | Acima de 3 dias: Atraso."
        )

        filtrado = _filtros(dados, "adm_cliente")

        _indicadores_farol(filtrado, "adm_cliente")
        _grafico_farol(filtrado, "adm_cliente")

        _tabela(
            filtrado,
            [
                "Status",
                "Ref.Cliente",
                "Nº Processo",
                "Responsável",
                "Categoria",
                "Exportador",
                "Modal",
                "Data Envio Numerário",
            ],
            "numerarios_adm_cliente",
        )

    # --------------------------------------------------------
    # ABA 3 — PAGAMENTO
    # --------------------------------------------------------

    with aba_pag:

        dados = _controle_pagamento(base)

        secao(
            "Controle de Pagamento Numerário",
            "Acompanhamento entre a solicitação e o recebimento do numerário.",
        )

        aviso(
            "A coluna Data Recebimento Numerário da planilha original "
            "foi preservada. Ela não foi considerada automaticamente "
            "equivalente a Data Recebimento Numerário Cliente.",
        )

        st.markdown("**Regra de medição**")
        st.caption(
            "0 a 1 dia: Dentro do Prazo | 2 dias: Atenção | "
            "3 dias: Alerta | Acima de 3 dias: Atraso."
        )

        filtrado = _filtros(dados, "pagamento")

        _indicadores_farol(filtrado, "pagamento")
        _grafico_farol(filtrado, "pagamento")

        _tabela(
            filtrado,
            [
                "Status",
                "Ref.Cliente",
                "Ref.Pibernat",
                "Nº Processo",
                "Responsável",
                "Categoria",
                "Exportador",
                "Modal",
                "Data Solicitação Numerário Cliente",
                "Data Recebimento Numerário Cliente",
                "Dias",
                "Farol",
                "Icon",
            ],
            "numerarios_pagamento",
        )
