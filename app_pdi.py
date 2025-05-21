import yaml
from yaml.loader import SafeLoader
import streamlit_authenticator as stauth
import streamlit as st
import pandas as pd
import gspread
from google.oauth2 import service_account
from google.oauth2.service_account import Credentials

from sheets_api import get_dropdown_options, append_row_to_sheet
from datetime import date
from datetime import datetime

st.set_page_config(
    page_title="Diário de PDI",
    page_icon="📕",  # You can use any emoji or a custom image URL
    layout="wide"    # Optional: makes the layout use full width
)

with open('config.yaml') as file:
    config = yaml.load(file, Loader=SafeLoader)

authenticator = stauth.Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days']
)

name, auth_status, username = authenticator.login(
    location='main',
    fields={
        'Form name': 'Login',
        'Username': 'Usuário',
        'Password': 'Senha',
        'Login': 'Entrar'
    }
)

if auth_status:
    authenticator.logout('Logout', 'main')
    st.sidebar.write(f"*Bem-vindo, {name}*")

    page = st.sidebar.radio("Navegar para:", ["Registrar Treino", "Visualizar Registros"])
    if page == "Registrar Treino":


        ####🔽 your main app starts here


        # Apply custom CSS for Helvetica Neue font
        st.markdown("""
            <style>
            @import url('https://fonts.googleapis.com/css2?family=Helvetica+Neue&display=swap');

            html, body, [class*="css"] {
                font-family: 'Helvetica Neue', sans-serif;
            }

            .block-container {
                padding-top: 2rem;
                padding-bottom: 2rem;
                padding-left: 2rem;
                padding-right: 2rem;
                max-width: none;
            }

            h1 {
                text-align: left;
                width: 100%;
            }
            </style>
            """, unsafe_allow_html=True)

        st.header("🗓️ Registro de Atividades Individuais")

        # Load dropdown options
        players, goals, sessions = get_dropdown_options()

        # Player Name
        player = st.selectbox("Nome do Atleta", options=players + ["Adicionar novo..."])
        if player == "Adicionar novo...":
            col1, col2, col3 = st.columns([1, 1, 2])
            with col2:
                st.markdown(
                    """
                    <div style='display: flex; align-items: center; justify-content: flex-end; height: 38px;'>
                        <span style='color: red;'>Insira o novo Atleta</span>
                    </div>
                    """, unsafe_allow_html=True)
            with col3:
                player = st.text_input("", key="new_player")

        # Training Goal
        goal = st.selectbox("Objetivo do Treino", options=goals + ["Adicionar novo..."])
        if goal == "Adicionar novo...":
            col1, col2, col3 = st.columns([1, 1, 2])
            with col2:
                st.markdown(
                    """
                    <div style='display: flex; align-items: center; justify-content: flex-end; height: 38px;'>
                        <span style='color: red;'>Insira o novo Objetivo</span>
                    </div>
                    """, unsafe_allow_html=True)
            with col3:
                goal = st.text_input("", key="new_goal")

        # Session Type
        session_type = st.selectbox("Tipo de Sessão", options=sessions + ["Adicionar novo..."])
        if session_type == "Adicionar novo...":
            col1, col2, col3 = st.columns([1, 1, 2])
            with col2:
                st.markdown(
                    """
                    <div style='display: flex; align-items: center; justify-content: flex-end; height: 38px;'>
                        <span style='color: red;'>Insira o novo Tipo de Sessão</span>
                    </div>
                    """, unsafe_allow_html=True)
            with col3:
                session_type = st.text_input("", key="new_session_type")

        # Data e submissão
        col1, col2, col3, col4 = st.columns([1, 1, 1, 1]) 

        with col1:
            session_date = st.date_input("Data", value=date.today())

        with col4:
            st.markdown("<div style='height: 32px;'></div>", unsafe_allow_html=True)  # vertical spacer
            submit = st.button("Registrar Treino")

        if submit:
            if all([player, goal, session_type, session_date]):
        # ✅ format as DD/MM/YYYY so Sheets (Brazilian locale) recognises the date
                locale_date = session_date.strftime("%d/%m/%Y")
                append_row_to_sheet(player, goal, session_type, locale_date)
                st.success("Treino registrado com sucesso!")
            else:
                st.error("Preencha todos os campos.")

    elif auth_status is False:
        st.error("Usuário ou senha incorretos")
    elif auth_status is None:
        st.warning("Insira seu login e senha para continuar")

    # Visualizar Registros
    elif page == "Visualizar Registros":
        st.header("📊 Visualização de Registros")
        
        tab1, tab2, tab3 = st.tabs(["Por Atleta", "Por Objetivo", "Todos os Registros"])

        with tab1:
            st.subheader("👤 Dados por Atleta")
            st.write("Em breve: filtros, tabelas e gráficos personalizados por atleta.")

        with tab2:
            st.subheader("🎯 Dados por Objetivo")
            st.write("Em breve: agrupamentos por tipo de treino e objetivo.")

        with tab3:
            st.subheader("📋 Todos os Dados")

            # --- constants for date limits ---
            from datetime import date, timedelta
            min_date = date(2025, 5, 5)
            max_date = date.today()

            # --- load sheet into DataFrame ---
            creds = service_account.Credentials.from_service_account_info(
                st.secrets["gcp_service_account"],
                scopes=["https://www.googleapis.com/auth/spreadsheets"]
            )
            client = gspread.authorize(creds)
            ws = client.open_by_url(st.secrets["gcp_service_account"]["private_gsheets_url"]).sheet1
            records = ws.get_all_records()
            df = pd.DataFrame(records)

            # remove legacy ID column if present
            if "ID" in df.columns:
                df = df.drop(columns=["ID"])

            if not df.empty:
                # --- harmonise column names -------------------------------------------------
                rename_map = {
                    "playerName": "Nome",
                    "trainingGoal": "Objetivo",
                    "sessionType": "Sessão",
                    "date": "Data"  # in case the header is lowercase
                }
                df = df.rename(columns={k: v for k, v in rename_map.items() if k in df.columns})

                # --- parse date column -------------------------------------------------------
                df["Data"] = pd.to_datetime(df["Data"], format="%d/%m/%Y", errors="coerce")
                df = df.dropna(subset=["Data"])
                df["Data"] = df["Data"].dt.date
                df = df.sort_values(by="Data", ascending=False)

                # --- add weekday name --------------------------------------------------------
                dias_semana = {
                    0: "Segunda", 1: "Terça", 2: "Quarta", 3: "Quinta",
                    4: "Sexta", 5: "Sábado", 6: "Domingo"
                }
                df["Dia da Semana"] = df["Data"].apply(lambda x: dias_semana[x.weekday()])

                # --- dynamic filter choices --------------------------------------------------
                atletas = sorted(df["Nome"].unique())
                objetivos = sorted(df["Objetivo"].unique())
                sessoes = sorted(df["Sessão"].unique())

                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    atleta_filter = st.selectbox("Filtrar por Atleta", ["Todos"] + atletas)
                with col2:
                    objetivo_filter = st.selectbox("Filtrar por Objetivo", ["Todos"] + objetivos)
                with col3:
                    sessao_filter = st.selectbox("Filtrar por Sessão", ["Todos"] + sessoes)
                with col4:
                    date_range = st.date_input(
                        "Período",
                        value=(min_date, max_date),
                        min_value=min_date,
                        max_value=max_date,
                    )

                # --- apply filters ------------------------------------------------------------
                if atleta_filter != "Todos":
                    df = df[df["Nome"] == atleta_filter]
                if objetivo_filter != "Todos":
                    df = df[df["Objetivo"] == objetivo_filter]
                if sessao_filter != "Todos":
                    df = df[df["Sessão"] == sessao_filter]
                if date_range and all(date_range):
                    df = df[(df["Data"] >= date_range[0]) & (df["Data"] <= date_range[1])]

                # --- column order: Nome, Data first ------------------------------------------
                cols = df.columns.tolist()
                priority = [c for c in ["Nome", "Data"] if c in cols]
                remaining = [c for c in cols if c not in priority]
                df = df[priority + remaining]

                st.dataframe(df, use_container_width=True, height=600)
            else:
                st.info("Nenhum dado encontrado na planilha.")