import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

# ---------------- PAGE CONFIG ----------------
st.set_page_config(page_title="Analytics", layout="wide")

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

st.title("📈 Analytics Dashboard")

# ================================
# 📚 STUDY TIME ANALYSIS
# ================================
st.subheader("📚 Study Time Analysis")

try:
    study = pd.read_excel(DB, sheet_name="StudyLog")
    user_study = study[study["Email"] == email]

    if user_study.empty:
        st.info("No study data available.")
    else:
        subject_summary = user_study.groupby("Subject")["Minutes"].sum() / 60

        fig, ax = plt.subplots()
        ax.bar(subject_summary.index, subject_summary.values)
        ax.set_ylabel("Hours")
        ax.set_title("Study Time by Subject")
        st.pyplot(fig)

except:
    st.warning("Study data not found.")

st.divider()

# ================================
# 🗓 ATTENDANCE ANALYSIS (DONUT)
# ================================
st.subheader("🗓 Attendance Analysis")

try:
    attendance = pd.read_excel(DB, sheet_name="Attendance")
    user_att = attendance[attendance["Email"] == email]

    total_days = user_att["Date"].nunique()
    attended = len(user_att)
    possible = total_days * 5 if total_days > 0 else 1

    percent = (attended / possible) * 100

    # ---- DONUT CHART ----
    fig, ax = plt.subplots()
    ax.pie(
        [percent, 100 - percent],
        labels=["Present", "Absent"],
        autopct="%1.1f%%",
        startangle=90,
        wedgeprops={"width": 0.4}
    )
    ax.set_title("Overall Attendance")
    st.pyplot(fig)

    st.metric("Overall Attendance %", f"{percent:.1f}%")

    if percent < 75:
        st.warning("⚠ Attendance below 75%")
    else:
        st.success("✅ Attendance is good")

except:
    st.warning("Attendance data not found.")

st.divider()

# ================================
# 🔥 HABIT ANALYSIS (FIXED)
# ================================
st.subheader("🔥 Habit Analysis")

try:
    habit_log = pd.read_excel(DB, sheet_name="HabitLog")
    user_log = habit_log[habit_log["Email"] == email]

    if user_log.empty:
        st.info("Not enough days to show habit trend.")
    else:
        daily_count = user_log.groupby("Date").size()

        if len(daily_count) < 2:
            st.info("Not enough days to show habit trend.")
        else:
            fig, ax = plt.subplots()
            ax.plot(daily_count.index, daily_count.values, marker="o")
            ax.set_ylabel("Habits Completed")
            ax.set_xlabel("Date")
            ax.set_title("Daily Habit Completion Trend")
            st.pyplot(fig)

except:
    st.warning("Habit data not found.")
