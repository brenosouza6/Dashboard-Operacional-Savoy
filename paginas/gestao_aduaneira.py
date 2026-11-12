
import streamlit as st
import pandas as pd
import holidays

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


# ==========================================================
# CONFIGURAÇÕES
# ==========================================================

COLUNAS_FILTRO = [
    "Responsável",
    "Planta",
    "Exportador",
    "Modal",
]

FAROIS = [
    "DENTRO DO PRAZO",
    "ATENÇÃO",
    "ALERTA",
    "ATRASO",
    "SEM DATA",
    "REVISAR REGRA",
]

# Calendário exclusivamente nacional
FERIADOS_NACIONAIS = holidays.Brazil()


# ==========================================================
# CÁLCULO DE DIAS ÚTEIS
# ==========================================================

def calcular_dias_uteis(data_inicio, data_fim=None):
    """
    Calcula dias úteis considerando:
    - Segunda a sexta-feira;
    - Exclusão de sábados e domingos;
    - Exclusão somente de feriados nacionais;
    - Contagem inclusiva das datas inicial e final.
    """

    if pd.isna(data_inicio):
        return None

    inicio = pd.to_datetime(data_inicio, errors="coerce")

    if pd.isna(inicio):
        return None

    inicio = inicio.normalize()

    if data_fim is None or pd.isna(data_fim):
        fim = pd.Timestamp.today().normalize()
    else:
        fim = pd.to_datetime(data_fim, errors="coerce")

        if pd.isna(fim):
            return None

        fim = fim.normalize()

    if fim < inicio:
        return 0

    # Atualiza o calendário para todos os anos envolvidos
    anos = range(inicio.year, fim.year + 1)

    feriados = holidays.Brazil(years=anos)

    dias = pd.date_range(
        start=inicio,
        end=fim,
        freq="D"
    )

    return sum(
        1
        for dia in dias
        if dia.weekday() < 5
        and dia.date() not in feriados
    )


def _calcular_coluna_dias(dados, coluna_inicio, coluna_fim,
                          somente_pendentes=False):
    """
    Calcula os dias úteis entre duas colunas de datas.
    Se a data final estiver vazia, considera a data atual.
    """

    if coluna_inicio not in dados.columns:
        return pd.Series(pd.NA, index=dados.index, dtype="object")

    if coluna_fim not in dados.columns:
        finais = pd.Series(pd.NaT, index=dados.index)
    else:
        finais = dados[coluna_fim]

    inicios = dados[coluna_inicio]

    resultados = []

    for inicio, fim in zip(inicios, finais):

        if somente_pendentes and pd.notna(fim):
            resultados.append(None)
            continue

        resultados.append(
            calcular_dias_uteis(inicio, fim)
        )

    return pd.Series(resultados, index=dados.index, dtype="object")


# ==========================================================
# FUNÇÕES AUXILIARES
# ==========================================================

def _coluna(df, nome):
    if nome in df.columns:
        return df[nome]

    return pd.Series(index=df.index, dtype="object")


def _numero(valor):
    return pd.to_numeric(valor, errors="coerce")


def _calcular_indicador(dados, coluna_metrica):
    """
    Recalcula os indicadores de dias úteis usando as datas
    operacionais. Se as datas necessárias não existirem,
    utiliza a coluna de indicador já existente na base.
    """

    calculos = {
        "Dias_Uteis_Registro_DI": (
            "Data Início Controle Registro DI",
            "Data Registro DI/DUIMP",
            False,
        ),

        "Dias_Uteis_Solicitacao_Danfe": (
            "Data Registro DI/DUIMP",
            "Data Solicitação DANFE",
            False,
        ),

        "[Dias] Farol - Recebimento Danfe": (
            "Data Solicitação DANFE",
            "Data Recebimento DANFE",
            True,
        ),

        "Dias_Uteis_Pagamento_ICMS": (
            "Data Solicitação Pagamento ICMS",
            "Data Pagamento ICMS",
            False,
        ),
    }

    if coluna_metrica not in calculos:
        if coluna_metrica in dados.columns:
            return _numero(dados[coluna_metrica])

        return pd.Series(pd.NA, index=dados.index)

    inicio, fim, somente_pendentes = calculos[coluna_metrica]

    if inicio not in dados.columns:
        if coluna_metrica in dados.columns:
            return _numero(dados[coluna_metrica])

        return pd.Series(pd.NA, index=dados.index)

    return _calcular_coluna_dias(
        dados,
        inicio,
        fim,
        somente_pendentes,
    )


