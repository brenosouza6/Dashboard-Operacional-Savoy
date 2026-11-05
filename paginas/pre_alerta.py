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

# As medições e os nomes das datas abaixo foram extraídos da página Pré-Alerta
# do PDF de referência. Algumas colunas variam conforme a base utilizada.
MEDICOES = [
    {
        "titulo": "Controle de Disponibilidade Inicial",
        "inicio": ["Data Recebimento do Pedido"],
        "fim": ["Data Previsão de Disponibilidade Carga Inicial"],
        "descricao": "Acompanhamento da previsão inicial de disponibilidade da carga.",
        "regra": "Menos de 1 dia: Dentro do Prazo | 2 dias: Atenção | 3 dias: Alerta | Mais de 3 dias: Atraso",
    },
    {
        "titulo": "Controle de Confirmação de Prontidão",
        "inicio": ["Data Previsão de Disponibilidade Carga Inicial"],
        "fim": ["Data Confirmação de Prontidão", "Data Confirmacao de Prontidao"],
        "descricao": "Acompanhamento da confirmação de prontidão da carga.",
        "regra": "Menos de 1 dia: Dentro do Prazo | 2 dias: Atenção | 3 dias: Alerta | Mais de 3 dias: Atraso",
    },
    {
        "titulo": "Controle de Booking",
        "inicio": ["Data Disponibilidade de Carga", "Data Previsão de Disponibilidade Carga Inicial"],
        "fim": ["Data Booking", "Data Confirmação Booking", "Data Confirmacao Booking"],
        "descricao": "Acompanhamento do processo de booking.",
        "regra": "Menos de 1 dia: Dentro do Prazo | 2 dias: Atenção | 3 dias: Alerta | Mais de 3 dias: Atraso",
    },
    {
        "titulo": "Controle de Recebimento de Cópia de Documentos",
        "inicio": ["Data Disponível na Origem", "Data Disponivel na Origem"],
        "fim": ["Data Recebimento Copia de Documentos", "Data Recebimento Cópia de Documentos"],
        "descricao": "Tempo entre a disponibilização na origem e o recebimento da cópia dos documentos.",
        "regra": "Menos de 1 dia: Dentro do Prazo | 2 dias: Atenção | 3 dias: Alerta | Mais de 3 dias: Atraso",
    },
    {
        "titulo": "Controle de Aprovação de Cópia de Documentos",
        "inicio": ["Data Recebimento Copia de Documentos", "Data Recebimento Cópia de Documentos"],
        "fim": ["Data Aprovação Copia de Documentos", "Data Aprovação Cópia de Documentos"],
        "descricao": "Acompanhamento da aprovação da cópia dos documentos.",
        "regra": "Faixas de prazo conforme instrução apresentada no PDF.",
    },
    {
        "titulo": "Controle de Atraso no Embarque com Base de Prontidão",
        "inicio": ["Data Disponibilidade de Carga", "Data Previsão de Disponibilidade Carga Inicial"],
        "fim": ["Data Embarque Efetivo"],
        "descricao": "Mede o intervalo entre a disponibilidade da carga e o embarque efetivo.",
        "regra": "Marítimo: menos de 10 dias no prazo; 10–14 atenção; 15–19 alerta; mais de 20 atraso. Aéreo: menos de 7 no prazo; 7–9 atenção; 10–14 alerta; 15 ou mais atraso. Rodoviário: 1 dia no prazo; 1 dia atenção (faixa ambígua no PDF); 2 alerta; 3 ou mais atraso.",
        "modal_especial": True,
    },
    {
        "titulo": "Controle de Data Efetiva de Embarque",
        "inicio": ["Data Estimado Embarque", "Data Estimado de Embarque"],
        "fim": ["Data Efetiva Embarque", "Data Embarque Efetivo"],
        "descricao": "Compara a data estimada com a data efetiva de embarque.",
        "regra": "Menos de 1 dia: Dentro do Prazo | 2 dias: Atenção | 3 dias: Alerta | Mais de 3 dias: Atraso",
    },
    {        "titulo": "Controle de Envio de Instrução de Desembaraço",
        "inicio": ["Data Efetiva Embarque", "Data Embarque Efetivo"],
        "fim": ["Data Envio Instrução Desembaraço", "Data Envio Instrução de Desembaraço"],
        "descricao": "Acompanhamento do envio da instrução de desembaraço.",
        "regra": "Menos de 1 dia: Dentro do Prazo | 2 dias: Atenção | 3 dias: Alerta | Mais de 3 dias: Atraso",
    },
    {
        "titulo": "Controle de Coleta",
        "inicio": ["Data carga Disponível Origem", "Data Carga Disponível Origem", "Data Disponibilidade de Carga"],
        "fim": ["Data Efetiva Coleta", "Data Efetiva de Coleta"],
        "descricao": "Acompanhamento entre a disponibilidade da carga na origem e a coleta efetiva.",
        "regra": "Menos de 1 dia: Dentro do Prazo | 2 dias: Atenção | 3 dias: Alerta | Mais de 3 dias: Atraso",
    },
    {
        "titulo": "Controle de Recebimento Draft BL",
        "inicio": ["Data Envio Draft BL", "Data Envio do Draft BL"],
        "fim": ["Data Recebimento Draft BL", "Data Recebimento do Draft BL"],
        "descricao": "Acompanhamento do recebimento do Draft BL.",
        "regra": "Menos de 1 dia: Dentro do Prazo | 2 dias: Atenção | 3 dias: Alerta | Mais de 3 dias: Atraso",
    },
]


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
    dados.loc[dados["Dias"] < 0, "Dias"] = pd.NA

    if config.get("modal_especial") and "Modal" in dados.columns:
        dados["Farol da etapa"] = dados.apply(
            lambda linha: _classificar_embarque(linha["Dias"], linha["Modal"]),
            axis=1,
        )
    else:
        dados["Farol da etapa"] = dados["Dias"].apply(_classificar_dias)

    return dados


