"""
Padrão visual profissional do dashboard Savoy/Pibernat (tema claro/escuro, componentes e análise interativa).

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
import re
import unicodedata

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
        "scheme": "light", "template": "plotly_white",
        "fundo": "#F3F6FB", "cartao": "#FFFFFF", "cartao2": "#F8FAFD",
        "borda": "#E3EAF2", "input_borda": "#D7E0EB", "input_bg": "#FFFFFF",
        "texto": "#12243A", "texto2": "#40536B", "texto3": "#708198", "hint": "#91A0B3",
        "acento": "#2468B4", "acento_suave": "#E7F0FA", "hover": "#F1F6FC",
        "destaque": "#163A5B", "grade": "#EAF0F6",
        "aviso_bg": "#FFF8E8", "aviso_borda": "#F2DDAA", "aviso_texto": "#795719",
        "hero": "linear-gradient(112deg,#0B1D31 0%,#123653 52%,#1C5278 100%)",
        "sombra": "0 2px 5px rgba(15,35,58,.035), 0 12px 34px rgba(15,35,58,.055)",
    },
    "escuro": {
        "scheme": "dark", "template": "plotly_dark",
        "fundo": "#0A1420", "cartao": "#111E2D", "cartao2": "#162638",
        "borda": "#26384D", "input_borda": "#344A62", "input_bg": "#0D1926",
        "texto": "#EDF3FA", "texto2": "#C0CEDD", "texto3": "#91A4B9", "hint": "#71859B",
        "acento": "#6CAEE8", "acento_suave": "#1A3651", "hover": "#1A2B3E",
        "destaque": "#E6F0FA", "grade": "#25364A",
        "aviso_bg": "#302817", "aviso_borda": "#665326", "aviso_texto": "#F2D995",
        "hero": "linear-gradient(112deg,#081522 0%,#102A42 52%,#17466A 100%)",
        "sombra": "0 2px 7px rgba(0,0,0,.22), 0 14px 38px rgba(0,0,0,.20)",
    },
}



def tema_ativo():
    """Paleta ativa, lida do estado da sessão (cada usuário tem a sua)."""
    return TEMAS["escuro" if st.session_state.get("tema_escuro") else "claro"]


def alternar_tema():
    st.session_state["tema_escuro"] = not st.session_state.get("tema_escuro", False)


CSS_BASE = """
<style>
:root { color-scheme: __scheme__; }
.stApp {
  background: radial-gradient(ellipse at 86% 0%, rgba(36,104,180,.055), transparent 34%),
              linear-gradient(180deg, __fundo__ 0%, __fundo__ 100%);
  font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
}
[data-testid="stAppViewContainer"], [data-testid="stMain"] {background: transparent;}
[data-testid="stHeader"] {background: transparent; height: 2.7rem;}
[data-testid="stHeader"] button {color: __texto2__;}
.block-container {max-width: 1680px; padding-top: 2.35rem; padding-bottom: 3.4rem;}
[data-testid="stMainBlockContainer"] {padding-left: clamp(1.25rem, 3vw, 3.4rem); padding-right: clamp(1.25rem, 3vw, 3.4rem);}
[data-testid="stMarkdownContainer"], [data-testid="stCaptionContainer"] {font-family: inherit;}
.stApp h1, .stApp h2, .stApp h3, .stApp h4 {color: __texto__; letter-spacing: -.025em;}
.stApp p, .stApp li {color: __texto2__;}
.stApp [data-testid="stCaptionContainer"] {color: __texto3__;}
.stApp [data-testid="stWidgetLabel"] p, .stApp label {color: __texto3__; font-weight: 650; font-size: .78rem; letter-spacing: .01em;}
.stApp [data-testid="stVerticalBlock"] {gap: .9rem;}
hr {border-color: __borda__ !important; opacity: .8;}
::-webkit-scrollbar {width: 9px; height: 9px;}
::-webkit-scrollbar-thumb {background: __borda__; border-radius: 20px; border: 2px solid transparent; background-clip: padding-box;}
::-webkit-scrollbar-track {background: transparent;}

