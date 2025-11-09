import streamlit as st
from utils.login import login_user
from views.daily_workout import show_daily_workout
from views.full_schedule import show_full_schedule
from views.progress_tracker import show_progress_tracker

st.set_page_config(page_title="Workout Scheduler", page_icon="💪", layout="wide")

# --- Login / Team Selection ---
username, schedule_key = login_user()

if not username:
    st.stop()

# --- Sidebar Navigation ---
st.sidebar.title("🏋️ Workout Scheduler")
view_mode = st.sidebar.radio(
    "Choose View",
    ["Daily Workout", "Full 4-Week Schedule", "Progress Tracker"]
)

# --- Main Views ---
if view_mode == "Daily Workout":
    show_daily_workout(username, schedule_key)
elif view_mode == "Full 4-Week Schedule":
    show_full_schedule(username, schedule_key)
else:
    show_progress_tracker(username)
