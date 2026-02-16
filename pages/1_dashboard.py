import streamlit as st
import pandas as pd
from pathlib import Path
from datetime import date
from utils.productivity import calculate_productivity
from utils.suggestions import get_suggestions

# ================= PAGE CONFIG =================
st.set_page_config(page_title="Dashboard", layout="wide")

DB = Path("data/database.xlsx")

# ================= 🔐 AUTH PROTECTION =================
if "logged_in" not in st.session_state or not st.session_state.logged_in:
    st.warning("Please login first")
    st.switch_page("app.py")
    st.stop()

email = str(st.session_state.email).strip().lower()
today = date.today()

# ================= LOAD CSS =================
css_path = Path(__file__).parent.parent / "assets" / "style.css"
if css_path.exists():
    st.markdown(f"<style>{css_path.read_text()}</style>", unsafe_allow_html=True)

# ================= SAFE READ FUNCTION =================
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

# =================================================
# HABITS (TODAY)
# =================================================
total_habits = len(habits)
completed_habits = 0

if not habit_log.empty and {"email", "date"}.issubset(habit_log.columns):
    habit_log["email"] = habit_log["email"].astype(str).str.lower()
    habit_log["date"] = pd.to_datetime(habit_log["date"], errors="coerce").dt.date

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
        study_log[date_col] = pd.to_datetime(study_log[date_col], errors="coerce")

        study_minutes = study_log[
            (study_log[date_col].dt.month == today.month) &
            (study_log[date_col].dt.year == today.year) &
            (study_log["email"].astype(str).str.lower() == email)
        ]["minutes"].astype(float).sum()

study_hours = round(study_minutes / 60, 2)

# =================================================
# ATTENDANCE (TODAY)
# =================================================
total_periods_today = 5
present_periods_today = 0
attendance_percent = 0.0

if not attendance.empty and {"email", "date"}.issubset(attendance.columns):
    attendance["email"] = attendance["email"].astype(str).str.lower()
    attendance["date"] = pd.to_datetime(attendance["date"], errors="coerce").dt.date

    today_att = attendance[
        (attendance["email"] == email) &
        (attendance["date"] == today)
    ]

    present_periods_today = len(today_att)
    attendance_percent = round((present_periods_today / total_periods_today) * 100, 1)

# =================================================
# TASKS (CLEAN CALCULATION)
# =================================================
total_tasks = 0
completed_tasks = 0

if not tasks.empty and {"email", "status"}.issubset(tasks.columns):

    tasks["email"] = tasks["email"].astype(str).str.lower()
    tasks["status"] = tasks["status"].astype(str).str.lower()

    user_tasks = tasks[tasks["email"] == email]

    total_tasks = len(user_tasks)
    completed_tasks = user_tasks[user_tasks["status"] == "completed"].shape[0]

task_percent = int((completed_tasks / total_tasks) * 100) if total_tasks else 0

# ================= DASHBOARD UI =================
st.title("📘 Student Productivity")
st.write("Welcome back 👋 Track your progress and stay consistent.")

c1, c2, c3, c4 = st.columns(4)

with c1:
    st.metric("Habits", total_habits, f"{completed_habits} completed today")

with c2:
    st.metric("Study Hours (This Month)", f"{study_hours} hrs")

with c3:
    st.metric("Attendance Today", f"{present_periods_today}/5", f"{attendance_percent}%")

with c4:
    st.metric("Tasks Completed", f"{task_percent}%", f"{completed_tasks}/{total_tasks}")

# =================================================
# PRODUCTIVITY SCORE
# =================================================
st.divider()

score = calculate_productivity(email)

st.subheader("📊 Today's Productivity Score")
st.progress(score / 100)

if score >= 80:
    st.success(f"🔥 Excellent Performance ({score}/100)")
elif score >= 60:
    st.info(f"👍 Good Progress ({score}/100)")
elif score >= 40:
    st.warning(f"⚠ You can improve ({score}/100)")
else:
    st.error(f"🚨 Low Productivity ({score}/100)")

# =================================================
# SMART SUGGESTIONS
# =================================================
st.subheader("🧠 Smart Study Suggestions")

tips = get_suggestions(email)

for tip in tips:
    st.info(tip)