def _exibir_bloco(df, config, indice):
    coluna_inicio = _encontrar_coluna(df, config["inicio"])
    coluna_fim = _encontrar_coluna(df, config["fim"])

    st.markdown("---")
    st.subheader(f"📐 {config['titulo']}")
    st.caption(config["descricao"])

    if not coluna_inicio or not coluna_fim:
        st.warning(
            "Esta medição está identificada no PDF, mas não foi possível "
            "localizar as duas colunas de data correspondentes na base. "
            f"Coluna inicial esperada: {', '.join(config['inicio'])}. "
            f"Coluna final esperada: {', '.join(config['fim'])}."
        )
        return

    etapa = _preparar_medicao(df, config, coluna_inicio, coluna_fim)

    c_ref, c_proc = st.columns(2)
    with c_ref:
        ref = st.text_input(
            "Pesquisar por Referência do Cliente",
            key=f"pre_alerta_ref_{indice}",
        ).strip()
    with c_proc:
        processo = st.text_input(
            "Pesquisar por Nº Processo",
            key=f"pre_alerta_proc_{indice}",
        ).strip()

    if ref and "Ref.Cliente" in etapa.columns:
        etapa = etapa[
            etapa["Ref.Cliente"].astype(str).str.contains(ref, case=False, na=False)
        ]
    if processo and "Nº Processo" in etapa.columns:
        etapa = etapa[
            etapa["Nº Processo"].astype(str).str.contains(
                processo, case=False, na=False
            )
        ]

    contagem = etapa["Farol da etapa"].value_counts()
    total = len(etapa)

    k1, k2, k3, k4, k5 = st.columns(5)
    k1.metric("Processos", total)
    k2.metric("Dentro do prazo", int(contagem.get("DENTRO DO PRAZO", 0)))
    k3.metric("Atenção", int(contagem.get("ATENÇÃO", 0)))
    k4.metric("Alerta", int(contagem.get("ALERTA", 0)))
    k5.metric("Atraso", int(contagem.get("ATRASO", 0)))

    graf, instrucao = st.columns([1.1, 1])
    with graf:
        st.markdown("**Percentual por Farol**")
        if total:
            resumo = contagem.rename_axis("Farol").reset_index(name="Quantidade")
            fig = px.pie(
                resumo,
                names="Farol",
                values="Quantidade",
                hole=0.60,
                color="Farol",
                color_discrete_map=CORES_FAROL,
            )
            fig.update_traces(textposition="inside", textinfo="percent")
            fig.update_layout(
                height=270,
                margin=dict(t=10, b=5, l=5, r=5),
                legend_title_text="",
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Nenhum processo encontrado para esta medição.")

    with instrucao:
        st.markdown("**Instrução da medição**")
        st.info(config["regra"])

    st.markdown("**Detalhamento dos processos**")
    colunas = [
        "Status", "Ref.Cliente", "Nº Processo", "Responsável", "Planta",
        "Categoria", "Exportador", "Modal", coluna_inicio, coluna_fim,
        "Dias", "Farol da etapa",
    ]
    colunas = [c for c in colunas if c in etapa.columns]
    tabela = etapa[colunas].copy()

    for coluna in (coluna_inicio, coluna_fim):
        if coluna in tabela.columns:
            tabela[coluna] = (
                pd.to_datetime(tabela[coluna], errors="coerce")
                .dt.strftime("%d/%m/%Y")
                .fillna("—")
            )

    tabela["Dias"] = tabela["Dias"].round(0)
    st.dataframe(tabela, use_container_width=True, hide_index=True, height=350)

    csv = etapa.to_csv(index=False, sep=";", encoding="utf-8-sig").encode("utf-8-sig")
    st.download_button(
        "Baixar dados desta medição",
        data=csv,
        file_name=f"pre_alerta_medicao_{indice + 1}.csv",
        mime="text/csv",
        key=f"pre_alerta_download_{indice}",
    )


def pagina_pre_alerta(df):
    st.title("Pré-Alerta")
    st.caption("Acompanhamento das etapas anteriores ao embarque e preparação documental")

    if df.empty:
        st.warning("Não há processos disponíveis para os filtros selecionados.")
        return

    for indice, config in enumerate(MEDICOES):
        _exibir_bloco(df, config, indice)
