import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import plotly.express as px
import os
import datetime

st.set_page_config(layout='wide')
st.title("Dados HBOnco")

try:
    database = pd.read_csv(st.secrets['DATABASE'])
    filename = st.secrets['CAMINHO']

except Exception as e:
    st.error(f"Erro ao carregar o banco de dados: {e}")
    st.stop()

stats = os.stat(filename)
creation_time = datetime.datetime.fromtimestamp(stats.st_ctime)
formatted_date = creation_time.strftime("%d/%m/%Y %H:%M:%S")
st.info(f"O dados do dasbhboard foram atualizados em: {formatted_date}")
st.success(f"Os dados do dashboard foram atualuzados em: {formatted_data}")

database = database.rename(columns={
    'sitio_primario___1':'Mama', 'sitio_primario___2':'Pulmão', 'sitio_primario___3':'C&P', 'sitio_primario___4':'SNC', 'sitio_primario___5':'Ovário', 'sitio_primario___6':'Próstata', 'sitio_primario___7':'Sarcoma', 'sitio_primario___8':'Esôfago', 'sitio_primario___9':'Via Biliar', 'sitio_primario___10':'Pênis', 'sitio_primario___11':'Gástrico', 'sitio_primario___12':'Pâncreas', 'sitio_primario___13':'Colorretal', 'sitio_primario___14':'Colo Útero', 'sitio_primario___15':'Endométrio', 'sitio_primario___16':'Fígado', 'sitio_primario___17':'Pele', 'sitio_primario___18':'Bexiga', 'sitio_primario___19':'Rim', 'sitio_primario___20':'Outro', 'sitio_primario___21':'Sarcomas', 'outro_sitio_primario':'Outro sítio primário', 'estagio_clinico':'Estágio clínico', 'metastase___1':'M Fígado', 'metastase___2':'M Pulmão', 'metastase___3':'M SNC', 'metastase___4':'M Peritônio', 'metastase___5':'M Osso', 'metastase___6':'M Linfonodos', 'metastase___7':'M Adrenal', 'metastase___8':'M Outro', 'metastase___9':'Não se aplica','metastase___10':'M Pleura', 'metastase___11':'Progressão locoregional - em cenário paliativo'})

admissao = database[database['redcap_repeat_instrument'].isna()]
st.header('Dados Admissão')

colunas_sp = [
    'Mama','Pulmão','C&P','SNC','Ovário','Próstata','Sarcoma',
    'Esôfago','Via Biliar','Pênis','Gástrico','Pâncreas',
    'Colorretal','Colo Útero','Endométrio','Fígado','Pele',
    'Bexiga','Rim','Outro','Sarcomas'
]

dados_sp = admissao[colunas_sp].sum().reset_index()
dados_sp.columns = ['Tipo', 'Total']

dados_sp = dados_sp.sort_values(by='Total', ascending=False)

# st.subheader('📋 Dados')

#col1, col2 = st.columns(2, border=True)
#with col1:
st.dataframe(dados_sp)

#fig = px.bar(
#    dados_sp,
#    x='Tipo',
#    y='Total',
#    title='Casos por Tipo de Câncer'
#)

#with col2:
#    st.plotly_chart(fig, use_container_width=True)

outro_sp = database['Outro sítio primário'].value_counts()
st.write(outro_sp)

estagio_map = {
    1 : 'Estágio I',
    2 : 'Estágio II',
    3 : 'Estágio III',
    4 : 'Estágio IV',
    5 : 'NA'
}

database['Estágio clínico'] = database['Estágio clínico'].map(estagio_map)
estagio_clinico = database['Estágio clínico'].value_counts()
st.write(estagio_clinico)

colunas_metastases = ['M Fígado', 'M Pulmão', 'M SNC', 'M Peritônio', 'M Osso', 'M Linfonodos', 'M Adrenal', 'M Outro', 'Não se aplica', 'M Pleura', 'Progressão locoregional - em cenário paliativo']

dados_mt = admissao[colunas_metastases].sum().reset_index()
dados_mt.columns = ['Tipo', 'Total']
dados_mt = dados_mt.sort_values(by='Total', ascending=False)
st.write(dados_mt)

###########################
#internação
col3, col4 = st.columns(2, border=True)

