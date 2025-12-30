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
st.set_page_config(page_title="Habits", layout="wide")

# ================= LOAD CSS =================
css_path = Path(__file__).parent.parent / "assets" / "style.css"
with open(css_path) as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# ================= DATABASE =================
DB = "data/database.xlsx"
today = date.today()
today_str = today.strftime("%Y-%m-%d")

# ================= TITLE =================
st.title("✅ Habit Tracker")

# ================= LOAD DATA =================
def load_sheet(name, cols):
    try:
        return pd.read_excel(DB, sheet_name=name, dtype=str)
    except:
        return pd.DataFrame(columns=cols)

habits = load_sheet("Habits", ["Habit"])
habit_log = load_sheet("HabitLog", ["Email", "Date", "Habit"])

# Normalize
habits["Habit"] = habits["Habit"].astype(str).str.strip()
habit_log["Email"] = habit_log["Email"].astype(str).str.strip().str.lower()
habit_log["Date"] = habit_log["Date"].astype(str).str.strip()
habit_log["Habit"] = habit_log["Habit"].astype(str).str.strip()

# ================= STREAK FUNCTION =================
def calculate_streak(log_df, user_email, habit_name):
    dates = log_df[
        (log_df["Email"] == user_email) &
        (log_df["Habit"] == habit_name)
    ]["Date"]

    if dates.empty:
        return 0

    dates = sorted(set(pd.to_datetime(dates).dt.date))
    streak = 0
    current = today

    for d in reversed(dates):
        if d == current:
            streak += 1
            current -= timedelta(days=1)
        else:
            break

    return streak

# ================= TODAY PROGRESS =================
st.subheader("📊 Today's Progress")

total_habits = len(habits)
done_today = habit_log[
    (habit_log["Email"] == email) &
    (habit_log["Date"] == today_str)
]

done_count = len(done_today)
progress = int((done_count / total_habits) * 100) if total_habits > 0 else 0

st.progress(progress / 100)
st.write(f"**{done_count} of {total_habits} habits completed ({progress}%)**")

st.divider()

# ================= ADD HABIT =================
st.subheader("➕ Add New Habit (One Time)")

new_habit = st.text_input("Enter habit name (e.g., Morning Exercise)")

if st.button("Add Habit"):
    clean_habit = new_habit.strip()

    if not clean_habit:
        st.warning("Habit name cannot be empty")
    elif clean_habit in habits["Habit"].values:
        st.info("Habit already exists")
    else:
        habits = pd.concat(
            [habits, pd.DataFrame([{"Habit": clean_habit}])],
            ignore_index=True
        )

        with pd.ExcelWriter(DB, engine="openpyxl", mode="a", if_sheet_exists="replace") as writer:
            habits.to_excel(writer, sheet_name="Habits", index=False)
            habit_log.to_excel(writer, sheet_name="HabitLog", index=False)

        st.success("Habit added successfully!")
        st.rerun()

st.divider()

# ================= MARK TODAY HABITS =================
st.subheader("📝 Mark Today's Habits")

if habits.empty:
    st.info("Add your first habit above.")
    st.stop()

for habit in habits["Habit"]:
    streak = calculate_streak(habit_log, email, habit)

    already_done = (
        (habit_log["Email"] == email) &
        (habit_log["Date"] == today_str) &
        (habit_log["Habit"] == habit)
    ).any()

    col1, col2 = st.columns([4, 1])

    with col1:
        if already_done:
            st.checkbox(habit, value=True, disabled=True)
        else:
            if st.checkbox(habit, key=f"{habit}_{today_str}"):
                habit_log = pd.concat(
                    [habit_log, pd.DataFrame([{
                        "Email": email,
                        "Date": today_str,
                        "Habit": habit
                    }])],
                    ignore_index=True
                )

                with pd.ExcelWriter(DB, engine="openpyxl", mode="a", if_sheet_exists="replace") as writer:
                    habits.to_excel(writer, sheet_name="Habits", index=False)
                    habit_log.to_excel(writer, sheet_name="HabitLog", index=False)

                st.success(f"Marked '{habit}' as completed today!")
                st.rerun()

    with col2:
        st.markdown(f"🔥 **{streak} days**")

# ================= WEEKLY SUMMARY =================
st.divider()
st.subheader("📅 Last 7 Days Summary")

last_7_days = [
    (today - timedelta(days=i)).strftime("%Y-%m-%d")
    for i in range(6, -1, -1)
]

weekly_data = []

for habit in habits["Habit"]:
    row = {"Habit": habit}
    for d in last_7_days:
        row[d] = "✅" if (
            (habit_log["Email"] == email) &
            (habit_log["Habit"] == habit) &
            (habit_log["Date"] == d)
        ).any() else "❌"
    weekly_data.append(row)

weekly_df = pd.DataFrame(weekly_data)
st.dataframe(weekly_df, use_container_width=True)
