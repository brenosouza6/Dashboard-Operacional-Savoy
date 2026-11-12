from html import escape

import pandas as pd
import streamlit as st

try:
    from padrao_visual import (
        CORES_FAROL, aviso, barra_filtros, cabecalho, cartao, faixa_farol,
        grafico_duracao, grafico_evolucao, grafico_farol, secao, tabela_detalhada,
        tema_ativo, titulo_card,
    )
except ModuleNotFoundError:  # quando as páginas são importadas como pacote (paginas.xxx)
    from paginas.padrao_visual import (
        CORES_FAROL, aviso, barra_filtros, cabecalho, cartao, faixa_farol,
        grafico_duracao, grafico_evolucao, grafico_farol, secao, tabela_detalhada,
        tema_ativo, titulo_card,
    )

REGRA_PADRAO = "Menos de 1 dia: Dentro do Prazo | 2 dias: Atenção | 3 dias: Alerta | Mais de 3 dias: Atraso"

# As medições e os nomes das datas abaixo foram extraídos da página Pré-Alerta
# do PDF de referência. Algumas colunas variam conforme a base utilizada.
# "aba" é só o nome curto exibido na aba da página.
MEDICOES = [
    {
        "aba": "Disponibilidade inicial",
        "titulo": "Controle de Disponibilidade Inicial",
        "inicio": ["Data Recebimento do Pedido"],
        "fim": ["Data Previsão Disponibilidade Carga Inicial"],
        "descricao": "Acompanhamento da previsão inicial de disponibilidade da carga.",
        "regra": REGRA_PADRAO,
    },
    {
        "aba": "Confirmação de prontidão",
        "titulo": "Controle de Confirmação de Prontidão",
        "inicio": ["Data Previsão Disponibilidade Carga Inicial"],
        "fim": ["Data Confirmação Prontidão"],
        "descricao": "Acompanhamento da confirmação de prontidão da carga.",
        "regra": REGRA_PADRAO,
    },
    {
        "aba": "Booking",
        "titulo": "Controle de Booking",
        "inicio": ["Data Previsão Disponibilidade Carga Inicial"],
        "fim": ["Data Booking", "Data Confirmação Booking", "Data Confirmacao Booking"],
        "descricao": "Acompanhamento do processo de booking.",
        "regra": REGRA_PADRAO,
    },
    {
        "aba": "Cópia de documentos",
        "titulo": "Controle de Recebimento de Cópia de Documentos",
        "inicio": ["Data Disponível na Origem", "Data Disponivel na Origem"],
        "fim": ["Data Recebimento Copia de Documentos", "Data Recebimento Cópia de Documentos"],
        "descricao": "Tempo entre a disponibilização na origem e o recebimento da cópia dos documentos.",
        "regra": REGRA_PADRAO,
    },
    {
        "aba": "Aprovação de documentos",
        "titulo": "Controle de Aprovação de Cópia de Documentos",
        "inicio": ["Data Recebimento Copia de Documentos", "Data Recebimento Cópia de Documentos"],
        "fim": ["Data Aprovação Copia de Documentos", "Data Aprovação Cópia de Documentos"],
        "descricao": "Acompanhamento da aprovação da cópia dos documentos.",
        "regra": "Faixas de prazo conforme instrução apresentada no PDF.",
    },
    {
        "aba": "Atraso no embarque",
        "titulo": "Controle de Atraso no Embarque com Base de Prontidão",
        "inicio": ["Data Disponibilidade de Carga", "Data Previsão de Disponibilidade Carga Inicial"],
        "fim": ["Data Embarque Efetivo"],
        "descricao": "Mede o intervalo entre a disponibilidade da carga e o embarque efetivo.",
        "regra": "Marítimo: menos de 10 dias no prazo; 10–14 atenção; 15–19 alerta; mais de 20 atraso. Aéreo: menos de 7 no prazo; 7–9 atenção; 10–14 alerta; 15 ou mais atraso. Rodoviário: 1 dia no prazo; 1 dia atenção (faixa ambígua no PDF); 2 alerta; 3 ou mais atraso.",
        "modal_especial": True,
    },
    {
        "aba": "Data efetiva de embarque",
        "titulo": "Controle de Data Efetiva de Embarque",
        "inicio": ["Data Estimada Embarque", "Data Estimada de Embarque"],
        "fim": ["Data Efetiva Embarque", "Data Embarque Efetiva"],
        "descricao": "Compara a data estimada com a data efetiva de embarque.",
        "regra": REGRA_PADRAO,
    },
    {
        "aba": "Instrução de desembaraço",
        "titulo": "Controle de Envio de Instrução de Desembaraço",
        "inicio": ["Data Efetiva Embarque", "Data Embarque Efetiva"],
        "fim": ["Data Envio Instrução Desembaraço", "Data Envio Instrução de Desembaraço"],
        "descricao": "Acompanhamento do envio da instrução de desembaraço.",
        "regra": REGRA_PADRAO,
    },
    {
        "aba": "Coleta",
        "titulo": "Controle de Coleta",
        "inicio": ["Data carga Disponível Origem", "Data Carga Disponível Origem", "Data Disponibilidade de Carga"],
        "fim": ["Data Efetiva Coleta", "Data Efetiva de Coleta"],
        "descricao": "Acompanhamento entre a disponibilidade da carga na origem e a coleta efetiva.",
        "regra": REGRA_PADRAO,
    },
    {
        "aba": "Draft BL",
        "titulo": "Controle de Recebimento Draft BL",
        "inicio": ["Data Envio Draft BL", "Data Envio do Draft BL"],
        "fim": ["Data Recebimento Draft BL", "Data Recebimento do Draft BL"],
        "descricao": "Acompanhamento do recebimento do Draft BL.",
        "regra": REGRA_PADRAO,
    },
]


