import pandas as pd
import plotly.express as px
import streamlit as st


CORES_FAROL = {
    "DENTRO DO PRAZO": "#239B56",
    "ATENÇÃO": "#E3B51A",
    "ALERTA": "#E67E22",
    "ATRASO": "#C0392B",
    "SEM DATA": "#8795A5",
    "REVISAR REGRA": "#6C757D",
}

ORDEM_ETAPAS = [
    "Prontidão",
    "Pré-Alerta",
    "Trânsito Internacional",
    "Controle de Numerário",
    "Controle de Desova",
    "Controle de Armazenagem",
    "Gestão Aduaneira",
    "Entrega da Carga",
    "Conclusão",
]


def _coluna_ou_vazia(df, coluna, padrao="Não informado"):
    if coluna in df.columns:
        return df[coluna].fillna(padrao).astype(str)
    return pd.Series([padrao] * len(df), index=df.index, dtype="object")


def _classificar_cliente(planta):
    texto = str(planta).strip().lower()
    if texto.startswith("savoy"):
        return "Savoy"
    if texto.startswith("coty"):
        return "Coty"
    return "Outros / não identificado"


def _preparar_base(df):
    dados = df.copy()

    if "Status" not in dados.columns:
        dados["Status"] = "Não informado"
    dados["Status"] = dados["Status"].fillna("Não informado").astype(str)

    if "Farol" not in dados.columns:
        dados["Farol"] = "SEM DATA"
    dados["Farol"] = (
        dados["Farol"].fillna("SEM DATA").astype(str).str.strip().str.upper()
    )

    dados["Cliente"] = _coluna_ou_vazia(dados, "Planta").apply(
        _classificar_cliente
    )

    if "Data Recebimento do Pedido" in dados.columns:
        dados["Data Recebimento do Pedido"] = pd.to_datetime(
            dados["Data Recebimento do Pedido"], errors="coerce"
        )
    else:
        dados["Data Recebimento do Pedido"] = pd.NaT

    if "Nº Processo" not in dados.columns:
        dados["Nº Processo"] = ""

    if "Ref.Cliente" not in dados.columns:
        dados["Ref.Cliente"] = ""

    return dados


def _metricas(df):
    total = len(df)
    concluidos = int(
        df["Status"].str.strip().str.casefold().eq("conclusão").sum()
    )
    ativos = total - concluidos
    farol = df["Farol"].value_counts()

    dentro = int(farol.get("DENTRO DO PRAZO", 0))
    atencao = int(farol.get("ATENÇÃO", 0))
    alerta = int(farol.get("ALERTA", 0))
    atraso = int(farol.get("ATRASO", 0))

    return {
        "total": total,
        "ativos": ativos,
        "concluidos": concluidos,
        "dentro": dentro,
        "atencao": atencao,
        "alerta": alerta,
        "atraso": atraso,
    }


def _grafico_farol(df):
    resumo = (
        df["Farol"].value_counts()
        .rename_axis("Farol")
        .reset_index(name="Processos")
    )
    if resumo.empty:
        st.info("Não há dados para apresentar.")
        return

    fig = px.pie(
        resumo,
        names="Farol",
        values="Processos",
        hole=0.60,
        color="Farol",
        color_discrete_map=CORES_FAROL,
    )   
    fig.update_traces(textposition="inside", textinfo="percent")
    fig.update_layout(
        height=320,
        margin=dict(t=15, b=10, l=5, r=5),
        legend_title_text="",
    )
    st.plotly_chart(fig, use_container_width=True)


def _grafico_etapas(df):
    resumo = df["Status"].value_counts().rename_axis("Etapa").reset_index(
        name="Processos"
    )
    ordem_existente = [etapa for etapa in ORDEM_ETAPAS if etapa in resumo["Etapa"].tolist()]
    ordem_existente += [
        etapa for etapa in resumo["Etapa"].tolist() if etapa not in ordem_existente
    ]
    resumo["Etapa"] = pd.Categorical(
        resumo["Etapa"], categories=ordem_existente, ordered=True
    )
    resumo = resumo.sort_values("Etapa")

    fig = px.bar(
        resumo,
        x="Etapa",
        y="Processos",
        text="Processos",
        color="Processos",
        color_continuous_scale="Blues",
    )
    fig.update_traces(textposition="outside")
    fig.update_layout(
        height=360,
        margin=dict(t=15, b=10, l=5, r=5),
        xaxis_title="",
        yaxis_title="Quantidade de processos",
        coloraxis_showscale=False,
    )
    st.plotly_chart(fig, use_container_width=True)


