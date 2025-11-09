import sys, os
sys.path.append(os.path.dirname(__file__))
import streamlit as st
from utils.login import login_user
from views.daily_workout import show_daily_workout
from views.full_schedule import show_full_schedule
from views.progress_tracker import show_progress_tracker
from views.leaderboard import show_leaderboard


st.set_page_config(page_title="Workout Scheduler", page_icon="💪", layout="wide")

# --- Login / Team Selection ---
username, schedule_key = login_user()

if not username:
    st.stop()

# --- Sidebar Navigation ---
st.sidebar.title("🏋️ Workout Scheduler")
view_mode = st.sidebar.radio(
    "Choose View",
    ["Daily Workout", "Full 4-Week Schedule", "Progress Tracker", "Leaderboard"]
)

# --- Main Views ---
if view_mode == "Daily Workout":
    show_daily_workout(username, schedule_key)
elif view_mode == "Full 4-Week Schedule":
    show_full_schedule(username, schedule_key)
elif view_mode == "Progress Tracker":
    show_progress_tracker(username)
else:
    show_leaderboard()

if entry["user"].lower() == st.session_state.get("username", "").lower():
    st.markdown(f"<div style='background-color:#222;padding:6px;border-radius:8px;'>"
                f"⭐ **You** — {entry['total']} workouts ({entry['team']})</div>", unsafe_allow_html=True)
    continue

