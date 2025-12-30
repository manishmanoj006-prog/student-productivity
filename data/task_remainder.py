import pandas as pd
import smtplib
from email.message import EmailMessage
from datetime import datetime, timedelta

DB = "data/database.xlsx"

# 🔐 EMAIL CONFIG
SENDER_EMAIL = "manishmanoj006@gmail.com"
SENDER_PASSWORD = "mcufkqtkowuemzjs"

def send_email(to_email, subject, body):
    msg = EmailMessage()
    msg["From"] = SENDER_EMAIL
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.set_content(body)

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.send_message(msg)

# LOAD TASKS
tasks = pd.read_excel(DB, sheet_name="Tasks")
now = datetime.now()

for i, task in tasks.iterrows():

    if task["Status"] != "Pending":
        continue

    priority = task["Priority"]
    last = task["Last_Reminded"]

    # Priority rules
    if priority == "High":
        hours = 3
    elif priority == "Medium":
        hours = 6
    else:
        hours = 9

    if pd.isna(last) or last == "":
        remind = True
    else:
        last_time = datetime.strptime(last, "%Y-%m-%d %H:%M:%S")
        remind = now - last_time >= timedelta(hours=hours)

    if remind:
        send_email(
            task["Email"],      # 👈 sends to correct user
            f"🔔 Task Reminder: {task['Task']}",
            f"""
Hi,

This is a reminder for your task:

Task: {task['Task']}
Priority: {priority}

Please complete it.

— Student Productivity App
"""
        )
        tasks.loc[i, "Last_Reminded"] = now.strftime("%Y-%m-%d %H:%M:%S")

# SAVE UPDATED TIME
with pd.ExcelWriter(DB, engine="openpyxl", mode="a", if_sheet_exists="replace") as writer:
    tasks.to_excel(writer, sheet_name="Tasks", index=False)
