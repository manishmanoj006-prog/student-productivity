import streamlit as st
import pandas as pd
from pathlib import Path

# ================= PAGE PROTECTION =================
if "logged_in" not in st.session_state or not st.session_state.logged_in:
    st.warning("Please login first.")
    st.switch_page("app.py")

email = st.session_state.email
DB = "data/database.xlsx"

# ================= PAGE CONFIG =================
st.set_page_config(page_title="Settings", layout="wide")
st.title("⚙ Profile & Settings")

# ================= LOAD CSS =================
css_path = Path(__file__).parent.parent / "assets" / "style.css"
with open(css_path) as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# ================= LOAD USERS =================
try:
    users = pd.read_excel(DB, sheet_name="Users", dtype=str)
except:
    users = pd.DataFrame(columns=[
        "email", "name", "monthlygoal", "minattendance"
    ])

users.columns = users.columns.str.strip().str.lower()

# Ensure required columns
for col in ["email", "name", "monthlygoal", "minattendance"]:
    if col not in users.columns:
        users[col] = ""

# ================= GET CURRENT USER =================
user_row = users[users["email"] == email]

if user_row.empty:
    # First-time profile creation
    users = pd.concat(
        [users, pd.DataFrame([{
            "email": email,
            "name": "",
            "monthlygoal": "40",
            "minattendance": "75"
        }])],
        ignore_index=True
    )
    idx = users.index[-1]
else:
    idx = user_row.index[0]

# ================= FORM =================
st.subheader("👤 Student Profile")

name = st.text_input("Full Name", users.loc[idx, "name"])

st.subheader("📚 Academic Settings")

monthly_goal = st.number_input(
    "Monthly Study Goal (hours)",
    min_value=10,
    max_value=300,
    value=int(users.loc[idx, "monthlygoal"] or 40),
    step=5
)

min_attendance = st.number_input(
    "Minimum Attendance Percentage",
    min_value=50,
    max_value=100,
    value=int(users.loc[idx, "minattendance"] or 75),
    step=5
)

# ================= SAVE =================
if st.button("💾 Save Settings"):
    users.loc[idx, "name"] = name.strip()
    users.loc[idx, "monthlygoal"] = str(monthly_goal)
    users.loc[idx, "minattendance"] = str(min_attendance)

    with pd.ExcelWriter(DB, engine="openpyxl", mode="a", if_sheet_exists="replace") as writer:
        users.to_excel(writer, sheet_name="Users", index=False)

        # Preserve other sheets safely
        for sheet in ["Habits", "HabitLog", "StudyLog", "Attendance", "Tasks"]:
            try:
                pd.read_excel(DB, sheet_name=sheet).to_excel(
                    writer, sheet_name=sheet, index=False
                )
            except:
                pass

    st.success("✅ Profile & settings updated successfully!")
