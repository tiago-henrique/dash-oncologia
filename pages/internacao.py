###########################
#internação

import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import plotly.express as px
import os
import datetime
import requests
import seaborn as sns

st.markdown("""
    <style>
        [data-testid="stSidebarNav"] {
            display: none;
        }
    </style>
""", unsafe_allow_html=True)

st.markdown("""
<style>
    /* Estilo para links personalizados */
    div.stPageLink a {
        background-color: #fff;
        color: white;
        padding: 5px;
        border-radius: 5px;
        text-decoration: none;
        border: 0px solid #d3d3d3;
        transition: all 0.3s ease;
    }
    
    /* Efeito ao passar o mouse */
    div.stPageLink a:hover {
        background-color: #fff;
        color: white;
        border-color: #fff;
    }
</style>
""", unsafe_allow_html=True)

st.image("imagem/logo-hbonco.webp")
st.sidebar.title("Menu")
st.sidebar.page_link("app.py", label="Dados das Admissões")
st.sidebar.title("Filtros")

filtrar_data = st.sidebar.radio("Aplicar o filtro de datas", ("Sim", "Não"), index=None)

# Inputs de data
data_inicial = st.sidebar.date_input('Selecione a data inicial')
data_final = st.sidebar.date_input('Selecione a data final')

# Caminho e metadata
file_path = st.secrets["CAMINHO"]
response = requests.head(file_path)
last_modified = response.headers.get("Last-Modified")

# Carregar base
try:
    database = pd.read_csv(st.secrets['DATABASE'])
except Exception as e:
    st.error(f"Erro ao carregar o banco de dados: {e}")
    st.stop()

database['data_da_interna_o'] = pd.to_datetime(
    database['data_da_interna_o'],
    errors='coerce'
)

# Remover datas inválidas
database = database.dropna(subset=['data_da_interna_o'])

# Aplicar filtros
if filtrar_data == "Não" or not filtrar_data:
    internacao = database[
        database['redcap_repeat_instrument'] == 'internao'
    ]
    total_internacoes = internacao.shape[0]
    st.write(f"Total de internações: {total_internacoes}")
else:
    if data_inicial > data_final:
        st.error("A data inicial não pode ser maior que a final")
        st.stop()

    # Converter datas de input
    data_inicial = pd.to_datetime(data_inicial)
    data_final = pd.to_datetime(data_final) + pd.Timedelta(days=1)

    internacao = database[
        (database['redcap_repeat_instrument'] == 'internao') &
        (database['data_da_interna_o'] >= data_inicial) &
        (database['data_da_interna_o'] < data_final)
    ]
    total_internacoes = internacao.shape[0]
    st.write(f"Total de Internações: {total_internacoes}")

estagio_map = {
    1 : 'Estágio I',
    2 : 'Estágio II',
    3 : 'Estágio III',
    4 : 'Estágio IV',
    5 : 'NA'
}
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
internacao['causa_internacao'] = database['causa_internacao'].map(causa_internacao_map)
st.header("Dados de Internação")

conta_internacao = (
    internacao['record_id']
    .value_counts()
    .rename_axis('Id. Paciente')
    .reset_index(name='Total de Internações')
)
st.write(conta_internacao)

col20, col21 = st.columns(2, border=True)
with col20:
    paciente = st.text_input("Digite o ID do paciente para visualizar os motivos das internações")
if paciente:
    try:
        paciente = int(paciente)
        causas_paciente = internacao[internacao['record_id'] == paciente]['causa_internacao'].reset_index()
        if not causas_paciente.empty:
            with col21:
                causas_paciente.columns = ['Registro', 'Motivo']
                st.subheader(f"Motivos da internação - Paciente {paciente}")
                st.write(causas_paciente.value_counts())
        else:
            with col21:
                st.error("Paciente não encontrado")
    except:
        with col21:
            st.error("ID deve ser numérico")

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

col5, col6 = st.columns(2, border=True)
with col5:
    st.plotly_chart(fig_idade_internacoes, use_container_width=True)
    
#Calcular tempo de internação
tempo_internacao = internacao['data_da_alta'] - internacao['data_da_interna_o']
dias_internacao = tempo_internacao.dt.days
dias_counts = dias_internacao.value_counts()
dias_counts = dias_counts.sort_values(ascending=False)

teste = (dias_internacao).sort_values().reset_index()
teste.columns = ['Id do Paciente', 'Dias Internado']
st.write(teste)

din = dias_counts.reset_index()
din.columns = ['Dias', 'Quantidade']
fig_din = px.bar(din, x='Dias', y='Quantidade', text='Quantidade', title='Dias de Internação')
fig_din.update_traces(textposition='inside')
with col6:
    st.plotly_chart(fig_din, use_container_width=True)

media_dias_internacao = dias_internacao.mean()
st.info(f'Média de dias de internação: {media_dias_internacao:.2f} dias')

col9, col10 = st.columns(2, border=True)
internacao['estagio_clinico_internacao'] = internacao['estagio_clinico_internacao'].map(estagio_map)
eci = internacao['estagio_clinico_internacao'].value_counts().reset_index()
eci.columns = ['Estágio', 'Quantidade']
fig_eci = px.bar(eci, x='Estágio', y='Quantidade', text='Quantidade', title='Estágio Clínico')
fig_eci.update_traces(textposition='outside')
with col9:
    st.plotly_chart(fig_eci)

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


obito_map = {
    1 : "Complicações clínicas",
    2 : "Complicações do tratamento",
    3 : "Evolução de doença neoplásica",
}

internacao['causa_obito'] = internacao['causa_obito'].replace(obito_map)
causa_obito = internacao['causa_obito'].value_counts().reset_index()
causa_obito.columns = ['Causa do óbito', 'Quantidade']
fig_causa_obito = px.bar(causa_obito, x='Causa do óbito', y='Quantidade', text='Quantidade', title='Causa do Óbito')
fig_causa_obito.update_traces(textposition='outside')
with col16:
    st.plotly_chart(fig_causa_obito, width='stretch')

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
