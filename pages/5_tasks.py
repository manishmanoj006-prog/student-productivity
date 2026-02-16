import streamlit as st
import pandas as pd
from datetime import date, datetime
from pathlib import Path
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import threading
import time

# ---------------- PAGE CONFIG ----------------
st.set_page_config(page_title="Tasks", layout="wide")

# ---------------- LOAD CSS ----------------
css_path = Path(__file__).parent.parent / "assets" / "style.css"
if css_path.exists():
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

# ---------------- EMAIL FUNCTION ----------------
def send_task_email(receiver_email, task, priority):

    if priority == "Low":
        return

    if priority == "High":
        subject = "🚨 HIGH PRIORITY TASK ALERT"
        body = f"""
Hello,

You still have a HIGH PRIORITY pending task.

Task: {task}

Please complete it immediately.

- Student Productivity Tracker
"""
    else:
        subject = "Task Reminder"
        body = f"""
Hello,

Reminder to complete your task:

Task: {task}
Priority: Medium

- Student Productivity Tracker
"""

    try:
        msg = MIMEMultipart()
        msg["From"] = SENDER_EMAIL
        msg["To"] = receiver_email
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))

        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.ehlo()
        server.starttls()
        server.ehlo()
        server.login(SENDER_EMAIL, APP_PASSWORD)
        server.send_message(msg)
        server.quit()

        print("Reminder mail sent")

    except Exception as e:
        print("MAIL ERROR:", e)

# ---------------- LOAD DATA ----------------
def load_tasks():
    try:
        return pd.read_excel(DB, sheet_name="Tasks")
    except:
        return pd.DataFrame(columns=[
            "Email", "Task", "Priority", "Status", "Created_Date", "Last_Reminded"
        ])

def load_users():
    try:
        return pd.read_excel(DB, sheet_name="Users")
    except:
        return pd.DataFrame(columns=["Email", "Password"])

tasks = load_tasks()
users = load_users()

# ---------------- REMINDER INTERVALS (HOURS) ----------------
REMINDER_INTERVAL = {
    "High": 3,
    "Medium": 6,
    "Low": 9
}

def should_send(priority, last_reminded):

    if last_reminded == "" or str(last_reminded) == "nan":
        return True

    try:
        last_time = datetime.strptime(str(last_reminded), "%Y-%m-%d %H:%M:%S")
    except:
        return True

    hours_passed = (datetime.now() - last_time).total_seconds() / 3600

    return hours_passed >= REMINDER_INTERVAL.get(priority, 6)

# ---------------- REMINDER ENGINE ----------------
def check_pending_tasks():

    tasks_df = load_tasks()
    updated = False

    for i, row in tasks_df.iterrows():

        if row["Status"] != "Pending":
            continue

        priority = row["Priority"]
        last_reminded = row.get("Last_Reminded", "")

        if should_send(priority, last_reminded):
            print(f"Sending reminder for: {row['Task']}")
            send_task_email(row["Email"], row["Task"], priority)

            tasks_df.loc[i, "Last_Reminded"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            updated = True

    if updated:
        with pd.ExcelWriter(DB, engine="openpyxl", mode="a", if_sheet_exists="replace") as writer:
            users.to_excel(writer, sheet_name="Users", index=False)
            tasks_df.to_excel(writer, sheet_name="Tasks", index=False)

# ---------------- BACKGROUND THREAD ----------------
def background_reminder():
    while True:
        check_pending_tasks()
        time.sleep(300)  # check every 5 minutes

# start ONLY ONCE
if "scheduler_running" not in st.session_state:
    st.session_state.scheduler_running = True
    threading.Thread(target=background_reminder, daemon=True).start()

# ---------------- UI ----------------
st.title("📋 Mandatory Tasks")

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
            "Created_Date": TODAY,
            "Last_Reminded": ""
        }])

        tasks = pd.concat([tasks, new_task], ignore_index=True)

        with pd.ExcelWriter(DB, engine="openpyxl", mode="a", if_sheet_exists="replace") as writer:
            users.to_excel(writer, sheet_name="Users", index=False)
            tasks.to_excel(writer, sheet_name="Tasks", index=False)

        st.success("Task added successfully ✅")
        st.rerun()

# ---------------- DISPLAY TASKS ----------------
st.subheader("🗂 Your Tasks")

user_tasks = tasks[tasks["Email"] == email]

for i, row in user_tasks.iterrows():

    col1, col2, col3 = st.columns([6,2,2])

    with col1:
        st.write(f"**{row['Task']}** | Priority: {row['Priority']}")

    with col2:
        if row["Status"] == "Pending":
            if st.button("✅ Complete", key=f"done_{i}"):
                tasks.loc[i, "Status"] = "Completed"

    with col3:
        if st.button("🗑 Delete", key=f"del_{i}"):
            tasks = tasks.drop(i)

with pd.ExcelWriter(DB, engine="openpyxl", mode="a", if_sheet_exists="replace") as writer:
    users.to_excel(writer, sheet_name="Users", index=False)
    tasks.to_excel(writer, sheet_name="Tasks", index=False)

# ---------------- SUMMARY ----------------
st.divider()

total = len(user_tasks)
completed = len(user_tasks[user_tasks["Status"] == "Completed"])
pending = total - completed

st.write(f"Total Tasks: {total}")
st.write(f"Completed: {completed}")
st.write(f"Pending: {pending}")
