
import numpy as np
import pandas as pd
import streamlit as st

import holidays

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

# ============================================================
# CONFIGURAÇÃO DAS QUATRO MÉTRICAS
# ============================================================

MEDICOES = [
    {
        "titulo": "Controle de Conhecimento de Embarque (B/L) Assinado",
        "descricao": (
            "Acompanhamento do intervalo entre a solicitação "
            "e o recebimento do B/L assinado."
        ),
        "inicio": "Data Solicitação B/L Assinado",
        "fim": "Data Recebimento B/L Assinado",
        "chave": "bl_assinado",
        "arquivo": "transito_bl_assinado.csv",
    },
    {
        "titulo": "Controle de Redirecionamento para Decimar",
        "descricao": (
            "Acompanhamento do intervalo entre a solicitação "
            "e a confirmação do redirecionamento para Decimar."
        ),
        "inicio": "Data Solicitação Redirecionamento Decimar",
        "fim": "Data Confirmação Redirecionamento Decimar",
        "chave": "redirecionamento_decimar",
        "arquivo": "transito_redirecionamento_decimar.csv",
    },
    {
        "titulo": "Controle de Chegada da Carga",
        "descricao": (
            "Acompanhamento do intervalo entre a data estimada "
            "de chegada e a chegada efetiva da carga."
        ),
        "inicio": "Data Estimada Chegada",
        "fim": "Data Chegada Carga",
        "chave": "chegada_carga",
        "arquivo": "transito_chegada_carga.csv",
    },
    {
        "titulo": "Controle de Presença de Carga",
        "descricao": (
            "Acompanhamento do intervalo entre a chegada da carga "
            "e a confirmação da presença de carga."
        ),
        "inicio": "Data Chegada Carga",
        "fim": "Data Presença Carga",
        "chave": "presenca_carga",
        "arquivo": "transito_presenca_carga.csv",
    },
]


# ============================================================
# FERIADOS NACIONAIS BRASILEIROS
# ============================================================

def obter_feriados(anos):
    """
    Considera exclusivamente feriados nacionais brasileiros.
    Não considera feriados estaduais ou municipais.
    """

    calendario = holidays.Brazil(
        years=list(anos),
        observed=True,
    )

    return {
        pd.Timestamp(data).date()
        for data in calendario.keys()
    }


# ============================================================
# CÁLCULO DE DIAS ÚTEIS
# ============================================================

def calcular_dias_uteis(inicio, fim, feriados):
    """
    Calcula os dias úteis entre duas datas.

    Regras:
    - Não conta a data inicial.
    - Não conta a data final.
    - Exclui sábados e domingos.
    - Exclui somente feriados nacionais brasileiros.
    """

    if pd.isna(inicio) or pd.isna(fim):
        return np.nan

    inicio = pd.Timestamp(inicio).normalize()
    fim = pd.Timestamp(fim).normalize()

    if fim < inicio:
        return np.nan

    # Começa no dia seguinte ao início.
    # O np.busday_count não inclui a data final.
    data_inicio = (inicio + pd.Timedelta(days=1)).date()
    data_fim = fim.date()

    feriados_periodo = [
        data
        for data in feriados
        if data_inicio <= data < data_fim
    ]

    return int(
        np.busday_count(
            data_inicio,
            data_fim,
            holidays=feriados_periodo,
        )
    )


# ============================================================
# CLASSIFICAÇÃO
# ============================================================

def classificar_transito(dias, data_inicio):
    """
    Os limites de prazo de Trânsito Internacional ainda não
    foram definidos. Por isso, não são inventadas classificações.

    Registros sem data inicial recebem SEM DATA.
    Registros com data inicial válida recebem REVISAR REGRA.
    """

    if pd.isna(data_inicio) or pd.isna(dias):
        return "SEM DATA"

    return "REVISAR REGRA"


# ============================================================
# PREPARAÇÃO DA MEDIÇÃO
# ============================================================

def preparar_medicao(df, titulo, coluna_inicio, coluna_fim):

    dados = df.copy()

    # Garante que as colunas existam.
    for coluna in (coluna_inicio, coluna_fim):
        if coluna not in dados.columns:
            dados[coluna] = pd.NaT

        dados[coluna] = pd.to_datetime(
            dados[coluna],
            errors="coerce",
        )

    hoje = pd.Timestamp.today().normalize()

    # Data final de cálculo:
    # - usa a data de conclusão, quando preenchida;
    # - usa hoje, quando a etapa ainda está em andamento.
    dados["_data_calculo"] = dados[coluna_fim].fillna(hoje)

    anos = set()

    for coluna in (coluna_inicio, coluna_fim, "_data_calculo"):
        anos.update(
            dados[coluna].dropna().dt.year.astype(int).tolist()
        )

    anos.add(hoje.year)

    feriados = obter_feriados(anos)

    dados["Dias"] = dados.apply(
        lambda linha: calcular_dias_uteis(
            linha[coluna_inicio],
            linha["_data_calculo"],
            feriados,
        ),
        axis=1,
    )

    dados["Farol da etapa"] = dados.apply(
        lambda linha: classificar_transito(
            linha["Dias"],
            linha[coluna_inicio],
        ),
        axis=1,
    )

    dados["Situação da etapa"] = dados[coluna_fim].apply(
        lambda data: (
            "Concluída"
            if pd.notna(data)
            else "Em andamento"
        )
    )

    dados["Etapa"] = titulo

    return dados


# ============================================================
# INDICADORES
# ============================================================

