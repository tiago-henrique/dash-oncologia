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
st.title("Dashboard HBOnco")

#st.sidebar.title("Filtros")
#dt_inicial = st.sidebar.date_input('Selecione a data inicial')
#dt_final = st.sidebar.date_input('Selecione a data final')

#Falta criar o filtro para o dataset usando as datas inicial e final selecionadas

file_path = st.secrets["CAMINHO"]
response = requests.head(file_path)
last_modified = response.headers.get("Last-Modified")

st.success(f"Os dados do dashboard foram atualizados em: {last_modified}")

try:
    database = pd.read_csv(st.secrets['DATABASE'])
    #fileName = st.secrets['CAMINHO']
except Exception as e:
    st.error(f"Erro ao carregar o banco de dados: {e}")
    st.stop()


#Filtrar os dados se necessário
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
fig = px.bar(
    dados_sp,
    x='Tipo',
    y='Total',
    text='Total',
    title='Casos por Tipo de Câncer'
)
fig.update_traces(textposition='outside')

col1, col2 = st.columns(2, border=True)
with col1:
    st.plotly_chart(fig, use_container_width=True)

outro_sp = database['Outro sítio primário'].value_counts()
osp = outro_sp.reset_index()
osp.columns = ['Sítio', 'Quantidade']
fig_osp = px.bar(osp, x='Sítio', y='Quantidade', text='Quantidade', title='Outros Sítios Primários')
fig_osp.update_traces(textposition='outside')

with col2:
    st.plotly_chart(fig_osp)

estagio_map = {
    1 : 'Estágio I',
    2 : 'Estágio II',
    3 : 'Estágio III',
    4 : 'Estágio IV',
    5 : 'NA'
}

# Aplicar o mapeamento
database['Estágio clínico'] = database['Estágio clínico'].map(estagio_map)
estagio_clinico = database['Estágio clínico'].value_counts()
ec = estagio_clinico.reset_index()
ec.columns = ['Estágio', 'Quantidade']
fig_estagio = px.bar(ec, x='Estágio', y='Quantidade', text='Quantidade', title='Estágio Clínico')
fig_estagio.update_traces(textposition='inside')

col3, col4 = st.columns(2, border=True)

with col3:
    st.plotly_chart(fig_estagio)


colunas_metastases = ['M Fígado', 'M Pulmão', 'M SNC', 'M Peritônio', 'M Osso', 'M Linfonodos', 'M Adrenal', 'M Outro', 'Não se aplica', 'M Pleura']

dados_mt = admissao[colunas_metastases].sum().reset_index()
dados_mt.columns = ['Tipo', 'Total']
dados_mt = dados_mt.sort_values(by='Total', ascending=False)
fig_metastase = px.bar(dados_mt, x="Tipo", y="Total", text="Total", title="Metástase por Subsítios")
fig_metastase.update_traces(textposition='outside')
with col4:
    st.plotly_chart(fig_metastase, use_container_width=True)

###########################
#internação
st.header("Dados de Internação")

col5, col6 = st.columns(2, border=True)
internacao = database[database['redcap_repeat_instrument'] == 'internao']
conta_internacao = (
    internacao['record_id']
    .value_counts()
    .rename_axis('Id. Paciente')
    .reset_index(name='Total')
)

st.header("Frequência de Internações")
st.write(conta_internacao)

internacao['dob'] = pd.to_datetime(internacao['dob'], errors='coerce')
internacao['data_de_nascimento'] = pd.to_datetime(internacao['data_de_nascimento'], errors='coerce')
internacao['data_da_interna_o'] = pd.to_datetime(internacao['data_da_interna_o'], errors='coerce')
internacao['data_da_alta'] = pd.to_datetime(internacao['data_da_alta'], errors='coerce')

idade = internacao['data_da_interna_o'] - internacao['dob']
idade_anos = idade.dt.days // 365
idade_counts = idade_anos.value_counts().sort_index()

idade_internacoes = idade_counts.reset_index()
idade_internacoes.columns = ['Idade', 'Quantidade']

bins = [15, 20, 30, 40, 50, 60, 70, 80, 100]
labels = ['16-19', '20-29', '30-39', '40-49', '50-59', '60-69', '70-79', '80+']

idade_internacoes['faixa_etaria'] = pd.cut(
    idade_internacoes['Idade'],
    bins=bins,
    labels=labels,
    right=False
)

idade_internacoes = (
    idade_internacoes
    .groupby('faixa_etaria')['Quantidade']
    .sum()
    .reset_index()
)

fig_idade_internacoes = px.bar(
    idade_internacoes,
    x='faixa_etaria',
    y='Quantidade',
    text='Quantidade',
    title='Distribuição por Faixa Etária (Internações)'
)

fig_idade_internacoes.update_traces(textposition='outside')
fig_idade_internacoes.update_layout(uniformtext_minsize=8, uniformtext_mode='hide')

with col6:
    st.plotly_chart(fig_idade_internacoes, use_container_width=True)
    
#Calcular tempo de internação
tempo_internacao = internacao['data_da_alta'] - internacao['data_da_interna_o']
dias_internacao = tempo_internacao.dt.days
dias_counts = dias_internacao.value_counts()
dias_counts = dias_counts.sort_values(ascending=False)

din = dias_counts.reset_index()
din.columns = ['Dias', 'Quantidade']
fig_din = px.bar(din, x='Dias', y='Quantidade', text='Quantidade', title='Dias de Internação')
fig_din.update_traces(textposition='inside')
with col5:
    st.plotly_chart(fig_din, use_container_width=True)

