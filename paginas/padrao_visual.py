"""
Padrão visual compartilhado do dashboard (tema claro/escuro, cabeçalho, cartões, gráficos e tabela).

Todas as páginas usam este módulo, então qualquer ajuste de cor, fonte ou gráfico vale para o app inteiro.
Mantenha este arquivo na mesma pasta das páginas (por exemplo, "paginas/").

Uso básico em uma página:
    cabecalho("Título", "Subtítulo", chave="minha_pagina")
    filtrado = barra_filtros(dados, coluna_inicio, chave)
    cartao(...); faixa_farol(...); grafico_farol(...); grafico_duracao(...); grafico_evolucao(...)
    tabela_detalhada(filtrado, inicio, fim, chave, "arquivo.csv")
"""
from datetime import datetime
from html import escape

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

# ─────────────────────────────────────────────────────────────
# Constantes
# ─────────────────────────────────────────────────────────────
CORES_FAROL = {
    "DENTRO DO PRAZO": "#16A36A",
    "ATENÇÃO": "#E5A000",
    "ALERTA": "#E87524",
    "ATRASO": "#D64545",
    "SEM DATA": "#8795A5",
    "REVISAR REGRA": "#687386",
}
ORDEM_FAROL = ["DENTRO DO PRAZO", "ATENÇÃO", "ALERTA", "ATRASO", "REVISAR REGRA", "SEM DATA"]

MAX_LINHAS_TABELA = 500

PLOTLY_CONFIG = {
    "displaylogo": False,
    "modeBarButtonsToRemove": ["lasso2d", "select2d"],
    "toImageButtonOptions": {"format": "png", "scale": 2},
}


# ─────────────────────────────────────────────────────────────
# Temas claro/escuro, CSS e botão de alternar
# ─────────────────────────────────────────────────────────────
TEMAS = {
    "claro": {
        "template": "plotly_white",
        "fundo": "#F3F6FA", "cartao": "#FFFFFF", "cartao2": "#F7F9FC",
        "borda": "#DFE5EC", "input_borda": "#D3DCE6", "input_bg": "#F7F9FC",
        "texto": "#13233A", "texto2": "#3B4A5E", "texto3": "#64748B", "hint": "#8392A5",
        "acento": "#1F6FB2", "acento_suave": "#E3EEF8", "hover": "#EDF2F8",
        "destaque": "#13233A", "grade": "#EBEFF4",
        "aviso_bg": "#FFF6DB", "aviso_borda": "#F1DC9B", "aviso_texto": "#6B4E00",
        "hero": "linear-gradient(115deg,#142E4C 0%,#245783 100%)",
        "sombra": "0 1px 2px rgba(16,35,60,.05), 0 6px 16px rgba(16,35,60,.04)",
    },
    "escuro": {
        "template": "plotly_dark",
        "fundo": "#0B121C", "cartao": "#131E2C", "cartao2": "#182536",
        "borda": "#243246", "input_borda": "#2D3D54", "input_bg": "#0F1824",
        "texto": "#E8EEF6", "texto2": "#B9C6D6", "texto3": "#8FA0B5", "hint": "#6F8197",
        "acento": "#5AA2E0", "acento_suave": "#1C3350", "hover": "#1B2A3D",
        "destaque": "#E8EEF6", "grade": "#223045",
        "aviso_bg": "#2B2410", "aviso_borda": "#5A4A18", "aviso_texto": "#F0D58A",
        "hero": "linear-gradient(115deg,#0E2238 0%,#1B4A74 100%)",
        "sombra": "0 1px 2px rgba(0,0,0,.45), 0 6px 16px rgba(0,0,0,.25)",
    },
}


def tema_ativo():
    """Paleta ativa, lida do estado da sessão (cada usuário tem a sua)."""
    return TEMAS["escuro" if st.session_state.get("tema_escuro") else "claro"]


def alternar_tema():
    st.session_state["tema_escuro"] = not st.session_state.get("tema_escuro", False)


CSS_BASE = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

