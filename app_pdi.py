import streamlit as st
from sheets_api import get_dropdown_options, append_row_to_sheet
from datetime import date

# Apply custom CSS for Helvetica Neue font
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Helvetica+Neue&display=swap');
    html, body, [class*="css"]  {
        font-family: 'Helvetica Neue', sans-serif;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("🏋️ Training Session Logger")

# Load dropdown options
players, goals, sessions = get_dropdown_options()

# Player Name
player = st.selectbox("Player Name", options=players + ["Add new..."])
if player == "Add new...":
    player = st.text_input("Enter new player name")

# Training Goal
goal = st.selectbox("Training Goal", options=goals + ["Add new..."])
if goal == "Add new...":
    goal = st.text_input("Enter new training goal")

# Session Type
session_type = st.selectbox("Session Type", options=sessions + ["Add new..."])
if session_type == "Add new...":
    session_type = st.text_input("Enter new session type")

# Date Picker
session_date = st.date_input("Date", value=date.today())

# Submit Button
if st.button("Submit"):
    if all([player, goal, session_type, session_date]):
        append_row_to_sheet(player, goal, session_type, session_date)
        st.success("Training session logged successfully!")
    else:
        st.error("Please fill in all fields.")