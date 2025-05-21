import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

# Define the scope
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

# Authenticate using the service account
credentials = Credentials.from_service_account_info(
    st.secrets["gcp_service_account"],
    scopes=SCOPES,
)
client = gspread.authorize(credentials)

# Open the Google Sheet
SHEET_URL = st.secrets["gcp_service_account"]["private_gsheets_url"]
sheet = client.open_by_url(SHEET_URL).sheet1

def get_dropdown_options():
    records = sheet.get_all_records()
    players = sorted(set(row["Nome"] for row in records if row["Nome"]))
    goals = sorted(set(row["Objetivo"] for row in records if row["Objetivo"]))
    sessions = sorted(set(row["Sessão"] for row in records if row["Sessão"]))
    return players, goals, sessions

def append_row_to_sheet(player, goal, session_type, date_string):
    next_id = len(sheet.get_all_values())  # Assuming header is in the first row
    new_row = [
        str(next_id),
        player,
        goal,
        session_type,
        date_string,  # already in DD/MM/YYYY format
    ]
    sheet.append_row(new_row, value_input_option="USER_ENTERED")