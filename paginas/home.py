"""
Capa do Dashboard de Importação - Savoy
Reprodução vetorial da referência em HTML/CSS/SVG para Streamlit.
O PDF e a imagem de referência NÃO são usados na execução.

Estrutura esperada:
Projeto_Dashboard_Importacao/
├── app.py
├── capa.py
└── Arquivos png/
    ├── logo_pibernat.png
    ├── logo_savoy.png
    └── logo_coty.png

Os nomes dos arquivos precisam conter: pibernat, savoy e coty.
"""

import base64
import io
from pathlib import Path

import streamlit as st


# ============================================================
# CONFIGURAÇÕES EDITÁVEIS
# ============================================================

TITULO = "Dashboard"
SUBTITULO = "Operacional"
RODAPE = "BI Operacional Savoy | Importação"

AZUL = "#0033A0"
LAVANDA = "#99ADD9"

PASTA_IMAGENS = "Arquivos png"

LOGOS = {
    "pibernat": "PIBERNAT",
    "savoy": "SAVOY",
    "coty": "COTY",
}

EXTENSOES = {
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".webp": "image/webp",
    ".svg": "image/svg+xml",
}

PASTAS_CANDIDATAS = [
    "Arquivos png", "Aquivos png", "imagens", "images",
    "img", "assets", "logos", "logo", "static", "fotos",
]


# ============================================================
# LOCALIZAÇÃO E LEITURA DOS LOGOS
# ============================================================

def _pastas_de_imagens():
    arquivo_atual = Path(__file__).resolve().parent
    bases = [arquivo_atual, arquivo_atual.parent, Path.cwd()]
    nomes = ([PASTA_IMAGENS] if PASTA_IMAGENS else []) + PASTAS_CANDIDATAS

    pastas = []
    for nome in nomes:
        for base in bases:
            pasta = base / nome
            if pasta.is_dir() and pasta not in pastas:
                pastas.append(pasta)

    # Também permite deixar as imagens junto do próprio capa.py.
    for base in bases:
        if base.is_dir() and base not in pastas:
            pastas.append(base)

    return pastas


def _achar_logo(palavra):
    for pasta in _pastas_de_imagens():
        try:
            arquivos = sorted(pasta.iterdir())
        except OSError:
            continue

        for arquivo in arquivos:
            if (
                arquivo.is_file()
                and arquivo.suffix.lower() in EXTENSOES
                and palavra.lower() in arquivo.stem.lower()
            ):
                return arquivo

    return None


@st.cache_data(show_spinner=False)
def _logo_data_uri(caminho, modificado_em):
    """Converte o logo para data URI e remove margens transparentes/brancas."""
    arquivo = Path(caminho)
    mime = EXTENSOES[arquivo.suffix.lower()]
    dados = arquivo.read_bytes()

    if arquivo.suffix.lower() != ".svg":
        try:
            from PIL import Image, ImageChops

            imagem = Image.open(io.BytesIO(dados)).convert("RGBA")
            alfa = imagem.getchannel("A")

            if alfa.getextrema()[0] < 255:
                caixa = alfa.point(
                    lambda valor: 255 if valor > 8 else 0
                ).getbbox()
            else:
                branco = Image.new("RGB", imagem.size, (255, 255, 255))
                diferenca = ImageChops.difference(
                    imagem.convert("RGB"), branco
                ).convert("L")
                caixa = diferenca.point(
                    lambda valor: 255 if valor > 12 else 0
                ).getbbox()

            if caixa:
                imagem = imagem.crop(caixa)

            buffer = io.BytesIO()
            imagem.save(buffer, format="PNG", optimize=True)
            dados = buffer.getvalue()
            mime = "image/png"

        except Exception:
            # Se Pillow não estiver instalado ou o arquivo não puder ser tratado,
            # o logo original ainda será usado.
            pass

    codificado = base64.b64encode(dados).decode("ascii")
    return f"data:{mime};base64,{codificado}"


def _logo_html(palavra):
    arquivo = _achar_logo(palavra)

    if arquivo is None:
        return (
            f'<div class="logo-ausente">'
            f'{LOGOS[palavra]}'
            f'</div>'
        )

    uri = _logo_data_uri(str(arquivo), arquivo.stat().st_mtime)
    return (
        f'<img src="{uri}" '
        f'alt="{LOGOS[palavra]}" '
        f'class="imagem-logo imagem-logo-{palavra}">'
    )


# ============================================================
# HTML + CSS DA CAPA
# ============================================================

CSS = r"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@600;700;800&display=swap');

/* Área externa: proporção igual à referência (1800 x 810). */
.capa-savoy {
    position: relative;
    width: 100%;
    aspect-ratio: 1800 / 810;
    overflow: hidden;
    background: #FFFFFF;
    container-type: inline-size;
    font-family: 'Poppins', 'Arial', sans-serif;
    isolation: isolate;
}

/* Forma azul vetorial. O SVG acompanha a proporção da capa. */
.capa-forma-svg {
    position: absolute;
    inset: 0;
    width: 100%;
    height: 100%;
    z-index: 1;
    overflow: visible;
}

