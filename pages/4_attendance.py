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

# convert date properly
attendance_log["date"] = pd.to_datetime(
    attendance_log["date"], errors="coerce"
).dt.date

# remove duplicates
attendance_log = attendance_log.drop_duplicates(
    subset=["email", "date", "period"]
)

# ================= PERIOD TIMINGS =================
periods = {
    "Period 1": (time(10, 0), time(11, 0)),
    "Period 2": (time(11, 0), time(12, 0)),
    "Period 3": (time(12, 0), time(13, 0)),
    "Period 4": (time(13, 0), time(14, 0)),
    "Period 5": (time(14, 0), time(15, 0)),
}
# ================= TODAY STATUS =================
today_att = attendance_log[
    (attendance_log["email"] == email) &
    (attendance_log["date"] == date.today())
]

st.title("🗓 Attendance Tracker")

today_count = len(today_att)
today_percent = (today_count / PERIODS_PER_DAY) * 100

st.metric(
    "Today's Attendance",
    f"{today_count} / {PERIODS_PER_DAY}",
    f"{today_percent:.0f}%"
)

# ================= MARK ATTENDANCE =================
valid_periods = [
    p for p, (s, e) in periods.items()
    if s <= NOW <= e and p not in today_att["period"].values
]

if valid_periods:

    selected = st.selectbox("Select Period", valid_periods)

    if st.button("📍 Mark Attendance"):

        # prevent duplicate marking
        if not (
            (attendance_log["email"] == email) &
            (attendance_log["date"] == date.today()) &
            (attendance_log["period"] == selected)
        ).any():

            new_row = pd.DataFrame([{
                "email": email,
                "date": date.today(),
                "period": selected
            }])

            attendance_log = pd.concat(
                [attendance_log, new_row],
                ignore_index=True
            )

            safe_write(DB, {"Attendance": attendance_log})

            st.success("Attendance marked successfully ✅")

            st.rerun()

        else:
            st.warning("Attendance already marked for this period.")

else:
    st.info("No active periods right now.")

# ================= SUMMARY =================
st.divider()

user_all = attendance_log[attendance_log["email"] == email]

# Attended classes
A = len(user_all)

# ================= TOTAL CLASSES LOGIC =================
if not user_all.empty:

    first_day = user_all["date"].min()
    today = date.today()

    total_days = (today - first_day).days + 1

    T = total_days * PERIODS_PER_DAY

else:
    T = 0

attendance_percent = (A / T) * 100 if T > 0 else 0

st.metric("Overall Attendance %", f"{attendance_percent:.2f}%")
st.caption(f"Attended Classes: {A} / {T}")

# =====================================================
# 🎯 ATTENDANCE SHORTAGE PREDICTOR
# =====================================================
st.subheader("🎯 Attendance Shortage Predictor (75% Rule)")

if attendance_percent >= 75:

    st.success("✅ You are safe! Your attendance is above 75%.")

else:

    if T == 0:
        st.info("Attendance data not available yet.")
    else:

        classes_needed = math.ceil(
            (REQUIRED_PERCENT * T - A) / (1 - REQUIRED_PERCENT)
        )

        if classes_needed < 0:
            classes_needed = 0

        st.error(f"⚠ Your attendance is {attendance_percent:.1f}%")

        st.warning(
            f"You must attend the next **{classes_needed} classes continuously** "
            f"to reach the safe 75% attendance level."
        )

        new_percent = ((A + classes_needed) / (T + classes_needed)) * 100

        st.info(
            f"After attending them, your attendance will become approximately "
            f"**{new_percent:.1f}%**."
        )

# =====================================================
# 🎒 SAFE BUNK PLANNER
# =====================================================
st.divider()

st.subheader("🎒 Safe Bunk Planner (75% Rule)")

if T == 0:

    st.info("Not enough data to calculate safe bunks yet.")

else:

    safe_bunks = math.floor((A / REQUIRED_PERCENT) - T)

    if safe_bunks > 0:

        st.success(
            f"You can safely miss **{safe_bunks} classes** and still stay above 75% attendance."
        )

        future_percent = (A / (T + safe_bunks)) * 100

        st.info(
            f"If you skip {safe_bunks} classes, your attendance will become approximately "
            f"**{future_percent:.1f}%**."
        )

    elif safe_bunks == 0:

        st.warning(
            "You cannot miss any classes now. Missing even one class will drop you below 75% attendance."
        )

    else:

        shortage = abs(safe_bunks)

        st.error(
            f"⚠ You are below safe attendance. "
            f"You must attend at least **{shortage} more classes** to become safe."
        )