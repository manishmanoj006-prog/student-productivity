import streamlit as st
import pandas as pd
from datetime import datetime, date, time
from pathlib import Path

# ---------------- PAGE CONFIG ----------------
st.set_page_config(page_title="Attendance", layout="wide")

# ---------------- LOAD CSS ----------------
css_path = Path(__file__).parent.parent / "assets" / "style.css"
with open(css_path) as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# ---------------- SESSION CHECK ----------------
if "email" not in st.session_state or not st.session_state.email:
    st.warning("Please login first.")
    st.switch_page("app.py")
    st.stop()

email = st.session_state.email
DB = "data/database.xlsx"
TODAY = date.today().strftime("%Y-%m-%d")
NOW = datetime.now().time()

# ---------------- LOAD DATA ----------------
try:
    attendance = pd.read_excel(DB, sheet_name="Attendance")
except:
    attendance = pd.DataFrame(columns=["Email", "Date", "Period"])

users = pd.read_excel(DB, sheet_name="Users")

# ---------------- TITLE ----------------
st.title("🗓 Attendance Tracker")
st.write("Mark your attendance during the active class periods.")

# ---------------- PERIOD DEFINITIONS ----------------
periods = {
    "Period 1 (1:05 – 2:00 PM)": (time(13, 5), time(14, 0)),
    "Period 2 (2:00 – 3:00 PM)": (time(14, 0), time(15, 00)),
    "Period 3 (3:00 – 3:55 PM)": (time(15, 00), time(15, 55)),

    # 15-minute break: 3:50 – 4:15 PM

    "Period 4 (4:15 – 5:05 PM)": (time(16, 15), time(17, 5)),
    "Period 5 (5:05 – 6:00 PM)": (time(17, 5), time(18, 00)),
}


# ---------------- TODAY STATUS ----------------
today_attendance = attendance[
    (attendance["Email"] == email) &
    (attendance["Date"] == TODAY)
]

st.markdown(f"""
<div class="card">
    <div class="card-title">📌 Today's Attendance</div>
    <div class="stat">{len(today_attendance)} / 5</div>
</div>
""", unsafe_allow_html=True)

st.divider()

# ---------------- VALID PERIODS ----------------
valid_periods = []

for period, (start, end) in periods.items():
    if start <= NOW <= end and period not in today_attendance["Period"].values:
        valid_periods.append(period)

st.subheader("✅ Mark Attendance")

if not valid_periods:
    st.info("Attendance can only be marked during active class periods.")
    st.stop()

selected_period = st.selectbox("Select Current Period", valid_periods)

# ---------------- MARK ATTENDANCE ----------------
if st.button("📍 Mark Attendance"):
    if len(today_attendance) >= 5:
        st.error("Maximum 5 periods already marked today.")
        st.stop()

    new_row = pd.DataFrame([{
        "Email": email,
        "Date": TODAY,
        "Period": selected_period
    }])

    attendance = pd.concat([attendance, new_row], ignore_index=True)

    with pd.ExcelWriter(DB, engine="openpyxl", mode="a", if_sheet_exists="replace") as writer:
        users.to_excel(writer, sheet_name="Users", index=False)
        attendance.to_excel(writer, sheet_name="Attendance", index=False)

    st.success(f"Attendance marked for {selected_period}")
    st.rerun()

# ---------------- OVERALL ATTENDANCE ----------------
st.divider()
st.subheader("📊 Attendance Summary")

total_days = attendance[attendance["Email"] == email]["Date"].nunique()
total_marked = attendance[attendance["Email"] == email].shape[0]

possible = total_days * 5 if total_days > 0 else 1
attendance_percent = (total_marked / possible) * 100

st.metric("Overall Attendance %", f"{attendance_percent:.1f}%")

if attendance_percent < 75:
    st.warning("⚠ Attendance below 75%. Please improve.")
else:
    st.success("✅ Attendance is healthy!")
