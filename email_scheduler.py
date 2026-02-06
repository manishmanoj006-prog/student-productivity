import pandas as pd
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from pathlib import Path

BASE = Path(__file__).parent
DB = BASE / "data" / "database.xlsx"
LOG = BASE / "scheduler_log.txt"

REMINDER_HOURS = {
    "High": 3,
    "Medium": 6,
    "Low": 9
}

def log(msg):
    with open(LOG, "a") as f:
        f.write(f"{datetime.now()} - {msg}\n")

def send_email(to, subject, body):
    import streamlit as st
    sender = st.secrets["EMAIL_USER"]
    password = st.secrets["EMAIL_PASS"]

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = sender
    msg["To"] = to

    server = smtplib.SMTP("smtp.gmail.com", 587)
    server.starttls()
    server.login(sender, password)
    server.send_message(msg)
    server.quit()

log("Scheduler started")

try:
    tasks = pd.read_excel(DB, sheet_name="Tasks", dtype=str)
except Exception as e:
    log(f"ERROR reading Excel: {e}")
    raise

tasks.columns = tasks.columns.str.strip()

now = datetime.now()

for idx, row in tasks.iterrows():
    try:
        email = str(row["Email"]).strip().lower()
        status = str(row["Status"]).strip()
        priority = str(row["Priority"]).strip()

        if status != "Pending":
            continue

        hours = REMINDER_HOURS.get(priority, 9)
        last_sent = row.get("Last_Email_Sent", "")

        send_now = False

        if pd.isna(last_sent) or not str(last_sent).strip():
            send_now = True
        else:
            last_time = pd.to_datetime(last_sent)
            diff = (now - last_time).total_seconds() / 3600
            if diff >= hours:
                send_now = True

        if send_now:
            send_email(
                to=email,
                subject=f"⏰ Task Reminder ({priority})",
                body=f"Reminder for your task:\n\n{row['Task']}\n\nPriority: {priority}"
            )
            tasks.loc[idx, "Last_Email_Sent"] = now.strftime("%Y-%m-%d %H:%M:%S")
            log(f"Email sent to {email} for task {row['Task']}")

    except Exception as e:
        log(f"ERROR processing row {idx}: {e}")

with pd.ExcelWriter(DB, engine="openpyxl", mode="a", if_sheet_exists="replace") as writer:
    tasks.to_excel(writer, sheet_name="Tasks", index=False)

log("Scheduler finished")
