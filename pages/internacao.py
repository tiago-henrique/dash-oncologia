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

st.set_page_config(layout="wide")
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

st.markdown(f"<div class='titulo'>Dashboard HB Onco</div>", unsafe_allow_html=True)
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

#file_path = st.secrets["CAMINHO"]

#response = requests.head(file_path)
#last_modified = response.headers.get("Last-Modified")

#if last_modified:
#    dt_utc = parsedate_to_datetime(last_modified)
#    dt_br = dt_utc.astimezone(ZoneInfo("America/Sao_Paulo"))

#    st.success(
#        f"Dados atualizados em: {dt_br.strftime('%d/%m/%Y %H:%M:%S')}"
#    )
#else:
#    st.warning("Cabeçalho Last-Modified não encontrado.")

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
    st.markdown(f"<div class='total-internacao'><p>Total de Internações: {total_internacoes}</div>", unsafe_allow_html=True)
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
    st.markdown(f"<div class='total-internacao'><p>Total de Internações: {total_internacoes}</div>", unsafe_allow_html=True)

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

conta_internacoes = (
    internacao
    .groupby('record_id')['prontuario_alta']
    .value_counts()
    .reset_index(name='Total de Internações')
)

conta_internacoes = conta_internacoes.sort_values(
    by='Total de Internações',
    ascending=False
)

conta_internacoes.columns = [
    'Record ID',
    'Prontuário',
    'Total de Internações'
]

st.write(conta_internacoes)

internacao['dob'] = pd.to_datetime(internacao['dob'], errors='coerce')
internacao['data_de_nascimento'] = pd.to_datetime(internacao['data_de_nascimento'], errors='coerce')
internacao['data_da_interna_o'] = pd.to_datetime(internacao['data_da_interna_o'], errors='coerce')
internacao['data_da_alta'] = pd.to_datetime(internacao['data_da_alta'], errors='coerce')
tempo_internacao = internacao['data_da_alta'] - internacao['data_da_interna_o']
dias_internacao = tempo_internacao.dt.days
dias_counts = dias_internacao.value_counts()
dias_counts = dias_counts.sort_values(ascending=False)

col1, col2 = st.columns(2, border=True)
with col1:
    paciente = st.text_input("Digite o ID do paciente para visualizar os motivos das internações")
if paciente:
    try:
        paciente = int(paciente)
        causas_paciente = internacao[
            internacao['record_id'] == paciente
        ][['causa_internacao', 'dias_internacao']]
        if not causas_paciente.empty:
            causas_paciente.columns = [
                'Motivo',
                'Dias de Internação'
            ]
            with col2:
                st.subheader(
                    f"Motivos da internação - Paciente {paciente}"
                )

                st.dataframe(
                    causas_paciente,
                    use_container_width=True
                )
        else:
            with col2:
                st.error("Paciente não encontrado")
    except ValueError:
        with col2:
            st.error("ID deve ser numérico")

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

col3, col4 = st.columns(2, border=True)
with col3:
    st.plotly_chart(fig_idade_internacoes, use_container_width=True)
    
#Gráfico
dias_counts_1 = internacao['dias_internacao'].value_counts()
din = dias_counts_1.reset_index()
din.columns = ['Dias', 'Quantidade']
fig_din = px.bar(din, x='Dias', y='Quantidade', text='Quantidade', title='Dias de Internação')
fig_din.update_traces(textposition='inside', width=0.7)
fig_din.update_layout(bargap=0.2)

with col4:
    st.plotly_chart(fig_din, use_container_width=True)

media_dias_internacao = dias_internacao.mean()
st.info(f'Média de dias de internação: {media_dias_internacao:.0f} dias')

col5, col6 = st.columns(2, border=True)

internacao['estagio_clinico_internacao'] = internacao['estagio_clinico_internacao'].map(estagio_map)
eci = internacao['estagio_clinico_internacao'].value_counts().reset_index()
eci.columns = ['Estágio', 'Quantidade']
fig_eci = px.bar(eci, x='Estágio', y='Quantidade', text='Quantidade', title='Estágio Clínico')
fig_eci.update_traces(textposition='outside')
with col5:
    st.plotly_chart(fig_eci)

