
import hashlib
from datetime import date, timedelta

import pandas as pd
import streamlit as st

try:
    from padrao_visual import (
        cabecalho, secao, cartao, aviso, faixa_farol, CORES_FAROL,
        ORDEM_FAROL, grafico_farol, grafico_duracao, grafico_evolucao,
        tabela_detalhada, barra_filtros, titulo_card, tema_ativo, PLOTLY_CONFIG,
    )
except ModuleNotFoundError:
    from paginas.padrao_visual import (
        cabecalho, secao, cartao, aviso, faixa_farol, CORES_FAROL,
        ORDEM_FAROL, grafico_farol, grafico_duracao, grafico_evolucao,
        tabela_detalhada, barra_filtros, titulo_card, tema_ativo, PLOTLY_CONFIG,
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
# APRESENTAÇÃO PADRONIZADA DOS CONTROLES
# ============================================================

def _normalizar_para_padrao(dados, coluna_inicio, coluna_fim):
    """Adapta os nomes internos do Numerários aos componentes compartilhados."""
    resultado = dados.copy()
    resultado[coluna_inicio] = pd.to_datetime(resultado[coluna_inicio], errors="coerce")
    if coluna_fim not in resultado.columns:
        resultado[coluna_fim] = pd.NaT
    resultado[coluna_fim] = pd.to_datetime(resultado[coluna_fim], errors="coerce")
    resultado["Dias"] = pd.to_numeric(resultado["Dias"], errors="coerce")
    resultado["Farol da etapa"] = resultado["Farol"].fillna("SEM DATA")
    resultado["Situação da etapa"] = resultado[coluna_fim].apply(
        lambda data: "Concluída" if pd.notna(data) else "Em andamento"
    )
    return resultado


def _exibir_controle(dados, chave, titulo, descricao, coluna_inicio, coluna_fim,
                     arquivo, colunas_tabela, observacao=None):
    dados = _normalizar_para_padrao(dados, coluna_inicio, coluna_fim)

    titulo_card(titulo, descricao)
    if observacao:
        aviso(observacao, tipo="info")

    filtrado = barra_filtros(dados, coluna_inicio, chave)
    total = len(filtrado)
    if total == 0:
        aviso("Nenhum processo encontrado com os filtros selecionados.", tipo="info")
        return

    # Indicadores: total + cinco categorias de farol.
    contagem = filtrado["Farol da etapa"].value_counts().reindex(
        ["DENTRO DO PRAZO", "ATENÇÃO", "ALERTA", "ATRASO", "SEM DATA"],
        fill_value=0,
    )
    secao("Indicadores do controle", "Quantidade e participação dos processos em cada faixa.")
    c_total, c1, c2, c3 = st.columns(4)
    with c_total:
        cartao("Processos", total, "Total após os filtros", "#24476B", chave=chave)
    for coluna, farol in zip((c1, c2, c3), ("DENTRO DO PRAZO", "ATENÇÃO", "ALERTA")):
        qtd = int(contagem[farol])
        with coluna:
            cartao(farol.title(), qtd, f"{qtd / total:.1%} dos processos", CORES_FAROL[farol], farol=farol, chave=chave)
    c4, c5 = st.columns(2)
    for coluna, farol in zip((c4, c5), ("ATRASO", "SEM DATA")):
        qtd = int(contagem[farol])
        with coluna:
            cartao(farol.title(), qtd, f"{qtd / total:.1%} dos processos", CORES_FAROL[farol], farol=farol, chave=chave)

    faixa_farol(contagem.to_dict(), total=total)

    secao("Análise dos processos", "Distribuição do farol e duração do controle.")
    g1, g2 = st.columns([1, 1.35])
    with g1:
        with st.container(border=True):
            titulo_card("Distribuição por farol", "Participação dos processos em cada classificação.")
            grafico_farol(filtrado, chave=chave)
    with g2:
        with st.container(border=True):
            titulo_card("Duração do controle", "Dias corridos entre o início e a conclusão ou a data atual.")
            grafico_duracao(filtrado, chave=chave, marcos=((1, "1 dia"), (2, "2 dias"), (3, "3 dias")), usar_faixas=False)

    with st.container(border=True):
        titulo_card("Evolução dos processos", "Volume por mês de início do controle.")
        grafico_evolucao(filtrado, coluna_inicio=coluna_inicio, chave=chave)

    tabela_detalhada(filtrado, coluna_inicio, coluna_fim, chave, arquivo)


# ============================================================
# PÁGINA PRINCIPAL
# ============================================================

def pagina_numerarios(df):
    cabecalho(
        "Controle de Numerários",
        "Acompanhamento das solicitações pré-adm, solicitações ao cliente e pagamentos de numerários.",
        chave="numerarios",
    )

    if df is None or df.empty:
        aviso("A base de dados está vazia. Verifique a importação da planilha.", tipo="info")
        return

    base = _preparar_base(df)

    aviso(
        "Atenção: quando a planilha não possui uma data necessária ao controle, "
        "a página utiliza uma data sintética identificada para demonstração. "
        "Essas datas não alteram a base original.",
        tipo="info",
    )

    aba_pre, aba_adm, aba_pag = st.tabs([
        "Solicitação Pré-adm",
        "Solicitação Adm / Cliente",
        "Pagamento de Numerário",
    ])

    with aba_pre:
        dados = _controle_pre_adm(base)
        _exibir_controle(
            dados, "numerarios_pre_adm",
            "Controle de Solicitação de Numerário — Pré-adm",
            "Acompanhamento entre a instrução do despacho e o envio do numerário.",
            "Data Instrução Despacho", "Data Envio Numerário",
            "numerarios_pre_adm.csv",
            ["Status", "Ref.Cliente", "Nº Processo", "Responsável", "Planta", "Categoria",
             "Exportador", "Modal", "Solicita Numerário", "Data Instrução Despacho",
             "Data Envio Numerário", "Dias", "Farol da etapa", "Situação da etapa"],
            "As datas de instrução e envio são simuladas quando os campos correspondentes não existem na planilha.",
        )

    with aba_adm:
        dados = _controle_adm_cliente(base)
        dados["_Data Fim Adm Cliente"] = pd.NaT
        _exibir_controle(
            dados, "numerarios_adm_cliente",
            "Controle de Solicitação de Numerário — Adm / Cliente",
            "Acompanhamento do tempo desde o envio da solicitação ao cliente.",
            "Data Envio Numerário", "_Data Fim Adm Cliente",
            "numerarios_adm_cliente.csv",
            ["Status", "Ref.Cliente", "Nº Processo", "Responsável", "Planta", "Categoria",
             "Exportador", "Modal", "Data Envio Numerário", "Dias", "Farol da etapa", "Situação da etapa"],
            "A data de envio é simulada para demonstração quando não existe um campo equivalente na planilha. Esta etapa permanece em andamento até existir uma data de conclusão específica.",
        )

    with aba_pag:
        dados = _controle_pagamento(base)
        if "_Data Solicitação Simulada" in dados.columns:
            inicio_pagamento = "_Data Solicitação Simulada"
        else:
            inicio_pagamento = "Data Solicitação Numerário Cliente"
        _exibir_controle(
            dados, "numerarios_pagamento",
            "Controle de Pagamento de Numerário",
            "Acompanhamento entre a solicitação e o recebimento do numerário pelo cliente.",
            inicio_pagamento, "Data Recebimento Numerário Cliente",
            "numerarios_pagamento.csv",
            ["Status", "Ref.Cliente", "Ref.Pibernat", "Nº Processo", "Responsável", "Planta",
             "Categoria", "Exportador", "Modal", "Data Solicitação Numerário Cliente",
             "Data Recebimento Numerário Cliente", "Dias", "Farol da etapa", "Situação da etapa"],
            "A coluna Data Recebimento Numerário da planilha original foi preservada e não foi considerada automaticamente equivalente a Data Recebimento Numerário Cliente.",
        )
