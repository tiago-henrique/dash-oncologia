###########################
# internação
###########################

import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import plotly.express as px
import os
import datetime
import requests
import seaborn as sns

from scipy.stats import kruskal


# ============================================================
# CONFIGURAÇÃO DA PÁGINA
# ============================================================

st.set_page_config(layout="wide")


# ============================================================
# CSS
# ============================================================

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
        width: 100%;
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
        display: grid;
        background-color: #FFF;
        border-radius: 5px;
        border-bottom: 10px;
        color: #336799;
        padding: 0.2rem;
    }

    .content{
        grid-template-columns: 1fr 1fr;
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


# ============================================================
# TÍTULO
# ============================================================

st.markdown(
    "<div class='titulo'>Dashboard HB Onco</div>",
    unsafe_allow_html=True
)

st.image("imagem/logo-hbonco.webp")


# ============================================================
# SIDEBAR
# ============================================================

st.sidebar.title("Menu")

st.sidebar.page_link(
    "app.py",
    label="Dados das Admissões"
)

st.sidebar.title("Filtros")

filtrar_data = st.sidebar.radio(
    "Aplicar o filtro de datas",
    ("Sim", "Não"),
    index=None
)

data_inicial = st.sidebar.date_input(
    "Selecione a data inicial"
)

data_final = st.sidebar.date_input(
    "Selecione a data final"
)


# ============================================================
# REDCAP API
# ============================================================

@st.cache_data(ttl=300, show_spinner="Atualizando dados do REDCap...")
def carregar_dados_redcap():

    try:

        api_url = st.secrets["REDCAP_API_URL"]
        api_token = st.secrets["REDCAP_API_TOKEN"]

    except Exception as e:

        st.error(
            "Não foi possível encontrar as credenciais da API do REDCap "
            "nos Secrets do Streamlit."
        )

        st.error(str(e))

        st.stop()


    payload = {
        "token": api_token,
        "content": "record",
        "action": "export",
        "format": "json",
        "type": "flat",
        "rawOrLabel": "raw",
        "rawOrLabelHeaders": "raw",
        "exportCheckboxLabel": "false",
        "exportSurveyFields": "false",
        "exportDataAccessGroups": "true",
        "returnFormat": "json"
    }


    try:

        response = requests.post(
            api_url,
            data=payload,
            timeout=120
        )

        response.raise_for_status()

    except requests.exceptions.RequestException as e:

        st.error(
            f"Erro ao conectar à API do REDCap: {e}"
        )

        st.stop()


    try:

        dados = response.json()

    except ValueError:

        st.error(
            "A API do REDCap não retornou um JSON válido."
        )

        st.code(response.text[:2000])

        st.stop()


    if not isinstance(dados, list):

        st.error(
            "A API do REDCap retornou um formato inesperado."
        )

        st.write(dados)

        st.stop()


    database = pd.DataFrame(dados)

    if database.empty:

        st.warning(
            "A API do REDCap não retornou nenhum registro."
        )

        st.stop()


    return database


# ============================================================
# CARREGAR BANCO DIRETAMENTE DA API
# ============================================================

database = carregar_dados_redcap()


# ============================================================
# GARANTIR COLUNAS NECESSÁRIAS
# ============================================================

colunas_necessarias = [
    "record_id",
    "redcap_repeat_instrument",
    "data_da_interna_o",
    "prontuario_alta",
    "causa_internacao",
    "dob",
    "data_de_nascimento",
    "data_da_alta",
    "estagio_clinico_internacao",
    "tipo_infeccao",
    "manejo_de_sintomas",
    "dispositivos",
    "pd",
    "desfecho",
    "causa_obito"
]


for coluna in colunas_necessarias:

    if coluna not in database.columns:

        database[coluna] = np.nan


# ============================================================
# CONVERSÕES DE DATA
# ============================================================

database["data_da_interna_o"] = pd.to_datetime(
    database["data_da_interna_o"],
    errors="coerce"
)

database["dob"] = pd.to_datetime(
    database["dob"],
    errors="coerce"
)

database["data_de_nascimento"] = pd.to_datetime(
    database["data_de_nascimento"],
    errors="coerce"
)

database["data_da_alta"] = pd.to_datetime(
    database["data_da_alta"],
    errors="coerce"
)


# ============================================================
# REMOVER DATAS INVÁLIDAS
# ============================================================

database = database.dropna(
    subset=["data_da_interna_o"]
).copy()


# ============================================================
# FILTRO DE INTERNAÇÕES
# ============================================================

if filtrar_data == "Não" or not filtrar_data:

    internacao = database[
        database["redcap_repeat_instrument"] == "internao"
    ].copy()

else:

    if data_inicial > data_final:

        st.error(
            "A data inicial não pode ser maior que a final"
        )

        st.stop()


    data_inicial = pd.to_datetime(
        data_inicial
    )

    data_final = (
        pd.to_datetime(data_final)
        + pd.Timedelta(days=1)
    )


    internacao = database[
        (database["redcap_repeat_instrument"] == "internao")
        &
        (database["data_da_interna_o"] >= data_inicial)
        &
        (database["data_da_interna_o"] < data_final)
    ].copy()


# ============================================================
# TOTAL DE INTERNAÇÕES
# ============================================================

total_internacoes = internacao.shape[0]

st.markdown(
    f"""
    <div class='total-internacao'>
        <p>Total de Internações: {total_internacoes}</p>
    </div>
    """,
    unsafe_allow_html=True
)


# ============================================================
# MAPAS
# ============================================================

estagio_map = {
    1: "Estágio I",
    2: "Estágio II",
    3: "Estágio III",
    4: "Estágio IV",
    5: "NA"
}


causa_internacao_map = {
    29: "Progressão de doença",
    30: "Infecções",
    31: "Toxicidade do tratamento",
    32: "Manejo/instalação de dispositivos",
    41: "Manejo de sintomas",
    33: "Ablação hepática",
    34: "Eventos trombóticos (TVP, TEP, AVC)",
    35: "Eventos hemorrágicos (tumorais ou não)",
    36: "Disfunção renal",
    37: "Alterações endócrinas",
    38: "Biopsia",
    39: "Estadiamento",
    40: "Fase Final de Vida"
}


infeccao_map = {
    1: "Infecção urinária",
    2: "Pneumonia",
    3: "Infecção sitio tumoral",
    4: "Celulite",
    5: "Infecção em outras partes",
    6: "Síndrome Gripal / Influenza / Covid",
    7: "Dengue",
    8: "Diarréia/Colite",
    9: "Colangite"
}


manejo_map = {
    1: "Dor",
    2: "Dispneia",
    3: "Náusea e Vómitos",
    4: "Constipação"
}


dispositivos_map = {
    1: "Gastrostomia",
    2: "SNE",
    3: "Port-a-cath",
    4: "Dj/Nefrostomia",
    5: "Traqueostomia",
    6: "Protese Biliar",
    7: "Outro dispositivo"
}


pd_map = {
    1: "Hipercalcemia da Malignidade",
    2: "Insuficiencia Renal",
    3: "Síndrome colestática",
    4: "Obstrução / Pseudo-obstrução maligna (gástrica/intestinal)",
    5: "Compressão Medular",
    6: "Síndrome Veia Cava",
    7: "Urgência quimioterápica",
    8: "PD em SNC",
    10: "Insuficiência hepática",
    11: "Sd. Lise tumoral",
    12: "Progressão de doença"
}


desfecho_map = {
    1: "Alta Hospitalar",
    2: "Evasão",
    3: "Óbito",
    4: "Óbito - UTI",
    5: "Transferência de equipe",
    6: "Transferência Hospitalar definitiva",
    7: "Transferência Hospitalar para medicação"
}


obito_map = {
    1: "Complicações clínicas",
    2: "Complicações do tratamento",
    3: "Evolução de doença neoplásica"
}


# ============================================================
# APLICAR MAPAS
# ============================================================

internacao["causa_internacao"] = (
    pd.to_numeric(
        internacao["causa_internacao"],
        errors="coerce"
    )
    .map(causa_internacao_map)
)


internacao["estagio_clinico_internacao"] = (
    pd.to_numeric(
        internacao["estagio_clinico_internacao"],
        errors="coerce"
    )
    .map(estagio_map)
)


internacao["tipo_infeccao"] = (
    pd.to_numeric(
        internacao["tipo_infeccao"],
        errors="coerce"
    )
    .map(infeccao_map)
)


internacao["manejo_de_sintomas"] = (
    pd.to_numeric(
        internacao["manejo_de_sintomas"],
        errors="coerce"
    )
    .map(manejo_map)
)


internacao["dispositivos"] = (
    pd.to_numeric(
        internacao["dispositivos"],
        errors="coerce"
    )
    .map(dispositivos_map)
)


internacao["pd"] = (
    pd.to_numeric(
        internacao["pd"],
        errors="coerce"
    )
    .map(pd_map)
)


internacao["desfecho"] = (
    pd.to_numeric(
        internacao["desfecho"],
        errors="coerce"
    )
    .map(desfecho_map)
)


internacao["causa_obito"] = (
    pd.to_numeric(
        internacao["causa_obito"],
        errors="coerce"
    )
    .map(obito_map)
)


# ============================================================
# TEMPO DE INTERNAÇÃO
# ============================================================

internacao["tempo_internacao"] = (
    internacao["data_da_alta"]
    -
    internacao["data_da_interna_o"]
)

internacao["dias_internacao"] = (
    internacao["tempo_internacao"]
    .dt.days
)


# ============================================================
# DADOS DE INTERNAÇÃO
# ============================================================

st.header("Dados de Internação")


conta_internacoes = (
    internacao
    .groupby("record_id")["prontuario_alta"]
    .value_counts()
    .reset_index(
        name="Total de Internações"
    )
)


conta_internacoes = conta_internacoes.sort_values(
    by="Total de Internações",
    ascending=False
)


conta_internacoes.columns = [
    "Record ID",
    "Prontuário",
    "Total de Internações"
]


st.write(conta_internacoes)


# ============================================================
# PESQUISA DE PACIENTE
# ============================================================

col1, col2 = st.columns(
    2,
    border=True
)


with col1:

    paciente = st.text_input(
        "Digite o ID do paciente para visualizar os motivos das internações"
    )


if paciente:

    try:

        paciente = int(paciente)

        causas_paciente = internacao[
            internacao["record_id"].astype(str) == str(paciente)
        ][
            [
                "causa_internacao",
                "dias_internacao"
            ]
        ]


        if not causas_paciente.empty:

            causas_paciente = causas_paciente.copy()

            causas_paciente.columns = [
                "Motivo",
                "Dias de Internação"
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

                st.error(
                    "Paciente não encontrado"
                )


    except ValueError:

        with col2:

            st.error(
                "ID deve ser numérico"
            )


# ============================================================
# DISTRIBUIÇÃO POR IDADE
# ============================================================

idade = (
    internacao["data_da_interna_o"]
    -
    internacao["dob"]
)


idade_anos = (
    idade.dt.days // 365
)


idade_counts = (
    idade_anos
    .value_counts()
    .sort_index()
)


idade_internacoes = (
    idade_counts
    .reset_index()
)


idade_internacoes.columns = [
    "Idade",
    "Quantidade"
]


bins = [
    15,
    20,
    30,
    40,
    50,
    60,
    70,
    80,
    100
]


labels = [
    "16-19",
    "20-29",
    "30-39",
    "40-49",
    "50-59",
    "60-69",
    "70-79",
    "80+"
]


idade_internacoes["faixa_etaria"] = pd.cut(
    idade_internacoes["Idade"],
    bins=bins,
    labels=labels,
    right=False
)


idade_internacoes = (
    idade_internacoes
    .groupby(
        "faixa_etaria",
        observed=False
    )["Quantidade"]
    .sum()
    .reset_index()
)


fig_idade_internacoes = px.bar(
    idade_internacoes,
    x="faixa_etaria",
    y="Quantidade",
    text="Quantidade",
    title="Distribuição por Faixa Etária (Internações)"
)


fig_idade_internacoes.update_traces(
    textposition="outside"
)


fig_idade_internacoes.update_layout(
    uniformtext_minsize=8,
    uniformtext_mode="hide"
)


# ============================================================
# GRÁFICOS IDADE / DIAS
# ============================================================

col3, col4 = st.columns(
    2,
    border=True
)


with col3:

    st.plotly_chart(
        fig_idade_internacoes,
        use_container_width=True
    )


dias_counts_1 = (
    internacao["dias_internacao"]
    .value_counts()
)


din = (
    dias_counts_1
    .reset_index()
)


din.columns = [
    "Dias",
    "Quantidade"
]


fig_din = px.bar(
    din,
    x="Dias",
    y="Quantidade",
    text="Quantidade",
    title="Dias de Internação"
)


fig_din.update_traces(
    textposition="inside",
    width=0.7
)


fig_din.update_layout(
    bargap=0.2
)


with col4:

    st.plotly_chart(
        fig_din,
        use_container_width=True
    )


# ============================================================
# MÉDIA DE DIAS
# ============================================================

media_dias_internacao = (
    internacao["dias_internacao"]
    .mean()
)


if pd.notna(media_dias_internacao):

    st.info(
        f"Média de dias de internação: "
        f"{media_dias_internacao:.0f} dias"
    )


# ============================================================
# ESTÁGIO CLÍNICO / INFECÇÃO
# ============================================================

col5, col6 = st.columns(
    2,
    border=True
)


eci = (
    internacao["estagio_clinico_internacao"]
    .value_counts()
    .reset_index()
)


eci.columns = [
    "Estágio",
    "Quantidade"
]


fig_eci = px.bar(
    eci,
    x="Estágio",
    y="Quantidade",
    text="Quantidade",
    title="Estágio Clínico"
)


fig_eci.update_traces(
    textposition="outside"
)


with col5:

    st.plotly_chart(
        fig_eci,
        use_container_width=True
    )


tipo_infeccao = (
    internacao["tipo_infeccao"]
    .value_counts()
    .reset_index()
)


tipo_infeccao.columns = [
    "Tipo de Infecção",
    "Quantidade"
]


fig_tipo_infeccao = px.bar(
    tipo_infeccao,
    x="Tipo de Infecção",
    y="Quantidade",
    text="Quantidade",
    title="Tipo de Infecção"
)


fig_tipo_infeccao.update_traces(
    textposition="outside"
)


with col6:

    st.plotly_chart(
        fig_tipo_infeccao,
        use_container_width=True
    )


# ============================================================
# GRÁFICO CLICÁVEL - MANEJO
# ============================================================

tipo_manejo = (
    internacao["manejo_de_sintomas"]
    .value_counts()
    .reset_index()
)


tipo_manejo.columns = [
    "Tipo de Manejo",
    "Quantidade"
]


fig_clicavel = px.bar(
    tipo_manejo,
    x="Tipo de Manejo",
    y="Quantidade"
)


col7, col8 = st.columns(
    2,
    border=True
)


with col7:

    st.plotly_chart(
        fig_clicavel,
        on_select="rerun",
        key="meu_grafico",
        use_container_width=True
    )


with col8:

    selecao = st.session_state.get(
        "meu_grafico"
    )


    if (
        selecao
        and "selection" in selecao
        and "points" in selecao["selection"]
        and len(selecao["selection"]["points"]) > 0
    ):

        ponto = selecao["selection"]["points"][0]

        tipo_selecionado = ponto["x"]


        dados_filtrados = internacao[
            internacao["manejo_de_sintomas"]
            ==
            tipo_selecionado
        ][
            [
                "record_id",
                "prontuario_alta",
                "dias_internacao"
            ]
        ].copy()


        dados_filtrados.columns = [
            "Record ID",
            "Prontuário",
            "Dias de Internação"
        ]


        dados_filtrados = (
            dados_filtrados
            .sort_values(
                by="Dias de Internação",
                ascending=False
            )
        )


        st.header(
            f"Tipo de Manejo Selecionado: "
            f"{tipo_selecionado}"
        )


        st.dataframe(
            dados_filtrados,
            use_container_width=True
        )


        media_dias = (
            dados_filtrados[
                "Dias de Internação"
            ].mean()
        )


        if pd.notna(media_dias):

            media_dias = round(
                media_dias,
                0
            )


            st.success(
                f"Média de dias de internação: "
                f"{media_dias:.0f} dias"
            )

    else:

        st.info(
            "Nenhuma barra selecionada."
        )


# ============================================================
# GRÁFICO CLICÁVEL - DISPOSITIVOS
# ============================================================

dispositivo = (
    internacao["dispositivos"]
    .value_counts()
    .reset_index()
)


dispositivo.columns = [
    "Tipo de Dispositivo",
    "Quantidade"
]


fig_clicavel_dispositivo = px.bar(
    dispositivo,
    x="Tipo de Dispositivo",
    y="Quantidade"
)


col9, col10 = st.columns(
    2,
    border=True
)


with col9:

    st.plotly_chart(
        fig_clicavel_dispositivo,
        on_select="rerun",
        key="meu_grafico_dispositivo",
        use_container_width=True
    )


with col10:

    selecao_dispositivo = (
        st.session_state.get(
            "meu_grafico_dispositivo"
        )
    )


    if (
        selecao_dispositivo
        and "selection" in selecao_dispositivo
        and "points" in selecao_dispositivo["selection"]
        and len(
            selecao_dispositivo["selection"]["points"]
        ) > 0
    ):

        ponto_dispositivo = (
            selecao_dispositivo["selection"]["points"][0]
        )


        tipo_selecionado_dispositivo = (
            ponto_dispositivo["x"]
        )


        dados_filtrados_dispositivo = internacao[
            internacao["dispositivos"]
            ==
            tipo_selecionado_dispositivo
        ][
            [
                "record_id",
                "prontuario_alta",
                "dias_internacao"
            ]
        ].copy()


        dados_filtrados_dispositivo.columns = [
            "Record ID",
            "Prontuário",
            "Dias de Internação"
        ]


        dados_filtrados_dispositivo = (
            dados_filtrados_dispositivo
            .sort_values(
                by="Dias de Internação",
                ascending=False
            )
        )


        st.header(
            "Tipo de dispositivo selecionado: "
            f"{tipo_selecionado_dispositivo}"
        )


        st.dataframe(
            dados_filtrados_dispositivo,
            use_container_width=True
        )


        media_dias_dispositivo = (
            dados_filtrados_dispositivo[
                "Dias de Internação"
            ].mean()
        )


        if pd.notna(media_dias_dispositivo):

            media_dias_dispositivo = round(
                media_dias_dispositivo,
                0
            )


            st.success(
                f"Média de dias de internação: "
                f"{media_dias_dispositivo:.0f} dias"
            )

    else:

        st.info(
            "Nenhuma barra selecionada."
        )


# ============================================================
# PROGRESSÃO DA DOENÇA
# ============================================================

progressao_doenca = (
    internacao["pd"]
    .value_counts()
    .reset_index()
)


progressao_doenca.columns = [
    "Progressão",
    "Quantidade"
]


fig_progressao = px.bar(
    progressao_doenca,
    x="Progressão",
    y="Quantidade",
    text="Quantidade",
    title="Progressão da Doença"
)


fig_progressao.update_traces(
    textposition="outside"
)


col11, col12 = st.columns(
    2,
    border=True
)


with col11:

    st.plotly_chart(
        fig_progressao,
        use_container_width=True
    )


# ============================================================
# DESFECHO DA INTERNAÇÃO
# ============================================================

desfecho_internacao = (
    internacao["desfecho"]
    .value_counts()
    .reset_index()
)


desfecho_internacao.columns = [
    "Desfecho",
    "Quantidade"
]


fig_desfecho = px.bar(
    desfecho_internacao,
    x="Desfecho",
    y="Quantidade",
    text="Quantidade",
    title="Desfecho Hospitalar"
)


fig_desfecho.update_traces(
    textposition="outside"
)


with col12:

    st.plotly_chart(
        fig_desfecho,
        use_container_width=True
    )


# ============================================================
# CAUSA DO ÓBITO
# ============================================================

causa_obito = (
    internacao["causa_obito"]
    .value_counts()
    .reset_index()
)


causa_obito.columns = [
    "Causa do óbito",
    "Quantidade"
]


fig_causa_obito = px.bar(
    causa_obito,
    x="Causa do óbito",
    y="Quantidade",
    text="Quantidade",
    title="Causa do Óbito"
)


fig_causa_obito.update_traces(
    textposition="outside"
)


col13, col14 = st.columns(
    2,
    border=True
)


with col13:

    st.plotly_chart(
        fig_causa_obito,
        use_container_width=True
    )


# ============================================================
# MÉDIA DE TEMPO DE INTERNAÇÃO POR CAUSA
# ============================================================

st.header(
    "Média de Tempo de Internação por Causas de Internação"
)


df = internacao.copy()


df["tempo_dias"] = (
    df["data_da_alta"]
    -
    df["data_da_interna_o"]
).dt.days


resultado = (
    df
    .groupby(
        "causa_internacao"
    )["tempo_dias"]
    .mean()
    .reset_index()
)


resultado.columns = [
    "Causa da Internação",
    "Média de Tempo (dias)"
]


resultado = (
    resultado
    .sort_values(
        by="Média de Tempo (dias)",
        ascending=False
    )
)


resultado["Média de Tempo (dias)"] = (
    resultado["Média de Tempo (dias)"]
    .round(0)
)


st.write(resultado)


# ============================================================
# TESTE DE KRUSKAL-WALLIS
# ============================================================

grupos = [
    grupo["tempo_dias"]
    .dropna()
    .values
    for _, grupo
    in df.groupby(
        "causa_internacao",
        dropna=True
    )
    if len(
        grupo["tempo_dias"].dropna()
    ) > 0
]


if len(grupos) >= 2:

    try:

        stat, p = kruskal(
            *grupos
        )


        st.error(
            "Teste de Kruskal-Wallis comparando "
            "tempo de internação e motivo de internação "
            f"p-valor: {p:.2f}"
        )

    except Exception as e:

        st.warning(
            f"Não foi possível realizar o teste estatístico: {e}"
        )

else:

    st.warning(
        "Não há grupos suficientes para realizar "
        "o teste de Kruskal-Wallis."
    )


# ============================================================
# CAUSAS DE ÓBITO
# ============================================================

obitos = internacao[
    (internacao["desfecho"] == "Óbito")
    |
    (internacao["desfecho"] == "Óbito - UTI")
].copy()


st.header(
    "Motivo da Internação / Causa do Óbito"
)


motivo_internacao = obitos[
    [
        "record_id",
        "prontuario_alta",
        "causa_internacao",
        "causa_obito"
    ]
].copy()


motivo_internacao.columns = [
    "Record Id",
    "Prontuário",
    "Causa da Internação",
    "Causa do óbito"
]


st.write(
    motivo_internacao
)


# ============================================================
# INFORMAÇÃO DA FONTE
# ============================================================

st.caption(
    "Dados obtidos diretamente da API do REDCap."
)


# ============================================================
# FOOTER
# ============================================================

st.write(
    "Desenvolvido por Tiago Henrique - 2026"
)
