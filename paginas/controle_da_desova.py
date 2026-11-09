
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from paginas.padrao_visual import (
    cabecalho,
    cartao,
    secao,
    aviso,
    faixa_farol,
    CORES_FAROL,
    PLOTLY_CONFIG,
    tema_ativo,
    base_layout,
)


# ============================================================
# CONFIGURAÇÕES
# ============================================================

ORDEM_FAROIS = [
    "DENTRO DO PRAZO",
    "ATENÇÃO",
    "ALERTA",
    "ATRASO",
    "REVISAR REGRA",
    "SEM DATA",
]

EMOJIS = {
    "DENTRO DO PRAZO": "🟢",
    "ATENÇÃO": "🟡",
    "ALERTA": "🟠",
    "ATRASO": "🔴",
    "REVISAR REGRA": "⚪",
    "SEM DATA": "⚪",
}

COLUNAS_BASE = [
    "Status",
    "Ref.Cliente",
    "Nº Processo",
    "Responsável",
    "Categoria",
    "Exportador",
    "Modal",
    "Data Presença Carga",
    "Data Registro DI/DUIMP",
    "Data Solicitação Desova",
    "Data Realização Desova",
]


# ============================================================
# TRATAMENTO E CÁLCULOS
# ============================================================

def _converter_datas(df):
    dados = df.copy()

    for coluna in COLUNAS_BASE:
        if coluna not in dados.columns:
            dados[coluna] = pd.NaT if coluna.startswith("Data ") else ""

    colunas_data = [c for c in COLUNAS_BASE if c.startswith("Data ")]

    for coluna in colunas_data:
        dados[coluna] = pd.to_datetime(
            dados[coluna], errors="coerce"
        )

    return dados


def _horas_uteis(inicio, fim):
    """
    Calcula horas decorridas de segunda a sexta.
    Considera o dia útil completo, sem limitar horário comercial.
    """

    if pd.isna(inicio) or pd.isna(fim):
        return None

    inicio = pd.Timestamp(inicio)
    fim = pd.Timestamp(fim)

    if fim < inicio:
        return None

    if inicio == fim:
        return 0.0

    total = 0.0
    dia = inicio.normalize()

    while dia < fim:
        if dia.weekday() < 5:
            inicio_dia = max(inicio, dia)
            fim_dia = min(fim, dia + pd.Timedelta(days=1))

            if fim_dia > inicio_dia:
                total += (
                    fim_dia - inicio_dia
                ).total_seconds() / 3600

        dia += pd.Timedelta(days=1)

    return total


def _classificar_horas(horas):
    if pd.isna(horas):
        return "SEM DATA"

    if horas < 0:
        return "REVISAR REGRA"

    if horas <= 12:
        return "DENTRO DO PRAZO"

    if horas <= 24:
        return "ATENÇÃO"

    return "ATRASO"


def _classificar_dias(dias):
    if pd.isna(dias):
        return "SEM DATA"

    if dias < 0:
        return "REVISAR REGRA"

    if dias <= 1:
        return "DENTRO DO PRAZO"

    if dias <= 2:
        return "ATENÇÃO"

    if dias == 3:
        return "ALERTA"

    if dias > 5:
        return "ATRASO"

    # A planilha não define a classificação de 4 e 5 dias.
    return "REVISAR REGRA"


def _preparar_solicitacao(df, tipo):
    dados = df.copy()

    coluna_inicio = (
        "Data Presença Carga"
        if tipo == "antes"
        else "Data Registro DI/DUIMP"
    )

    coluna_fim = "Data Solicitação Desova"

    inicio = dados[coluna_inicio]
    fim = dados[coluna_fim]

    # Separa as solicitações conforme a posição da solicitação
    # em relação ao registro da DI.
    if tipo == "antes":
        mascara = (
            dados[coluna_fim].notna()
            & (
                dados["Data Registro DI/DUIMP"].isna()
                | (
                    dados[coluna_fim]
                    <= dados["Data Registro DI/DUIMP"]
                )
            )
        )
    else:
        mascara = (
            dados[coluna_fim].notna()
            & dados["Data Registro DI/DUIMP"].notna()
            & (
                dados[coluna_fim]
                > dados["Data Registro DI/DUIMP"]
            )
        )

    dados = dados.loc[mascara].copy()

    # Para solicitações ainda não realizadas, conta até o momento atual.
    agora = pd.Timestamp.now()

    fim_calculo = dados[coluna_fim].fillna(agora)

    dados["Horas"] = [
        _horas_uteis(i, f)
        for i, f in zip(dados[coluna_inicio], fim_calculo)
    ]

    dados["Dias"] = dados["Horas"] / 24

    dados["Farol"] = dados["Horas"].apply(
        _classificar_horas
    )

    dados["Situação"] = dados[coluna_fim].apply(
        lambda x: "Concluída" if pd.notna(x) else "Em andamento"
    )

    dados["Data Inicial"] = dados[coluna_inicio]
    dados["Data Final"] = dados[coluna_fim]

    return dados


