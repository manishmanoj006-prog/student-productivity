import streamlit as st
import pandas as pd
from datetime import date

st.set_page_config(page_title="Study Time Tracker", layout="wide")

# ---------------- SESSION ----------------
if "logged_in" not in st.session_state or not st.session_state.logged_in:
    st.warning("Please login first.")
    st.switch_page("app.py")
    st.stop()

email = st.session_state.email.strip().lower()
DB = "data/database.xlsx"

st.title("📚 Study Time Tracker")

# ======================================================
# 🧠 ADD SUBJECT SECTION
# ======================================================
st.subheader("➕ Add New Subject")

new_subject = st.text_input("Enter Subject Name")

if st.button("Add Subject"):

    if new_subject.strip() == "":
        st.warning("Enter a valid subject name")
        st.stop()

    try:
        subjects = pd.read_excel(DB, sheet_name="Subjects")
    except:
        subjects = pd.DataFrame(columns=["email", "subject"])

    subjects.columns = [c.strip().lower() for c in subjects.columns]

    if "email" in subjects.columns:
        subjects["email"] = subjects["email"].astype(str).str.strip().str.lower()

    duplicate = (
        (subjects["email"] == email) &
        (subjects["subject"].str.lower() == new_subject.lower())
    )

    if duplicate.any():
        st.info("Subject already added.")
    else:

        new_row = pd.DataFrame({
            "email": [email],
            "subject": [new_subject.strip()]
        })

        subjects = pd.concat([subjects, new_row], ignore_index=True)

        with pd.ExcelWriter(DB, engine="openpyxl", mode="a", if_sheet_exists="replace") as writer:
            subjects.to_excel(writer, sheet_name="Subjects", index=False)

        st.success("Subject added successfully!")

st.divider()

# ======================================================
# 📊 RECORD STUDY TIME
# ======================================================
st.subheader("⏱ Record Study Time")

# load subjects
try:
    subjects = pd.read_excel(DB, sheet_name="Subjects")
    subjects.columns = [c.strip().lower() for c in subjects.columns]
    subjects["email"] = subjects["email"].astype(str).str.strip().str.lower()

    user_subjects = subjects[subjects["email"] == email]["subject"].tolist()

except:
    user_subjects = []

if len(user_subjects) == 0:
    st.warning("Add at least one subject first.")
    st.stop()

subject = st.selectbox("Select Subject", user_subjects)

minutes = st.number_input(
    "Study Time (minutes)",
    min_value=1,
    max_value=600,
    step=5
)

# ---------------- SAVE STUDY TIME ----------------
if st.button("Save Study Time"):

    today = date.today()

    try:
        study_log = pd.read_excel(DB, sheet_name="StudyLog")
    except:
        study_log = pd.DataFrame(columns=["email", "subject", "minutes", "date"])

    study_log.columns = [c.strip().lower() for c in study_log.columns]

    if "email" in study_log.columns:
        study_log["email"] = study_log["email"].astype(str).str.strip().str.lower()

    if not study_log.empty:
        study_log["date"] = pd.to_datetime(study_log["date"], errors="coerce").dt.date

    existing = (
        (study_log["email"] == email) &
        (study_log["subject"] == subject) &
        (study_log["date"] == today)
    )

    if existing.any():

        study_log.loc[existing, "minutes"] = minutes
        st.info("Today's study time updated.")

    else:

        new_row = pd.DataFrame({
            "email": [email],
            "subject": [subject],
            "minutes": [minutes],
            "date": [today]
        })

        study_log = pd.concat([study_log, new_row], ignore_index=True)

        st.success("Study time saved!")

    with pd.ExcelWriter(DB, engine="openpyxl", mode="a", if_sheet_exists="replace") as writer:
        study_log.to_excel(writer, sheet_name="StudyLog", index=False)

st.divider()

# ======================================================
# 📅 TODAY LOG
# ======================================================
st.subheader("Today's Study Record")

try:
    study_log = pd.read_excel(DB, sheet_name="StudyLog")
    study_log.columns = [c.strip().lower() for c in study_log.columns]

    study_log["email"] = study_log["email"].astype(str).str.strip().str.lower()
    study_log["date"] = pd.to_datetime(study_log["date"], errors="coerce").dt.date

    today_log = study_log[
        (study_log["email"] == email) &
        (study_log["date"] == date.today())
    ]

    if today_log.empty:
        st.info("No study recorded today.")
    else:
        st.dataframe(today_log[["subject", "minutes"]], use_container_width=True)

except:
    st.info("No study data available.")