st.header("Dados de Internação")
st.write("#Distribuição de idade")
internacao = database[database['redcap_repeat_instrument'] == 'internao']
conta_internacao = internacao['record_id'].value_counts()

internacao['dob'] = pd.to_datetime(internacao['dob'], errors='coerce')
internacao['data_de_nascimento'] = pd.to_datetime(internacao['data_de_nascimento'], errors='coerce')
internacao['data_da_interna_o'] = pd.to_datetime(internacao['data_da_interna_o'], errors='coerce')
internacao['data_da_alta'] = pd.to_datetime(internacao['data_da_alta'], errors='coerce')

idade = internacao['data_da_interna_o'] - internacao['dob']
idade_anos = idade.dt.days // 365
idade_counts = idade_anos.value_counts().sort_index()

#Calcular tempo de internação
tempo_internacao = internacao['data_da_alta'] - internacao['data_da_interna_o']
dias_internacao = tempo_internacao.dt.days
dias_counts = dias_internacao.value_counts()
dias_counts = dias_counts.sort_values(ascending=False)

st.header("Distrubuição por idade")
st.write(idade_counts)
st.header("Tempo de internaçaõ")
st.write(dias_internacao)

with col3:
    st.write(conta_internacao)


causa_internacao_map = {
    29 : "Progressão de doença",
    30 : "Infecções",
    31 : "Toxicidade do tratamento",
    32 : "Manejo/instalação de dispositivos",
    41 : "Manejo de sintomas",
    33 : "Ablação hepática",
    34 : "Eventos trombóticos (TVP, TEP, AVC)",
    35 : "Eventos hemorrágicos (tumorais ou não)",
    36 : "Disfunção renal",
    37 : "Alterações endócrinas",
    38 : "Biopsia",
    39 : "Estadiamento",
    40 : "Fase Final de Vida"
}

internacao['estagio_clinico_internacao'] = internacao['estagio_clinico_internacao'].map(estagio_map)
eci = internacao['estagio_clinico_internacao'].value_counts()
st.write(eci)
internacao['causa_internacao'] = database['causa_internacao'].map(causa_internacao_map)
causa_internacao = internacao['causa_internacao'].value_counts()

#with col4:
#    st.bar_chart(causa_internacao)
#
infeccao_map = {
    1 : "Infecção urinária",
    2 : "Pneumonia",
    3 : "Infecção sitio tumoral",
    4 : "Celulite",
    5 : "Infecção em outras partes",
    6 : "Síndrome Gripal / Influenza / Covid",
    7 : "Dengue",
    8 : "Diarréia/Colite",
    9 : "Colangite"
}
internacao['tipo_infeccao'] = internacao['tipo_infeccao'].map(infeccao_map)
tipo_infeccao = internacao['tipo_infeccao'].value_counts()
st.write(tipo_infeccao)

manejo_map = {
    1 : "Dor",
    2 : "Dispneia",
    3 : "Náusea e Vómitos",
    4 : "Constipação"
}
internacao['manejo_de_sintomas'] = internacao['manejo_de_sintomas'].map(manejo_map)
manejo_sintomas = internacao['manejo_de_sintomas'].value_counts()
st.write(manejo_sintomas)

dispositivos_map = {
    1 : "Gastrostomia",
    2 : "SNE",
    3 : "Port-a-cath",
    4 : "Dj/Nefrostomia",
    5 : "Traqueostomia"
}
internacao['dispositivos'] = internacao['dispositivos'].map(dispositivos_map)
dispositivos = internacao['dispositivos'].value_counts()
st.write(dispositivos)

pd_map = {
    1 : "Hipercalcemia da Malignidade",
    2 : "Insuficiencia Renal",
    3 : "Síndrome colestática",
    4 : "Obstrução / Pseudo-obstrução maligna (gástrica/intestinal)",
    5 : "Compressão Medular",
    6 : "Síndrome Veia Cava",
    7 : "Urgência quimioterápica",
    8 : "PD em SNC",
    10 : "Insuficiência hepática",
    11 : "Sd. Lise tumoral",
    12 : "Progressão de doença"
}

internacao['pd'] = internacao['pd'].map(pd_map)
progressao_doenca = internacao['pd'].value_counts()
st.write(progressao_doenca)

st.write("Criado por Tiago Henrique")