def _preparar_realizacao(df):
    dados = df.copy()

    inicio = dados["Data Solicitação Desova"]
    fim = dados["Data Realização Desova"]

    agora = pd.Timestamp.now()
    fim_calculo = fim.fillna(agora)

    dados["Dias"] = (
        fim_calculo - inicio
    ).dt.total_seconds() / 86400

    dados.loc[
        inicio.isna() | (dados["Dias"] < 0),
        "Dias"
    ] = float("nan")

    dados["Farol"] = dados["Dias"].apply(
        _classificar_dias
    )

    dados["Situação"] = fim.apply(
        lambda x: "Concluída" if pd.notna(x) else "Em andamento"
    )

    dados["Data Inicial"] = inicio
    dados["Data Final"] = fim

    return dados


# ============================================================
# FILTROS
# ============================================================

def _filtros(dados, chave):
    filtrado = dados.copy()

    st.markdown("#### Filtros")

    c1, c2, c3, c4 = st.columns([1.3, 1.3, 1, 1])

    with c1:
        referencia = st.text_input(
            "Referência do cliente",
            key=f"desova_ref_{chave}",
            placeholder="Pesquisar referência...",
        ).strip()

    with c2:
        processo = st.text_input(
            "Nº do processo",
            key=f"desova_proc_{chave}",
            placeholder="Pesquisar processo...",
        ).strip()

    with c3:
        farois_disponiveis = [
            f for f in ORDEM_FAROIS
            if f in filtrado["Farol"].unique()
        ]

        farois = st.multiselect(
            "Farol",
            farois_disponiveis,
            key=f"desova_farol_{chave}",
            placeholder="Todos",
        )

    with c4:
        situacao = st.selectbox(
            "Situação",
            ["Todas", "Em andamento", "Concluída"],
            key=f"desova_situacao_{chave}",
        )

    if referencia:
        filtrado = filtrado[
            filtrado["Ref.Cliente"].astype(str)
            .str.contains(referencia, case=False, na=False)
        ]

    if processo:
        filtrado = filtrado[
            filtrado["Nº Processo"].astype(str)
            .str.contains(processo, case=False, na=False)
        ]

    if farois:
        filtrado = filtrado[
            filtrado["Farol"].isin(farois)
        ]

    if situacao != "Todas":
        filtrado = filtrado[
            filtrado["Situação"] == situacao
        ]

    return filtrado


# ============================================================
# INDICADORES
# ============================================================

def _indicadores(dados, chave):
    total = len(dados)

    contagem = (
        dados["Farol"]
        .value_counts()
        .reindex(ORDEM_FAROIS, fill_value=0)
    )

    st.markdown("#### Distribuição dos prazos")

    colunas = st.columns(5)

    indicadores = [
        ("Dentro do prazo", "DENTRO DO PRAZO"),
        ("Atenção", "ATENÇÃO"),
        ("Alerta", "ALERTA"),
        ("Atraso", "ATRASO"),
        ("Revisar regra / Sem data", "REVISAR REGRA"),
    ]

    for coluna, (titulo, farol) in zip(colunas, indicadores):
        quantidade = int(contagem.get(farol, 0))

        percentual = (
            quantidade / total * 100
            if total else 0
        )

        with coluna:
            cartao(
                titulo,
                quantidade,
                f"{percentual:.1f}% dos processos",
                CORES_FAROL.get(farol, "#8795A5"),
            )

    if total:
        faixa_farol(contagem.to_dict(), total)


# ============================================================
# GRÁFICO
# ============================================================

def _grafico_farol(dados, chave):
    resumo = (
        dados["Farol"]
        .value_counts()
        .reindex(ORDEM_FAROIS, fill_value=0)
    )

    resumo = resumo[resumo > 0]

    if resumo.empty:
        aviso("Não há dados suficientes para gerar o gráfico.")
        return

    tema = tema_ativo()

    fig = go.Figure(
        data=[
            go.Pie(
                labels=[
                    f"{EMOJIS.get(f, '')} {f.title()}"
                    for f in resumo.index
                ],
                values=resumo.values.tolist(),
                hole=0.68,
                sort=False,
                marker=dict(
                    colors=[
                        CORES_FAROL.get(f, "#8795A5")
                        for f in resumo.index
                    ],
                    line=dict(
                        color=tema["cartao"],
                        width=3,
                    ),
                ),
                textinfo="percent",
                hovertemplate=(
                    "<b>%{label}</b><br>"
                    "Processos: %{value}<br>"
                    "Participação: %{percent}"
                    "<extra></extra>"
                ),
            )
        ]
    )

    total = int(resumo.sum())

    fig.add_annotation(
        text=(
            f"<b><span style='font-size:30px;color:{tema['texto']}'>"
            f"{total}</span></b><br>"
            f"<span style='color:{tema['texto3']}'>processos</span>"
        ),
        x=0.5,
        y=0.5,
        showarrow=False,
    )

    base_layout(fig, 320)

    st.plotly_chart(
        fig,
        use_container_width=True,
        config=PLOTLY_CONFIG,
        key=f"grafico_desova_{chave}",
        theme=None,
    )