/* Título e subtítulo. */
.capa-titulo,
.capa-subtitulo,
.capa-rodape {
    position: absolute;
    z-index: 2;
    left: 8.45%;
    margin: 0;
    padding: 0;
    white-space: nowrap;
    font-family: 'Poppins', 'Arial', sans-serif;
    font-weight: 800;
    line-height: 1.08;
}

.capa-titulo {
    top: 28.8%;
    color: #FFFFFF;
    font-size: 5.55cqw;
    letter-spacing: -0.035em;
}

.capa-subtitulo {
    top: 44.0%;
    color: __LAVANDA__;
    font-size: 4.0cqw;
    letter-spacing: -0.025em;
}

.capa-rodape {
    top: 72.7%;
    color: #FFFFFF;
    font-size: 1.42cqw;
    font-weight: 700;
    letter-spacing: -0.015em;
}

/* Faixa dos logotipos no canto inferior direito. */
.capa-logo {
    position: absolute;
    z-index: 3;
    top: 77.8%;
    height: 12.5%;
    transform: translateY(-50%);
    display: flex;
    align-items: center;
    justify-content: center;
}

.capa-logo img {
    display: block;
    width: 100%;
    height: 100%;
    object-fit: contain;
}

.logo-pibernat {
    left: 59.7%;
    width: 10.2%;
}

.logo-savoy {
    left: 73.2%;
    width: 10.4%;
}

.logo-coty {
    left: 85.3%;
    width: 10.5%;
}

/* Divisor vertical entre Pibernat e Savoy. */
.capa-divisor {
    position: absolute;
    z-index: 3;
    left: 71.55%;
    top: 68.3%;
    width: max(2px, 0.16cqw);
    height: 18.5%;
    background: __AZUL__;
}

/* Reserva visual caso algum arquivo de logo não seja encontrado. */
.logo-ausente {
    width: 100%;
    min-height: 45%;
    display: flex;
    align-items: center;
    justify-content: center;
    box-sizing: border-box;
    padding: 0.35cqw;
    border: 1px dashed #9DB0DD;
    border-radius: 4px;
    color: __AZUL__;
    font-size: 1.05cqw;
    font-weight: 800;
    text-align: center;
}

/* Evita que estilos globais do Streamlit alterem os textos da capa. */
.capa-savoy * {
    box-sizing: border-box;
}

/* Em telas menores, preserva a proporção e reduz o risco de quebra. */
@media (max-width: 600px) {
    .capa-savoy {
        min-width: 520px;
    }
}
</style>
"""


def _html_linha_unica(texto):
    return "\n".join(
        linha.strip()
        for linha in texto.splitlines()
        if linha.strip()
    )


def montar_capa_html():
    css = (
        CSS
        .replace("__AZUL__", AZUL)
        .replace("__LAVANDA__", LAVANDA)
    )

    # Caminho vetorial desenhado para reproduzir a grande forma azul
    # da referência, sem usar PDF ou imagem como plano de fundo.
    corpo = f"""
    <div class="capa-savoy">

        <svg class="capa-forma-svg"
             viewBox="0 0 1800 810"
             preserveAspectRatio="none"
             xmlns="http://www.w3.org/2000/svg"
             aria-hidden="true">
            <defs>
                <filter id="sombra-forma"
                        x="-5%" y="-5%" width="115%" height="115%">
                    <feGaussianBlur in="SourceAlpha" stdDeviation="5"/>
                    <feOffset dx="5" dy="6" result="deslocamento"/>
                    <feComponentTransfer>
                        <feFuncA type="linear" slope="0.28"/>
                    </feComponentTransfer>
                    <feMerge>
                        <feMergeNode/>
                        <feMergeNode in="SourceGraphic"/>
                    </feMerge>
                </filter>
            </defs>

            <path
                d="
                    M 67,1
                    H 1060
                    C 1101,1 1125,27 1125,67
                    V 190
                    C 1125,365 1060,510 951,626
                    C 850,733 712,790 568,810
                    H 65
                    C 28,810 4,783 4,746
                    V 66
                    C 4,28 29,1 67,1
                    Z
                "
                fill="{AZUL}"
                filter="url(#sombra-forma)"
            />
        </svg>

        <div class="capa-titulo">{TITULO}</div>
        <div class="capa-subtitulo">{SUBTITULO}</div>
        <div class="capa-rodape">{RODAPE}</div>

        <div class="capa-logo logo-pibernat">
            {_logo_html("pibernat")}
        </div>

        <div class="capa-divisor"></div>

        <div class="capa-logo logo-savoy">
            {_logo_html("savoy")}
        </div>

        <div class="capa-logo logo-coty">
            {_logo_html("coty")}
        </div>

    </div>
    """

    return _html_linha_unica(css) + "\n" + _html_linha_unica(corpo)


def pagina_home():
    """Renderiza a capa na página Home do Streamlit."""
    st.markdown(
        montar_capa_html(),
        unsafe_allow_html=True,
    )


# Compatibilidade com o nome usado em versões anteriores do projeto.
def pagina_capa():
    pagina_home()


if __name__ == "__main__":
    st.set_page_config(
        page_title="Dashboard de Importação - Savoy",
        layout="wide",
        initial_sidebar_state="collapsed",
    )
    pagina_home()