def _classificar(valor, regra):

    if pd.isna(valor):
        return "SEM DATA"

    valor = float(valor)

    if regra == "registro_di":
        if valor <= 1:
            return "DENTRO DO PRAZO"
        elif valor <= 2:
            return "ALERTA"
        elif valor <= 3:
            return "ATENÇÃO"

        return "ATRASO"

    if regra == "danfe_recebimento":
        if valor <= 1:
            return "DENTRO DO PRAZO"
        elif valor <= 2:
            return "ATENÇÃO"
        elif valor <= 3:
            return "ALERTA"

        return "ATRASO"

    if regra == "padrao_atencao":
        if valor <= 1:
            return "DENTRO DO PRAZO"
        elif valor <= 2:
            return "ATENÇÃO"
        elif valor <= 3:
            return "ALERTA"

        return "ATRASO"

    if regra == "desembaraco":
        if valor <= 6:
            return "DENTRO DO PRAZO"
        elif valor <= 12:
            return "ATENÇÃO"
        elif valor <= 23:
            return "ALERTA"

        return "ATRASO"

    return "REVISAR REGRA"


def _preparar_dados(df, coluna_metrica, regra):

    dados = df.copy()

    if coluna_metrica == "Horas_Uteis_Desembaraco":
        if coluna_metrica in dados.columns:
            dados["Indicador"] = _numero(dados[coluna_metrica])
        else:
            dados["Indicador"] = pd.NA
    else:
        dados["Indicador"] = _calcular_indicador(
            dados,
            coluna_metrica,
        )

    dados["Farol da etapa"] = dados["Indicador"].apply(
        lambda x: _classificar(x, regra)
    )

    return dados


def _aplicar_filtros(df, chave):

    filtrado = df.copy()

    st.markdown("### Filtros")

    colunas = st.columns(4)

    for i, coluna in enumerate(COLUNAS_FILTRO):

        if coluna not in filtrado.columns:
            continue

        opcoes = sorted(
            filtrado[coluna]
            .dropna()
            .astype(str)
            .unique()
            .tolist()
        )

        with colunas[i]:
            selecionados = st.multiselect(
                coluna,
                opcoes,
                key=f"{chave}_{coluna}",
            )

        if selecionados:
            filtrado = filtrado[
                filtrado[coluna].astype(str).isin(selecionados)
            ]

    return filtrado


def _mostrar_indicadores(dados, unidade):

    total = len(dados)

    dentro = (dados["Farol da etapa"] == "DENTRO DO PRAZO").sum()
    atencao = (dados["Farol da etapa"] == "ATENÇÃO").sum()
    alerta = (dados["Farol da etapa"] == "ALERTA").sum()
    atraso = (dados["Farol da etapa"] == "ATRASO").sum()

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        cartao(
            "Total de processos",
            total,
            "Processos filtrados",
            "#1F6FB2",
        )

    with c2:
        cartao(
            "Dentro do prazo",
            dentro,
            "Indicadores regulares",
            CORES_FAROL["DENTRO DO PRAZO"],
        )

    with c3:
        cartao(
            "Em atenção / alerta",
            atencao + alerta,
            "Processos que exigem acompanhamento",
            CORES_FAROL["ALERTA"],
        )

    with c4:
        cartao(
            "Em atraso",
            atraso,
            "Processos fora do prazo",
            CORES_FAROL["ATRASO"],
        )

    if total:
        contagem = dados["Farol da etapa"].value_counts().to_dict()

        faixa_farol(contagem, total)

        legenda = st.columns(4)

        for i, farol in enumerate(FAROIS[:4]):
            with legenda[i]:
                st.markdown(
                    f"""
                    <div style="font-size:12px">
                        <span style="
                            display:inline-block;
                            width:9px;
                            height:9px;
                            border-radius:50%;
                            background:{CORES_FAROL[farol]};
                            margin-right:5px;">
                        </span>
                        {farol.title()}: {contagem.get(farol, 0)}
                    </div>
                    """,
                    unsafe_allow_html=True,
                )


