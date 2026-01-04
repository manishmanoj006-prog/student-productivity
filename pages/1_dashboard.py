import streamlit as st
import pandas as pd
from datetime import datetime
from pathlib import Path

# ================= PAGE PROTECTION =================
if "logged_in" not in st.session_state or not st.session_state.logged_in:
    st.warning("Please login first.")
    st.switch_page("app.py")

email = st.session_state.email

# ================= PAGE CONFIG =================
st.set_page_config(page_title="Dashboard", layout="wide")

# ================= LOAD CSS =================
css_path = Path(__file__).parent.parent / "assets" / "style.css"
with open(css_path) as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# ================= DATABASE =================
DB = "data/database.xlsx"
today = datetime.now().strftime("%Y-%m-%d")

# ================= TITLE =================
st.title("📘 Student Productivity")
st.write("Welcome back 👋 Track your progress and stay consistent.")

# ================= LOAD DATA =================
def load_sheet(name, cols):
    try:
        df = pd.read_excel(DB, sheet_name=name)
        df.columns = df.columns.str.strip().str.lower()
        return df
    except:
        return pd.DataFrame(columns=cols)

habits = load_sheet("Habits", ["habit"])
habit_log = load_sheet("HabitLog", ["email", "date", "habit"])
study_log = load_sheet("StudyLog", ["email", "date", "subject", "minutes"])
attendance = load_sheet("Attendance", ["email", "date", "period"])
tasks = load_sheet("Tasks", ["email", "task", "status"])
fit_data = load_sheet("GoogleFitData", ["email", "date", "steps"])

# ================= NORMALIZE =================
habit_log["date"] = habit_log["date"].astype(str)
study_log["minutes"] = pd.to_numeric(study_log["minutes"], errors="coerce").fillna(0)
fit_data["date"] = fit_data["date"].astype(str)
fit_data["steps"] = pd.to_numeric(fit_data["steps"], errors="coerce").fillna(0)

# ================= CALCULATIONS =================
total_habits = len(habits)

today_habits_done = len(
    habit_log[(habit_log["email"] == email) & (habit_log["date"] == today)]
)

today_study_hours = round(
    study_log[
        (study_log["email"] == email) & (study_log["date"] == today)
    ]["minutes"].sum() / 60,
    2
)

today_attendance = len(
    attendance[(attendance["email"] == email) & (attendance["date"] == today)]
)

user_tasks = tasks[tasks["email"] == email]
completed_tasks = len(user_tasks[user_tasks["status"] == "Completed"])
total_tasks = len(user_tasks)
progress_percent = int((completed_tasks / total_tasks) * 100) if total_tasks else 0

# ================= GOOGLE FIT STEPS (FINAL SAFE) =================
today_steps = None

today_fit = fit_data[
    (fit_data["email"] == email) &
    (fit_data["date"] == today)
]

if not today_fit.empty:
    today_steps = int(today_fit.iloc[0]["steps"])
else:
    # fallback to last available data
    user_fit = fit_data[fit_data["email"] == email].sort_values("date", ascending=False)
    if not user_fit.empty:
        today_steps = int(user_fit.iloc[0]["steps"])

# ================= DASHBOARD CARDS =================
c1, c2, c3, c4 = st.columns(4)

with c1:
    st.markdown(f"""
    <div class="card">
        <div class="card-title">Habits</div>
        <div class="stat">{today_habits_done} / {total_habits}</div>
        <div class="card-text">
            👣 {today_steps if today_steps is not None else "Not synced"} steps
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.caption("ℹ️ Step count may lag behind Google Fit app due to sync delay")

with c2:
    st.markdown(f"""
    <div class="card">
        <div class="card-title">Study Time</div>
        <div class="stat">{today_study_hours} hrs</div>
        <div class="card-text">Today</div>
    </div>
    """, unsafe_allow_html=True)

with c3:
    st.markdown(f"""
    <div class="card">
        <div class="card-title">Attendance</div>
        <div class="stat">{today_attendance} / 5</div>
        <div class="card-text">Periods marked</div>
    </div>
    """, unsafe_allow_html=True)

with c4:
    st.markdown(f"""
    <div class="card">
        <div class="card-title">Tasks</div>
        <div class="stat">{progress_percent}%</div>
        <div class="card-text">Completed</div>
    </div>
    """, unsafe_allow_html=True)

# ================= SIDEBAR =================
with st.sidebar:
    if st.button("🚪 Logout"):
        st.session_state.logged_in = False
        st.session_state.email = None
        st.switch_page("app.py")

    # OPTIONAL DEBUG (remove after testing)
    st.markdown("---")
    st.write("DEBUG: Google Fit Data")
    st.dataframe(fit_data)
