import streamlit as st
import sqlite3
from pathlib import Path
import pandas as pd

# ---------------- DATABASE INITIALIZER ----------------
DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)

DB = DATA_DIR / "database.xlsx"

if not DB.exists():
    with pd.ExcelWriter(DB, engine="openpyxl") as writer:

        pd.DataFrame(columns=["email", "date", "period"]).to_excel(
            writer, sheet_name="Attendance", index=False
        )

        pd.DataFrame(columns=["email", "subject", "minutes", "date"]).to_excel(
            writer, sheet_name="StudyLog", index=False
        )

        pd.DataFrame(columns=["email", "habit", "date"]).to_excel(
            writer, sheet_name="HabitLog", index=False
        )

# ================= PAGE CONFIG =================
st.set_page_config(page_title="Student Productivity", layout="wide")

# ================= SQLITE DATABASE =================
DB_PATH = "data/users.db"

def get_conn():
    return sqlite3.connect(DB_PATH, check_same_thread=False)

def init_db():
    with get_conn() as conn:
        conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            email TEXT PRIMARY KEY,
            password TEXT NOT NULL,
            name TEXT
        )
        """)
        conn.commit()

init_db()

# ================= SESSION INIT =================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "email" not in st.session_state:
    st.session_state.email = None

# ================= CSS =================
css_path = Path("assets/style.css")

if css_path.exists():
    st.markdown(f"<style>{css_path.read_text()}</style>", unsafe_allow_html=True)

# ================= TITLE =================
st.markdown(
    "<h2 style='text-align:center'>🔐 Student Productivity</h2>",
    unsafe_allow_html=True
)

tab_login, tab_register = st.tabs(["Login", "Register"])

# ==================================================
# LOGIN
# ==================================================
with tab_login:

    with st.form("login_form"):

        login_email = st.text_input("Email").strip().lower()
        login_password = st.text_input("Password", type="password")

        login_btn = st.form_submit_button("Login")

    if login_btn:

        with get_conn() as conn:

            # 1️⃣ Check if email exists
            cur = conn.execute(
                "SELECT * FROM users WHERE email=?",
                (login_email,)
            )

            user = cur.fetchone()

        if not user:

            st.warning("⚠ Account not found. Please register first.")

        else:

            stored_password = user[1]

            # 2️⃣ Check password
            if stored_password != login_password:

                st.error("❌ Incorrect password")

            else:

                st.session_state.logged_in = True
                st.session_state.email = login_email

                st.success("✅ Login successful")

                st.switch_page("pages/1_dashboard.py")

# ==================================================
# REGISTER
# ==================================================
with tab_register:

    reg_name = st.text_input("Full Name").strip()
    reg_email = st.text_input("Email").strip().lower()
    reg_password = st.text_input("Password", type="password")

    if st.button("Register"):

        if not reg_name or not reg_email or not reg_password:

            st.warning("All fields are required")

        else:

            try:

                with get_conn() as conn:

                    conn.execute(
                        "INSERT INTO users (email, password, name) VALUES (?, ?, ?)",
                        (reg_email, reg_password, reg_name)
                    )

                    conn.commit()

                st.success("Registered successfully. Please login.")

                st.rerun()

            except sqlite3.IntegrityError:

                st.warning("⚠ Email already registered")