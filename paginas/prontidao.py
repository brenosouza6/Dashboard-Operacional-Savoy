import pandas as pd
import streamlit as st

try:
    from padrao_visual import (
        CORES_FAROL, ORDEM_FAROL, aviso, barra_filtros, cabecalho, cartao,
        faixa_farol, grafico_duracao, grafico_evolucao, grafico_farol, nome_farol,
        secao, tabela_detalhada, tema_ativo, titulo_card,
    )
except ModuleNotFoundError:  # quando as páginas são importadas como pacote (paginas.xxx)
    from paginas.padrao_visual import (
        CORES_FAROL, ORDEM_FAROL, aviso, barra_filtros, cabecalho, cartao,
        faixa_farol, grafico_duracao, grafico_evolucao, grafico_farol, nome_farol,
        secao, tabela_detalhada, tema_ativo, titulo_card,
    )

REGRAS_FAROL = {
    "DENTRO DO PRAZO": "menos de 1 dia",
    "REVISAR REGRA": "exatamente 1 dia (regra a confirmar)",
    "ATENÇÃO": "entre 1 e 3 dias",
    "ALERTA": "exatamente 3 dias",
    "ATRASO": "mais de 3 dias",
    "SEM DATA": "sem data de início ou data inconsistente",
}


# ─────────────────────────────────────────────────────────────
# Regras de negócio (inalteradas)
# ─────────────────────────────────────────────────────────────
def classificar_prontidao(dias):
    if pd.isna(dias) or dias < 0:
        return "SEM DATA"
    if dias < 1:
        return "DENTRO DO PRAZO"
    if dias == 1:
        return "REVISAR REGRA"
    if dias < 3:
        return "ATENÇÃO"
    if dias == 3:
        return "ALERTA"
    return "ATRASO"


def preparar_medicao(df, titulo, coluna_inicio, coluna_fim):
    dados = df.copy()
    for coluna in (coluna_inicio, coluna_fim):
        if coluna not in dados.columns:
            dados[coluna] = pd.NaT
        dados[coluna] = pd.to_datetime(dados[coluna], errors="coerce")

    hoje = pd.Timestamp.today().normalize()
    dados["_data_calculo"] = dados[coluna_fim].fillna(hoje)
    dados["Dias"] = (dados["_data_calculo"] - dados[coluna_inicio]).dt.total_seconds() / 86400
    dados.loc[dados[coluna_inicio].isna() | (dados["Dias"] < 0), "Dias"] = float("nan")
    dados["Farol da etapa"] = dados["Dias"].apply(classificar_prontidao)
    dados["Situação da etapa"] = dados[coluna_fim].apply(
        lambda x: "Concluída" if pd.notna(x) else "Em andamento"
    )
    dados["Etapa"] = titulo
    return dados


# ─────────────────────────────────────────────────────────────
# Bloco de cada medição
# ─────────────────────────────────────────────────────────────
def bloco_medicao(df, titulo, descricao, coluna_inicio, coluna_fim, chave):
    dados = preparar_medicao(df, titulo, coluna_inicio, coluna_fim)
    secao(titulo, descricao)
    filtrado = barra_filtros(dados, coluna_inicio, chave)

    with st.expander("Como o farol é calculado"):
        for f in ORDEM_FAROL:
            st.markdown(
                f'<span style="display:inline-block;width:10px;height:10px;border-radius:50%;'
                f'background:{CORES_FAROL[f]};margin-right:8px"></span>**{nome_farol(f)}** — {REGRAS_FAROL[f]}',
                unsafe_allow_html=True,
            )

    contagem = filtrado["Farol da etapa"].value_counts()
    total = len(filtrado)
    dentro = int(contagem.get("DENTRO DO PRAZO", 0))
    atencao = int(contagem.get("ATENÇÃO", 0))
    alerta = int(contagem.get("ALERTA", 0))
    atraso = int(contagem.get("ATRASO", 0))
    andamento = int((filtrado["Situação da etapa"] == "Em andamento").sum())
    concluidos = total - andamento
    percentual = dentro / total * 100 if total else 0

    secao("Indicadores da etapa")
    k = st.columns(5)
    metricas = [
        ("Processos", total, "No recorte atual", tema_ativo()["acento"]),
        ("Dentro do prazo", dentro, f"{percentual:.1f}% do total", CORES_FAROL["DENTRO DO PRAZO"]),
        ("Atenção / alerta", atencao + alerta, "Requer acompanhamento", CORES_FAROL["ATENÇÃO"]),
        ("Em atraso", atraso, "Acima da faixa prevista", CORES_FAROL["ATRASO"]),
        ("Em andamento", andamento, f"{concluidos} concluídos", "#7A8CA5"),
    ]
    for coluna, metrica in zip(k, metricas):
        with coluna:
            cartao(*metrica)

    if not total:
        aviso("Nenhum processo encontrado com os filtros selecionados. "
              "Ajuste os filtros para ver os gráficos.")
        return

    faixa_farol(contagem, total)

    g1, g2 = st.columns([1, 1.35])
    with g1:
        with st.container(border=True):
            titulo_card("Distribuição por farol",
                        "Passe o mouse para ver a regra · clique na legenda para ocultar")
            grafico_farol(filtrado, chave, regras=REGRAS_FAROL)
    with g2:
        with st.container(border=True):
            titulo_card("Distribuição do tempo de execução",
                        "Linhas pontilhadas marcam 1 e 3 dias · selecione uma área para dar zoom")
            grafico_duracao(filtrado, chave)

    with st.container(border=True):
        titulo_card("Evolução mensal", "Processos por farol (barras) e % dentro do prazo (linha)")
        grafico_evolucao(filtrado, coluna_inicio, chave)

    revisar = int(contagem.get("REVISAR REGRA", 0))
    if revisar:
        aviso(f"{revisar} processo(s) estão na faixa de exatamente 1 dia. "
              "A regra de negócio precisa ser confirmada.", "atencao")

    secao("Detalhamento dos processos", "Cada linha mostra o farol e o tempo decorrido da etapa")
    tabela_detalhada(filtrado, coluna_inicio, coluna_fim, chave, f"prontidao_{chave}.csv")


# ─────────────────────────────────────────────────────────────
# Página
# ─────────────────────────────────────────────────────────────
def pagina_prontidao(df):
    cabecalho("Prontidão | Gestão de Proformas",
              "Acompanhamento dos prazos de recebimento e conferência das Proformas",
              chave="prontidao")
    if df is None or df.empty:
        aviso("A base operacional não possui registros para exibir.", "atencao")
        return

    recebimento, conferencia = st.tabs([
        "Recebimento da Proforma",
        "Conferência da Proforma",
    ])
    with recebimento:
        bloco_medicao(
            df, "Controle de recebimento",
            "Intervalo entre o recebimento do pedido e o recebimento da Proforma.",
            "Data Recebimento do Pedido", "Data Recebimento Proforma",
            "recebimento_proforma",
        )
    with conferencia:
        bloco_medicao(
            df, "Controle de conferência",
            "Intervalo entre o recebimento da Proforma e a conferência.",
            "Data Recebimento Proforma", "Data Conferência Proforma",
            "conferencia_proforma",
        )