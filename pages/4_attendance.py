import streamlit as st
import pandas as pd
from datetime import datetime, date, time
from pathlib import Path
import math
from utils.excel_utils import safe_write

# ================= AUTH CHECK =================
if "logged_in" not in st.session_state or not st.session_state.logged_in:
    st.warning("Please login first.")
    st.switch_page("app.py")
    st.stop()

email = st.session_state.email.strip().lower()

# ================= PAGE CONFIG =================
st.set_page_config(page_title="Attendance", layout="wide")

# ================= LOAD CSS =================
css_path = Path(__file__).parent.parent / "assets" / "style.css"
if css_path.exists():
    st.markdown(f"<style>{css_path.read_text()}</style>", unsafe_allow_html=True)

# ================= CONSTANTS =================
DB = "data/database.xlsx"
TODAY = date.today().strftime("%Y-%m-%d")
NOW = datetime.now().time()

PERIODS_PER_DAY = 5
REQUIRED_PERCENT = 0.75

# ================= LOAD ATTENDANCE =================
try:
    attendance_log = pd.read_excel(DB, sheet_name="Attendance", dtype=str)
except:
    attendance_log = pd.DataFrame(columns=["email", "date", "period"])

attendance_log.columns = attendance_log.columns.str.strip().str.lower()
attendance_log["email"] = attendance_log["email"].astype(str).str.strip().str.lower()

# ================= PERIOD TIMINGS =================
periods = {
    "Period 1 (10:00 – 10:55)": (time(10, 0), time(10, 55)),
    "Period 2 (10:55 – 11:50)": (time(10, 55), time(11, 50)),
    "Period 3 (12:05 – 13:00)": (time(12, 5), time(13, 0)),
    "Period 4 (13:00 – 13:55)": (time(13, 0), time(13, 55)),
    "Period 5 (13:55 – 15:00)": (time(13, 55), time(15, 0)),
}
# (Break removed intentionally)

# ================= TODAY STATUS =================
today_att = attendance_log[
    (attendance_log["email"] == email) &
    (attendance_log["date"] == TODAY)
]

st.title("🗓 Attendance Tracker")
st.metric("Today's Attendance", f"{len(today_att)} / {PERIODS_PER_DAY}")

# ================= MARK ATTENDANCE =================
valid_periods = [
    p for p, (s, e) in periods.items()
    if s <= NOW <= e and p not in today_att["period"].values
]

if valid_periods:
    selected = st.selectbox("Select Period", valid_periods)

    if st.button("📍 Mark Attendance"):
        new_row = pd.DataFrame([{
            "email": email,
            "date": TODAY,
            "period": selected
        }])

        attendance_log = pd.concat([attendance_log, new_row], ignore_index=True)
        safe_write(DB, {"Attendance": attendance_log})

        st.success("Attendance marked successfully ✅")
        st.rerun()
else:
    st.info("No active periods right now.")

# ================= SUMMARY =================
st.divider()

user_all = attendance_log[attendance_log["email"] == email]

# A = attended classes
A = len(user_all)

# T = classes conducted till today
unique_days = user_all["date"].nunique()

if unique_days == 0:
    T = PERIODS_PER_DAY
else:
    T = unique_days * PERIODS_PER_DAY

attendance_percent = (A / T) * 100

st.metric("Overall Attendance %", f"{attendance_percent:.2f}%")
st.caption(f"Attended Classes: {A} / {T}")

# =====================================================
# 🎯 ATTENDANCE SHORTAGE PREDICTOR
# =====================================================
st.subheader("🎯 Attendance Shortage Predictor (75% Rule)")

if attendance_percent >= 75:
    st.success("✅ You are safe! Your attendance is above 75%.")
else:

    # x = classes to attend continuously
    classes_needed = math.ceil((REQUIRED_PERCENT*T - A) / (1 - REQUIRED_PERCENT))

    if classes_needed < 0:
        classes_needed = 0

    st.error(f"⚠ Your attendance is {attendance_percent:.1f}%")

    st.warning(
        f"You must attend the next **{classes_needed} classes continuously** "
        f"to reach the safe 75% attendance level."
    )

    new_percent = ((A + classes_needed) / (T + classes_needed)) * 100
    st.info(f"After attending them, your attendance will become approximately **{new_percent:.1f}%**.")

# =====================================================
# 🎒 SAFE BUNK PLANNER
# =====================================================
st.divider()
st.subheader("🎒 Safe Bunk Planner (75% Rule)")

safe_bunks = math.floor((A / REQUIRED_PERCENT) - T)

if safe_bunks > 0:
    st.success(
        f"You can safely miss **{safe_bunks} classes** and still stay above 75% attendance."
    )

    future_percent = (A / (T + safe_bunks)) * 100
    st.info(
        f"If you skip {safe_bunks} classes, your attendance will become approximately **{future_percent:.1f}%**."
    )

elif safe_bunks == 0:
    st.warning(
        "You cannot miss any classes now. Missing even one class will drop you below 75% attendance."
    )

else:
    shortage = abs(safe_bunks)
    st.error(
        f"⚠ You are below safe attendance. You must attend at least **{shortage} more classes** to become safe."
    )