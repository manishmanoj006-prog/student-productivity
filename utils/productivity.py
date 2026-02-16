import pandas as pd
from datetime import date

DB = "data/database.xlsx"
TODAY = date.today().strftime("%Y-%m-%d")

def calculate_productivity(user_email):

    try:
        tasks = pd.read_excel(DB, sheet_name="Tasks")
    except:
        return 0

    user_tasks = tasks[tasks["Email"] == user_email]

    score = 50   # base score (everyone starts neutral)

    for _, row in user_tasks.iterrows():

        if row["Status"] == "Completed":
            score += 10

        if row["Status"] == "Pending":
            score -= 3

        if row["Priority"] == "High" and row["Status"] == "Pending":
            score -= 7

    # Limit score between 0 and 100
    score = max(0, min(100, score))

    return score
