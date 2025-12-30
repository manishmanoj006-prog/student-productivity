import os
import streamlit as st
import pandas as pd
from pathlib import Path


DB = "data/database.xlsx"

if not os.path.exists(DB):
    df = pd.DataFrame(columns=["Email", "Password"])
    df.to_excel(DB, sheet_name="Users", index=False)
# ---------- PAGE CONFIG ----------
st.set_page_config(page_title="Login | Student Productivity", layout="centered")
# 🔐 Capture Google OAuth redirect globally
if "code" in st.query_params:
    st.session_state.google_fit_connected = True
    st.session_state.google_auth_code = st.query_params["code"]
# ---------- LOAD CSS ----------
css_path = Path(__file__).parent / "assets" / "style.css"
if css_path.exists():
    st.markdown(f"<style>{css_path.read_text()}</style>", unsafe_allow_html=True)

DB = "data/database.xlsx"

# ---------- SESSION ----------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.email = None

# ---------- LOAD USERS ----------
def load_users():
    try:
        df = pd.read_excel(DB, sheet_name="Users")
        df.columns = df.columns.str.strip()
        df.rename(columns={
            "email": "Email",
            "password": "Password",
            "name": "Name"
        }, inplace=True)
        return df
    except:
        return pd.DataFrame(columns=[
            "Email", "Password", "Name", "MonthlyGoal", "MinAttendance"
        ])

users = load_users()

# ---------- UI ----------
st.markdown("<h2 style='text-align:center'>🔐 Student Productivity Login</h2>", unsafe_allow_html=True)
tab1, tab2 = st.tabs(["Login", "Register"])

# ================= LOGIN =================
with tab1:
    email = st.text_input("Email", key="login_email").strip().lower()
    password = st.text_input("Password", type="password", key="login_password").strip()

    if st.button("Login"):
        if users.empty:
            st.error("No users found. Please register first.")
        else:
            users["Email"] = users["Email"].astype(str).str.strip().str.lower()
            users["Password"] = users["Password"].astype(str).str.strip()

            match = users[
                (users["Email"] == email) &
                (users["Password"] == password)
            ]

            if match.empty:
                st.error("Invalid email or password")
            else:
                st.session_state.logged_in = True
                st.session_state.email = email
                st.success("Login successful!")
                st.switch_page("pages/1_dashboard.py")
users = pd.read_excel("data/database.xlsx", sheet_name="Users")
st.write(users)

# ================= REGISTER =================
with tab2:
    name = st.text_input("Full Name", key="reg_name")
    new_email = st.text_input("Email", key="reg_email").strip().lower()
    new_password = st.text_input("Password", type="password", key="reg_password").strip()

    if st.button("Register"):
        if not name or not new_email or not new_password:
            st.warning("All fields are required")
        elif new_email in users["Email"].astype(str).str.lower().values:
            st.warning("Email already registered")
        else:
            new_user = pd.DataFrame([{
                "Email": new_email,
                "Password": new_password,
                "Name": name,
                "MonthlyGoal": 40,
                "MinAttendance": 75
            }])

            users = pd.concat([users, new_user], ignore_index=True)

            with pd.ExcelWriter(DB, engine="openpyxl", mode="a", if_sheet_exists="replace") as writer:
                users.to_excel(writer, sheet_name="Users", index=False)

            st.success("Registration successful! Please login.")
