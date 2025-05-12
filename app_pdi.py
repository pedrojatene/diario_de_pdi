import streamlit as st
from sheets_api import get_dropdown_options, append_row_to_sheet
from datetime import date

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
#player = st.selectbox("Nome do Atleta", options=players + ["Adicionar novo..."])
#if player == "Adicionar novo...":
#    player = st.text_input("Insira o novo Atleta")

player = st.selectbox("Nome do Atleta", options=players + ["Adicionar novo..."])
if player == "Adicionar novo...":
    col1, col2 = st.columns([1, 2])  # Adjust ratio for better spacing

    with col1:
        st.markdown(
            """
            <div style='display: flex; align-items: center; justify-content: flex-end; height: 38px;'>
                <span style='color: red;'>Insira o novo Atleta</span>
            </div>
            """,
            unsafe_allow_html=True
        )

    with col2:
        player = st.text_input("")

# Training Goal
goal = st.selectbox("Objetivo do Treino", options=goals + ["Adicionar novo..."])
if goal == "Adicionar novo...":
    goal = st.text_input("Insira o novo Objetivo")

# Session Type
session_type = st.selectbox("Tipo de Sessão", options=sessions + ["Adicionar novo..."])
if session_type == "Adicionar novo...":
    session_type = st.text_input("Insira o novo Tipo de Sessão")

# Date Picker
session_date = st.date_input("Date", value=date.today())

# Submit Button
if st.button("Registrar Treino"):
    if all([player, goal, session_type, session_date]):
        append_row_to_sheet(player, goal, session_type, session_date)
        st.success("Treino registrado com sucesso!")
    else:
        st.error("Preencha todos os campos.")