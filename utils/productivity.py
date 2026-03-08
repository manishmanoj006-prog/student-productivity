import pandas as pd
from datetime import date

DB = "data/database.xlsx"
TODAY = date.today()

def calculate_productivity(user_email):

    score = 0

    # ================= HABITS =================
    try:
        habits = pd.read_excel(DB, sheet_name="Habits")
        habit_log = pd.read_excel(DB, sheet_name="HabitLog")

        habits.columns = habits.columns.str.lower()
        habit_log.columns = habit_log.columns.str.lower()

        total_habits = len(habits)

        habit_log["date"] = pd.to_datetime(habit_log["date"], errors="coerce").dt.date
        habit_log["email"] = habit_log["email"].astype(str).str.lower()

        completed_habits = habit_log[
            (habit_log["email"] == user_email) &
            (habit_log["date"] == TODAY)
        ].shape[0]

        if total_habits > 0:
            score += (completed_habits / total_habits) * 25

    except:
        pass


    # ================= ATTENDANCE =================
    try:
        attendance = pd.read_excel(DB, sheet_name="Attendance")

        attendance.columns = attendance.columns.str.lower()
        attendance["email"] = attendance["email"].astype(str).str.lower()
        attendance["date"] = pd.to_datetime(attendance["date"], errors="coerce").dt.date

        today_att = attendance[
            (attendance["email"] == user_email) &
            (attendance["date"] == TODAY)
        ]

        periods_attended = len(today_att)

        score += (periods_attended / 5) * 25

    except:
        pass


    # ================= TASKS =================
    try:
        tasks = pd.read_excel(DB, sheet_name="Tasks")

        tasks.columns = tasks.columns.str.lower()

        user_tasks = tasks[tasks["email"].astype(str).str.lower() == user_email]

        total_tasks = len(user_tasks)

        completed_tasks = user_tasks[
            user_tasks["status"].astype(str).str.lower() == "completed"
        ].shape[0]

        if total_tasks > 0:
            score += (completed_tasks / total_tasks) * 25

    except:
        pass


    # ================= STUDY =================
    try:
        study = pd.read_excel(DB, sheet_name="StudyLog")

        study.columns = study.columns.str.lower()

        study["email"] = study["email"].astype(str).str.lower()

        date_col = next((c for c in study.columns if "date" in c), None)

        if date_col:
            study[date_col] = pd.to_datetime(study[date_col], errors="coerce")

            today_minutes = study[
                (study["email"] == user_email) &
                (study[date_col].dt.date == TODAY)
            ]["minutes"].astype(float).sum()

            study_hours = today_minutes / 60

            # target = 4 hours study = full 25 points
            score += min(study_hours / 4, 1) * 25

    except:
        pass


    # limit score
    score = round(score)

    score = max(0, min(100, score))

    return score