def _tabela_detalhada(dados, coluna_metrica, unidade):

    secao(
        "Detalhamento dos processos",
        "Consulte os processos e suas respectivas classificações.",
    )

    colunas_desejadas = [
        "Status",
        "Ref.Cliente",
        "Nº Processo",
        "Responsável",
        "Planta",
        "Exportador",
        "Modal",
    ]

    colunas_exibir = [
        c for c in colunas_desejadas if c in dados.columns
    ]

    resultado = dados.copy()

    resultado["Farol"] = resultado["Farol da etapa"]

    resultado[unidade] = resultado["Indicador"]

    if unidade not in colunas_exibir:
        colunas_exibir += [unidade]

    colunas_exibir += ["Farol"]

    colunas_exibir = [
        c for c in colunas_exibir if c in resultado.columns
    ]

    st.dataframe(
        resultado[colunas_exibir],
        use_container_width=True,
        hide_index=True,
        height=430,
    )

    csv = resultado[colunas_exibir].to_csv(
        index=False,
        sep=";",
        encoding="utf-8-sig",
    )

    st.download_button(
        "Baixar detalhamento em CSV",
        data=csv,
        file_name="gestao_aduaneira.csv",
        mime="text/csv",
        key=f"download_{coluna_metrica}",
    )


# ==========================================================
# BLOCO DE CADA CONTROLE
# ==========================================================

def _bloco_controle(
    df,
    titulo,
    descricao,
    coluna_metrica,
    regra,
    unidade,
    chave,
):

    secao(titulo, descricao)

    dados = _preparar_dados(
        df,
        coluna_metrica,
        regra,
    )

    dados = _aplicar_filtros(dados, chave)

    if dados.empty:
        aviso(
            "Nenhum processo encontrado com os filtros selecionados."
        )
        return

    if (
        coluna_metrica not in dados.columns
        and dados["Indicador"].isna().all()
    ):
        aviso(
            f"Não foi possível calcular o indicador '{coluna_metrica}'. "
            "Verifique se as colunas de datas necessárias existem na base.",
            "atencao",
        )
        return

    if dados["Indicador"].notna().sum() == 0:
        aviso(
            "Os campos de cálculo deste indicador ainda estão vazios. "
            "Preencha os dados operacionais para visualizar os faróis.",
            "atencao",
        )

    _mostrar_indicadores(dados, unidade)

    _tabela_detalhada(
        dados,
        coluna_metrica,
        unidade,
    )


# ==========================================================
# PÁGINA PRINCIPAL
# ==========================================================

def pagina_gestao_aduaneira(df):

    cabecalho(
        "Gestão Aduaneira",
        "Acompanhamento dos controles de registro, desembaraço, DANFE e pagamento de ICMS.",
        chave="gestao_aduaneira",
    )

    if df is None or df.empty:
        st.warning(
            "A base operacional não possui registros para exibir."
        )
        return

    abas = st.tabs([
        "Controle de Registro DI",
        "Controle de Desembaraço",
        "Controle de Solicitação DANFE",
        "Controle de Recebimento DANFE",
        "Controle de Pagamento ICMS",
    ])

    with abas[0]:
        _bloco_controle(
            df,
            "Controle de Registro DI",
            "Acompanhamento do prazo para registro da DI/DUIMP.",
            "Data Registro DI/DUIMP",
            "registro_di",
            "Dias úteis",
            "registro_di",
        )

    with abas[1]:
        _bloco_controle(
            df,
            "Controle de Desembaraço",
            "Acompanhamento do tempo útil entre o registro e o desembaraço.",
            "Data Desembaraço",
            "desembaraco",
            "Horas",
            "desembaraco",
        )

    with abas[2]:
        _bloco_controle(
            df,
            "Controle de Solicitação DANFE",
            "Acompanhamento do prazo de solicitação da DANFE após o registro da DI/DUIMP.",
            "Data Solicitação DANFE",
            "padrao_atencao",
            "Dias úteis",
            "solicitacao_danfe",
        )
    with abas[3]:
            _bloco_controle(
                df,
                "Controle de Recebimento DANFE",
                "Acompanhamento do prazo de Recebimento da DANFE após o registro da DI/DUIMP.",
                "Data Recebimento DANFE",
                "padrao_atencao",
                "Dias úteis",
                "recebimento_danfe",
        )
    with abas[4]:
        _bloco_controle(
            df,
            "Controle de Pagamento ICMS",
            "Acompanhamento do prazo de pagamento do ICMS.",
            "Data Pagamento ICMS",
            "padrao_atencao",
            "Dias úteis",
            "pagamento_icms",
        )
