import streamlit as st
import sqlite3
from pathlib import Path

# ================== PAGE CONFIG (ONLY PLACE) ==================
st.set_page_config(
    page_title="Student Productivity",
    layout="wide"
)

# ================== CLEAR OAUTH PARAMS ==================
# Google OAuth must be handled ONLY in GoogleFit page
if "code" in st.query_params:
    st.query_params.clear()

# ================== DATABASE (SQLite) ==================
DB_PATH = "data/users.db"
Path("data").mkdir(exist_ok=True)

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

# ================== SESSION INIT ==================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "email" not in st.session_state:
    st.session_state.email = None

# ❌ DO NOT AUTO-ROUTE HERE
# ❌ NO st.switch_page() here based on login state

# ================== LOAD CSS ==================
css_path = Path("assets/style.css")
if css_path.exists():
    st.markdown(f"<style>{css_path.read_text()}</style>", unsafe_allow_html=True)

# ================== UI ==================
st.markdown(
    "<h2 style='text-align:center'>🔐 Student Productivity</h2>",
    unsafe_allow_html=True
)

tab_login, tab_register = st.tabs(["Login", "Register"])

# ================== LOGIN ==================
with tab_login:
    login_email = st.text_input("Email", key="login_email").strip().lower()
    login_password = st.text_input("Password", type="password", key="login_password")

    if st.button("Login"):
        with get_conn() as conn:
            cur = conn.execute(
                "SELECT * FROM users WHERE email=? AND password=?",
                (login_email, login_password)
            )
            user = cur.fetchone()

        if not user:
            st.error("Invalid email or password")
        else:
            st.session_state.logged_in = True
            st.session_state.email = login_email
            st.success("Login successful")
            st.switch_page("pages/1_dashboard.py")

# ================== REGISTER ==================
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
                st.warning("Email already registered")
