import os
import streamlit as st
import pandas as pd
from pathlib import Path

# ================== PAGE CONFIG ==================
st.set_page_config(
    page_title="Login | Student Productivity",
    layout="centered"
)

# ================== LOAD CSS ==================
css_path = Path("assets/style.css")
if css_path.exists():
    st.markdown(f"<style>{css_path.read_text()}</style>", unsafe_allow_html=True)

# ================== DATABASE SETUP ==================
DB = "data/database.xlsx"

# Ensure data folder exists
os.makedirs("data", exist_ok=True)

# Ensure database + Users sheet exists
if not os.path.exists(DB):
    df = pd.DataFrame(
        columns=["Email", "Password", "Name", "MonthlyGoal", "MinAttendance"]
    )
    df.to_excel(DB, sheet_name="Users", index=False)

# ================== SESSION ==================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.email = None

# ================== LOAD USERS ==================
def load_users():
    try:
        df = pd.read_excel(DB, sheet_name="Users")
        df.columns = df.columns.str.strip()
        df["Email"] = df["Email"].astype(str).str.lower().str.strip()
        df["Password"] = df["Password"].astype(str)
        return df
    except Exception:
        return pd.DataFrame(
            columns=["Email", "Password", "Name", "MonthlyGoal", "MinAttendance"]
        )

users = load_users()

# ================== UI ==================
st.markdown(
    "<h2 style='text-align:center'>🔐 Student Productivity Login</h2>",
    unsafe_allow_html=True
)

tab_login, tab_register = st.tabs(["Login", "Register"])

# ================== LOGIN ==================
with tab_login:
    login_email = st.text_input(
        "Email",
        key="login_email"
    ).strip().lower()

    login_password = st.text_input(
        "Password",
        type="password",
        key="login_password"
    ).strip()

    if st.button("Login", key="login_btn"):
        if users.empty:
            st.error("No users found. Please register first.")
        else:
            match = users[
                (users["Email"] == login_email) &
                (users["Password"] == login_password)
            ]

            if match.empty:
                st.error("Invalid email or password")
            else:
                st.session_state.logged_in = True
                st.session_state.email = login_email
                st.success("Login successful!")
                st.switch_page("pages/1_dashboard.py")

# ================== REGISTER ==================
with tab_register:
    reg_name = st.text_input(
        "Full Name",
        key="reg_name"
    )

    reg_email = st.text_input(
        "Email",
        key="reg_email"
    ).strip().lower()

    reg_password = st.text_input(
        "Password",
        type="password",
        key="reg_password"
    ).strip()

    if st.button("Register", key="register_btn"):
        if not reg_name or not reg_email or not reg_password:
            st.warning("All fields are required")
        elif reg_email in users["Email"].values:
            st.warning("Email already registered")
        else:
            new_user = pd.DataFrame([{
                "Email": reg_email,
                "Password": reg_password,
                "Name": reg_name,
                "MonthlyGoal": 40,
                "MinAttendance": 75
            }])

            users = pd.concat([users, new_user], ignore_index=True)

            # Write fresh file (safe on Streamlit Cloud)
            with pd.ExcelWriter(DB, engine="openpyxl", mode="w") as writer:
                users.to_excel(writer, sheet_name="Users", index=False)

            st.success("Registration successful! Please login.")
