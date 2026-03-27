import streamlit as st
import gspread
from google.oauth2.service_account import Credentials

# =========================
# GOOGLE SHEETS CONNECT
# =========================
scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]

# ✅ GET SECRETS
gcp_info = dict(st.secrets["gcp_service_account"])

# ✅ FIX PRIVATE KEY (MOST IMPORTANT)
gcp_info["private_key"] = gcp_info["private_key"].replace("\\n", "\n")

# ✅ CREATE CREDS
creds = Credentials.from_service_account_info(
    gcp_info,
    scopes=scope
)

# ✅ AUTHORIZE
client = gspread.authorize(creds)

# ✅ OPEN SHEET
sheet = client.open_by_key("1y60dTYBKgkOi7J37jtGK4BkkmUoZF8yD4P5J3xA5q6Q")

pg_sheet = sheet.sheet1
order_sheet = sheet.worksheet("orders")