causa_internacao = internacao['causa_internacao'].value_counts().reset_index()
causa_internacao.columns = ['Causa', 'Quantidade']
fig_causa_internacao = px.bar(causa_internacao, x='Causa', y='Quantidade', text='Quantidade', title='Causas de Internação')
fig_causa_internacao.update_traces(textposition='outside')
#with col10:
    #st.plotly_chart(fig_causa_internacao, use_container_width=True)

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
tipo_infeccao = internacao['tipo_infeccao'].value_counts().reset_index()
tipo_infeccao.columns = ['Tipo de Infecção', 'Quantidade']
fig_tipo_infeccao = px.bar(tipo_infeccao, x='Tipo de Infecção', y='Quantidade', text='Quantidade', title='Tipo de Infecção')
fig_tipo_infeccao.update_traces(textposition='outside')
with col6:
    st.plotly_chart(fig_tipo_infeccao)

manejo_map = {
    1 : "Dor",
    2 : "Dispneia",
    3 : "Náusea e Vómitos",
    4 : "Constipação"
}

# #Tipo de manejo
    # manejo_sintomas = internacao['manejo_de_sintomas'].value_counts().reset_index()
    # manejo_sintomas.columns = ['Tipo de Manejo', 'Quantidade']
    # fig_manejo_sintomas = px.bar(manejo_sintomas, x='Tipo de Manejo', y='Quantidade', text='Quantidade', title='Tipo de Manejo')
    # fig_manejo_sintomas.update_traces(textposition='outside')
# with col12:
#     st.plotly_chart(fig_manejo_sintomas, use_container_width=True)

##Início gráfico clicável
internacao['manejo_de_sintomas'] = internacao['manejo_de_sintomas'].map(manejo_map)
# internacao['dias_internacao'] = dias_internacao

# Contagem dos tipos de manejo
tipo_manejo = (
    internacao['manejo_de_sintomas']
    .value_counts()
    .reset_index()
)

tipo_manejo.columns = ['Tipo de Manejo', 'Quantidade']

# Gráfico
fig_clicavel = px.bar(
    tipo_manejo,
    x='Tipo de Manejo',
    y='Quantidade'
)
col7, col8 = st.columns(2, border=True)

with col7:
    evento = st.plotly_chart(
        fig_clicavel,
        on_select="rerun",
        key="meu_grafico",
        use_container_width=True
    )

# Captura seleção
with col8:
    selecao = st.session_state.get("meu_grafico")
    if (
        selecao
        and "selection" in selecao
        and "points" in selecao["selection"]
        and len(selecao["selection"]["points"]) > 0
    ):
        ponto = selecao["selection"]["points"][0]
        # Nome da barra clicada
        tipo_selecionado = ponto["x"]
        # Filtrar pacientes daquele tipo
        dados_filtrados = internacao[
            internacao['manejo_de_sintomas'] == tipo_selecionado
        ][[
            'record_id',
            'prontuario_alta',
            'dias_internacao'
        ]]
    
        dados_filtrados.columns = ['Record ID','Prontuário','Dias de Internação']
        
        dados_filtrados = dados_filtrados.sort_values(by='Dias de Internação', ascending=False)
        st.header(f"Tipo de Manejo Selecionado: {tipo_selecionado}")

        st.dataframe(dados_filtrados)
        # Quantidade de internações
        tamanho_internacao = len(dados_filtrados)
        #st.write("Quantidade de pacientes:", tamanho_internacao)
        # Estatísticas dos dias internados
        media_dias = dados_filtrados['Dias de Internação'].mean()
        media_dias = round(media_dias, 0)
        st.success(f"Média de dias de internação: {media_dias} dias")
        #st.markdown(f'<div class="media_dias"><div class="content"><h1>Quantidade de Pacientes</h1><p>{tamanho_internacao}</p><h1>Média de dias internados<h1><p>{media_dias}</p></div></div>', unsafe_allow_html=True)
    else:
        st.info("Nenhuma barra selecionada.")
##Término gráfico clicável

dispositivos_map = {
    1 : "Gastrostomia",
	2 : "SNE",
	3 : "Port-a-cath",
	4 : "Dj/Nefrostomia",
	5 : "Traqueostomia",
	6 : "Protese Biliar",
	7 : "Outro dispositivo"
}
#Inpicio clicavel dispositivo
internacao['dispositivos'] = internacao['dispositivos'].replace(dispositivos_map)
dispositivo = (
    internacao['dispositivos']
    .value_counts()
    .reset_index()
)
dispositivo.columns = ['Tipo de Dispositivo', 'Quantidade']
# Gráfico
fig_clicavel_dispositivo = px.bar(
    dispositivo,
    x='Tipo de Dispositivo',
    y='Quantidade'
)

col9, col10 = st.columns(2, border=True)

