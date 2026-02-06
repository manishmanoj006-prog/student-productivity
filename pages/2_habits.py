import streamlit as st
import pandas as pd
from datetime import date, timedelta
from pathlib import Path

# ================= PAGE CONFIG =================
st.set_page_config(page_title="Habits", layout="wide")

# ================= AUTH =================
if "logged_in" not in st.session_state or not st.session_state.logged_in:
    st.switch_page("app.py")
    st.stop()

email = st.session_state.email.strip().lower()
DB = Path("data/database.xlsx")
today = date.today().strftime("%Y-%m-%d")

# ================= LOAD CSS =================
css_path = Path(__file__).parent.parent / "assets" / "style.css"
if css_path.exists():
    st.markdown(f"<style>{css_path.read_text()}</style>", unsafe_allow_html=True)

st.title("✅ Habit Tracker")

# ==================================================
# SAFE READ FUNCTION
# ==================================================
def read_sheet(sheet, cols):
    try:
        df = pd.read_excel(DB, sheet_name=sheet, dtype=str)
        df.columns = df.columns.str.strip().str.lower()
        return df
    except:
        return pd.DataFrame(columns=cols)

# ==================================================
# LOAD DATA
# ==================================================
habits = read_sheet("Habits", ["habit"])
habit_log = read_sheet("HabitLog", ["email", "date", "habit"])

# Normalize
habits["habit"] = habits["habit"].astype(str).str.strip()
habit_log["email"] = habit_log["email"].astype(str).str.strip().str.lower()
habit_log["habit"] = habit_log["habit"].astype(str).str.strip()
habit_log["date"] = pd.to_datetime(
    habit_log["date"], errors="coerce"
).dt.strftime("%Y-%m-%d")

# ==================================================
# TODAY PROGRESS
# ==================================================
st.subheader("📊 Today's Progress")

total_habits = len(habits)

done_today = habit_log[
    (habit_log["email"] == email) &
    (habit_log["date"] == today)
]

done_count = len(done_today)
progress = int((done_count / total_habits) * 100) if total_habits else 0

st.progress(progress / 100)
st.write(f"**{done_count} of {total_habits} habits completed ({progress}%)**")

st.divider()

# ==================================================
# ADD NEW HABIT
# ==================================================
st.subheader("➕ Add New Habit")

new_habit = st.text_input("Habit name (e.g. Exercise)")

if st.button("Add Habit"):
    clean = new_habit.strip()

    if not clean:
        st.warning("Habit name cannot be empty")
    elif clean.lower() in habits["habit"].str.lower().tolist():
        st.info("Habit already exists")
    else:
        habits = pd.concat(
            [habits, pd.DataFrame([{"habit": clean}])],
            ignore_index=True
        )
        with pd.ExcelWriter(DB, engine="openpyxl", mode="a", if_sheet_exists="replace") as w:
            habits.to_excel(w, sheet_name="Habits", index=False)
            habit_log.to_excel(w, sheet_name="HabitLog", index=False)

        st.success("Habit added ✅")
        st.rerun()

st.divider()

# ==================================================
# MARK TODAY'S HABITS
# ==================================================
st.subheader("📝 Mark Today's Habits")

if habits.empty:
    st.info("No habits added yet.")
    st.stop()

for habit in habits["habit"]:

    already_done = (
        (habit_log["email"] == email) &
        (habit_log["habit"] == habit) &
        (habit_log["date"] == today)
    ).any()

    col1, col2 = st.columns([4, 1])

    with col1:
        if already_done:
            st.checkbox(habit, value=True, disabled=True)
        else:
            if st.checkbox(habit, key=f"{habit}_{today}"):
                habit_log = pd.concat(
                    [habit_log, pd.DataFrame([{
                        "email": email,
                        "habit": habit,
                        "date": today
                    }])],
                    ignore_index=True
                )

                with pd.ExcelWriter(DB, engine="openpyxl", mode="a", if_sheet_exists="replace") as w:
                    habits.to_excel(w, sheet_name="Habits", index=False)
                    habit_log.to_excel(w, sheet_name="HabitLog", index=False)

                st.success(f"Marked '{habit}' as done ✅")
                st.rerun()

    with col2:
        # -------- STREAK --------
        dates = habit_log[
            (habit_log["email"] == email) &
            (habit_log["habit"] == habit)
        ]["date"]

        streak = 0
        current = date.today()

        for d in sorted(pd.to_datetime(dates, errors="coerce").dt.date, reverse=True):
            if d == current:
                streak += 1
                current -= timedelta(days=1)
            else:
                break

        st.markdown(f"🔥 **{streak}**")

# ==================================================
# WEEKLY SUMMARY
# ==================================================
st.divider()
st.subheader("📅 Last 7 Days Summary")

last_7_days = [
    (date.today() - timedelta(days=i)).strftime("%Y-%m-%d")
    for i in range(6, -1, -1)
]

weekly_data = []

for habit in habits["habit"]:
    row = {"Habit": habit}
    for d in last_7_days:
        row[d] = "✅" if (
            (habit_log["email"] == email) &
            (habit_log["habit"] == habit) &
            (habit_log["date"] == d)
        ).any() else "❌"
    weekly_data.append(row)

st.dataframe(pd.DataFrame(weekly_data), use_container_width=True)
