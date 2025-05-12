import yaml
from yaml.loader import SafeLoader
import streamlit_authenticator as stauth
import streamlit as st
from sheets_api import get_dropdown_options, append_row_to_sheet
from datetime import date


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

if auth_status is False:
    st.error('Usuário ou senha incorretos')
elif auth_status is None:
    st.warning('Insira seu login e senha')
else:
    authenticator.logout('Logout', 'main')
    st.write(f"👋🏼 Bem-vindo, *{name}*")


    # 🔽 your main app starts here


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
        append_row_to_sheet(player, goal, session_type, session_date)
        st.success("Treino registrado com sucesso!")
    else:
        st.error("Preencha todos os campos.")