with col9:
    evento_dispositivo = st.plotly_chart(
        fig_clicavel_dispositivo,
        on_select="rerun",
        key="meu_grafico_dispositivo",
        use_container_width=True
    )

# Captura seleção
with col10:
    selecao_dispositivo = st.session_state.get("meu_grafico_dispositivo")
    if (
        selecao_dispositivo
        and "selection" in selecao_dispositivo
        and "points" in selecao_dispositivo["selection"]
        and len(selecao_dispositivo["selection"]["points"]) > 0
    ):
        ponto_dispositivo = selecao_dispositivo["selection"]["points"][0]
        # Nome da barra clicada
        tipo_selecionado_dispositivo = ponto_dispositivo["x"]
        # Filtrar pacientes daquele tipo
        dados_filtrados_dispositivo = internacao[
            internacao['dispositivos'] == tipo_selecionado_dispositivo
        ][[
            'record_id',
            'prontuario_alta',
            'dias_internacao'
        ]]
    
        dados_filtrados_dispositivo.columns = ['Record ID','Prontuário','Dias de Internação']
        
        dados_filtrados_dispositivo = dados_filtrados_dispositivo.sort_values(by='Dias de Internação', ascending=False)
        st.header(f"Tipo de dispositivo selecionado: {tipo_selecionado_dispositivo}")

        st.dataframe(dados_filtrados_dispositivo)
        # Quantidade de internações
        tamanho_internacao_dispositivo = len(dados_filtrados_dispositivo)
        #st.write("Quantidade de pacientes:", tamanho_internacao)
        # Estatísticas dos dias internados
        media_dias_dispositivo = dados_filtrados_dispositivo['Dias de Internação'].mean()
        media_dias_dispositivo = round(media_dias_dispositivo, 0)
        st.success(f"Média de dias de internação: {media_dias_dispositivo} dias")
        #st.markdown(f'<div class="media_dias"><div class="content"><h1>Quantidade de Pacientes</h1><p>{tamanho_internacao}</p><h1>Média de dias internados<h1><p>{media_dias}</p></div></div>', unsafe_allow_html=True)
    else:
        st.info("Nenhuma barra selecionada.")

#Fim clicavel dispositivo
# internacao['dispositivos'] = internacao['dispositivos'].map(dispositivos_map)
# dispositivos = internacao['dispositivos'].value_counts().reset_index()
# dispositivos.columns = ['Dispositivo', 'Quantidade']
# fig_dispositivo = px.bar(dispositivos, x='Dispositivo', y='Quantidade', text='Quantidade', title='Tipo de Dispositivo')
# fig_dispositivo.update_traces(textposition='outside')
#with col13:
#    st.plotly_chart(fig_dispositivo)

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

col11, col12 = st.columns(2, border=True)

with col11:
    st.plotly_chart(fig_progressao)

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
with col12:
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

col13, col14 = st.columns(2, border=True)
with col13:
    st.plotly_chart(fig_causa_obito, width='stretch')

#Correlações
st.header("Média de Tempo de Internação por Causas de Internação")

df = internacao.copy()
df['tempo_dias'] = (df['data_da_alta'] - df['data_da_interna_o']).dt.days
resultado = df.groupby('causa_internacao')['tempo_dias'].mean().reset_index()
resultado.columns = ['Causa da Internação', 'Média de Tempo (dias)']
resultado = resultado.sort_values(by='Média de Tempo (dias)', ascending=False)
resultado = round(resultado,0)
st.write(resultado)

#Análise estatística comparando tempo de internação com motivo da internação
from scipy.stats import kruskal
grupos = [
    grupo['tempo_dias'].dropna().values
    for _, grupo in df.groupby('causa_internacao')
]
stat, p = kruskal(*grupos)
st.error(f"Teste de Kuskal comparando tempo de internação e motivo de internação p-valor: {p:.2f}")

#Causas de óbito
obitos = internacao[(internacao['desfecho'] == 'Óbito') | (internacao['desfecho'] == 'Óbito - UTI')]

st.header("Motivo da Internação / Causa do Óbito")
motivo_internacao = obitos[['record_id','prontuario_alta','causa_internacao','causa_obito']]
motivo_internacao.columns = ['Record Id','Prontuário', 'Causa da Internação','Causa do óbito']
st.write(motivo_internacao)
#Footer
st.write("Desenvolvido por Tiago Henrique - 2026")

# * Média de reinternações 
# * Inserir prontuário na primeira planilha "Dados da internação"