# ─────────────────────────────────────────────────────────────
# Regras de negócio (inalteradas)
# ─────────────────────────────────────────────────────────────
def _encontrar_coluna(df, candidatas):
    for coluna in candidatas:
        if coluna in df.columns:
            return coluna
    return None


def _classificar_dias(dias):
    if pd.isna(dias):
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


def _classificar_embarque(dias, modal):
    if pd.isna(dias):
        return "SEM DATA"

    modal = str(modal).strip().upper()
    if "MAR" in modal:
        if dias < 10:
            return "DENTRO DO PRAZO"
        if dias <= 14:
            return "ATENÇÃO"
        if dias <= 19:
            return "ALERTA"
        return "ATRASO"

    if "AÉR" in modal or "AER" in modal:
        if dias < 7:
            return "DENTRO DO PRAZO"
        if dias <= 9:
            return "ATENÇÃO"
        if dias <= 14:
            return "ALERTA"
        return "ATRASO"

    if "ROD" in modal:
        if dias < 1:
            return "DENTRO DO PRAZO"
        if dias == 1:
            return "REVISAR REGRA"
        if dias == 2:
            return "ALERTA"
        return "ATRASO"

    return "REVISAR REGRA"


def _preparar_medicao(df, config, coluna_inicio, coluna_fim):
    dados = df.copy()
    dados[coluna_inicio] = pd.to_datetime(dados[coluna_inicio], errors="coerce")
    dados[coluna_fim] = pd.to_datetime(dados[coluna_fim], errors="coerce")

    hoje = pd.Timestamp.today().normalize()
    dados["_data_calculo"] = dados[coluna_fim].fillna(hoje)
    dados["Dias"] = (
        dados["_data_calculo"] - dados[coluna_inicio]
    ).dt.total_seconds() / 86400
    dados.loc[dados["Dias"] < 0, "Dias"] = float("nan")
    dados["Dias"] = pd.to_numeric(dados["Dias"], errors="coerce")

    if config.get("modal_especial") and "Modal" in dados.columns:
        dados["Farol da etapa"] = dados.apply(
            lambda linha: _classificar_embarque(linha["Dias"], linha["Modal"]),
            axis=1,
        )
    else:
        dados["Farol da etapa"] = dados["Dias"].apply(_classificar_dias)

    # usado pelo filtro "Situação" e pela tabela (mesmo padrão da página de Prontidão)
    dados["Situação da etapa"] = dados[coluna_fim].apply(
        lambda x: "Concluída" if pd.notna(x) else "Em andamento"
    )
    return dados


