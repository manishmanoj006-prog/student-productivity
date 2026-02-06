import streamlit as st
import pandas as pd
from pathlib import Path
from datetime import date

# ================= PAGE CONFIG =================
st.set_page_config(page_title="Dashboard", layout="wide")

DB = Path("data/database.xlsx")

# ================= AUTH =================
if "logged_in" not in st.session_state or not st.session_state.logged_in:
    st.switch_page("app.py")
    st.stop()

email = st.session_state.email.strip().lower()
today = date.today()

# ================= LOAD CSS =================
css_path = Path(__file__).parent.parent / "assets" / "style.css"
if css_path.exists():
    st.markdown(f"<style>{css_path.read_text()}</style>", unsafe_allow_html=True)

# ================= SAFE READ =================
def read_sheet(sheet):
    try:
        df = pd.read_excel(DB, sheet_name=sheet)
        df.columns = df.columns.astype(str).str.strip().str.lower()
        return df
    except:
        return pd.DataFrame()

# ================= LOAD DATA =================
habits = read_sheet("Habits")
habit_log = read_sheet("HabitLog")
study_log = read_sheet("StudyLog")
attendance = read_sheet("Attendance")
tasks = read_sheet("Tasks")
settings = read_sheet("Settings")

# ================= SETTINGS =================
monthly_goal_min = 0
if not settings.empty and "monthly_study_goal" in settings.columns:
    try:
        monthly_goal_min = int(settings["monthly_study_goal"].iloc[0])
    except:
        monthly_goal_min = 0

# ================= CSS CARD =================
st.markdown("""
<style>
.card {
    background: linear-gradient(145deg, #0f172a, #020617);
    padding: 22px;
    border-radius: 18px;
    box-shadow: 0 0 18px rgba(56,189,248,0.18);
    height: 170px;
}
.card h3 { color: white; }
.big {
    font-size: 34px;
    font-weight: 700;
    color: #38bdf8;
}
.small {
    margin-top: 10px;
    color: #94a3b8;
    font-size: 14px;
}
</style>
""", unsafe_allow_html=True)

# =================================================
# HABITS (TODAY)
# =================================================
total_habits = len(habits)
completed_habits = 0

if not habit_log.empty and {"email", "date"}.issubset(habit_log.columns):
    habit_log["email"] = habit_log["email"].astype(str).str.lower()
    habit_log["date"] = pd.to_datetime(
        habit_log["date"], errors="coerce"
    ).dt.date

    completed_habits = habit_log[
        (habit_log["email"] == email) &
        (habit_log["date"] == today)
    ].shape[0]

# =================================================
# STUDY (MONTHLY)
# =================================================
study_minutes = 0

if not study_log.empty and "minutes" in study_log.columns:
    date_col = next((c for c in study_log.columns if "date" in c), None)
    if date_col:
        study_log[date_col] = pd.to_datetime(
            study_log[date_col], errors="coerce"
        )

        study_minutes = study_log[
            (study_log[date_col].dt.month == today.month) &
            (study_log[date_col].dt.year == today.year)
        ]["minutes"].astype(float).sum()

study_hours = round(study_minutes / 60, 2)
goal_hours = round(monthly_goal_min / 60, 2) if monthly_goal_min else 0

# =================================================
# ATTENDANCE (TODAY – PERIOD BASED)
# =================================================
total_periods_today = 5
present_periods_today = 0
attendance_percent = 0.0

if not attendance.empty and {"email", "date"}.issubset(attendance.columns):
    attendance["email"] = attendance["email"].astype(str).str.lower()
    attendance["date"] = pd.to_datetime(
        attendance["date"], errors="coerce"
    ).dt.date

    today_att = attendance[
        (attendance["email"] == email) &
        (attendance["date"] == today)
    ]

    present_periods_today = len(today_att)
    attendance_percent = round(
        (present_periods_today / total_periods_today) * 100, 1
    )

# =================================================
# TASKS (🔥 FINAL CORRECT LOGIC)
# =================================================
# =================================================
# TASKS (FINAL FIX – DUPLICATE COLUMN SAFE)
# =================================================
# =================================================
# TASKS (FINAL – BULLETPROOF FIX)
# =================================================
# =================================================
# TASKS (FIX FOR DUPLICATE / MIXED COLUMNS)
# =================================================
total_tasks = 0
completed_tasks = 0

if not tasks.empty:

    # Map correct columns
    email_col = tasks["email"] if "email" in tasks.columns else tasks["email".capitalize()]
    status_col = tasks["status"] if "status" in tasks.columns else tasks["status".capitalize()]

    email_col = email_col.astype(str).str.strip().str.lower()
    status_col = status_col.astype(str).str.strip().str.lower()

    user_tasks = tasks[email_col == email]

    total_tasks = len(user_tasks)
    completed_tasks = status_col[user_tasks.index].isin(["completed"]).sum()

task_percent = int((completed_tasks / total_tasks) * 100) if total_tasks else 0




# ================= DASHBOARD UI =================
st.title("📘 Student Productivity")
st.write("Welcome back 👋 Track your progress and stay consistent.")

c1, c2, c3, c4 = st.columns(4)

with c1:
    st.markdown(f"""
    <div class="card">
        <h3>Habits</h3>
        <div class="big">{total_habits}</div>
        <div class="small">✅ {completed_habits} completed today</div>
    </div>
    """, unsafe_allow_html=True)

with c2:
    st.markdown(f"""
    <div class="card">
        <h3>Study</h3>
        <div class="big">{study_hours} hrs</div>
        <div class="small">📚 Goal: {goal_hours} hrs</div>
    </div>
    """, unsafe_allow_html=True)

with c3:
    st.markdown(f"""
    <div class="card">
        <h3>Attendance</h3>
        <div class="big">{present_periods_today} / {total_periods_today}</div>
        <div class="small">🏫 {attendance_percent}% attendance</div>
    </div>
    """, unsafe_allow_html=True)

with c4:
    st.markdown(f"""
    <div class="card">
        <h3>Tasks</h3>
        <div class="big">{task_percent}%</div>
        <div class="small">📝 {completed_tasks} / {total_tasks} completed</div>
    </div>
    """, unsafe_allow_html=True)
