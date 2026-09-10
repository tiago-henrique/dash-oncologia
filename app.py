```python
import streamlit as st
import pandas as pd
import plotly.express as px
import requests


# ============================================================
# CONFIGURAÇÃO DA PÁGINA
# ============================================================

st.set_page_config(
    page_title="Dashboard HB Onco",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ============================================================
# CSS
# ============================================================

st.markdown("""
<style>

    /* Oculta navegação padrão do Streamlit */
    [data-testid="stSidebarNav"] {
        display: none;
    }

    /* Título principal */
    .titulo {
        background-color: #004170;
        color: white;
        font-size: 42px;
        font-weight: bold;
        width: 100%;
        margin-bottom: 20px;
        padding: 15px;
        text-align: center;
        border-radius: 8px;
    }

    /* Cards KPI */
    .kpi {
        background-color: #004170;
        color: white;
        padding: 18px;
        border-radius: 10px;
        text-align: center;
        box-shadow: 0 2px 6px rgba(0,0,0,0.15);
    }

    .kpi-title {
        font-size: 15px;
        font-weight: 500;
        margin-bottom: 8px;
    }

    .kpi-value {
        font-size: 30px;
        font-weight: bold;
    }

    /* Informação de atualização */
    .atualizacao {
        background-color: #f2f6fa;
        color: #004170;
        padding: 10px 15px;
        border-radius: 6px;
        margin-bottom: 20px;
        font-size: 14px;
    }

</style>
""", unsafe_allow_html=True)


# ============================================================
# SIDEBAR
# ============================================================

st.sidebar.title("Menu")

st.sidebar.page_link(
    "pages/internacao.py",
    label="Dados das Internações"
)


# ============================================================
# TÍTULO
# ============================================================

st.markdown(
    "<div class='titulo'>Dashboard HB Onco</div>",
    unsafe_allow_html=True
)


# ============================================================
# LOGO
# ============================================================

try:
    st.image(
        "imagem/logo-hbonco.webp",
        use_container_width=True
    )
except Exception:
    st.warning("Logo do HB Onco não encontrada.")


# ============================================================
# CONFIGURAÇÕES
# ============================================================

REDCAP_API_URL = st.secrets.get("REDCAP_API_URL", "")
REDCAP_API_TOKEN = st.secrets.get("REDCAP_API_TOKEN", "")

DATABASE_PATH = st.secrets.get("DATABASE", "")
CAMINHO_ATUALIZACAO = st.secrets.get("CAMINHO", "")


# ============================================================
# FUNÇÃO — DATA DA ÚLTIMA ATUALIZAÇÃO
# ============================================================

def obter_ultima_atualizacao(url):
    """
    Obtém a informação Last-Modified de um arquivo remoto.
    """

    if not url:
        return None

    try:
        response = requests.head(
            url,
            timeout=10,
            allow_redirects=True
        )

        response.raise_for_status()

        return response.headers.get("Last-Modified")

    except requests.RequestException:
        return None


# ============================================================
# FUNÇÃO — CARREGAR BANCO
# ============================================================

@st.cache_data(ttl=300)
def carregar_database(caminho):
    """
    Carrega o banco de dados CSV.
    O cache evita recarregar o arquivo a cada interação.
    """

    if not caminho:
        raise ValueError(
            "A variável DATABASE não foi configurada no secrets.toml."
        )

    return pd.read_csv(caminho)


# ============================================================
# FUNÇÃO — RENOMEAR VARIÁVEIS
# ============================================================

def renomear_colunas(database):

    mapa_colunas = {

        # Sítio primário
        "sitio_primario___1": "Mama",
        "sitio_primario___2": "Pulmão",
        "sitio_primario___3": "C&P",
        "sitio_primario___4": "SNC",
        "sitio_primario___5": "Ovário",
        "sitio_primario___6": "Próstata",
        "sitio_primario___8": "Esôfago",
        "sitio_primario___9": "Via Biliar",
        "sitio_primario___10": "Pênis",
        "sitio_primario___11": "Gástrico",
        "sitio_primario___12": "Pâncreas",
        "sitio_primario___13": "Colorretal",
        "sitio_primario___14": "Colo Útero",
        "sitio_primario___15": "Endométrio",
        "sitio_primario___16": "Fígado",
        "sitio_primario___17": "Pele",
        "sitio_primario___18": "Bexiga",
        "sitio_primario___19": "Rim",
        "sitio_primario___20": "Outro",
        "sitio_primario___21": "Sarcomas",

        # Outros
        "outro_sitio_primario": "Outro sítio primário",

        # Estágio
        "estagio_clinico": "Estágio clínico",

        # Metástases
        "metastase___1": "M Fígado",
        "metastase___2": "M Pulmão",
        "metastase___3": "M SNC",
        "metastase___4": "M Peritônio",
        "metastase___5": "M Osso",
        "metastase___6": "M Linfonodos",
        "metastase___7": "M Adrenal",
        "metastase___8": "M Outro",
        "metastase___9": "Não se aplica",
        "metastase___10": "M Pleura",
        "metastase___11": (
            "Progressão locoregional - em cenário paliativo"
        )
    }

    return database.rename(columns=mapa_colunas)


# ============================================================
# FUNÇÃO — PREPARAR DADOS
# ============================================================

def preparar_dados(database):

    database = database.copy()

    # --------------------------------------------------------
    # Identificação dos registros de admissão
    # --------------------------------------------------------

    if "redcap_repeat_instrument" in database.columns:

        admissao = database[
            database["redcap_repeat_instrument"].isna()
        ].copy()

    else:

        # Caso a coluna não exista, considera todo banco
        admissao = database.copy()

    # --------------------------------------------------------
    # Converter campos binários para numérico
    # --------------------------------------------------------

    colunas_binarias = [

        "Mama",
        "Pulmão",
        "C&P",
        "SNC",
        "Ovário",
        "Próstata",
        "Esôfago",
        "Via Biliar",
        "Gástrico",
        "Pâncreas",
        "Colorretal",
        "Colo Útero",
        "Endométrio",
        "Fígado",
        "Pele",
        "Bexiga",
        "Rim",
        "Outro",
        "Sarcomas",

        "M Fígado",
        "M Pulmão",
        "M SNC",
        "M Peritônio",
        "M Osso",
        "M Linfonodos",
        "M Adrenal",
        "M Outro",
        "Não se aplica",
        "M Pleura"
    ]

    for coluna in colunas_binarias:

        if coluna in admissao.columns:

            admissao[coluna] = pd.to_numeric(
                admissao[coluna],
                errors="coerce"
            ).fillna(0)

    # --------------------------------------------------------
    # Estágio clínico
    # --------------------------------------------------------

    if "Estágio clínico" in admissao.columns:

        mapa_estagio = {
            1: "Estágio I",
            2: "Estágio II",
            3: "Estágio III",
            4: "Estágio IV",
            5: "NA"
        }

        admissao["Estágio clínico"] = (
            pd.to_numeric(
                admissao["Estágio clínico"],
                errors="coerce"
            )
            .map(mapa_estagio)
        )

    return admissao


# ============================================================
# FUNÇÃO — GRÁFICO DE SÍTIO PRIMÁRIO
# ============================================================

def grafico_sitio_primario(admissao):

    colunas = [
        "Mama",
        "Pulmão",
        "C&P",
        "SNC",
        "Ovário",
        "Próstata",
        "Esôfago",
        "Via Biliar",
        "Gástrico",
        "Pâncreas",
        "Colorretal",
        "Colo Útero",
        "Endométrio",
        "Fígado",
        "Pele",
        "Bexiga",
        "Rim",
        "Outro",
        "Sarcomas"
    ]

    colunas_existentes = [
        coluna
        for coluna in colunas
        if coluna in admissao.columns
    ]

    if not colunas_existentes:
        return None

    dados = (
        admissao[colunas_existentes]
        .sum()
        .reset_index()
    )

    dados.columns = [
        "Tipo",
        "Total"
    ]

    dados = dados.sort_values(
        "Total",
        ascending=False
    )

    fig = px.bar(
        dados,
        x="Tipo",
        y="Total",
        text="Total",
        title="Casos por Tipo de Câncer"
    )

    fig.update_traces(
        textposition="outside"
    )

    fig.update_layout(
        xaxis_title="",
        yaxis_title="Número de casos",
        margin=dict(
            l=20,
            r=20,
            t=60,
            b=20
        )
    )

    return fig


# ============================================================
# FUNÇÃO — OUTROS SÍTIOS PRIMÁRIOS
# ============================================================

def grafico_outros_sitios(admissao):

    coluna = "Outro sítio primário"

    if coluna not in admissao.columns:
        return None

    dados = (
        admissao[coluna]
        .dropna()
        .astype(str)
        .str.strip()
    )

    dados = dados[dados != ""]

    if dados.empty:
        return None

    dados = (
        dados
        .value_counts()
        .reset_index()
    )

    dados.columns = [
        "Sítio",
        "Quantidade"
    ]

    fig = px.bar(
        dados,
        x="Sítio",
        y="Quantidade",
        text="Quantidade",
        title="Outros Sítios Primários"
    )

    fig.update_traces(
        textposition="outside"
    )

    fig.update_layout(
        xaxis_title="",
        yaxis_title="Quantidade",
        margin=dict(
            l=20,
            r=20,
            t=60,
            b=20
        )
    )

    return fig


# ============================================================
# FUNÇÃO — ESTÁGIO CLÍNICO
# ============================================================

def grafico_estagio(admissao):

    coluna = "Estágio clínico"

    if coluna not in admissao.columns:
        return None

    dados = (
        admissao[coluna]
        .dropna()
        .value_counts()
        .reset_index()
    )

    dados.columns = [
        "Estágio",
        "Quantidade"
    ]

    ordem = [
        "Estágio I",
        "Estágio II",
        "Estágio III",
        "Estágio IV",
        "NA"
    ]

    dados["Estágio"] = pd.Categorical(
        dados["Estágio"],
        categories=ordem,
        ordered=True
    )

    dados = dados.sort_values("Estágio")

    fig = px.bar(
        dados,
        x="Estágio",
        y="Quantidade",
        text="Quantidade",
        title="Estágio Clínico"
    )

    fig.update_traces(
        textposition="outside"
    )

    fig.update_layout(
        xaxis_title="",
        yaxis_title="Quantidade",
        margin=dict(
            l=20,
            r=20,
            t=60,
            b=20
        )
    )

    return fig


# ============================================================
# FUNÇÃO — METÁSTASES
# ============================================================

def grafico_metastases(admissao):

    colunas = [
        "M Fígado",
        "M Pulmão",
        "M SNC",
        "M Peritônio",
        "M Osso",
        "M Linfonodos",
        "M Adrenal",
        "M Outro",
        "Não se aplica",
        "M Pleura"
    ]

    colunas_existentes = [
        coluna
        for coluna in colunas
        if coluna in admissao.columns
    ]

    if not colunas_existentes:
        return None

    dados = (
        admissao[colunas_existentes]
        .sum()
        .reset_index()
    )

    dados.columns = [
        "Tipo",
        "Total"
    ]

    dados = dados.sort_values(
        "Total",
        ascending=False
    )

    fig = px.bar(
        dados,
        x="Tipo",
        y="Total",
        text="Total",
        title="Metástase por Subsítios"
    )

    fig.update_traces(
        textposition="outside"
    )

    fig.update_layout(
        xaxis_title="",
        yaxis_title="Número de casos",
        margin=dict(
            l=20,
            r=20,
            t=60,
            b=20
        )
    )

    return fig


# ============================================================
# CARREGAMENTO DO BANCO
# ============================================================

if not DATABASE_PATH:

    st.error(
        "O caminho do banco de dados não foi configurado "
        "em st.secrets['DATABASE']."
    )

    st.stop()


try:

    database = carregar_database(
        DATABASE_PATH
    )

except Exception as e:

    st.error(
        f"Erro ao carregar o banco de dados: {e}"
    )

    st.stop()


# ============================================================
# PREPARAÇÃO
# ============================================================

database = renomear_colunas(database)

admissao = preparar_dados(database)


# ============================================================
# DATA DE ATUALIZAÇÃO
# ============================================================

ultima_atualizacao = obter_ultima_atualizacao(
    CAMINHO_ATUALIZACAO
)

if ultima_atualizacao:

    st.markdown(
        f"""
        <div class="atualizacao">
            <b>Última atualização dos dados:</b>
            {ultima_atualizacao}
        </div>
        """,
        unsafe_allow_html=True
    )

else:

    st.info(
        "Não foi possível identificar a data da última atualização."
    )


# ============================================================
# CABEÇALHO
# ============================================================

st.header("Dados de Admissão")


# ============================================================
# KPIs
# ============================================================

total_pacientes = len(admissao)

total_estagio_iv = 0

if "Estágio clínico" in admissao.columns:

    total_estagio_iv = (
        admissao["Estágio clínico"]
        .eq("Estágio IV")
        .sum()
    )


total_metastase = 0

colunas_metastases = [
    "M Fígado",
    "M Pulmão",
    "M SNC",
    "M Peritônio",
    "M Osso",
    "M Linfonodos",
    "M Adrenal",
    "M Outro",
    "M Pleura"
]

colunas_metastases_existentes = [
    coluna
    for coluna in colunas_metastases
    if coluna in admissao.columns
]

if colunas_metastases_existentes:

    total_metastase = (
        admissao[colunas_metastases_existentes]
        .sum(axis=1)
        .gt(0)
        .sum()
    )


# ============================================================
# EXIBIÇÃO DOS KPIs
# ============================================================

kpi1, kpi2, kpi3 = st.columns(3)

with kpi1:

    st.markdown(
        f"""
        <div class="kpi">
            <div class="kpi-title">
                Total de admissões
            </div>
            <div class="kpi-value">
                {total_pacientes:,}
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )


with kpi2:

    st.markdown(
        f"""
        <div class="kpi">
            <div class="kpi-title">
                Estágio IV
            </div>
            <div class="kpi-value">
                {total_estagio_iv:,}
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )


with kpi3:

    st.markdown(
        f"""
        <div class="kpi">
            <div class="kpi-title">
                Pacientes com metástase
            </div>
            <div class="kpi-value">
                {total_metastase:,}
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )


st.markdown("<br>", unsafe_allow_html=True)


# ============================================================
# GRÁFICOS — LINHA 1
# ============================================================

col1, col2 = st.columns(2)

with col1:

    fig = grafico_sitio_primario(
        admissao
    )

    if fig:

        st.plotly_chart(
            fig,
            use_container_width=True
        )

    else:

        st.warning(
            "Dados de sítio primário não disponíveis."
        )


with col2:

    fig = grafico_outros_sitios(
        admissao
    )

    if fig:

        st.plotly_chart(
            fig,
            use_container_width=True
        )

    else:

        st.info(
            "Não existem dados de outros sítios primários."
        )


# ============================================================
# GRÁFICOS — LINHA 2
# ============================================================

col3, col4 = st.columns(2)

with col3:

    fig = grafico_estagio(
        admissao
    )

    if fig:

        st.plotly_chart(
            fig,
            use_container_width=True
        )

    else:

        st.warning(
            "Dados de estágio clínico não disponíveis."
        )


with col4:

    fig = grafico_metastases(
        admissao
    )

    if fig:

        st.plotly_chart(
            fig,
            use_container_width=True
        )

    else:

        st.warning(
            "Dados de metástases não disponíveis."
        )


# ============================================================
# RODAPÉ
# ============================================================

st.markdown("---")

st.caption(
    "Desenvolvido por Tiago Henrique • HB Onco • 2026"
)
```
