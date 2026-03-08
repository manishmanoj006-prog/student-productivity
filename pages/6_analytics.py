import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from datetime import date

# ---------------- PAGE CONFIG ----------------
st.set_page_config(page_title="Analytics", layout="wide")

# ---------------- SESSION CHECK ----------------
if "logged_in" not in st.session_state or not st.session_state.logged_in:
    st.warning("Please login first.")
    st.switch_page("app.py")
    st.stop()

if "email" not in st.session_state or not st.session_state.email:
    st.warning("Please login first.")
    st.switch_page("app.py")
    st.stop()

email = st.session_state.email.strip().lower()
DB = "data/database.xlsx"

st.title("📈 Analytics Dashboard")

# ---------------- SAFE EXCEL LOADER ----------------
def load_sheet_safe(sheet_name):
    try:
        df = pd.read_excel(DB, sheet_name=sheet_name)
        df.columns = [str(c).strip().lower() for c in df.columns]
        return df
    except:
        return pd.DataFrame()

# =====================================================
# 📚 STUDY TIME ANALYSIS
# =====================================================
st.subheader("📚 Study Time Analysis")

study = load_sheet_safe("StudyLog")

if study.empty:
    st.info("No study data available.")

else:

    if "email" in study.columns:

        study["email"] = study["email"].astype(str).str.strip().str.lower()

        user_study = study[study["email"] == email]

        if user_study.empty:
            st.info("No study data available.")

        else:

            user_study["minutes"] = pd.to_numeric(
                user_study["minutes"], errors="coerce"
            ).fillna(0)

            subject_summary = user_study.groupby("subject")["minutes"].sum() / 60

            fig, ax = plt.subplots()

            ax.bar(subject_summary.index, subject_summary.values)

            ax.set_ylabel("Hours")
            ax.set_title("Study Time by Subject")

            plt.xticks(rotation=45)
            plt.tight_layout()

            st.pyplot(fig)

st.divider()

# =====================================================
# 🗓 ATTENDANCE ANALYSIS
# =====================================================
st.subheader("🗓 Attendance Analysis")

attendance = load_sheet_safe("Attendance")

if attendance.empty:
    st.info("No attendance data found.")

else:

    required_cols = ["email", "date", "period"]

    if not all(col in attendance.columns for col in required_cols):
        st.error("Attendance sheet format incorrect.")
        st.stop()

    # ---------------- CLEAN DATA ----------------

    attendance["email"] = attendance["email"].astype(str).str.strip().str.lower()

    attendance["date"] = pd.to_datetime(
        attendance["date"], errors="coerce"
    ).dt.date

    attendance = attendance.dropna(subset=["date"])

    attendance = attendance.drop_duplicates(
        subset=["email", "date", "period"]
    )

    user_att = attendance[attendance["email"] == email]

    if user_att.empty:
        st.info("No attendance records yet.")

    else:

        PERIODS_PER_DAY = 5

        # ---------------- PRESENT CLASSES ----------------
        present_classes = len(user_att)

        # ---------------- TOTAL CLASSES LOGIC ----------------
        first_day = user_att["date"].min()
        today = date.today()

        total_days = (today - first_day).days + 1
        total_classes = total_days * PERIODS_PER_DAY

        percent = (present_classes / total_classes) * 100 if total_classes > 0 else 0

        absent_classes = max(0, total_classes - present_classes)

        # ---------------- CHART ----------------
        fig, ax = plt.subplots()

        ax.pie(
            [present_classes, absent_classes],
            labels=["Present", "Absent"],
            autopct="%1.1f%%",
            startangle=90,
            wedgeprops=dict(width=0.4)
        )

        ax.set_title("Overall Attendance")

        st.pyplot(fig)

        # ---------------- METRICS ----------------
        st.metric("Overall Attendance %", f"{percent:.1f}%")

        st.caption(f"Attended Classes: {present_classes} / {total_classes}")

        if percent < 75:
            st.warning("⚠ Attendance below 75%")
        else:
            st.success("✅ Attendance is good")

# =====================================================
# 🔥 HABIT ANALYSIS
# =====================================================
st.subheader("🔥 Habit Analysis")

habit_log = load_sheet_safe("HabitLog")

if habit_log.empty:
    st.info("No habit data available.")

else:

    if "email" in habit_log.columns:

        habit_log["email"] = habit_log["email"].astype(str).str.strip().str.lower()

        user_log = habit_log[habit_log["email"] == email]

        if user_log.empty:
            st.info("No habits recorded yet.")

        else:

            user_log["date"] = pd.to_datetime(
                user_log["date"], errors="coerce"
            ).dt.date

            daily_count = user_log.groupby("date").size()

            fig, ax = plt.subplots()

            ax.plot(
                daily_count.index,
                daily_count.values,
                marker="o"
            )

            ax.set_ylabel("Habits Completed")
            ax.set_xlabel("Date")
            ax.set_title("Daily Habit Completion Trend")

            plt.xticks(rotation=45)
            plt.tight_layout()

            st.pyplot(fig)