def exibir_indicadores(dados, chave):

    total = len(dados)

    concluidos = int(
        (dados["Situação da etapa"] == "Concluída").sum()
    )

    andamento = int(
        (dados["Situação da etapa"] == "Em andamento").sum()
    )

    sem_data = int(
        (dados["Farol da etapa"] == "SEM DATA").sum()
    )

    revisar = int(
        (dados["Farol da etapa"] == "REVISAR REGRA").sum()
    )

    duracoes = dados["Dias"].dropna()

    media = duracoes.mean() if not duracoes.empty else 0
    mediana = duracoes.median() if not duracoes.empty else 0
    maior = duracoes.max() if not duracoes.empty else 0

    percentual_conclusao = (
        concluidos / total * 100
        if total
        else 0
    )

    secao(
        "Indicadores da etapa",
        "Resumo dos processos conforme os filtros selecionados.",
    )

    colunas = st.columns(5)

    indicadores = [
        (
            "Processos",
            total,
            "Total no recorte atual",
            "#24476B",
        ),
        (
            "Concluídos",
            concluidos,
            f"{percentual_conclusao:.1f}% dos processos",
            CORES_FAROL["DENTRO DO PRAZO"],
        ),
        (
            "Em andamento",
            andamento,
            "Etapas ainda não concluídas",
            CORES_FAROL["ATENÇÃO"],
        ),
        (
            "Sem data inicial",
            sem_data,
            "Registros sem início informado",
            CORES_FAROL["SEM DATA"],
        ),
        (
            "Revisar regra",
            revisar,
            "Prazo ainda sem classificação definida",
            CORES_FAROL["REVISAR REGRA"],
        ),
    ]

    for coluna, indicador in zip(colunas, indicadores):
        with coluna:
            cartao(*indicador)

    return {
        "total": total,
        "concluidos": concluidos,
        "andamento": andamento,
        "sem_data": sem_data,
        "revisar": revisar,
        "media": media,
        "mediana": mediana,
        "maior": maior,
    }


# ============================================================
# BLOCO DE CADA MEDIÇÃO
# ============================================================

def bloco_medicao(df, configuracao):

    titulo = configuracao["titulo"]
    descricao = configuracao["descricao"]
    inicio = configuracao["inicio"]
    fim = configuracao["fim"]
    chave = configuracao["chave"]
    arquivo = configuracao["arquivo"]

    dados = preparar_medicao(
        df,
        titulo,
        inicio,
        fim,
    )

    # --------------------------------------------------------
    # Cabeçalho da medição
    # --------------------------------------------------------

    titulo_card(titulo, descricao)

    # --------------------------------------------------------
    # Filtros padrão compartilhados
    # --------------------------------------------------------

    filtrado = barra_filtros(
        dados,
        inicio,
        chave,
    )

    total = len(filtrado)

    if total == 0:
        aviso(
            "Nenhum processo encontrado com os filtros selecionados.",
            tipo="info",
        )
        return

    # --------------------------------------------------------
    # Indicadores
    # --------------------------------------------------------

    resumo = exibir_indicadores(
        filtrado,
        chave,
    )

    # --------------------------------------------------------
    # Distribuição por farol
    # --------------------------------------------------------

    secao(
        "Análise dos processos",
        "Distribuição dos registros e acompanhamento dos tempos.",
    )

    contagem_farol = (
        filtrado["Farol da etapa"]
        .value_counts()
        .reindex(ORDEM_FAROL, fill_value=0)
    )

    faixa_farol(
        contagem_farol,
        total=total,
    )

    c1, c2 = st.columns([1, 1.35])

    with c1:
        with st.container(border=True):
            titulo_card(
                "Distribuição por farol",
                "Classificação atual dos processos.",
            )

            grafico_farol(
                filtrado,
                chave=chave,
            )

    with c2:
        with st.container(border=True):
            titulo_card(
                "Distribuição do tempo de execução",
                "Quantidade de processos por dias úteis decorridos.",
            )

            # Não há faixas de prazo configuradas para esta etapa.
            grafico_duracao(
                filtrado,
                chave=chave,
                marcos=(),
                usar_faixas=False,
            )

    # --------------------------------------------------------
    # Evolução mensal
    # --------------------------------------------------------

    with st.container(border=True):
        titulo_card(
            "Evolução mensal",
            "Volume de processos por mês de início da etapa.",
        )

        grafico_evolucao(
            filtrado,
            coluna_inicio=inicio,
            chave=chave,
        )

    # --------------------------------------------------------
    # Tabela detalhada padrão
    # --------------------------------------------------------

    tabela_detalhada(
        filtrado,
        inicio,
        fim,
        chave,
        arquivo,
    )


# ============================================================
# PÁGINA PRINCIPAL
# ============================================================

def pagina_transito_internacional(df):

    cabecalho(
        "Trânsito Internacional",
        (
            "Acompanhamento dos marcos de embarque, documentação, "
            "chegada e presença de carga."
        ),
        chave="transito_internacional",
    )

    if df is None or df.empty:
        aviso(
            "A base operacional não possui registros para exibir.",
            tipo="info",
        )
        return

    # Verifica as colunas utilizadas nas quatro medições.
    colunas_necessarias = set()

    for medicao in MEDICOES:
        colunas_necessarias.add(medicao["inicio"])
        colunas_necessarias.add(medicao["fim"])

    ausentes = [
        coluna
        for coluna in colunas_necessarias
        if coluna not in df.columns
    ]

    if ausentes:
        aviso(
            "Algumas colunas de datas não foram encontradas na base: "
            + ", ".join(ausentes),
            tipo="warning",
        )

    # --------------------------------------------------------
    # Abas das quatro medições
    # --------------------------------------------------------

    abas = st.tabs([
        "Controle de Draft de Conhecimento Assinado",
        "Controle de Redirecionamento Decimar",
        "Controle de Chegada da Carga",
        "Controle de Presença de Carga",
    ])

    for aba, medicao in zip(abas, MEDICOES):
        with aba:
            bloco_medicao(
                df,
                medicao,
            )