# ============================================================
# TABELA
# ============================================================

def _formatar_data(valor):
    if pd.isna(valor):
        return "—"

    return pd.Timestamp(valor).strftime("%d/%m/%Y %H:%M")


def _tabela(dados, tipo, chave):
    st.markdown("#### Detalhamento dos processos")

    if dados.empty:
        aviso("Nenhum processo encontrado com os filtros selecionados.")
        return

    colunas = [
        "Status",
        "Ref.Cliente",
        "Nº Processo",
        "Responsável",
        "Categoria",
        "Exportador",
        "Modal",
    ]

    if tipo in ("antes", "depois"):
        colunas += [
            "Data Presença Carga",
            "Data Registro DI/DUIMP",
            "Data Solicitação Desova",
            "Horas",
            "Farol",
            "Situação",
        ]
    else:
        colunas += [
            "Data Solicitação Desova",
            "Data Realização Desova",
            "Dias",
            "Farol",
            "Situação",
        ]

    tabela = dados.copy()

    for coluna in [
        "Data Presença Carga",
        "Data Registro DI/DUIMP",
        "Data Solicitação Desova",
        "Data Realização Desova",
    ]:
        if coluna in tabela.columns:
            tabela[coluna] = tabela[coluna].apply(_formatar_data)

    if "Horas" in tabela.columns:
        tabela["Horas"] = tabela["Horas"].apply(
            lambda x: f"{x:.1f} h" if pd.notna(x) else "—"
        )

    if "Dias" in tabela.columns:
        tabela["Dias"] = tabela["Dias"].apply(
            lambda x: f"{x:.1f}" if pd.notna(x) else "—"
        )

    tabela["Icon"] = tabela["Farol"].map(EMOJIS)

    if tipo in ("antes", "depois"):
        colunas += ["Icon"]
    else:
        colunas += ["Icon"]

    tabela = tabela[colunas].copy()

    st.dataframe(
        tabela,
        use_container_width=True,
        hide_index=True,
        height=440,
        key=f"tabela_desova_{chave}",
    )

    csv = tabela.to_csv(
        index=False,
        sep=";",
        encoding="utf-8-sig",
    )

    st.download_button(
        "⬇️ Exportar dados em CSV",
        data=csv,
        file_name=f"controle_desova_{chave}.csv",
        mime="text/csv",
        key=f"download_desova_{chave}",
    )


# ============================================================
# BLOCO DE CADA MEDIÇÃO
# ============================================================

def _bloco_medicao(df, titulo, descricao, tipo, chave):
    secao(titulo, descricao)

    if tipo == "realizacao":
        dados = _preparar_realizacao(df)
    else:
        dados = _preparar_solicitacao(df, tipo)

    if dados.empty:
        aviso("Não existem processos disponíveis para esta medição.")
        return

    filtrado = _filtros(dados, chave)

    _indicadores(filtrado, chave)

    st.markdown("#### Visão geral dos faróis")

    _grafico_farol(filtrado, chave)

    _tabela(filtrado, tipo, chave)


# ============================================================
# PÁGINA PRINCIPAL
# ============================================================

def pagina_controle_da_desova(df):
    cabecalho(
        "Controle da Desova",
        "Acompanhamento das solicitações e da realização da desova",
        chave="controle_desova",
    )

    if df is None or df.empty:
        aviso("A base operacional não possui registros para exibir.", "atencao")
        return

    dados = _converter_datas(df)

    # Mantém somente processos identificados na etapa de desova,
    # sem descartar registros que tenham campos de data ainda vazios.
    if "Etapa" in dados.columns:
        dados = dados[
            dados["Etapa"].astype(str).str.contains(
                "Desova", case=False, na=False
            )
        ].copy()

    if dados.empty:
        aviso("Não foram encontrados processos da etapa de desova.")
        return

    antes, depois, realizacao = st.tabs([
        "01 · Desova Antes da DI",
        "02 · Solicitação Depois da DI",
        "03 · Realização da Desova",
    ])

    with antes:
        _bloco_medicao(
            dados,
            "Medição: Controle da Desova Antes da DI — Solicitação",
            "Tempo entre a presença da carga e a solicitação da desova, "
            "para solicitações anteriores ao registro da DI.",
            "antes",
            "desova_antes_di",
        )

    with depois:
        _bloco_medicao(
            dados,
            "Medição: Controle de Solicitação da Desova Depois da DI",
            "Tempo entre o registro da DI e a solicitação da desova. "
            "O cálculo considera dias de segunda a sexta-feira.",
            "depois",
            "desova_depois_di",
        )

    with realizacao:
        _bloco_medicao(
            dados,
            "Medição: Controle de Realização da Desova",
            "Tempo entre a solicitação e a realização efetiva da desova.",
            "realizacao",
            "desova_realizacao",
        )