def _grafico_clientes(df):
    resumo = (
        df["Cliente"].value_counts()
        .rename_axis("Cliente")
        .reset_index(name="Processos")
    )
    fig = px.bar(
        resumo,
        x="Cliente",
        y="Processos",
        text="Processos",
        color="Cliente",
    )
    fig.update_traces(textposition="outside")
    fig.update_layout(
        height=300,
        margin=dict(t=15, b=10, l=5, r=5),
        xaxis_title="",
        yaxis_title="Quantidade de processos",
        showlegend=False,
    )
    st.plotly_chart(fig, use_container_width=True)


def _grafico_evolucao(df):
    serie = df.dropna(subset=["Data Recebimento do Pedido"]).copy()
    if serie.empty:
        st.info("Não há datas de recebimento válidas para montar a evolução mensal.")
        return

    serie["Mês"] = (
        serie["Data Recebimento do Pedido"].dt.to_period("M").dt.to_timestamp()
    )
    resumo = serie.groupby("Mês").size().reset_index(name="Processos recebidos")

    fig = px.line(
        resumo,
        x="Mês",
        y="Processos recebidos",
        markers=True,
    )
    fig.update_layout(
        height=300,
        margin=dict(t=15, b=10, l=5, r=5),
        xaxis_title="",
        yaxis_title="Processos recebidos",
    )
    st.plotly_chart(fig, use_container_width=True)


def _tabela_pendencias(df):
    pendencias = df[
        ~df["Status"].str.strip().str.casefold().eq("conclusão")
    ].copy()
    pendencias = pendencias[
        pendencias["Farol"].isin(["ATRASO", "ALERTA", "ATENÇÃO"])
    ]

    colunas = [
        "Status", "Ref.Cliente", "Nº Processo", "Responsável",
        "Planta", "Exportador", "Modal", "Farol", "Dias na Etapa",
    ]
    colunas = [coluna for coluna in colunas if coluna in pendencias.columns]

    if pendencias.empty:
        st.success("Não há pendências classificadas como Atenção, Alerta ou Atraso.")
        return

    if "Farol" in pendencias.columns:
        ordem = {"ATRASO": 0, "ALERTA": 1, "ATENÇÃO": 2}
        pendencias["_ordem"] = pendencias["Farol"].map(ordem)
        pendencias = pendencias.sort_values("_ordem").drop(columns="_ordem")

    st.dataframe(
        pendencias[colunas],
        use_container_width=True,
        hide_index=True,
        height=350,
    )


def pagina_visao_geral(df):
    st.title("Visão Geral")
    st.caption(
        "Painel executivo do gerenciamento de importações — Savoy, Coty e Pibernat"
    )

    dados = _preparar_base(df)

    if dados.empty:
        st.warning("Não há processos disponíveis para os filtros selecionados.")
        return

    m = _metricas(dados)

    # Indicadores principais
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total de processos", m["total"])
    c2.metric("Processos ativos", m["ativos"])
    c3.metric("Processos concluídos", m["concluidos"])
    c4.metric(
        "Percentual concluído",
        f'{(m["concluidos"] / m["total"] * 100):.1f}%' if m["total"] else "0%",
    )

    st.markdown("---")
    st.subheader("Panorama dos prazos")

    f1, f2, f3, f4 = st.columns(4)
    f1.metric("Dentro do prazo", m["dentro"])
    f2.metric("Atenção", m["atencao"])
    f3.metric("Alerta", m["alerta"])
    f4.metric("Atraso", m["atraso"])

    g1, g2 = st.columns([1, 1.35])
    with g1:
        st.markdown("**Distribuição por Farol**")
        _grafico_farol(dados)
    with g2:
        st.markdown("**Quantidade de processos por etapa**")
        _grafico_etapas(dados)

    st.markdown("---")
    st.subheader("Distribuição da operação")

    g3, g4 = st.columns(2)
    with g3:
        st.markdown("**Processos por cliente**")
        _grafico_clientes(dados)
    with g4:
        st.markdown("**Entrada de processos por mês**")
        _grafico_evolucao(dados)

    st.markdown("---")
    st.subheader("Pendências que exigem atenção")
    st.caption(
        "Exibe processos não concluídos cujo Farol está classificado como Atenção, Alerta ou Atraso."
    )
    _tabela_pendencias(dados)