# ─────────────────────────────────────────────────────────────
# Bloco de cada medição
# ─────────────────────────────────────────────────────────────
def _exibir_bloco(df, config, indice):
    coluna_inicio = _encontrar_coluna(df, config["inicio"])
    coluna_fim = _encontrar_coluna(df, config["fim"])
    chave = f"pre_alerta_{indice}"

    secao(config["titulo"], config["descricao"])

    if not coluna_inicio or not coluna_fim:
        aviso(
            "Esta medição está identificada no PDF, mas não foi possível "
            "localizar as duas colunas de data correspondentes na base. "
            f"Coluna inicial esperada: {escape(', '.join(config['inicio']))}. "
            f"Coluna final esperada: {escape(', '.join(config['fim']))}.",
            "atencao",
        )
        return

    etapa = _preparar_medicao(df, config, coluna_inicio, coluna_fim)

    aviso(f"<b>Instrução da medição:</b> {escape(config['regra'])}", "info")
    filtrado = barra_filtros(etapa, coluna_inicio, chave)

    # ── Indicadores (as mesmas métricas da versão anterior) ──
    contagem = filtrado["Farol da etapa"].value_counts()
    total = len(filtrado)
    dentro = int(contagem.get("DENTRO DO PRAZO", 0))
    atencao = int(contagem.get("ATENÇÃO", 0))
    alerta = int(contagem.get("ALERTA", 0))
    atraso = int(contagem.get("ATRASO", 0))

    def pct(n):
        return f"{n / total * 100:.1f}% do total" if total else "—"

    secao("Indicadores da etapa")
    k = st.columns(5)
    metricas = [
        ("Processos", total, "No recorte atual", tema_ativo()["acento"]),
        ("Dentro do prazo", dentro, pct(dentro), CORES_FAROL["DENTRO DO PRAZO"]),
        ("Atenção", atencao, pct(atencao), CORES_FAROL["ATENÇÃO"]),
        ("Alerta", alerta, pct(alerta), CORES_FAROL["ALERTA"]),
        ("Atraso", atraso, pct(atraso), CORES_FAROL["ATRASO"]),
    ]
    for coluna, metrica in zip(k, metricas):
        with coluna:
            cartao(*metrica)

    if not total:
        aviso("Nenhum processo encontrado para esta medição com os filtros selecionados. "
              "Ajuste os filtros para ver os gráficos.")
        return

    faixa_farol(contagem, total)

    # Nas medições com regra por modal (embarque) os limites mudam por linha,
    # então o histograma não desenha as marcas fixas de 1 e 3 dias.
    modal_especial = bool(config.get("modal_especial"))
    marcos = () if modal_especial else ((1, "1 dia"), (3, "3 dias"))
    sub_hist = ("Dias decorridos por farol · selecione uma área para dar zoom" if modal_especial
                else "Linhas pontilhadas marcam 1 e 3 dias · selecione uma área para dar zoom")

    g1, g2 = st.columns([1, 1.35])
    with g1:
        with st.container(border=True):
            titulo_card("Percentual por farol",
                        "Passe o mouse para ver os números · clique na legenda para ocultar")
            grafico_farol(filtrado, chave)
    with g2:
        with st.container(border=True):
            titulo_card("Distribuição do tempo de execução", sub_hist)
            grafico_duracao(filtrado, chave, marcos=marcos, usar_faixas=not modal_especial)

    with st.container(border=True):
        titulo_card("Evolução mensal", "Processos por farol (barras) e % dentro do prazo (linha)")
        grafico_evolucao(filtrado, coluna_inicio, chave)

    revisar = int(contagem.get("REVISAR REGRA", 0))
    if revisar:
        aviso(f"{revisar} processo(s) estão em 'Revisar regra' (faixa de exatamente 1 dia ou "
              "modal não reconhecido). A regra de negócio precisa ser confirmada.", "atencao")

    secao("Detalhamento dos processos", "Cada linha mostra o farol e o tempo decorrido da etapa")
    tabela_detalhada(filtrado, coluna_inicio, coluna_fim, chave,
                     f"pre_alerta_medicao_{indice + 1}.csv")


# ─────────────────────────────────────────────────────────────
# Página
# ─────────────────────────────────────────────────────────────
def pagina_pre_alerta(df):
    cabecalho("Pré-Alerta",
              "Acompanhamento das etapas anteriores ao embarque e preparação documental",
              chave="pre_alerta")

    if df is None or df.empty:
        aviso("Não há processos disponíveis para os filtros selecionados.", "atencao")
        return

    abas = st.tabs([c.get("aba") or c["titulo"].replace("Controle de " "") for c in MEDICOES])
    for indice, (aba, config) in enumerate(zip(abas, MEDICOES)):
        with aba:
            _exibir_bloco(df, config, indice)