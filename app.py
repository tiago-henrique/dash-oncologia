import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import plotly.express as px
import os
import datetime
import requests
import seaborn as sns

st.set_page_config(layout='wide')
st.markdown("""
    <style>
        [data-testid="stSidebarNav"] {
            display: none;
        }
    </style>
""", unsafe_allow_html=True)

st.markdown("""
<style>
    header{
        width{
            display: flex;
            flex-wrap: wrap;
            width: 100%;
        }
    }
    .titulo{
        background-color: #004170;  
        color: #FFF;
        font-size: 54px;
        font-weight: bold;
        width: 100%;
        margin-bottom: 10px;
        text-align: center;
    }
    .total-internacao{
        border-radius: 5px;
        background-color: #004170;
        margin-top: 10px;
        width: 15%;
        text-align: center;
    }
    .total-internacao p{
        font-weight: bold;
        padding: 1rem;
        color: #FFF;
        font-size: 14px;
    }

    div.stPageLink a {
        background-color: #fff;
        color: white;
        padding: 5px;
        border-radius: 5px;
        text-decoration: none;
        border: 0px solid #d3d3d3;
        transition: all 0.3s ease;
    }
    
    div.stPageLink a:hover {
        background-color: #fff;
        color: white;
        border-color: #fff;
    }
            
    .media_dias{
        display: gird;
        background-color: #FFF;
        border-radius: 5px;
        border-bottom: 10px;
        color: #336799;
        padding: 0.2rem;
    }

    .content{
        grid-tempplate-columns: 1fr 1fr;        
    }

    .media_dias h1{
        font-size: 16px;
        text-align: center;
    }

    .media_dias p{
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

st.sidebar.title("Menu")
st.sidebar.page_link(
    "pages/internacao.py",
    label="Dados das Internações"
)

st.markdown(
    f"<div class='titulo'>Dashboard HB Onco</div>",
    unsafe_allow_html=True
)

st.image("imagem/logo-hbonco.webp")

@st.cache_data(ttl=300)
def carregar_dados_redcap():

    api_url = st.secrets["REDCAP_API_URL"]
    api_token = st.secrets["REDCAP_API_TOKEN"]

    payload = {
        "token": api_token,
        "content": "record",
        "action": "export",
        "format": "csv",
        "type": "flat",
        "rawOrLabel": "raw",
        "rawOrLabelHeaders": "raw",
        "exportCheckboxLabel": "false",
        "exportSurveyFields": "false",
        "exportDataAccessGroups": "false",
        "returnFormat": "csv"
    }

    response = requests.post(
        api_url,
        data=payload,
        timeout=60
    )

    response.raise_for_status()

    if not response.text.strip():
        raise ValueError("A API do REDCap retornou dados vazios.")

    database = pd.read_csv(
        pd.io.common.StringIO(response.text)
    )

    return database

try:
    database = carregar_dados_redcap()
    data_atualizacao = datetime.datetime.now().strftime(
        "%d/%m/%Y às %H:%M:%S"
    )

    st.success(
        f"Os dados do dashboard foram obtidos da API do REDCap em: "
        f"{data_atualizacao}"
    )

except requests.exceptions.RequestException as e:

    st.error(
        f"Erro de comunicação com a API do REDCap: {e}"
    )

    st.stop()

except Exception as e:

    st.error(
        f"Erro ao carregar os dados do REDCap: {e}"
    )

    st.stop()


database = database.rename(columns={
    'sitio_primario___1': 'Mama',
    'sitio_primario___2': 'Pulmão',
    'sitio_primario___3': 'C&P',
    'sitio_primario___4': 'SNC',
    'sitio_primario___5': 'Ovário',
    'sitio_primario___6': 'Próstata',
    'sitio_primario___8': 'Esôfago',
    'sitio_primario___9': 'Via Biliar',
    'sitio_primario___10': 'Pênis',
    'sitio_primario___11': 'Gástrico',
    'sitio_primario___12': 'Pâncreas',
    'sitio_primario___13': 'Colorretal',
    'sitio_primario___14': 'Colo Útero',
    'sitio_primario___15': 'Endométrio',
    'sitio_primario___16': 'Fígado',
    'sitio_primario___17': 'Pele',
    'sitio_primario___18': 'Bexiga',
    'sitio_primario___19': 'Rim',
    'sitio_primario___20': 'Outro',
    'sitio_primario___21': 'Sarcomas',
    'outro_sitio_primario': 'Outro sítio primário',
    'estagio_clinico': 'Estágio clínico',
    'metastase___1': 'M Fígado',
    'metastase___2': 'M Pulmão',
    'metastase___3': 'M SNC',
    'metastase___4': 'M Peritônio',
    'metastase___5': 'M Osso',
    'metastase___6': 'M Linfonodos',
    'metastase___7': 'M Adrenal',
    'metastase___8': 'M Outro',
    'metastase___9': 'Não se aplica',
    'metastase___10': 'M Pleura',
    'metastase___11': 'Progressão locoregional - em cenário paliativo'
})


admissao = database[
    database['redcap_repeat_instrument'].isna()
]

st.header('Dados Admissão')

colunas_sp = [
    'Mama',
    'Pulmão',
    'C&P',
    'SNC',
    'Ovário',
    'Próstata',
    'Esôfago',
    'Via Biliar',
    'Gástrico',
    'Pâncreas',
    'Colorretal',
    'Colo Útero',
    'Endométrio',
    'Fígado',
    'Pele',
    'Bexiga',
    'Rim',
    'Outro',
    'Sarcomas'
]


dados_sp = admissao[colunas_sp].sum().reset_index()

dados_sp.columns = [
    'Tipo',
    'Total'
]

dados_sp = dados_sp.sort_values(
    by='Total',
    ascending=False
)


fig = px.bar(
    dados_sp,
    x='Tipo',
    y='Total',
    text='Total',
    title='Casos por Tipo de Câncer'
)

fig.update_traces(
    textposition='outside'
)


col1, col2 = st.columns(
    2,
    border=True
)


with col1:

    st.plotly_chart(
        fig,
        use_container_width=True
    )

outro_sp = database[
    'Outro sítio primário'
].value_counts()

osp = outro_sp.reset_index()

osp.columns = [
    'Sítio',
    'Quantidade'
]


fig_osp = px.bar(
    osp,
    x='Sítio',
    y='Quantidade',
    text='Quantidade',
    title='Outros Sítios Primários'
)

fig_osp.update_traces(
    textposition='inside'
)


with col2:

    st.plotly_chart(
        fig_osp,
        use_container_width=True
    )

estagio_map = {
    1: 'Estágio I',
    2: 'Estágio II',
    3: 'Estágio III',
    4: 'Estágio IV',
    5: 'NA'
}

database['Estágio clínico'] = database[
    'Estágio clínico'
].map(estagio_map)

estagio_clinico = database[
    'Estágio clínico'
].value_counts()

ec = estagio_clinico.reset_index()

ec.columns = [
    'Estágio',
    'Quantidade'
]


fig_estagio = px.bar(
    ec,
    x='Estágio',
    y='Quantidade',
    text='Quantidade',
    title='Estágio Clínico'
)

fig_estagio.update_traces(
    textposition='outside'
)


col3, col4 = st.columns(
    2,
    border=True
)


with col3:
    st.plotly_chart(
        fig_estagio,
        use_container_width=True
    )

colunas_metastases = [
    'M Fígado',
    'M Pulmão',
    'M SNC',
    'M Peritônio',
    'M Osso',
    'M Linfonodos',
    'M Adrenal',
    'M Outro',
    'Não se aplica',
    'M Pleura'
]

dados_mt = admissao[
    colunas_metastases
].sum().reset_index()

dados_mt.columns = [
    'Tipo',
    'Total'
]

dados_mt = dados_mt.sort_values(
    by='Total',
    ascending=False
)

fig_metastase = px.bar(
    dados_mt,
    x="Tipo",
    y="Total",
    text="Total",
    title="Metástase por Subsítios"
)

fig_metastase.update_traces(
    textposition='outside'
)


with col4:

    st.plotly_chart(
        fig_metastase,
        use_container_width=True
    )

st.write(
    "Desenvolvido por Tiago Henrique - 2026"
)