/* ── Estrutura geral ───────────────────────── */
.stApp {background:__fundo__}
[data-testid="stHeader"] {background:transparent;pointer-events:none}
[data-testid="stHeader"] button, [data-testid="stHeader"] a,
[data-testid="stHeader"] [data-baseweb] {pointer-events:auto}
[class*="st-key-botao_tema"] {position:relative;z-index:1000001}
.block-container {padding-top:4.4rem;padding-bottom:3rem;max-width:1500px}
.prontidao-hero, .kpi, .secao, .card-titulo, .aviso, .tabela-wrap,
[data-testid="stMarkdownContainer"] {font-family:'Inter','Segoe UI',sans-serif}
::-webkit-scrollbar {width:10px;height:10px}
::-webkit-scrollbar-thumb {background:__borda__;border-radius:8px}
::-webkit-scrollbar-track {background:transparent}

/* ── Barra lateral (se existir) ────────────── */
[data-testid="stSidebar"] {background:__cartao__;border-right:1px solid __borda__}
[data-testid="stSidebar"] p, [data-testid="stSidebar"] label,
[data-testid="stSidebar"] span, [data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 {color:__texto2__}

/* ── Texto ─────────────────────────────────── */
.stApp [data-testid="stMarkdownContainer"] p,
.stApp [data-testid="stMarkdownContainer"] li,
.stApp [data-testid="stCaptionContainer"] {color:__texto2__}
.stApp h1, .stApp h2, .stApp h3, .stApp h4 {color:__texto__}
.stApp [data-testid="stWidgetLabel"] p {color:__texto3__;font-weight:600;font-size:12.5px}

/* ── Cabeçalho ─────────────────────────────── */
.prontidao-hero {
  background:__hero__;padding:26px 30px;border-radius:16px;margin-bottom:18px;
  display:flex;justify-content:space-between;align-items:center;gap:20px;flex-wrap:wrap;
  box-shadow:__sombra__
}
.stApp .prontidao-hero h1 {color:#fff;font-size:27px;margin:0 0 4px;font-weight:700;letter-spacing:-.01em;padding:0}
.stApp .prontidao-hero p {color:#DCE8F4;margin:0;font-size:13.5px}
.hero-chip {
  background:rgba(255,255,255,.12);border:1px solid rgba(255,255,255,.22);
  padding:7px 14px;border-radius:999px;font-size:12px;color:#EAF2FA;white-space:nowrap
}

.hero-marca {display:flex;align-items:center;gap:22px;flex-wrap:wrap}
.hero-logo {
  background:#FFFFFF;border-radius:12px;padding:9px 18px;display:flex;align-items:center;
  box-shadow:0 2px 10px rgba(0,0,0,.18)
}
.hero-logo img {height:42px;width:auto;display:block}

/* ── Cartões de indicador ──────────────────── */
.kpi {
  background:__cartao__;border:1px solid __borda__;border-radius:12px;box-shadow:__sombra__;
  padding:14px 16px 12px 20px;position:relative;overflow:hidden;min-height:108px
}
.kpi::before {content:"";position:absolute;left:0;top:0;bottom:0;width:5px;background:var(--cor)}
.kpi-titulo {font-size:12.5px;color:__texto3__;font-weight:600}
.kpi-valor {font-size:31px;color:__texto__;font-weight:700;line-height:1.35;letter-spacing:-.02em}
.kpi-detalhe {font-size:12px;color:__hint__}

/* ── Faixa de faróis ───────────────────────── */
.faixa {display:flex;height:10px;border-radius:999px;overflow:hidden;gap:2px;margin:14px 0 6px}
.faixa div {min-width:4px;transition:filter .15s}
.faixa div:hover {filter:brightness(1.12)}

/* ── Títulos e avisos ──────────────────────── */
.secao {font-size:17px;font-weight:700;color:__texto__;margin:26px 0 2px}
.secao-sub {font-size:12.5px;color:__texto3__;margin:0 0 10px;font-family:'Inter','Segoe UI',sans-serif}
.card-titulo {font-size:14px;font-weight:650;color:__texto__;margin-bottom:2px}
.card-sub {font-size:11.5px;color:__hint__;margin-bottom:6px;font-family:'Inter','Segoe UI',sans-serif}
.aviso {padding:12px 16px;border-radius:12px;font-size:13px;border:1px solid;margin:10px 0}
.aviso-info {background:__acento_suave__;border-color:__borda__;color:__texto2__}
.aviso-atencao {background:__aviso_bg__;border-color:__aviso_borda__;color:__aviso_texto__}

/* ── Contêineres, expander, botões ─────────── */
[data-testid="stVerticalBlockBorderWrapper"] {
  border-radius:12px;border-color:__borda__;background:__cartao__;box-shadow:__sombra__
}
.stApp [data-testid="stExpander"] {background:__cartao__;border-color:__borda__;border-radius:12px}
.stApp [data-testid="stExpander"] summary,
.stApp [data-testid="stExpander"] summary p {color:__texto__}
.stApp .stDownloadButton button, .stApp .stButton button {
  background:__cartao__;color:__texto__;border:1px solid __input_borda__;border-radius:10px;
  font-weight:600;box-shadow:__sombra__;transition:border-color .15s,color .15s
}
.stApp .stDownloadButton button:hover, .stApp .stButton button:hover {
  border-color:__acento__;background:__hover__
}
.stApp .stDownloadButton button:hover p, .stApp .stButton button:hover p {color:__acento__}
.stApp .stButton button:focus:not(:active) {border-color:__acento__;box-shadow:0 0 0 3px __acento_suave__}

/* ── Campos de filtro ──────────────────────── */
.stApp [data-baseweb="input"], .stApp [data-baseweb="base-input"],
.stApp [data-baseweb="select"] > div {
  background-color:__input_bg__;border-color:__input_borda__;border-radius:10px;color:__texto__
}
.stApp [data-baseweb="input"]:focus-within, .stApp [data-baseweb="select"]:focus-within > div {
  border-color:__acento__;box-shadow:0 0 0 3px __acento_suave__
}
.stApp input {color:__texto__}
.stApp input::placeholder {color:__hint__}
.stApp [data-baseweb="select"] div {color:__texto__}
.stApp [data-baseweb="select"] svg {fill:__texto3__}
.stApp [data-baseweb="select"] [data-baseweb="tag"] {background-color:__acento_suave__;border-radius:8px}
.stApp [data-baseweb="select"] [data-baseweb="tag"],
.stApp [data-baseweb="select"] [data-baseweb="tag"] span {color:__acento__;font-weight:600}
.stApp [data-baseweb="select"] [data-baseweb="tag"] svg {fill:__acento__}

/* ── Listas suspensas e calendário ─────────── */
[data-baseweb="popover"] > div {
  background:__cartao__;border:1px solid __borda__;border-radius:12px;box-shadow:__sombra__
}
[data-baseweb="menu"], [data-baseweb="calendar"] {background:__cartao__;color:__texto__}
[data-baseweb="menu"] li {color:__texto2__}
[data-baseweb="menu"] li:hover {background:__hover__}
[data-baseweb="menu"] li[aria-selected="true"] {background:__acento_suave__;color:__acento__}
[data-baseweb="calendar"] button, [data-baseweb="calendar"] div {color:__texto2__}

/* ── Abas ──────────────────────────────────── */
button[data-baseweb="tab"] {font-weight:600;font-size:14.5px;padding:10px 18px}
.stApp button[data-baseweb="tab"] p {color:__texto3__}
.stApp button[data-baseweb="tab"][aria-selected="true"] p {color:__acento__}
[data-baseweb="tab-highlight"] {background-color:__acento__}
[data-baseweb="tab-border"] {background-color:__borda__}

/* ── Tabela de detalhamento ────────────────── */
.tabela-wrap {
  max-height:440px;overflow:auto;border:1px solid __borda__;border-radius:12px;
  background:__cartao__;box-shadow:__sombra__
}
.tabela-wrap table {width:100%;border-collapse:separate;border-spacing:0;font-size:12.5px}
.tabela-wrap th {
  position:sticky;top:0;z-index:1;background:__cartao2__;color:__texto3__;font-weight:600;
  text-align:left;padding:11px 14px;border-bottom:1px solid __borda__;white-space:nowrap
}
.tabela-wrap td {padding:9px 14px;border-bottom:1px solid __borda__;color:__texto2__;white-space:nowrap}
.tabela-wrap tbody tr:hover td {background:__hover__}
.tabela-wrap tbody tr:last-child td {border-bottom:none}
.chip {
  display:inline-flex;align-items:center;gap:7px;padding:3px 10px;border-radius:999px;
  border:1px solid;font-size:11.5px;font-weight:600;color:__texto__
}
.chip i {width:7px;height:7px;border-radius:50%;display:inline-block}
.dias {display:flex;align-items:center;gap:10px;min-width:120px}
.dias span {min-width:46px;font-variant-numeric:tabular-nums;color:__texto__}
.barra {flex:1;height:6px;border-radius:999px;background:__borda__;overflow:hidden}
.barra i {display:block;height:100%;border-radius:999px}
</style>
"""


def gerar_css(t):
    css = CSS_BASE
    for chave, valor in t.items():
        css = css.replace(f"__{chave}__", str(valor))
    return css



def html_limpo(texto):
    """Remove indentação/linhas vazias para o Markdown não tratar o HTML como bloco de código."""
    return "\n".join(l.strip() for l in texto.splitlines() if l.strip())



# ─────────────────────────────────────────────────────────────
# Componentes visuais
# ─────────────────────────────────────────────────────────────
def cartao(titulo, valor, detalhe, cor):
    st.markdown(
        html_limpo(f"""
        <div class="kpi" style="--cor:{cor}">
          <div class="kpi-titulo">{titulo}</div>
          <div class="kpi-valor">{valor}</div>
          <div class="kpi-detalhe">{detalhe}</div>
        </div>"""),
        unsafe_allow_html=True,
    )


def titulo_card(titulo, subtitulo=""):
    st.markdown(
        html_limpo(f"""
        <div class="card-titulo">{titulo}</div>
        <div class="card-sub">{subtitulo}</div>"""),
        unsafe_allow_html=True,
    )


def secao(titulo, subtitulo=""):
    st.markdown(
        html_limpo(f"""
        <div class="secao">{titulo}</div>
        <div class="secao-sub">{subtitulo}</div>"""),
        unsafe_allow_html=True,
    )


def aviso(texto, tipo="info"):
    st.markdown(f'<div class="aviso aviso-{tipo}">{texto}</div>', unsafe_allow_html=True)


def faixa_farol(contagem, total):
    segmentos = ""
    for farol in ORDEM_FAROL:
        n = int(contagem.get(farol, 0))
        if n:
            pct = n / total * 100
            segmentos += (
                f'<div title="{nome_farol(farol)}: {n} ({pct:.1f}%)" '
                f'style="width:{pct:.2f}%;background:{CORES_FAROL[farol]}"></div>'
            )
    st.markdown(f'<div class="faixa">{segmentos}</div>', unsafe_allow_html=True)


MESES_PT = ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"]


def nome_farol(farol):
    """Nome de exibição do farol: só a primeira letra maiúscula, em vez de caixa alta."""
    return farol.capitalize()


def base_layout(fig, altura, legenda_y=-0.18):
    t = tema_ativo()
    fig.update_layout(
        template=t["template"],
        height=altura,
        margin=dict(l=8, r=8, t=10, b=8),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, Segoe UI, sans-serif", color=t["texto2"], size=12),
        hoverlabel=dict(bgcolor=t["cartao"], bordercolor=t["borda"], align="left",
                        font=dict(size=12, color=t["texto"])),
        legend=dict(orientation="h", y=legenda_y, x=0, itemsizing="constant",
                    font=dict(size=11, color=t["texto2"]), title_text=""),
        modebar=dict(bgcolor="rgba(0,0,0,0)", color=t["hint"], activecolor=t["acento"]),
    )
    return fig


def estilizar_eixos(fig):
    """Eixos discretos: sem linhas, sem marcas, grade pontilhada na cor do tema."""
    t = tema_ativo()
    comum = dict(
        showline=False, zeroline=False, ticks="",
        gridcolor=t["grade"], griddash="dot",
        tickfont=dict(size=11, color=t["texto3"]),
        title_font=dict(size=11, color=t["texto3"]),
    )
    fig.update_xaxes(showgrid=False, **comum)
    fig.update_yaxes(showgrid=True, **comum)


# ─────────────────────────────────────────────────────────────
# Gráficos
# ─────────────────────────────────────────────────────────────
def grafico_farol(dados, chave, regras=None):
    resumo = dados["Farol da etapa"].value_counts().reindex(ORDEM_FAROL, fill_value=0)
    resumo = resumo[resumo > 0]
    if resumo.empty:
        aviso("Sem dados para exibir.")
        return

    total = int(resumo.sum())
    pct_prazo = int(resumo.get("DENTRO DO PRAZO", 0)) / total * 100
    t = tema_ativo()
    nomes = [nome_farol(f) for f in resumo.index]
    fig = go.Figure(
        go.Pie(
            labels=[f"{n} · {v}" for n, v in zip(nomes, resumo.values)],
            values=list(resumo.values),
            hole=0.7,
            sort=False,
            direction="clockwise",
            marker=dict(
                colors=[CORES_FAROL[f] for f in resumo.index],
                line=dict(color=t["cartao"], width=3),
            ),
            textinfo="percent",
            textposition="outside",
            textfont=dict(size=11, color=t["texto2"]),
            automargin=True,
            customdata=[[n, (regras or {}).get(f, "")] for n, f in zip(nomes, resumo.index)],
            hovertemplate=(
                "<b>%{customdata[0]}</b><br>Processos: %{value}<br>"
                "Participação: %{percent}"
                + ("<br><i>Regra: %{customdata[1]}</i>" if regras else "")
                + "<extra></extra>"
            ),
        )
    )
    fig.add_annotation(
        text=(
            f"<b><span style='font-size:30px;color:{t['texto']}'>{total}</span></b><br>"
            f"<span style='font-size:12px;color:{t['texto3']}'>processos</span><br>"
            f"<span style='font-size:12px;color:{CORES_FAROL['DENTRO DO PRAZO']}'>{pct_prazo:.0f}% no prazo</span>"
        ),
        x=0.5, y=0.5, showarrow=False,
    )
    base_layout(fig, 340, legenda_y=-0.1)
    st.plotly_chart(fig, use_container_width=True, key=f"farol_{chave}",
                    config=PLOTLY_CONFIG, theme=None)


def grafico_duracao(dados, chave, marcos=((1, "1 dia"), (3, "3 dias")), usar_faixas=True):
    base = dados.loc[dados["Dias"].notna(), ["Dias", "Farol da etapa"]].copy()
    if base.empty:
        aviso("Ainda não há durações calculáveis.")
        return

    t = tema_ativo()
    base["Farol"] = base["Farol da etapa"].map(nome_farol)
    cores = {nome_farol(k): v for k, v in CORES_FAROL.items()}
    fig = px.histogram(
        base, x="Dias", color="Farol", nbins=24,
        color_discrete_map=cores,
        category_orders={"Farol": [nome_farol(f) for f in ORDEM_FAROL]},
        labels={"Dias": "Dias decorridos"},
    )
    fig.update_traces(
        marker_line_color=t["cartao"], marker_line_width=1.5,
        hovertemplate="Faixa: %{x} dias<br>Processos: %{y}<extra>%{fullData.name}</extra>",
    )

    # Faixas de fundo que representam as zonas da regra
    topo = max(float(base["Dias"].max()), 3.5) * 1.05
    faixas = ((0, 1, "DENTRO DO PRAZO"), (1, 3, "ATENÇÃO"), (3, topo, "ATRASO")) if usar_faixas else ()
    for x0, x1, farol in faixas:
        fig.add_vrect(x0=x0, x1=x1, fillcolor=CORES_FAROL[farol], opacity=0.08,
                      line_width=0, layer="below")

    for marco, rotulo in marcos:
        fig.add_vline(x=marco, line_dash="dot", line_color=t["texto3"], line_width=1,
                      annotation_text=rotulo, annotation_position="top left",
                      annotation_font=dict(size=10, color=t["texto3"]))
    media = float(base["Dias"].mean())
    fig.add_vline(x=media, line_dash="dash", line_color=t["destaque"], line_width=2,
                  annotation_text=f"Média {media:.1f} d", annotation_position="top right",
                  annotation_font=dict(size=11, color=t["destaque"]))

    base_layout(fig, 340, legenda_y=-0.22)
    estilizar_eixos(fig)
    fig.update_layout(barmode="stack", bargap=0.06, hovermode="closest",
                      xaxis_title="Duração (dias)", yaxis_title="Quantidade de processos")
    st.plotly_chart(fig, use_container_width=True, key=f"duracao_{chave}",
                    config=PLOTLY_CONFIG, theme=None)


def grafico_evolucao(dados, coluna_inicio, chave):
    base = dados.loc[dados[coluna_inicio].notna(), [coluna_inicio, "Farol da etapa"]].copy()
    if base.empty:
        aviso("Sem datas de início para montar a evolução.")
        return

    base["Mês"] = base[coluna_inicio].dt.to_period("M").dt.to_timestamp()
    tabela = base.groupby(["Mês", "Farol da etapa"]).size().unstack(fill_value=0)
    tabela = tabela.reindex(columns=[f for f in ORDEM_FAROL if f in tabela.columns])
    total = tabela.sum(axis=1)
    if "DENTRO DO PRAZO" in tabela.columns:
        pct_prazo = tabela["DENTRO DO PRAZO"] / total * 100
    else:
        pct_prazo = pd.Series(0.0, index=tabela.index)

    t = tema_ativo()
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    for farol in tabela.columns:
        fig.add_trace(
            go.Bar(
                x=tabela.index, y=tabela[farol], name=nome_farol(farol),
                marker=dict(color=CORES_FAROL[farol], line=dict(color=t["cartao"], width=1)),
                hovertemplate=f"{nome_farol(farol)}: %{{y}}<extra></extra>",
            ),
            secondary_y=False,
        )
    # Total de cada mês, no topo da barra
    fig.add_trace(
        go.Scatter(
            x=tabela.index, y=total, mode="text",
            text=[str(int(v)) for v in total], textposition="top center",
            textfont=dict(size=11, color=t["texto3"]),
            showlegend=False, hoverinfo="skip",
        ),
        secondary_y=False,
    )
    fig.add_trace(
        go.Scatter(
            x=tabela.index, y=pct_prazo, name="% dentro do prazo",
            mode="lines+markers",
            line=dict(color=t["destaque"], width=2.5, shape="spline"),
            marker=dict(size=7, color=t["cartao"], line=dict(color=t["destaque"], width=2)),
            hovertemplate="% dentro do prazo: %{y:.1f}%<extra></extra>",
        ),
        secondary_y=True,
    )

    base_layout(fig, 420, legenda_y=-0.36)
    estilizar_eixos(fig)
    fig.update_layout(barmode="stack", bargap=0.35, hovermode="x unified",
                      margin=dict(l=8, r=8, t=46, b=8))
    fig.update_yaxes(title_text="Processos", range=[0, float(total.max()) * 1.18],
                     secondary_y=False)
    fig.update_yaxes(title_text="% dentro do prazo", range=[0, 105], ticksuffix="%",
                     showgrid=False, secondary_y=True)

    eixo_x = dict(
        hoverformat="%m/%Y",
        rangeslider=dict(visible=False),
        rangeselector=dict(
            buttons=[
                dict(count=3, label="3 meses", step="month", stepmode="backward"),
                dict(count=6, label="6 meses", step="month", stepmode="backward"),
                dict(count=1, label="1 ano", step="year", stepmode="backward"),
                dict(step="all", label="Tudo"),
            ],
            x=0, xanchor="left", y=1.03, yanchor="bottom",
            bgcolor=t["cartao2"], activecolor=t["acento_suave"],
            bordercolor=t["borda"], borderwidth=1,
            font=dict(size=11, color=t["texto2"]),
        ),

    )
    if len(tabela) <= 18:
        eixo_x.update(
            tickmode="array", tickvals=list(tabela.index),
            ticktext=[f"{MESES_PT[d.month - 1]}/{str(d.year)[2:]}" for d in tabela.index],
        )
    else:
        eixo_x.update(tickformat="%m/%y")
    fig.update_xaxes(**eixo_x)
    st.plotly_chart(fig, use_container_width=True, key=f"evolucao_{chave}",
                    config=PLOTLY_CONFIG, theme=None)


# ─────────────────────────────────────────────────────────────
# Tabela (HTML próprio, acompanha o tema)
# ─────────────────────────────────────────────────────────────
def chip(texto, cor):
    return (
        f'<span class="chip" style="background:{cor}22;border-color:{cor}55">'
        f'<i style="background:{cor}"></i>{escape(texto)}</span>'
    )


def tabela_html(dados, colunas, inicio, fim, dias_max):
    cabecalho = "".join(f"<th>{escape(c)}</th>" for c in colunas)
    cor_situacao = {"Concluída": tema_ativo()["acento"], "Em andamento": CORES_FAROL["ATENÇÃO"]}
    linhas = []
    for _, r in dados.iterrows():
        farol = r.get("Farol da etapa")
        celulas = []
        for c in colunas:
            v = r[c]
            if c in (inicio, fim):
                txt = v.strftime("%d/%m/%Y") if pd.notna(v) else "—"
                celulas.append(f"<td>{txt}</td>")
            elif c == "Dias":
                if pd.isna(v):
                    celulas.append("<td>—</td>")
                else:
                    pct = min(float(v) / dias_max * 100, 100)
                    cor = CORES_FAROL.get(farol, "#8795A5")
                    celulas.append(
                        f'<td><div class="dias"><span>{v:.1f} d</span>'
                        f'<div class="barra"><i style="width:{pct:.0f}%;background:{cor}"></i></div></div></td>'
                    )
            elif c == "Farol da etapa":
                celulas.append(f"<td>{chip(str(v).capitalize(), CORES_FAROL.get(v, '#8795A5'))}</td>")
            elif c == "Situação da etapa":
                celulas.append(f"<td>{chip(str(v), cor_situacao.get(v, '#8795A5'))}</td>")
            else:
                txt = "—" if pd.isna(v) else escape(str(v))
                celulas.append(f"<td>{txt}</td>")
        linhas.append("<tr>" + "".join(celulas) + "</tr>")
    return (
        '<div class="tabela-wrap"><table><thead><tr>' + cabecalho + "</tr></thead><tbody>"
        + "".join(linhas) + "</tbody></table></div>"
    )


def tabela_detalhada(dados, inicio, fim, chave, nome_arquivo):
    ordens = {
        "Maior tempo decorrido": ("Dias", False),
        "Menor tempo decorrido": ("Dias", True),
        "Início mais recente": (inicio, False),
        "Início mais antigo": (inicio, True),
    }
    c1, _ = st.columns([1, 3])
    with c1:
        escolha = st.selectbox("Ordenar por", list(ordens), key=f"ordem_{chave}")
    coluna_ordem, crescente = ordens[escolha]
    dados = dados.sort_values(coluna_ordem, ascending=crescente, na_position="last")

    preferidas = [
        "Status", "Ref.Cliente", "Nº Processo", "Responsável", "Planta",
        "Categoria", "Exportador", "Modal", inicio, fim, "Dias",
        "Farol da etapa", "Situação da etapa",
    ]
    colunas = [c for c in preferidas if c in dados.columns]
    dias_max = float(dados["Dias"].max()) if dados["Dias"].notna().any() else 1.0
    dias_max = max(dias_max, 1.0)

    exibir = dados.head(MAX_LINHAS_TABELA)
    st.markdown(tabela_html(exibir, colunas, inicio, fim, dias_max), unsafe_allow_html=True)
    if len(dados) > MAX_LINHAS_TABELA:
        st.caption(f"Exibindo {MAX_LINHAS_TABELA} de {len(dados)} processos. "
                   "O CSV exportado contém todos.")

    exportar = dados.drop(columns=["_data_calculo"], errors="ignore")
    csv = exportar.to_csv(index=False, sep=";", encoding="utf-8-sig").encode("utf-8-sig")
    st.download_button(
        "⬇️ Exportar dados filtrados (CSV)", csv,
        file_name=nome_arquivo, mime="text/csv",
        key=f"download_{chave}",
    )


# ─────────────────────────────────────────────────────────────
# Blocos de página reutilizáveis: cabeçalho e barra de filtros
# ─────────────────────────────────────────────────────────────
def aplicar_tema():
    """Chame UMA vez no app.py, logo depois de criar o menu lateral.
    Aplica o tema claro/escuro em todo o app (todas as páginas, inclusive a Home)
    e coloca o botão de alternar na barra lateral."""
    escuro = bool(st.session_state.get("tema_escuro", False))
    st.sidebar.button(
        "☀️ Modo claro" if escuro else "🌙 Modo escuro",
        key="botao_tema_global", on_click=alternar_tema,
        use_container_width=True,
    )
    st.sidebar.markdown(gerar_css(tema_ativo()), unsafe_allow_html=True)
    st.session_state["_tema_global"] = True


def cabecalho(titulo, subtitulo, chave="topo"):
    """CSS do tema + botão claro/escuro + cabeçalho com o logo. Chamar no início de cada página."""
    if not st.session_state.get("_tema_global"):  # app.py não chamou aplicar_tema(): a página cuida do tema
        escuro = bool(st.session_state.get("tema_escuro", False))
        _, col_tema = st.columns([4, 1])
        with col_tema:
            st.button(
                "☀️ Modo claro" if escuro else "🌙 Modo escuro",
                key=f"botao_tema_{chave}", on_click=alternar_tema,
                use_container_width=True,
            )
        st.markdown(gerar_css(tema_ativo()), unsafe_allow_html=True)

    agora = datetime.now().strftime("%d/%m/%Y %H:%M")
    st.markdown(
        html_limpo(f"""
        <div class="prontidao-hero">
          <div class="hero-marca">
            {logo_html()}
            <div>
            <h1>{titulo}</h1>
            <p>{subtitulo}</p>
            </div>
          </div>
          <div class="hero-chip">Atualizado em {agora}</div>
        </div>"""),
        unsafe_allow_html=True,
    )


def barra_filtros(dados, coluna_inicio, chave):
    """Barra de filtros padrão. Devolve o DataFrame filtrado.
    Exige as colunas "Farol da etapa" e "Situação da etapa" em `dados`."""
    dmin = dmax = None
    with st.container(border=True):
        f1, f2, f3, f4, f5 = st.columns([1.3, 1.3, 1.5, 1, 1.5])
        with f1:
            referencia = st.text_input(
                "Referência do cliente", key=f"ref_{chave}", placeholder="Buscar referência..."
            ).strip()
        with f2:
            processo = st.text_input(
                "Nº do processo", key=f"proc_{chave}", placeholder="Buscar processo..."
            ).strip()
        with f3:
            opcoes = [x for x in ORDEM_FAROL if x in dados["Farol da etapa"].unique()]
            farois = st.multiselect(
                "Farol", opcoes, key=f"farol_filtro_{chave}", placeholder="Todos os faróis"
            )
        with f4:
            situacao = st.selectbox("Situação", ["Todas", "Em andamento", "Concluída"],
                                    key=f"situacao_{chave}")
        with f5:
            validas = dados[coluna_inicio].dropna()
            periodo = None
            if not validas.empty:
                dmin, dmax = validas.min().date(), validas.max().date()
                periodo = st.date_input(
                    "Período (início da etapa)", value=(dmin, dmax),
                    min_value=dmin, max_value=dmax, key=f"periodo_{chave}",
                    format="DD/MM/YYYY",
                )

    filtrado = dados.copy()
    if referencia and "Ref.Cliente" in filtrado:
        filtrado = filtrado[filtrado["Ref.Cliente"].astype(str).str.contains(
            referencia, case=False, na=False, regex=False)]
    if processo and "Nº Processo" in filtrado:
        filtrado = filtrado[filtrado["Nº Processo"].astype(str).str.contains(
            processo, case=False, na=False, regex=False)]
    if farois:
        filtrado = filtrado[filtrado["Farol da etapa"].isin(farois)]
    if situacao != "Todas":
        filtrado = filtrado[filtrado["Situação da etapa"] == situacao]
    if (periodo and isinstance(periodo, (tuple, list)) and len(periodo) == 2
            and (periodo[0], periodo[1]) != (dmin, dmax)):
        ini = pd.Timestamp(periodo[0])
        fim_ = pd.Timestamp(periodo[1]) + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)
        filtrado = filtrado[filtrado[coluna_inicio].between(ini, fim_)]
    return filtrado


# ─────────────────────────────────────────────────────────────
# Logo Savoy (PNG recortado, embutido em base64 para o arquivo ser autossuficiente)
# ─────────────────────────────────────────────────────────────
LOGO_SAVOY_B64 = "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"


def logo_html():
    if not LOGO_SAVOY_B64:
        return ""
    return (
        '<div class="hero-logo"><img alt="Savoy Indústria de Cosméticos S.A." '
        f'src="data:image/png;base64,{LOGO_SAVOY_B64}"></div>'
    )