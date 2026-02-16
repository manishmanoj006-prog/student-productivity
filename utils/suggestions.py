import pandas as pd

DB = "data/database.xlsx"

def get_suggestions(user_email):

    try:
        tasks = pd.read_excel(DB, sheet_name="Tasks")
    except:
        return ["Start adding your academic tasks to track performance."]

    user_tasks = tasks[tasks["Email"] == user_email]

    suggestions = []

    pending = len(user_tasks[user_tasks["Status"] == "Pending"])
    completed = len(user_tasks[user_tasks["Status"] == "Completed"])

    high_pending = len(user_tasks[(user_tasks["Priority"] == "High") & (user_tasks["Status"] == "Pending")])

    if pending == 0 and completed == 0:
        suggestions.append("Add tasks regularly to monitor your studies.")

    if pending > completed:
        suggestions.append("You have more pending tasks than completed ones. Focus on clearing backlog.")

    if high_pending >= 2:
        suggestions.append("High priority tasks are pending. Complete them immediately.")

    if completed >= 5:
        suggestions.append("Great consistency! Maintain this study routine.")

    if pending >= 5:
        suggestions.append("Too many pending tasks detected. Plan a study schedule today.")

    if not suggestions:
        suggestions.append("Your performance is balanced. Keep going!")

    return suggestions