/* Navegação institucional */
[data-testid="stSidebar"] {
  background: linear-gradient(180deg, #0B1B2C 0%, #102A40 52%, #0D2236 100%);
  border-right: 1px solid rgba(255,255,255,.07);
}
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p,
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] li,
[data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3, [data-testid="stSidebar"] label,
[data-testid="stSidebar"] [data-testid="stWidgetLabel"] p {color: #DCE7F2 !important;}
[data-testid="stSidebar"] [data-testid="stCaptionContainer"] {color: #91A7BC !important;}
[data-testid="stSidebar"] hr {border-color: rgba(221,235,248,.14) !important;}
[data-testid="stSidebar"] [data-testid="stRadio"] [role="radiogroup"] {gap: .34rem;}
[data-testid="stSidebar"] [data-testid="stRadio"] label {
  border: 1px solid transparent; border-radius: 10px; padding: .47rem .68rem;
  transition: background .18s ease, border-color .18s ease, transform .18s ease;
}
[data-testid="stSidebar"] [data-testid="stRadio"] label:hover {
  background: rgba(255,255,255,.075); border-color: rgba(255,255,255,.08); transform: translateX(2px);
}
[data-testid="stSidebar"] [data-testid="stRadio"] label:has(input:checked) {
  background: linear-gradient(100deg, rgba(73,145,207,.27), rgba(73,145,207,.09));
  border-color: rgba(125,184,231,.28); box-shadow: inset 3px 0 0 #79B8E8;
}
[data-testid="stSidebar"] [data-testid="stRadio"] label p,
[data-testid="stSidebar"] [data-testid="stRadio"] label span {color: #DCE7F2 !important; font-weight: 600;}
[data-testid="stSidebar"] .stButton button {
  width: 100%; background: rgba(255,255,255,.07) !important; color: #EAF3FA !important;
  border: 1px solid rgba(255,255,255,.15) !important; border-radius: 10px !important;
  box-shadow: none !important; font-weight: 650;
}
[data-testid="stSidebar"] .stButton button:hover {background: rgba(255,255,255,.13) !important; border-color: rgba(255,255,255,.28) !important;}

/* Cabeçalho premium */
.prontidao-hero {
  position: relative; isolation: isolate; overflow: hidden;
  background: __hero__; border: 1px solid rgba(255,255,255,.10);
  border-radius: 20px; padding: 27px 30px; margin: 0 0 22px;
  display: flex; justify-content: space-between; align-items: center; gap: 24px; flex-wrap: wrap;
  box-shadow: 0 15px 42px rgba(8,28,48,.16);
}
.prontidao-hero::before {
  content: ""; position: absolute; z-index: -1; width: 440px; height: 440px; right: -120px; top: -280px;
  border: 1px solid rgba(255,255,255,.13); border-radius: 50%;
  box-shadow: 0 0 0 34px rgba(255,255,255,.025), 0 0 0 72px rgba(255,255,255,.018);
}
.prontidao-hero::after {
  content: ""; position: absolute; z-index: -1; width: 240px; height: 240px; right: 17%; bottom: -205px;
  border: 1px solid rgba(255,255,255,.10); border-radius: 50%;
}
.hero-marca {display: flex; align-items: center; gap: 22px; flex-wrap: wrap; min-width: 0;}
.hero-logo {
  background: rgba(255,255,255,.98); border: 1px solid rgba(255,255,255,.45);
  border-radius: 14px; padding: 10px 17px; display: flex; align-items: center; justify-content: center;
  min-width: 114px; min-height: 66px; box-shadow: 0 7px 20px rgba(0,0,0,.17);
}
.hero-logo img {height: 43px; max-width: 190px; width: auto; object-fit: contain; display: block;}
.hero-eyebrow {font-size: 10px; text-transform: uppercase; letter-spacing: .19em; font-weight: 750; color: #9FC7E7; margin-bottom: 7px;}
.stApp .prontidao-hero h1 {color: #FFFFFF; font-size: clamp(1.45rem, 2.4vw, 2rem); line-height: 1.18; margin: 0 0 7px; font-weight: 750; letter-spacing: -.035em; padding: 0;}
.stApp .prontidao-hero p {color: #D2E1EE; margin: 0; font-size: .88rem; line-height: 1.55; max-width: 760px;}
.hero-side {display: flex; flex-direction: column; align-items: flex-end; gap: 6px; min-width: 150px;}
.hero-chip {display: inline-flex; align-items: center; gap: 8px; background: rgba(255,255,255,.10); border: 1px solid rgba(255,255,255,.18); padding: 8px 13px; border-radius: 999px; font-size: 11px; color: #F2F7FC; white-space: nowrap; backdrop-filter: blur(8px);}
.hero-dot {width: 7px; height: 7px; border-radius: 50%; background: #64D7A3; box-shadow: 0 0 0 4px rgba(100,215,163,.13); display: inline-block;}
.hero-updated {font-size: 10px; color: #A9C1D5; letter-spacing: .04em;}

/* Indicadores */
.kpi {
  position: relative; overflow: hidden; min-height: 126px; padding: 17px 19px 16px 20px;
  background: __cartao__; border: 1px solid __borda__; border-radius: 16px; box-shadow: __sombra__;
  transition: transform .2s ease, box-shadow .2s ease, border-color .2s ease;
}
.kpi:hover {transform: translateY(-3px); border-color: color-mix(in srgb, var(--cor) 38%, __borda__); box-shadow: 0 12px 30px rgba(12,37,64,.10);}
.kpi::before {content: ""; position: absolute; left: 0; top: 16px; bottom: 16px; width: 4px; border-radius: 0 5px 5px 0; background: var(--cor);}
.kpi::after {content: ""; position: absolute; width: 118px; height: 118px; right: -50px; top: -55px; border-radius: 50%; background: var(--cor); opacity: .055;}
.kpi-head {display: flex; align-items: center; justify-content: space-between; gap: 10px; margin-bottom: 8px;}
.kpi-titulo {font-size: 11px; line-height: 1.4; color: __texto3__; font-weight: 750; text-transform: uppercase; letter-spacing: .075em;}
.kpi-icone {width: 29px; height: 29px; flex: 0 0 29px; border-radius: 9px; background: color-mix(in srgb, var(--cor) 12%, __cartao__); color: var(--cor); display: grid; place-items: center; font-size: 14px; font-weight: 800;}
.kpi-valor {font-size: clamp(1.65rem, 2.1vw, 2.15rem); color: __texto__; font-weight: 780; line-height: 1.16; letter-spacing: -.045em; font-variant-numeric: tabular-nums;}
.kpi-detalhe {font-size: 11px; color: __hint__; margin-top: 7px; line-height: 1.4;}

/* Distribuição / secções */
.faixa {display: flex; height: 9px; border-radius: 20px; overflow: hidden; gap: 3px; margin: 15px 0 7px; background: __borda__;}
.faixa div {min-width: 3px; transition: filter .16s ease, transform .16s ease;}
.faixa div:hover {filter: brightness(1.12); transform: scaleY(1.35);}
.secao {display: flex; align-items: center; gap: 10px; font-size: 16px; line-height: 1.3; font-weight: 760; color: __texto__; margin: 26px 0 3px; letter-spacing: -.02em;}
.secao::before {content: ""; width: 4px; height: 18px; flex: 0 0 4px; border-radius: 5px; background: __acento__;}
.secao-sub {font-size: 11.5px; color: __texto3__; margin: 0 0 10px 14px;}
.card-titulo {font-size: 13px; font-weight: 750; color: __texto__; margin: 0 0 3px; letter-spacing: -.01em;}
.card-sub {font-size: 11px; color: __hint__; margin: 0 0 7px;}
.aviso {padding: 13px 16px; border-radius: 12px; font-size: 12.5px; line-height: 1.5; border: 1px solid; margin: 10px 0;}
.aviso-info {background: __acento_suave__; border-color: __borda__; color: __texto2__;}
.aviso-atencao {background: __aviso_bg__; border-color: __aviso_borda__; color: __aviso_texto__;}

/* Superfícies */
[data-testid="stVerticalBlockBorderWrapper"] {border-radius: 15px !important; border-color: __borda__ !important; background: __cartao__ !important; box-shadow: __sombra__;}
[data-testid="stExpander"] {border: 1px solid __borda__ !important; border-radius: 13px !important; background: __cartao__ !important;}
[data-testid="stExpander"] summary, [data-testid="stExpander"] summary p {color: __texto__ !important; font-weight: 650;}
[data-testid="stAlert"] {border-radius: 12px;}

/* Botões e controles */
.stApp .stButton button, .stApp .stDownloadButton button {
  min-height: 2.55rem; border-radius: 10px; border: 1px solid __input_borda__;
  background: __cartao__; color: __texto__; font-weight: 680; box-shadow: 0 2px 5px rgba(15,35,58,.035);
  transition: all .18s ease;
}
.stApp .stButton button:hover, .stApp .stDownloadButton button:hover {border-color: __acento__; color: __acento__; background: __hover__; transform: translateY(-1px);}
.stApp .stButton button:focus-visible, .stApp .stDownloadButton button:focus-visible {box-shadow: 0 0 0 3px __acento_suave__; outline: none;}
.stApp [data-baseweb="input"], .stApp [data-baseweb="base-input"],
.stApp [data-baseweb="select"] > div, .stApp [data-baseweb="textarea"] {
  background: __input_bg__; border-color: __input_borda__; border-radius: 10px; color: __texto__;
}
.stApp [data-baseweb="input"]:focus-within, .stApp [data-baseweb="select"]:focus-within > div,
.stApp [data-baseweb="textarea"]:focus-within {border-color: __acento__; box-shadow: 0 0 0 3px __acento_suave__;}
.stApp input, .stApp textarea {color: __texto__ !important;}
.stApp input::placeholder, .stApp textarea::placeholder {color: __hint__ !important;}
.stApp [data-baseweb="select"] div {color: __texto__;}
.stApp [data-baseweb="select"] svg {fill: __texto3__;}
.stApp [data-baseweb="select"] [data-baseweb="tag"] {background: __acento_suave__; border-radius: 7px;}
.stApp [data-baseweb="select"] [data-baseweb="tag"], .stApp [data-baseweb="select"] [data-baseweb="tag"] span {color: __acento__; font-weight: 650;}
[data-baseweb="popover"] > div {background: __cartao__; border: 1px solid __borda__; border-radius: 12px; box-shadow: __sombra__;}
[data-baseweb="menu"], [data-baseweb="calendar"] {background: __cartao__; color: __texto__;}
[data-baseweb="menu"] li {color: __texto2__;}
[data-baseweb="menu"] li:hover {background: __hover__;}
[data-baseweb="menu"] li[aria-selected="true"] {background: __acento_suave__; color: __acento__;}
[data-baseweb="calendar"] button, [data-baseweb="calendar"] div {color: __texto2__;}
.stApp [data-testid="stCheckbox"] label, .stApp [data-testid="stRadio"] label {color: __texto2__;}

/* Abas */
.stApp button[data-baseweb="tab"] {font-weight: 700; font-size: 12px; padding: 10px 16px; border-radius: 9px 9px 0 0;}
.stApp button[data-baseweb="tab"] p {color: __texto3__;}
.stApp button[data-baseweb="tab"][aria-selected="true"] p {color: __acento__;}
[data-baseweb="tab-highlight"] {background: __acento__; height: 3px; border-radius: 5px;}
[data-baseweb="tab-border"] {background: __borda__;}

/* Tabela interativa: moldura, controles e navegação */
/* Busca e selectboxes do detalhamento */
.stApp [class*="st-key-busca_tabela_"] input {min-height: 42px; border-radius: 10px !important;}
/* O tema do Streamlit/BaseWeb pode aplicar fundo inline nos selectboxes.
   Aplicamos a paleta no wrapper, no controle interno e em todos os descendentes. */
.stApp [class*="st-key-ordem_"],
.stApp [class*="st-key-tamanho_tabela_"] {color: __texto__ !important;}
.stApp [class*="st-key-ordem_"] [data-testid="stSelectbox"],
.stApp [class*="st-key-tamanho_tabela_"] [data-testid="stSelectbox"],
.stApp [class*="st-key-ordem_"] [data-baseweb="select"],
.stApp [class*="st-key-tamanho_tabela_"] [data-baseweb="select"] {
  background: transparent !important; background-color: transparent !important;
  color: __texto__ !important; border-radius: 10px !important;
}
.stApp [class*="st-key-ordem_"] [data-baseweb="select"] > div,
.stApp [class*="st-key-tamanho_tabela_"] [data-baseweb="select"] > div,
.stApp [class*="st-key-ordem_"] [data-baseweb="select"] [role="combobox"],
.stApp [class*="st-key-tamanho_tabela_"] [data-baseweb="select"] [role="combobox"] {
  background: __input_bg__ !important; background-color: __input_bg__ !important;
  border: 1px solid __input_borda__ !important; border-radius: 10px !important;
  color: __texto__ !important; box-shadow: none !important;
  opacity: 1 !important;
}
.stApp [class*="st-key-ordem_"] [data-baseweb="select"] *,
.stApp [class*="st-key-tamanho_tabela_"] [data-baseweb="select"] * {
  color: __texto__ !important; -webkit-text-fill-color: __texto__ !important;
}
.stApp [class*="st-key-ordem_"] [data-baseweb="select"] svg,
.stApp [class*="st-key-tamanho_tabela_"] [data-baseweb="select"] svg {
  fill: __texto3__ !important; color: __texto3__ !important;
}
.stApp [class*="st-key-ordem_"] [data-baseweb="select"]:focus-within > div,
.stApp [class*="st-key-tamanho_tabela_"] [data-baseweb="select"]:focus-within > div {
  border-color: __acento__ !important; box-shadow: 0 0 0 2px __acento_suave__ !important;
}
/* Acabamento final dos selects da tabela: replica o campo Busca rápida.
   O Select do BaseWeb possui camadas internas com fundo próprio; por isso
   o fundo é aplicado também aos elementos internos do controle fechado. */
.stApp [class*="st-key-ordem_"] [data-testid="stSelectbox"] [data-baseweb="select"] > div,
.stApp [class*="st-key-tamanho_tabela_"] [data-testid="stSelectbox"] [data-baseweb="select"] > div,
.stApp [class*="st-key-ordem_"] [data-testid="stSelectbox"] [role="combobox"],
.stApp [class*="st-key-tamanho_tabela_"] [data-testid="stSelectbox"] [role="combobox"] {
  min-height: 42px !important;
  height: 42px !important;
  box-sizing: border-box !important;
  background: __input_bg__ !important;
  background-color: __input_bg__ !important;
  border: 1px solid __input_borda__ !important;
  border-radius: 8px !important;
  color: __texto__ !important;
  box-shadow: none !important;
}
.stApp [class*="st-key-ordem_"] [data-testid="stSelectbox"] [data-baseweb="select"] > div > div,
.stApp [class*="st-key-tamanho_tabela_"] [data-testid="stSelectbox"] [data-baseweb="select"] > div > div {
  background: transparent !important;
  background-color: transparent !important;
  color: __texto__ !important;
}
.stApp [class*="st-key-ordem_"] [data-testid="stSelectbox"] [data-baseweb="select"] span,
.stApp [class*="st-key-tamanho_tabela_"] [data-testid="stSelectbox"] [data-baseweb="select"] span,
.stApp [class*="st-key-ordem_"] [data-testid="stSelectbox"] [data-baseweb="select"] div,
.stApp [class*="st-key-tamanho_tabela_"] [data-testid="stSelectbox"] [data-baseweb="select"] div {
  -webkit-text-fill-color: __texto__ !important;
}
.stApp [class*="st-key-ordem_"] [data-testid="stSelectbox"] [data-baseweb="select"] svg,
.stApp [class*="st-key-tamanho_tabela_"] [data-testid="stSelectbox"] [data-baseweb="select"] svg {
  fill: __texto3__ !important;
  color: __texto3__ !important;
}
.stApp [class*="st-key-ordem_"] [data-testid="stSelectbox"] [data-baseweb="select"]:focus-within > div,
.stApp [class*="st-key-tamanho_tabela_"] [data-testid="stSelectbox"] [data-baseweb="select"]:focus-within > div {
  border-color: __acento__ !important;
  box-shadow: 0 0 0 2px __acento_suave__ !important;
}

/* Menu de opções: BaseWeb o renderiza em um portal fora do contêiner do widget. */
[data-baseweb="popover"],
[data-baseweb="popover"] > div,
[data-baseweb="popover"] [data-baseweb="menu"],
[data-baseweb="popover"] [role="listbox"] {
  background: __cartao__ !important; background-color: __cartao__ !important;
  border-color: __borda__ !important; color: __texto__ !important;
}
[data-baseweb="popover"] [role="option"],
[data-baseweb="popover"] [role="option"] * {
  background: __cartao__ !important; color: __texto2__ !important;
  -webkit-text-fill-color: __texto2__ !important;
}
[data-baseweb="popover"] [role="option"]:hover,
[data-baseweb="popover"] [role="option"][aria-selected="true"] {
  background: __hover__ !important; color: __texto__ !important;
}
[data-baseweb="popover"] [role="option"]:hover *,
[data-baseweb="popover"] [role="option"][aria-selected="true"] * {
  color: __texto__ !important; -webkit-text-fill-color: __texto__ !important;
}
/* Tabela analítica própria: aparência uniforme nos temas claro e escuro */
.data-table-card {background: __cartao__; border: 1px solid __borda__; border-radius: 15px; overflow: hidden; box-shadow: __sombra__; margin: 3px 0 12px;}
.data-table-scroll {width: 100%; max-height: 590px; overflow: auto; overscroll-behavior: contain; scrollbar-width: thin; scrollbar-color: __borda__ transparent;}
.data-table {width: 100%; min-width: 1080px; border-collapse: separate; border-spacing: 0; table-layout: auto; color: __texto2__; font-size: 12px;}
.data-table thead th {position: sticky; top: 0; z-index: 3; padding: 13px 14px; text-align: left; white-space: nowrap; background: __cartao2__; color: __texto3__; border-bottom: 1px solid __borda__; font-size: 9px; line-height: 1.35; font-weight: 800; letter-spacing: .09em; text-transform: uppercase;}
.data-table tbody td {height: 49px; padding: 10px 14px; border-bottom: 1px solid __borda__; color: __texto2__; background: __cartao__; vertical-align: middle; white-space: nowrap; max-width: 245px; overflow: hidden; text-overflow: ellipsis;}
.data-table tbody tr:nth-child(even) td {background: __cartao2__;}
.data-table tbody tr:hover td {background: __hover__; color: __texto__;}
.data-table tbody tr:last-child td {border-bottom: 0;}
.data-table .cell-primary {color: __texto__; font-weight: 750;}
.data-table .cell-muted {color: __texto3__;}
.data-table .cell-center {text-align: center;}
.data-table .status-pill {display: inline-flex; align-items: center; gap: 7px; max-width: 100%; padding: 5px 9px; border: 1px solid; border-radius: 999px; font-size: 10px; font-weight: 750; line-height: 1.2; white-space: nowrap;}
.data-table .status-dot {width: 6px; height: 6px; border-radius: 50%; flex: 0 0 6px;}
.data-table .days-cell {display: flex; flex-direction: column; gap: 5px; min-width: 76px;}
.data-table .days-value {font-variant-numeric: tabular-nums; color: __texto__; font-weight: 750;}
.data-table .days-track {display: block; height: 4px; border-radius: 99px; background: __borda__; overflow: hidden;}
.data-table .days-track i {display: block; height: 100%; border-radius: inherit;}
.data-table-empty {padding: 30px 18px; text-align: center; color: __texto3__; font-size: 12px;}
.data-table-footnote {display: flex; justify-content: space-between; gap: 12px; flex-wrap: wrap; padding: 10px 14px; border-top: 1px solid __borda__; background: __cartao2__; color: __texto3__; font-size: 10px;}
@media (max-width: 850px) { .data-table {min-width: 920px;} .data-table thead th, .data-table tbody td {padding-left: 10px; padding-right: 10px;} }

/* Cards KPI clicáveis — conteúdo visual separado do botão transparente de interação */
.stApp [class*="st-key-kpi_panel_"] {
  position: relative !important; min-height: 128px !important; height: 128px !important;
  overflow: visible !important; padding: 0 !important;
}
.stApp [class*="st-key-kpi_panel_"] .kpi {
  min-height: 128px; height: 128px; box-sizing: border-box;
  display: flex; flex-direction: column; justify-content: space-between;
  gap: 9px; padding: 16px 17px 14px 19px;
}
.stApp [class*="st-key-kpi_panel_"] .kpi-topline {
  display: flex; align-items: flex-start; justify-content: space-between;
  gap: 9px; min-width: 0;
}
.stApp [class*="st-key-kpi_panel_"] .kpi-titulo {
  flex: 1 1 auto; min-width: 0; max-width: calc(100% - 38px);
  font-size: 10px; line-height: 1.35; font-weight: 800;
  text-transform: uppercase; letter-spacing: .075em;
  color: __texto3__; white-space: normal; overflow-wrap: anywhere;
}
.stApp [class*="st-key-kpi_panel_"] .kpi-icone {
  flex: 0 0 29px; width: 29px; height: 29px; border-radius: 9px;
  display: grid; place-items: center; font-size: 14px; font-weight: 800;
  background: color-mix(in srgb, var(--cor) 12%, __cartao__); color: var(--cor);
}
.stApp [class*="st-key-kpi_panel_"] .kpi-bottom {min-width: 0; display: flex; flex-direction: column; gap: 4px;}
.stApp [class*="st-key-kpi_panel_"] .kpi-valor {
  font-size: clamp(1.65rem, 2.05vw, 2.1rem); line-height: 1.06;
  font-weight: 800; letter-spacing: -.045em; color: __texto__;
  font-variant-numeric: tabular-nums; white-space: nowrap;
}
.stApp [class*="st-key-kpi_panel_"] .kpi-detalhe {
  display: block; max-width: 100%; min-width: 0; margin: 0;
  color: __texto3__; font-size: 10px; line-height: 1.35;
  white-space: normal; overflow-wrap: anywhere; word-break: normal;
  display: -webkit-box; -webkit-box-orient: vertical; -webkit-line-clamp: 2;
  overflow: hidden; text-overflow: ellipsis;
}
.stApp [class*="st-key-kpi_panel_"] .kpi-click-hint {
  position: absolute; right: 12px; bottom: 11px; font-size: 8px;
  letter-spacing: .07em; text-transform: uppercase; font-weight: 800;
  color: var(--cor); opacity: .8; pointer-events: none;
}
.stApp [class*="st-key-kpi_panel_"] .kpi.is-selected {
  border-color: var(--cor); background: linear-gradient(145deg, __cartao__, color-mix(in srgb, var(--cor) 9%, __cartao2__));
  box-shadow: 0 0 0 2px color-mix(in srgb, var(--cor) 65%, transparent), 0 12px 28px rgba(10,35,62,.18);
}
/* O botão real ocupa o card todo, mas fica visualmente invisível; o card HTML é a camada visual. */
.stApp [class*="st-key-kpi_panel_"] [data-testid="stElementContainer"]:has(.stButton) {
  position: absolute !important; inset: 0 !important; z-index: 8 !important;
  width: 100% !important; height: 100% !important; margin: 0 !important;
  padding: 0 !important;
}
.stApp [class*="st-key-kpi_panel_"] .stButton,
.stApp [class*="st-key-kpi_panel_"] .stButton > div {width: 100% !important; height: 100% !important;}
.stApp [class*="st-key-kpi_panel_"] .stButton button {
  position: absolute !important; inset: 0 !important; width: 100% !important; height: 100% !important;
  min-height: 128px !important; padding: 0 !important; margin: 0 !important;
  border: 1px solid transparent !important; border-radius: 16px !important;
  background: transparent !important; box-shadow: none !important;
  color: transparent !important; opacity: 1 !important; cursor: pointer !important;
}
.stApp [class*="st-key-kpi_panel_"] .stButton button p,
.stApp [class*="st-key-kpi_panel_"] .stButton button span {
  color: transparent !important; font-size: 0 !important; line-height: 0 !important;
}
.stApp [class*="st-key-kpi_panel_"]:has(.stButton button:hover) .kpi {
  transform: translateY(-3px); border-color: var(--cor); box-shadow: 0 12px 28px rgba(10,35,62,.16);
}
.stApp [class*="st-key-kpi_panel_"]:has(.stButton button:focus-visible) .kpi {
  outline: 3px solid __acento_suave__; outline-offset: 3px;
}
.stApp [class*="st-key-kpi_panel_"]:has(.stButton button[kind="primary"]) .kpi {
  border-color: var(--cor); box-shadow: 0 0 0 2px var(--cor), 0 12px 28px rgba(10,35,62,.16);
}
/* Popovers, calendário e menus acompanham o tema escolhido */
[data-baseweb="popover"] *, [data-baseweb="menu"] *, [data-baseweb="calendar"] * {color: __texto__ !important;}
[data-baseweb="popover"] [role="option"]:hover, [data-baseweb="menu"] li:hover {background: __hover__ !important;}
.stApp [data-testid="stDateInput"] input, .stApp [data-testid="stTextInput"] input,
.stApp [data-testid="stNumberInput"] input, .stApp [data-testid="stTextArea"] textarea {background: __input_bg__ !important; color: __texto__ !important;}

/* Ajustes responsivos */
@media (max-width: 850px) {
  .block-container {padding-top: 1.25rem;}
  .prontidao-hero {padding: 22px; border-radius: 15px;}
  .hero-side {align-items: flex-start;}
  .hero-logo {min-width: 95px; padding: 8px 12px;}
  .hero-logo img {height: 36px;}
  .stApp [class*="st-key-kpi_panel_"] {height: 122px !important; min-height: 122px !important;}
  .stApp [class*="st-key-kpi_panel_"] .kpi, .stApp [class*="st-key-kpi_panel_"] .stButton button {height: 122px !important; min-height: 122px !important;}
}
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {scroll-behavior: auto !important; transition-duration: .01ms !important; animation-duration: .01ms !important;}
}
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
def _normalizar_texto(valor):
    texto = unicodedata.normalize("NFKD", str(valor)).encode("ascii", "ignore").decode("ascii")
    return re.sub(r"\s+", " ", texto).strip().casefold()


def _selecao_cartao(titulo, farol=None):
    """Converte títulos de indicadores conhecidos em filtros globais da etapa."""
    if farol:
        valores = [farol] if isinstance(farol, str) else list(farol)
        return {"tipo": "farol", "valores": valores}
    texto = _normalizar_texto(titulo)
    if "dentro do prazo" in texto:
        return {"tipo": "farol", "valores": ["DENTRO DO PRAZO"]}
    if "atencao" in texto and "alerta" in texto:
        return {"tipo": "farol", "valores": ["ATENÇÃO", "ALERTA"]}
    if "atencao" in texto:
        return {"tipo": "farol", "valores": ["ATENÇÃO"]}
    if "alerta" in texto:
        return {"tipo": "farol", "valores": ["ALERTA"]}
    if "atras" in texto or "vencid" in texto:
        return {"tipo": "farol", "valores": ["ATRASO"]}
    if "sem data" in texto:
        return {"tipo": "farol", "valores": ["SEM DATA"]}
    if "revisar regra" in texto:
        return {"tipo": "farol", "valores": ["REVISAR REGRA"]}
    if "em andamento" in texto:
        return {"tipo": "situacao", "valores": ["Em andamento"]}
    if "concluid" in texto or "finalizad" in texto:
        return {"tipo": "situacao", "valores": ["Concluída"]}
    if "total de processo" in texto or texto == "processos" or texto == "total":
        return {"tipo": "todos", "valores": []}
    return None


def _chave_pagina_atual():
    return str(st.session_state.get("_pagina_filtros_ativa", "global"))


def cartao(titulo, valor, detalhe, cor, farol=None, chave=None):
    """Card de KPI com hierarquia visual fixa; quando mapeado, filtra a página toda ao clicar."""
    titulo_txt = str(titulo)
    selecao = _selecao_cartao(titulo_txt, farol=farol)
    page_key = str(chave or _chave_pagina_atual())
    state_key = f"_farol_card_filtro_{page_key}"
    atual = st.session_state.get(state_key)
    selecionado = bool(selecao is not None and atual == selecao)

    titulo_norm = _normalizar_texto(titulo_txt)
    if any(p in titulo_norm for p in ("total", "processos", "embarques")):
        icone = "▦"
    elif any(p in titulo_norm for p in ("prazo", "regular", "conclu")):
        icone = "✓"
    elif any(p in titulo_norm for p in ("atencao", "alerta", "pend")):
        icone = "!"
    elif any(p in titulo_norm for p in ("atras", "venc")):
        icone = "↗"
    elif any(p in titulo_norm for p in ("valor", "custo", "numerario", "finance")):
        icone = "$"
    else:
        icone = "◈"

    cor_css = escape(str(cor), quote=True)
    card_classes = "kpi" + (" is-selected" if selecionado else "")
    detalhe_txt = escape(str(detalhe))
    conteudo = f"""<div class="{card_classes}" style="--cor:{cor_css}">
      <div class="kpi-topline">
        <div class="kpi-titulo">{escape(titulo_txt)}</div>
        <div class="kpi-icone">{icone}</div>
      </div>
      <div class="kpi-bottom">
        <div class="kpi-valor">{escape(str(valor))}</div>
        <div class="kpi-detalhe">{detalhe_txt}</div>
      </div>
      {('<div class="kpi-click-hint">FILTRO ATIVO</div>' if selecionado else '')}
    </div>"""

    if selecao is None:
        st.markdown(conteudo, unsafe_allow_html=True)
        return

    slug = re.sub(r"[^a-z0-9]+", "_", _normalizar_texto(titulo_txt)).strip("_")[:28] or "indicador"
    page_slug = re.sub(r"[^a-zA-Z0-9_]+", "_", page_key)[:24] or "pagina"
    panel_key = f"kpi_panel_{page_slug}_{slug}"
    widget_key = f"kpi_card_{page_slug}_{slug}"

    # Container com chave permite posicionar um botão transparente sobre o cartão HTML.
    # Assim, conteúdo, valor e descrição não dependem do layout limitado do rótulo de st.button.
    with st.container(key=panel_key):
        st.markdown(conteudo, unsafe_allow_html=True)
        clicou = st.button(
            f"Filtrar por {titulo_txt}: {valor}", key=widget_key,
            help=(f"Filtro ativo: {titulo_txt}. Clique para remover." if selecionado
                  else f"Filtrar a página inteira por {titulo_txt}. Clique novamente para remover."),
            use_container_width=True,
            type="primary" if selecionado else "secondary",
        )

    if clicou:
        if selecionado or selecao.get("tipo") == "todos":
            st.session_state.pop(state_key, None)
        else:
            st.session_state[state_key] = selecao
        st.rerun()



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
    tipo_css = "atencao" if str(tipo).casefold() in ("atencao", "atenção", "warning") else "info"
    st.markdown(
        f'<div class="aviso aviso-{tipo_css}">{escape(str(texto))}</div>',
        unsafe_allow_html=True,
    )



def faixa_farol(contagem, total):
    if not total or total <= 0:
        return
    segmentos = ""
    for farol in ORDEM_FAROL:
        n = int(contagem.get(farol, 0))
        if n > 0:
            pct = n / total * 100
            segmentos += (
                f'<div title="{escape(nome_farol(farol))}: {n} ({pct:.1f}%)" '
                f'style="width:{pct:.2f}%;background:{CORES_FAROL[farol]}"></div>'
            )
    st.markdown(f'<div class="faixa">{segmentos}</div>', unsafe_allow_html=True)



MESES_PT = ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"]


def nome_farol(farol):
    """Nome de exibição do farol: só a primeira letra maiúscula, em vez de caixa alta."""
    return farol.capitalize()


def base_layout(fig, altura, legenda_y=-0.18):
    """Aplica o mesmo acabamento e comportamento aos gráficos Plotly."""
    t = tema_ativo()
    fig.update_layout(
        template=t["template"], height=altura,
        margin=dict(l=12, r=12, t=18, b=18),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, Segoe UI, sans-serif", color=t["texto2"], size=12),
        hoverlabel=dict(
            bgcolor=t["cartao"], bordercolor=t["borda"], align="left",
            font=dict(size=12, color=t["texto"]),
        ),
        legend=dict(
            orientation="h", y=legenda_y, x=0, itemsizing="constant",
            font=dict(size=10, color=t["texto2"]), title_text="",
            bgcolor="rgba(0,0,0,0)",
        ),
        modebar=dict(bgcolor="rgba(0,0,0,0)", color=t["hint"], activecolor=t["acento"]),
        hovermode="closest",
        uniformtext_minsize=9,
        uniformtext_mode="hide",
    )
    return fig



def estilizar_eixos(fig):
    """Eixos limpos, grade discreta e tipografia consistente com o tema ativo."""
    t = tema_ativo()
    comum = dict(
        showline=False, zeroline=False, ticks="", showspikes=True,
        spikemode="across", spikesnap="cursor", spikethickness=1,
        spikecolor=t["borda"], gridcolor=t["grade"], griddash="dot",
        tickfont=dict(size=10, color=t["texto3"]),
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
    no_prazo = int(resumo.get("DENTRO DO PRAZO", 0))
    pct_prazo = no_prazo / total * 100 if total else 0
    t = tema_ativo()
    nomes = [nome_farol(f) for f in resumo.index]
    fig = go.Figure(go.Pie(
        labels=nomes, values=list(resumo.values), hole=0.74, sort=False,
        direction="clockwise", rotation=270,
        marker=dict(colors=[CORES_FAROL[f] for f in resumo.index],
                    line=dict(color=t["cartao"], width=4)),
        textinfo="percent", textposition="inside",
        textfont=dict(size=10, color="#FFFFFF"),
        hovertemplate=("<b>%{label}</b><br>Processos: %{value:,}<br>Participação: %{percent}"
                       + ("<br><i>Regra: %{customdata}</i>" if regras else "")
                       + "<extra></extra>"),
        customdata=[(regras or {}).get(f, "") for f in resumo.index] if regras else None,
    ))
    fig.add_annotation(
        text=(f"<span style='font-size:29px;color:{t['texto']};font-weight:750'>{total:,}</span>"
              f"<br><span style='font-size:11px;color:{t['texto3']}'>processos</span>"
              f"<br><span style='font-size:12px;color:{CORES_FAROL['DENTRO DO PRAZO']};font-weight:700'>{pct_prazo:.0f}% no prazo</span>"),
        x=0.5, y=0.5, showarrow=False, align="center",
    )
    base_layout(fig, 330, legenda_y=-0.12)
    fig.update_layout(showlegend=True, legend=dict(orientation="h", y=-0.06, x=0.5, xanchor="center"),
                      margin=dict(l=10, r=10, t=8, b=40))
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
        base, x="Dias", color="Farol", nbins=26, color_discrete_map=cores,
        category_orders={"Farol": [nome_farol(f) for f in ORDEM_FAROL]},
        labels={"Dias": "Dias decorridos", "count": "Processos"},
        opacity=.94,
    )
    fig.update_traces(
        marker_line_color=t["cartao"], marker_line_width=1.2,
        hovertemplate="<b>%{fullData.name}</b><br>Faixa: %{x} dias<br>Processos: %{y}<extra></extra>",
    )
    topo = max(float(base["Dias"].max()), 3.5) * 1.08
    faixas = ((0, 1, "DENTRO DO PRAZO"), (1, 3, "ATENÇÃO"), (3, topo, "ATRASO")) if usar_faixas else ()
    for x0, x1, farol in faixas:
        fig.add_vrect(x0=x0, x1=x1, fillcolor=CORES_FAROL[farol], opacity=.075,
                      line_width=0, layer="below")
    for marco, rotulo in marcos:
        fig.add_vline(x=marco, line_dash="dot", line_color=t["texto3"], line_width=1,
                      annotation_text=rotulo, annotation_position="top left",
                      annotation_font=dict(size=9, color=t["texto3"]))
    media = float(base["Dias"].mean())
    fig.add_vline(x=media, line_dash="dash", line_color=t["destaque"], line_width=2,
                  annotation_text=f"Média {media:.1f} d", annotation_position="top right",
                  annotation_font=dict(size=10, color=t["destaque"]))
    base_layout(fig, 340, legenda_y=-.22)
    estilizar_eixos(fig)
    fig.update_layout(barmode="stack", bargap=.09, hovermode="x unified",
                      xaxis_title="Duração (dias)", yaxis_title="Quantidade de processos")
    st.plotly_chart(fig, use_container_width=True, key=f"duracao_{chave}",
                    config=PLOTLY_CONFIG, theme=None)



def grafico_evolucao(dados, coluna_inicio, chave):
    base = dados.loc[dados[coluna_inicio].notna(), [coluna_inicio, "Farol da etapa"]].copy()
    if base.empty:
        aviso("Sem datas de início para montar a evolução.")
        return

    base["Mês"] = pd.to_datetime(base[coluna_inicio], errors="coerce").dt.to_period("M").dt.to_timestamp()
    base = base.dropna(subset=["Mês"])
    if base.empty:
        aviso("Não há datas válidas para montar a evolução.")
        return
    tabela = base.groupby(["Mês", "Farol da etapa"]).size().unstack(fill_value=0)
    tabela = tabela.reindex(columns=[f for f in ORDEM_FAROL if f in tabela.columns])
    total = tabela.sum(axis=1)
    pct_prazo = (tabela["DENTRO DO PRAZO"] / total * 100
                 if "DENTRO DO PRAZO" in tabela.columns else pd.Series(0.0, index=tabela.index))

    t = tema_ativo()
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    for farol in tabela.columns:
        fig.add_trace(go.Bar(
            x=tabela.index, y=tabela[farol], name=nome_farol(farol),
            marker=dict(color=CORES_FAROL[farol], line=dict(color=t["cartao"], width=1)),
            hovertemplate=f"<b>{nome_farol(farol)}</b>: %{{y}}<extra></extra>",
        ), secondary_y=False)
    fig.add_trace(go.Scatter(
        x=tabela.index, y=total, mode="text", text=[str(int(v)) for v in total],
        textposition="top center", textfont=dict(size=10, color=t["texto3"]),
        showlegend=False, hoverinfo="skip",
    ), secondary_y=False)
    fig.add_trace(go.Scatter(
        x=tabela.index, y=pct_prazo, name="% dentro do prazo", mode="lines+markers",
        line=dict(color=t["destaque"], width=2.8, shape="spline"),
        marker=dict(size=7, color=t["cartao"], line=dict(color=t["destaque"], width=2)),
        hovertemplate="% dentro do prazo: %{y:.1f}%<extra></extra>",
    ), secondary_y=True)

    base_layout(fig, 390, legenda_y=-.28)
    estilizar_eixos(fig)
    fig.update_layout(barmode="stack", bargap=.32, hovermode="x unified",
                      margin=dict(l=10, r=10, t=48, b=12))
    fig.update_yaxes(title_text="Processos", range=[0, max(float(total.max()) * 1.18, 1)], secondary_y=False)
    fig.update_yaxes(title_text="% dentro do prazo", range=[0, 105], ticksuffix="%",
                     showgrid=False, secondary_y=True)

    eixo_x = dict(
        hoverformat="%m/%Y", rangeslider=dict(visible=False),
        rangeselector=dict(buttons=[
            dict(count=3, label="3 meses", step="month", stepmode="backward"),
            dict(count=6, label="6 meses", step="month", stepmode="backward"),
            dict(count=1, label="1 ano", step="year", stepmode="backward"),
            dict(step="all", label="Tudo"),
        ], x=0, xanchor="left", y=1.03, yanchor="bottom",
           bgcolor=t["cartao2"], activecolor=t["acento_suave"],
           bordercolor=t["borda"], borderwidth=1,
           font=dict(size=10, color=t["texto2"])),
    )
    if len(tabela) <= 18:
        eixo_x.update(tickmode="array", tickvals=list(tabela.index),
                      ticktext=[f"{MESES_PT[d.month - 1]}/{str(d.year)[2:]}" for d in tabela.index])
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


def _cor_farol(valor):
    chave = str(valor).strip().upper()
    return CORES_FAROL.get(chave, "#8795A5")


def _valor_exibicao(valor):
    if valor is None or (not isinstance(valor, (list, tuple, dict)) and pd.isna(valor)):
        return "—"
    if hasattr(valor, "strftime"):
        return valor.strftime("%d/%m/%Y")
    if isinstance(valor, float) and valor.is_integer():
        return f"{int(valor):,}".replace(",", ".")
    return str(valor)


def tabela_html(dados, colunas, inicio, fim, dias_max):
    """Gera uma grade HTML responsiva, com cabeçalho fixo e cores do tema ativo."""
    if dados is None or dados.empty:
        return '<div class="data-table-card"><div class="data-table-empty">Nenhum registro para exibir.</div></div>'

    cabecalho = "".join(f'<th scope="col">{escape(str(c))}</th>' for c in colunas)
    linhas = []
    for _, r in dados.iterrows():
        farol = str(r.get("Farol da etapa", "")).strip().upper()
        cor_farol = _cor_farol(farol)
        celulas = []
        for c in colunas:
            valor = r.get(c)
            exibicao = _valor_exibicao(valor)
            seguro = escape(exibicao)
            title = f' title="{escape(exibicao, quote=True)}"' if exibicao != "—" else ""

            if c == "Farol da etapa":
                label = escape(exibicao.capitalize())
                celulas.append(
                    f'<td{title}><span class="status-pill" style="color:{cor_farol};'
                    f'background:{cor_farol}14;border-color:{cor_farol}48">'
                    f'<i class="status-dot" style="background:{cor_farol}"></i>{label}</span></td>'
                )
            elif c == "Situação da etapa":
                norm = _normalizar_texto(exibicao)
                cor = CORES_FAROL["DENTRO DO PRAZO"] if "conclu" in norm else CORES_FAROL["ATENÇÃO"]
                celulas.append(
                    f'<td{title}><span class="status-pill" style="color:{cor};'
                    f'background:{cor}14;border-color:{cor}48">'
                    f'<i class="status-dot" style="background:{cor}"></i>{seguro}</span></td>'
                )
            elif c == "Dias":
                if exibicao == "—":
                    celulas.append('<td class="cell-muted">—</td>')
                else:
                    try:
                        numero = float(valor)
                        pct = max(0.0, min(100.0, numero / max(float(dias_max or 1), 1.0) * 100))
                        dias_txt = f"{numero:.1f} d"
                    except (TypeError, ValueError):
                        pct, dias_txt = 0.0, seguro
                    celulas.append(
                        f'<td{title}><div class="days-cell"><span class="days-value">{escape(dias_txt)}</span>'
                        f'<span class="days-track"><i style="width:{pct:.0f}%;background:{cor_farol}"></i></span>'
                        f'</div></td>'
                    )
            elif c in (inicio, fim):
                celulas.append(f'<td class="cell-muted"{title}>{seguro}</td>')
            elif c in ("Nº Processo", "Ref.Cliente", "Status"):
                celulas.append(f'<td class="cell-primary"{title}>{seguro}</td>')
            else:
                celulas.append(f'<td{title}>{seguro}</td>')
        linhas.append("<tr>" + "".join(celulas) + "</tr>")

    return (
        '<div class="data-table-card"><div class="data-table-scroll">'
        '<table class="data-table"><thead><tr>' + cabecalho + '</tr></thead><tbody>'
        + "".join(linhas) + '</tbody></table></div>'
        f'<div class="data-table-footnote"><span>Exibindo {len(dados):,} registro(s) nesta página</span>'
        '<span>Role horizontalmente para visualizar todas as colunas</span></div></div>'
    )


def tabela_detalhada(dados, inicio, fim, chave, nome_arquivo):
    """Tabela analítica customizada com busca, ordenação, paginação e exportação."""
    st.markdown('<div class="secao">Detalhamento dos processos</div>', unsafe_allow_html=True)
    if dados is None or dados.empty:
        aviso("Nenhum processo encontrado com os filtros selecionados.")
        return

    preferidas = [
        "Status", "Ref.Cliente", "Nº Processo", "Responsável", "Planta",
        "Categoria", "Exportador", "Modal", inicio, fim, "Dias",
        "Farol da etapa", "Situação da etapa",
    ]
    colunas = [c for c in preferidas if c in dados.columns]
    if not colunas:
        colunas = list(dados.columns)

    # Busca global sobre os campos disponíveis no detalhamento.
    c_busca, c_ordem, c_tamanho = st.columns([2.2, 1.45, 1.05])
    with c_busca:
        busca = st.text_input("Busca rápida", key=f"busca_tabela_{chave}",
                              placeholder="Digite referência, processo, responsável...")
    ordens = {
        "Maior tempo decorrido": ("Dias", False),
        "Menor tempo decorrido": ("Dias", True),
        "Início mais recente": (inicio, False),
        "Início mais antigo": (inicio, True),
    }
    opcoes_ordem = [nome for nome, (col, _) in ordens.items() if col in dados.columns]
    with c_ordem:
        escolha = st.selectbox("Ordenar por", opcoes_ordem or ["Ordem original"],
                               key=f"ordem_{chave}")
    with c_tamanho:
        tamanho = st.selectbox("Linhas por página", [25, 50, 100, 250], index=1,
                               key=f"tamanho_tabela_{chave}")

    filtrado = dados.copy()
    if busca.strip():
        termo = busca.strip()
        mascara = filtrado[colunas].astype(str).apply(
            lambda serie: serie.str.contains(termo, case=False, na=False, regex=False)
        ).any(axis=1)
        filtrado = filtrado.loc[mascara]
    if escolha in ordens:
        coluna_ordem, crescente = ordens[escolha]
        try:
            filtrado = filtrado.sort_values(coluna_ordem, ascending=crescente, na_position="last", kind="stable")
        except (TypeError, ValueError):
            filtrado = filtrado.sort_values(coluna_ordem, ascending=crescente, na_position="last", key=lambda s: s.astype(str))

    # O usuário escolhe quais campos quer manter visíveis.
    chave_colunas = f"colunas_tabela_{chave}"
    if chave_colunas in st.session_state:
        st.session_state[chave_colunas] = [c for c in st.session_state[chave_colunas] if c in colunas]
    with st.expander("Personalizar colunas", expanded=False):
        visiveis = st.multiselect("Campos exibidos", colunas, default=colunas,
                                  key=chave_colunas, help="A tabela mantém a ordenação e a busca nos campos selecionados.")
    if not visiveis:
        visiveis = colunas

    total = len(filtrado)
    paginas = max(1, (total + tamanho - 1) // tamanho)
    chave_pagina = f"pagina_tabela_{chave}"
    if chave_pagina not in st.session_state:
        st.session_state[chave_pagina] = 1
    # Mantém a página válida quando busca, filtros ou tamanho da página mudam.
    pagina_atual = max(1, min(int(st.session_state[chave_pagina]), paginas))
    st.session_state[chave_pagina] = pagina_atual
    st.caption(f"**{total:,}** processo(s) encontrado(s) · {len(dados):,} após os filtros da página")

    inicio_linha = (pagina_atual - 1) * tamanho
    # A grade é HTML próprio para manter o mesmo acabamento da prévia em qualquer versão do Streamlit.
    pagina_df = filtrado.iloc[inicio_linha:inicio_linha + tamanho][visiveis].copy()
    if "Dias" in pagina_df.columns:
        serie_dias = pd.to_numeric(pagina_df["Dias"], errors="coerce")
        dias_max = float(serie_dias.max()) if serie_dias.notna().any() else 1.0
    else:
        dias_max = 1.0
    st.markdown(tabela_html(pagina_df, visiveis, inicio, fim, dias_max), unsafe_allow_html=True)

    # Paginação compacta abaixo da tabela: somente voltar, posição atual e avançar.
    st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)
    espaco_esq, voltar_col, indicador_col, avancar_col, espaco_dir = st.columns([1, 0.55, 0.8, 0.55, 1])
    with voltar_col:
        if st.button("‹", key=f"pagina_anterior_{chave}", disabled=pagina_atual <= 1,
                     use_container_width=True, help="Página anterior"):
            st.session_state[chave_pagina] = pagina_atual - 1
            st.rerun()
    with indicador_col:
        st.markdown(
            f"<div style='height:40px;display:flex;align-items:center;justify-content:center;font-size:12px;font-weight:750;color:inherit;font-variant-numeric:tabular-nums;'>{pagina_atual} / {paginas}</div>",
            unsafe_allow_html=True,
        )
    with avancar_col:
        if st.button("›", key=f"proxima_pagina_{chave}", disabled=pagina_atual >= paginas,
                     use_container_width=True, help="Próxima página"):
            st.session_state[chave_pagina] = pagina_atual + 1
            st.rerun()

    csv = filtrado.drop(columns=["_data_calculo"], errors="ignore").to_csv(
        index=False, sep=";", encoding="utf-8-sig"
    ).encode("utf-8-sig")
    c_download, c_rodape = st.columns([1.35, 3])
    with c_download:
        st.download_button(
            "↓ Exportar resultado (CSV)", csv, file_name=nome_arquivo,
            mime="text/csv", key=f"download_{chave}", use_container_width=True,
        )
    with c_rodape:
        st.caption("Dica: use a lupa no cabeçalho da tabela para localizar valores, arraste as colunas para reorganizar e clique nos títulos para ordenar.")



# ─────────────────────────────────────────────────────────────
# Blocos de página reutilizáveis: cabeçalho e barra de filtros
# ─────────────────────────────────────────────────────────────
def _tematizar_figura_plotly(fig):
    """Reaplica a paleta da sessão a qualquer figura Plotly, inclusive criada nas páginas."""
    t = tema_ativo()
    fig.update_layout(
        template=t["template"], paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, Segoe UI, sans-serif", color=t["texto2"], size=12),
        hoverlabel=dict(bgcolor=t["cartao"], bordercolor=t["borda"], font=dict(color=t["texto"])),
        legend=dict(font=dict(color=t["texto2"]), bgcolor="rgba(0,0,0,0)"),
        modebar=dict(bgcolor="rgba(0,0,0,0)", color=t["hint"], activecolor=t["acento"]),
    )
    fig.update_xaxes(color=t["texto3"], gridcolor=t["grade"], linecolor=t["borda"], zerolinecolor=t["borda"])
    fig.update_yaxes(color=t["texto3"], gridcolor=t["grade"], linecolor=t["borda"], zerolinecolor=t["borda"])
    return fig


def _instalar_tema_plotly_global():
    """Intercepta st.plotly_chart para garantir a paleta ativa em gráficos de qualquer página."""
    if getattr(st, "_savoy_plotly_theme_installed", False):
        return
    original = st.plotly_chart

    def _plotly_chart_com_tema(figure_or_data, *args, **kwargs):
        if isinstance(figure_or_data, go.Figure):
            _tematizar_figura_plotly(figure_or_data)
            kwargs["theme"] = None
        return original(figure_or_data, *args, **kwargs)

    st.plotly_chart = _plotly_chart_com_tema
    st._savoy_plotly_theme_installed = True


def aplicar_tema():
    """Aplica o tema global, alternador, tematização automática de Plotly e controles."""
    _instalar_tema_plotly_global()
    escuro = bool(st.session_state.get("tema_escuro", False))
    st.sidebar.button(
        "☀️  Alternar para tema claro" if escuro else "☾  Alternar para tema escuro",
        key="botao_tema_global", on_click=alternar_tema,
        use_container_width=True,
    )
    st.sidebar.markdown(gerar_css(tema_ativo()), unsafe_allow_html=True)
    st.session_state["_tema_global"] = True



def cabecalho(titulo, subtitulo, chave="topo"):
    """Cabeçalho institucional comum a todas as páginas do dashboard."""
    _instalar_tema_plotly_global()
    if not st.session_state.get("_tema_global"):
        escuro = bool(st.session_state.get("tema_escuro", False))
        _, col_tema = st.columns([5, 1])
        with col_tema:
            st.button(
                "☀️ Tema claro" if escuro else "☾ Tema escuro",
                key=f"botao_tema_{chave}", on_click=alternar_tema,
                use_container_width=True,
            )
        st.markdown(gerar_css(tema_ativo()), unsafe_allow_html=True)

    agora = datetime.now().strftime("%d/%m/%Y · %H:%M")
    st.markdown(
        html_limpo(f"""
        <div class="prontidao-hero">
          <div class="hero-marca">
            {logo_html()}
            <div>
              <div class="hero-eyebrow">Pibernat · Gestão de Importação</div>
              <h1>{escape(str(titulo))}</h1>
              <p>{escape(str(subtitulo))}</p>
            </div>
          </div>
          <div class="hero-side">
            <div class="hero-chip"><span class="hero-dot"></span> PAINEL OPERACIONAL</div>
            <div class="hero-updated">ATUALIZADO EM {agora}</div>
          </div>
        </div>"""),
        unsafe_allow_html=True,
    )



def barra_filtros(dados, coluna_inicio, chave):
    """Filtros padrão + filtros avançados; devolve o DataFrame filtrado sem alterar a origem."""
    if dados is None or dados.empty:
        aviso("Não há dados disponíveis para aplicar filtros.")
        return dados.copy() if dados is not None else pd.DataFrame()

    st.session_state["_pagina_filtros_ativa"] = str(chave)
    state_farol_card = f"_farol_card_filtro_{chave}"
    selecao_card = st.session_state.get(state_farol_card)
    validas = dados[coluna_inicio].dropna() if coluna_inicio in dados.columns else pd.Series(dtype="datetime64[ns]")
    dmin = dmax = None
    chaves_widget = [
        f"ref_{chave}", f"proc_{chave}", f"farol_filtro_{chave}",
        f"situacao_{chave}", f"periodo_{chave}",
    ]
    colunas_avancadas = [c for c in ("Responsável", "Planta", "Modal", "Categoria", "Exportador", "Status") if c in dados.columns]
    chaves_widget.extend(f"avancado_{chave}_{c.lower().replace(' ', '_')}" for c in colunas_avancadas)

    def _limpar_filtros():
        for k in chaves_widget:
            st.session_state.pop(k, None)
        st.session_state.pop(state_farol_card, None)

    if selecao_card:
        rotulo_card = ", ".join(selecao_card.get("valores", [])) or "Todos os processos"
        cor_ativa = CORES_FAROL.get(selecao_card.get("valores", [""])[0], "#2468B4") if selecao_card.get("tipo") == "farol" else "#2468B4"
        try:
            r, g, b = tuple(int(cor_ativa[i:i+2], 16) for i in (1, 3, 5))
        except Exception:
            r, g, b = (36, 104, 180)
        st.markdown(
            f"<style>.stApp{{background-image:radial-gradient(ellipse at 88% 6%,rgba({r},{g},{b},.17),transparent 38%),linear-gradient(180deg,__fundo__,__fundo__);}}</style>".replace("__fundo__", tema_ativo()["fundo"]),
            unsafe_allow_html=True,
        )
        info_card, limpar_card = st.columns([5, 1])
        with info_card:
            st.markdown(
                f'<div class="aviso aviso-info">✦ <b>Filtro aplicado pelo indicador:</b> {escape(rotulo_card)} · gráficos, indicadores e tabela foram atualizados.</div>',
                unsafe_allow_html=True,
            )
        with limpar_card:
            if st.button("Remover", key=f"remover_card_filtro_{chave}", use_container_width=True):
                st.session_state.pop(state_farol_card, None)
                st.rerun()

    with st.container(border=True):
        topo1, topo2 = st.columns([4, 1])
        with topo1:
            st.markdown("<div class='card-titulo'>Filtros de análise</div><div class='card-sub'>Refine os processos e atualize os indicadores desta página em tempo real.</div>", unsafe_allow_html=True)
        with topo2:
            st.button("↺ Limpar filtros", key=f"limpar_filtros_{chave}",
                      on_click=_limpar_filtros, use_container_width=True)

        f1, f2, f3, f4, f5 = st.columns([1.35, 1.35, 1.45, 1.05, 1.55])
        with f1:
            referencia = st.text_input("Referência do cliente", key=f"ref_{chave}",
                                       placeholder="Buscar referência...").strip()
        with f2:
            processo = st.text_input("Nº do processo", key=f"proc_{chave}",
                                     placeholder="Buscar processo...").strip()
        with f3:
            opcoes = [x for x in ORDEM_FAROL if x in dados["Farol da etapa"].dropna().unique()]
            farois = st.multiselect("Farol", opcoes, key=f"farol_filtro_{chave}",
                                    placeholder="Todos os faróis")
        with f4:
            situacao = st.selectbox("Situação", ["Todas", "Em andamento", "Concluída"],
                                    key=f"situacao_{chave}")
        with f5:
            periodo = None
            if not validas.empty:
                dmin, dmax = pd.to_datetime(validas).min().date(), pd.to_datetime(validas).max().date()
                periodo = st.date_input(
                    "Período de início", value=(dmin, dmax), min_value=dmin,
                    max_value=dmax, key=f"periodo_{chave}", format="DD/MM/YYYY",
                )

        if colunas_avancadas:
            with st.expander("＋ Filtros avançados", expanded=False):
                cols = st.columns(min(3, len(colunas_avancadas)))
                selecoes = {}
                for i, coluna in enumerate(colunas_avancadas):
                    opcoes_coluna = sorted(dados[coluna].dropna().astype(str).unique().tolist(), key=str.casefold)
                    with cols[i % len(cols)]:
                        selecoes[coluna] = st.multiselect(
                            coluna, opcoes_coluna,
                            key=f"avancado_{chave}_{coluna.lower().replace(' ', '_')}",
                            placeholder=f"Todos: {coluna.lower()}",
                        )
        else:
            selecoes = {}

    filtrado = dados.copy()
    if referencia and "Ref.Cliente" in filtrado:
        filtrado = filtrado[filtrado["Ref.Cliente"].astype(str).str.contains(referencia, case=False, na=False, regex=False)]
    if processo and "Nº Processo" in filtrado:
        filtrado = filtrado[filtrado["Nº Processo"].astype(str).str.contains(processo, case=False, na=False, regex=False)]
    if farois:
        filtrado = filtrado[filtrado["Farol da etapa"].isin(farois)]
    if situacao != "Todas" and "Situação da etapa" in filtrado.columns:
        filtrado = filtrado[filtrado["Situação da etapa"] == situacao]
    if (periodo and isinstance(periodo, (tuple, list)) and len(periodo) == 2
            and dmin is not None and (periodo[0], periodo[1]) != (dmin, dmax)):
        ini = pd.Timestamp(periodo[0])
        fim_ = pd.Timestamp(periodo[1]) + pd.Timedelta(days=1) - pd.Timedelta(microseconds=1)
        filtrado = filtrado[filtrado[coluna_inicio].between(ini, fim_)]
    for coluna, selecionados in selecoes.items():
        if selecionados:
            filtrado = filtrado[filtrado[coluna].astype(str).isin(selecionados)]

    if selecao_card:
        tipo_card = selecao_card.get("tipo")
        valores_card = selecao_card.get("valores", [])
        if tipo_card == "farol" and "Farol da etapa" in filtrado.columns:
            filtrado = filtrado[filtrado["Farol da etapa"].isin(valores_card)]
        elif tipo_card == "situacao":
            coluna_situacao = "Situação da etapa" if "Situação da etapa" in filtrado.columns else ("Status" if "Status" in filtrado.columns else None)
            if coluna_situacao:
                procurados = {_normalizar_texto(v) for v in valores_card}
                filtrado = filtrado[filtrado[coluna_situacao].map(_normalizar_texto).isin(procurados)]

    ativos = sum(bool(x) for x in (referencia, processo, farois, situacao != "Todas"))
    ativos += sum(bool(v) for v in selecoes.values())
    ativos += int(bool(selecao_card))
    st.caption(f"{len(filtrado):,} de {len(dados):,} processo(s) · {ativos} grupo(s) de filtros ativo(s)")
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