import streamlit as st
import pandas as pd
from datetime import date
from pathlib import Path
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# ---------------- PAGE CONFIG ----------------
st.set_page_config(page_title="Tasks", layout="wide")

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

# ---------------- EMAIL CONFIG ----------------
SENDER_EMAIL = st.secrets["SENDER_EMAIL"]
APP_PASSWORD = st.secrets["APP_PASSWORD"]

def send_task_email(receiver_email, task, priority):

    # No mail for low priority
    if priority == "Low":
        return

    if priority == "High":
        subject = "🚨 HIGH PRIORITY TASK ALERT"
        body = f"""
Hello,

You have a HIGH PRIORITY task pending.

Task: {task}

Please complete it as soon as possible.

- Student Productivity Tracker
"""
    else:
        subject = "Task Reminder"
        body = f"""
Hello,

You added a task:

Task: {task}
Priority: Medium

Try to complete it today.

- Student Productivity Tracker
"""

    try:
        msg = MIMEMultipart()
        msg["From"] = SENDER_EMAIL
        msg["To"] = receiver_email
        msg["Subject"] = subject

        msg.attach(MIMEText(body, "plain"))

        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(SENDER_EMAIL, APP_PASSWORD)
        server.send_message(msg)
        server.quit()

    except Exception as e:
        st.error("Email notification failed.")

# ---------------- LOAD DATA ----------------
try:
    tasks = pd.read_excel(DB, sheet_name="Tasks")
except:
    tasks = pd.DataFrame(columns=[
        "Email", "Task", "Priority", "Status", "Created_Date"
    ])

# SAFE USER LOAD
try:
    users = pd.read_excel(DB, sheet_name="Users")
except:
    users = pd.DataFrame(columns=["Email", "Password"])

# ---------------- TITLE ----------------
st.title("📋 Mandatory Tasks")
st.write("Manage important tasks with priority tracking.")

# ---------------- ADD TASK ----------------
st.markdown("<div class='section'>➕ Add New Task</div>", unsafe_allow_html=True)

task_name = st.text_input("Task Name")
priority = st.selectbox("Priority", ["High", "Medium", "Low"])

if st.button("Add Task"):
    if not task_name:
        st.warning("Task name cannot be empty")
    else:
        new_task = pd.DataFrame([{
            "Email": email,
            "Task": task_name,
            "Priority": priority,
            "Status": "Pending",
            "Created_Date": TODAY
        }])

        tasks = pd.concat([tasks, new_task], ignore_index=True)

        # ---- SEND EMAIL HERE ----
        send_task_email(email, task_name, priority)

        with pd.ExcelWriter(DB, engine="openpyxl", mode="a", if_sheet_exists="replace") as writer:
            users.to_excel(writer, sheet_name="Users", index=False)
            tasks.to_excel(writer, sheet_name="Tasks", index=False)

        st.success("Task added successfully ✅")
        st.rerun()

st.divider()

# ---------------- DISPLAY TASKS ----------------
st.subheader("🗂 Your Tasks")

user_tasks = tasks[tasks["Email"] == email]

if user_tasks.empty:
    st.info("No tasks added yet.")
else:
    for i, row in user_tasks.iterrows():
        col1, col2, col3 = st.columns([6, 2, 2])

        with col1:
            st.markdown(f"""
            <div class="card">
                <b>{row['Task']}</b><br>
                <small>Priority: {row['Priority']}</small>
            </div>
            """, unsafe_allow_html=True)

        with col2:
            if row["Status"] == "Pending":
                if st.button("✅ Complete", key=f"done_{i}"):
                    tasks.loc[i, "Status"] = "Completed"

        with col3:
            if st.button("🗑 Delete", key=f"del_{i}"):
                tasks = tasks.drop(i)

    # SAVE UPDATES
    with pd.ExcelWriter(DB, engine="openpyxl", mode="a", if_sheet_exists="replace") as writer:
        users.to_excel(writer, sheet_name="Users", index=False)
        tasks.to_excel(writer, sheet_name="Tasks", index=False)

# ---------------- TASK SUMMARY ----------------
st.divider()
st.subheader("📊 Task Summary")

total = len(user_tasks)
completed = len(user_tasks[user_tasks["Status"] == "Completed"])
pending = total - completed

st.markdown(f"""
<div class="card">
    <div class="card-title">Task Overview</div>
    <div class="stat">Total: {total}</div>
    <div class="card-text">Completed: {completed} | Pending: {pending}</div>
</div>
""", unsafe_allow_html=True)