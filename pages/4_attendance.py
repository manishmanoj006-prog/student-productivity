import streamlit as st
import pandas as pd
from datetime import datetime, date, time
from pathlib import Path

from utils.excel_utils import safe_write

def load_sheet_safe(sheet_name, expected_cols):
    try:
        df = pd.read_excel(DB, sheet_name=sheet_name)
    except:
        return pd.DataFrame(columns=expected_cols)

    df.columns = [
        c.strip().lower() if isinstance(c, str) else c
        for c in df.columns
    ]

    if list(df.columns) != expected_cols:
        return pd.DataFrame(columns=expected_cols)

    return df

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

# ================= LOAD USERS =================
try:
    users = pd.read_excel(DB, sheet_name="Users", dtype=str)
except:
    users = pd.DataFrame(columns=["email", "attendance"])

# normalize columns
users.columns = users.columns.str.strip().str.lower()

if "email" not in users.columns:
    users["email"] = ""

if "attendance" not in users.columns:
    users["attendance"] = "0"

users["email"] = users["email"].astype(str).str.strip().str.lower()
users["attendance"] = pd.to_numeric(users["attendance"], errors="coerce").fillna(0).astype(int)

user_row = users[users["email"] == email]
attendance_score = int(user_row.iloc[0]["attendance"]) if not user_row.empty else 0

# ================= LOAD ATTENDANCE LOG =================
try:
    attendance_log = pd.read_excel(DB, sheet_name="Attendance", dtype=str)
except:
    attendance_log = pd.DataFrame(columns=["email", "date", "period"])

attendance_log.columns = attendance_log.columns.str.strip().str.lower()
attendance_log["email"] = attendance_log["email"].astype(str).str.strip().str.lower()

# ================= PERIODS =================
from datetime import time

periods = {
    "Period 1 (08:00 – 08:55)": (time(8, 0), time(8, 55)),
    "Period 2 (08:55 – 09:50)": (time(8, 55), time(9, 50)),
    "Break (09:50 – 10:05)": (time(9, 50), time(10, 5)),
    "Period 3 (10:05 – 11:00)": (time(10, 5), time(11, 0)),
    "Period 4 (11:00 – 11:55)": (time(11, 0), time(11, 55)),
    "Period 5 (11:55 – 13:00)": (time(11, 55), time(13, 0)),
}


# ================= TODAY STATUS =================
today_att = attendance_log[
    (attendance_log["email"] == email) &
    (attendance_log["date"] == TODAY)
]

st.title("🗓 Attendance Tracker")
st.metric("Today's Attendance", f"{len(today_att)} / 5")

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

        if user_row.empty:
            users = pd.concat([users, pd.DataFrame([{
                "email": email,
                "attendance": 1
            }])], ignore_index=True)
        else:
            users.loc[users["email"] == email, "attendance"] = attendance_score + 1

        safe_write(DB, {
            "Users": users,
            "Attendance": attendance_log
        })

        st.success("Attendance marked")
        st.rerun()
else:
    st.info("No active periods right now.")

# ================= SUMMARY =================
st.divider()

user_all = attendance_log[attendance_log["email"] == email]
total_days = user_all["date"].nunique()
total_periods = user_all.shape[0]
possible = max(total_days * 5, 1)

percent = (total_periods / possible) * 100
st.metric("Overall Attendance %", f"{percent:.1f}%")
