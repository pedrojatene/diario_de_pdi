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
    players = sorted(set(row["playerName"] for row in records if row["playerName"]))
    goals = sorted(set(row["trainingGoal"] for row in records if row["trainingGoal"]))
    sessions = sorted(set(row["sessionType"] for row in records if row["sessionType"]))
    return players, goals, sessions

def append_row_to_sheet(player, goal, session_type, session_date):
    next_id = len(sheet.get_all_values())  # Assuming header is in the first row
    new_row = [
        str(next_id),
        player,
        goal,
        session_type,
        session_date.strftime("%Y-%m-%d"),
    ]
    sheet.append_row(new_row)