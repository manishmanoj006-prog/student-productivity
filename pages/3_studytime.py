import streamlit as st
import pandas as pd
from datetime import date, timedelta
from pathlib import Path

# ================= PAGE PROTECTION =================
if "logged_in" not in st.session_state or not st.session_state.logged_in:
    st.warning("Please login first.")
    st.switch_page("app.py")

email = st.session_state.email

# ================= PAGE CONFIG =================
st.set_page_config(page_title="Study Time", layout="wide")

# ================= LOAD CSS =================
css_path = Path(__file__).parent.parent / "assets" / "style.css"
with open(css_path) as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# ================= DATABASE =================
DB = "data/database.xlsx"
today = date.today().strftime("%Y-%m-%d")

# ================= TITLE =================
st.title("📚 Study Time Tracker")

# ================= LOAD DATA =================
def load_sheet(name, cols):
    try:
        return pd.read_excel(DB, sheet_name=name, dtype=str)
    except:
        return pd.DataFrame(columns=cols)

study_log = load_sheet("StudyLog", ["Email", "Date", "Subject", "Minutes"])

# ================= NORMALIZE DATA =================
study_log["Email"] = study_log["Email"].astype(str).str.strip().str.lower()
study_log["Date"] = study_log["Date"].astype(str).str.strip()
study_log["Subject"] = study_log["Subject"].astype(str).str.strip()
study_log["Minutes"] = pd.to_numeric(
    study_log["Minutes"], errors="coerce"
).fillna(0).astype(int)

# ================= SUBJECT LISTS =================
all_subjects = sorted(
    study_log[study_log["Email"] == email]["Subject"].unique().tolist()
)

subjects_logged_today = study_log[
    (study_log["Email"] == email) &
    (study_log["Date"] == today)
]["Subject"].tolist()

# ================= TODAY SUMMARY =================
st.subheader("📊 Today's Study Summary")

today_data = study_log[
    (study_log["Email"] == email) &
    (study_log["Date"] == today)
]

total_minutes_today = today_data["Minutes"].sum()
st.metric("⏱ Total Study Time Today", f"{total_minutes_today} minutes")

st.divider()

# ================= ADD STUDY TIME =================
st.subheader("➕ Add Study Time")

mode = st.radio(
    "Choose how to add subject",
    ["Select existing subject", "Add new subject"],
    horizontal=True
)

minutes = st.number_input(
    "Study time (minutes)",
    min_value=10,
    max_value=600,
    step=5
)

# -------- SELECT EXISTING SUBJECT --------
if mode == "Select existing subject":
    if not all_subjects:
        st.info("No subjects found. Add a new subject first.")
    else:
        selected_subject = st.selectbox("Select subject", all_subjects)

        if st.button("Add Study Time"):
            mask = (
                (study_log["Email"] == email) &
                (study_log["Date"] == today) &
                (study_log["Subject"].str.lower() == selected_subject.lower())
            )

            if mask.any():
                # UPDATE existing minutes
                study_log.loc[mask, "Minutes"] = (
                    study_log.loc[mask, "Minutes"].astype(int) + minutes
                )
            else:
                # CREATE new row (your merged logic)
                new_row = pd.DataFrame([{
                    "Email": email,
                    "Date": today,
                    "Subject": selected_subject,
                    "Minutes": minutes
                }])

                study_log = pd.concat([study_log, new_row], ignore_index=True)

            with pd.ExcelWriter(
                DB,
                engine="openpyxl",
                mode="a",
                if_sheet_exists="replace"
            ) as writer:
                study_log.to_excel(writer, sheet_name="StudyLog", index=False)

            st.success(f"Added {minutes} minutes to {selected_subject}")
            st.rerun()

# -------- ADD NEW SUBJECT --------
else:
    new_subject = st.text_input("Enter new subject name")
    clean_subject = new_subject.strip()

    if st.button("Add New Subject & Log Time"):
        if not clean_subject:
            st.warning("Subject name cannot be empty")

        elif clean_subject.lower() in [s.lower() for s in subjects_logged_today]:
            st.warning("You have already logged this subject today")

        else:
            new_row = pd.DataFrame([{
                "Email": email,
                "Date": today,
                "Subject": clean_subject,
                "Minutes": minutes
            }])

            study_log = pd.concat([study_log, new_row], ignore_index=True)

            with pd.ExcelWriter(
                DB,
                engine="openpyxl",
                mode="a",
                if_sheet_exists="replace"
            ) as writer:
                study_log.to_excel(writer, sheet_name="StudyLog", index=False)

            st.success(f"Added {minutes} minutes for {clean_subject}")
            st.rerun()

st.divider()

# ================= TODAY SUBJECT VIEW =================
st.subheader("📘 Subject-wise Study (Today)")

if today_data.empty:
    st.info("No study time logged today.")
else:
    st.dataframe(
        today_data[["Subject", "Minutes"]],
        use_container_width=True
    )

# ================= WEEKLY SUMMARY =================
st.divider()
st.subheader("📅 Last 7 Days Study Summary")

weekly_data = []
for i in range(6, -1, -1):
    d = (date.today() - timedelta(days=i)).strftime("%Y-%m-%d")
    mins = study_log[
        (study_log["Email"] == email) &
        (study_log["Date"] == d)
    ]["Minutes"].sum()

    weekly_data.append({
        "Date": d,
        "Total Minutes": mins
    })

weekly_df = pd.DataFrame(weekly_data)
st.dataframe(weekly_df, use_container_width=True)