#st.write(df)

col9, col10 = st.columns(2, border=True)

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
eci = internacao['estagio_clinico_internacao'].value_counts().reset_index()
eci.columns = ['Estágio', 'Quantidade']
fig_eci = px.bar(eci, x='Estágio', y='Quantidade', text='Quantidade', title='Estágio Clínico')
fig_eci.update_traces(textposition='outside')

with col9:
    st.plotly_chart(fig_eci)

internacao['causa_internacao'] = database['causa_internacao'].map(causa_internacao_map)
causa_internacao = internacao['causa_internacao'].value_counts().reset_index()
causa_internacao.columns = ['Causa', 'Quantidade']
fig_causa_internacao = px.bar(causa_internacao, x='Causa', y='Quantidade', text='Quantidade', title='Causas de Internação')
fig_causa_internacao.update_traces(textposition='outside')
with col10:
    st.plotly_chart(fig_causa_internacao, use_container_width=True)

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

col11, col12 = st.columns(2, border=True)

internacao['tipo_infeccao'] = internacao['tipo_infeccao'].map(infeccao_map)
tipo_infeccao = internacao['tipo_infeccao'].value_counts().reset_index()
tipo_infeccao.columns = ['Tipo de Infecção', 'Quantidade']
fig_tipo_infeccao = px.bar(tipo_infeccao, x='Tipo de Infecção', y='Quantidade', text='Quantidade', title='Tipo de Infecção')
fig_tipo_infeccao.update_traces(textposition='outside')
with col11:
    st.plotly_chart(fig_tipo_infeccao)

manejo_map = {
    1 : "Dor",
    2 : "Dispneia",
    3 : "Náusea e Vómitos",
    4 : "Constipação"
}
internacao['manejo_de_sintomas'] = internacao['manejo_de_sintomas'].map(manejo_map)
manejo_sintomas = internacao['manejo_de_sintomas'].value_counts().reset_index()
manejo_sintomas.columns = ['Tipo de Manejo', 'Quantidade']
fig_manejo_sintomas = px.bar(manejo_sintomas, x='Tipo de Manejo', y='Quantidade', text='Quantidade', title='Tipo de Manejo')
fig_manejo_sintomas.update_traces(textposition='outside')
with col12:
    st.plotly_chart(fig_manejo_sintomas, use_container_width=True)

col13, col14 = st.columns(2, border=True)    
dispositivos_map = {
    1 : "Gastrostomia",
    2 : "SNE",
    3 : "Port-a-cath",
    4 : "Dj/Nefrostomia",
    5 : "Traqueostomia"
}

internacao['dispositivos'] = internacao['dispositivos'].map(dispositivos_map)
dispositivos = internacao['dispositivos'].value_counts().reset_index()
dispositivos.columns = ['Dispositivo', 'Quantidade']
fig_dispositivo = px.bar(dispositivos, x='Dispositivo', y='Quantidade', text='Quantidade', title='Tipo de Dispositivo')
fig_dispositivo.update_traces(textposition='outside')

with col13:
    st.plotly_chart(fig_dispositivo)

#dispositivos internacao
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
progressao_doenca = internacao['pd'].value_counts().reset_index()
progressao_doenca.columns = ['Progressão', 'Quantidade']
fig_progressao = px.bar(progressao_doenca, x='Progressão', y='Quantidade', text='Quantidade', title='Progressão da Doença')
fig_progressao.update_traces(textposition='outside')

with col14:
    st.plotly_chart(fig_progressao)


col15, col16 = st.columns(2, border=True)
#Desfecho internação
desfecho_map = {
    1 : "Alta Hospitalar",
    2 : "Evasão",
    3 : "Óbito",
    4 : "Óbito - UTI",
    5 : "Transferência de equipe",
    6 : "Transferência Hospitalar definitiva",
    7 : "Transferência Hospitalar para medicação",
}
internacao['desfecho'] = internacao['desfecho'].replace(desfecho_map)
desfecho_internacao = internacao['desfecho'].value_counts().reset_index()
desfecho_internacao.columns = ['Desfecho', 'Quantidade']
fig_desfecho = px.bar(desfecho_internacao, x='Desfecho', y='Quantidade', text='Quantidade', title='Desfecho Hospitalar')
fig_desfecho.update_traces(textposition='outside')
with col15:
    st.plotly_chart(fig_desfecho, use_container_width=True)

#Correlações
st.header("Média de Tempo de Internação por Causas de Internação")

df = internacao.copy()
df['tempo_dias'] = (df['data_da_alta'] - df['data_da_interna_o']).dt.days
resultado = df.groupby('causa_internacao')['tempo_dias'].mean().reset_index()
resultado.columns = ['Causa da Internação', 'Média de Tempo (dias)']
resultado = resultado.sort_values(by='Média de Tempo (dias)', ascending=False)
st.write(resultado)

#Análise estatística comparando tempo de internação com motivo da internação
from scipy.stats import kruskal
grupos = [
    grupo['tempo_dias'].dropna().values
    for _, grupo in df.groupby('causa_internacao')
]
stat, p = kruskal(*grupos)
st.error(f"Teste de Kuskal comparando tempo de internação e motivo de internação p-valor: {p:.2f}")

#Footer
st.write("Criado por Tiago Henrique")
