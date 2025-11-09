import streamlit as st
import time
import json
import os
from helpers import (
    load_weights, update_weight, generate_base_day, build_user_day_from_base,
    mark_workout_done, check_workout_done, unmark_workout_done,
    load_progress, load_user_schedule, save_user_schedule,
    get_shared_base_day, set_shared_base_day
)

def show_daily_workout(username, schedule_key):
    """Display daily workout view with timer and set tracking."""
    st.title(f"📅 Daily Workout — {username.title()}")

    # --- Determine Team Sync Info ---
    if schedule_key != username.strip().lower():
        st.info(f"🤝 You're training with team: **{schedule_key.title()}**")

    phase_names = [
        "Build Phase (4–6 reps)",
        "Strength Phase (6–8 reps)",
        "Hypertrophy Phase (8–10 reps)",
        "Deload / Endurance Phase (12–15 reps)",
    ]

    # --- Load user schedule ---
    if "weekly_schedule" not in st.session_state or st.session_state.get("active_user") != schedule_key:
        st.session_state.weekly_schedule = load_user_schedule(schedule_key)
        st.session_state.active_user = schedule_key

    # --- Helper: get or build a day plan ---
    def get_day_plan(week, day):
        if week not in st.session_state.weekly_schedule:
            st.session_state.weekly_schedule[week] = {}

        if day in st.session_state.weekly_schedule[week]:
            return st.session_state.weekly_schedule[week][day]

        base_day = get_shared_base_day(schedule_key, week, day)
        if not base_day:
            base_day = generate_base_day(week, day)
            set_shared_base_day(schedule_key, week, day, base_day)

        user_day = build_user_day_from_base(base_day, week, username)
        st.session_state.weekly_schedule[week][day] = user_day
        save_user_schedule(schedule_key, st.session_state.weekly_schedule)
        return user_day

    # --- Week/Day selectors ---
    week = st.selectbox("Select Week", [1, 2, 3, 4], index=0)
    day = st.radio("Select Day", [1, 2, 3, 4], horizontal=True)
    st.session_state.day_plan = get_day_plan(week, day)

    st.subheader(f"Week {week} – {phase_names[week - 1]}")
    st.caption(f"Day {day}")

    # --- Rest Timer ---
    st.markdown("### 🕒 Rest Timer")
    rest_mins = st.number_input("Minutes", 0, 3, 1, step=1)
    rest_secs = st.number_input("Seconds", 0, 59, 0, step=15)
    total_rest = rest_mins * 60 + rest_secs

    if "timer_running" not in st.session_state:
        st.session_state.timer_running = False
    if "timer_end_time" not in st.session_state:
        st.session_state.timer_end_time = None

    col1, col2 = st.columns(2)
    with col1:
        if st.button("▶️ Start Rest Timer"):
            st.session_state.timer_running = True
            st.session_state.timer_end_time = time.time() + total_rest
            st.rerun()
    with col2:
        if st.session_state.timer_running and st.button("⏹ Cancel Timer"):
            st.session_state.timer_running = False
            st.session_state.timer_end_time = None
            st.rerun()

    if st.session_state.timer_running:
        remaining = int(st.session_state.timer_end_time - time.time())
        if remaining > 0:
            mins, secs = divmod(remaining, 60)
            st.markdown(
                f"<h1 style='text-align:center; color:#00BFFF;'>⏳ {mins:02d}:{secs:02d}</h1>",
                unsafe_allow_html=True,
            )
            time.sleep(1)
            st.rerun()
        else:
            st.session_state.timer_running = False
            st.session_state.timer_end_time = None
            st.success("✅ Rest complete! Let's crush the next set! 💪")

    # --- Today's Workout ---
    st.write("### Today's Workout")

    SET_PROGRESS_DIR = "user_data"
    def get_set_progress_file(user): return os.path.join(SET_PROGRESS_DIR, f"{user}_setprogress.json")

    def load_set_progress(user):
        path = get_set_progress_file(user)
        if os.path.exists(path):
            try:
                with open(path, "r") as f:
                    return json.load(f)
            except json.JSONDecodeError:
                return {}
        return {}

    def save_set_progress(user, data):
        with open(get_set_progress_file(user), "w") as f:
            json.dump(data, f, indent=4)

    # Load or initialize set progress
    set_progress = load_set_progress(username)
    progress_key = f"week{week}_day{day}"
    set_progress.setdefault(progress_key, {})

    total_sets = total_done = 0
    for group, text in st.session_state.day_plan.items():
        exercise_name = text.split("—")[0].strip()
        st.write(f"**{group}:** {text}")

        if exercise_name not in set_progress[progress_key]:
            set_progress[progress_key][exercise_name] = [False, False, False]

        cols = st.columns(3)
        for i in range(3):
            with cols[i]:
                done = st.checkbox(
                    f"Set {i+1}",
                    value=set_progress[progress_key][exercise_name][i],
                    key=f"{exercise_name}_set{i+1}_{week}_{day}",
                )
                set_progress[progress_key][exercise_name][i] = done

        done_count = sum(set_progress[progress_key][exercise_name])
        total_sets += 3
        total_done += done_count
        st.caption(f"Sets complete: {done_count}/3 ✅")
        st.markdown("---")

    save_set_progress(username, set_progress)
    st.markdown(f"### 🔥 Overall Progress: {total_done}/{total_sets} sets complete!")

    # --- Workout Completion ---
    if check_workout_done(username, week, day):
        st.success("✅ Workout complete! Great job 💪")
        if st.button("↩️ Undo Completion"):
            unmark_workout_done(username, week, day)
            st.warning("Workout unmarked. You can mark it complete again anytime.")
            st.rerun()
    else:
        if st.button("🎉 I Did It!"):
            mark_workout_done(username, week, day)
            st.success("✅ Workout complete! Great job 💪")
            st.rerun()

    # --- Weekly Progress ---
    progress = load_progress(username)
    completed_days = [d for d in range(1, 5) if f"Week {week} Day {d}" in progress]
    pct = len(completed_days) / 4
    st.progress(pct)
    if len(completed_days) == 4:
        st.success("🎯 Week complete!")
    else:
        st.caption(f"Week {week} progress: {len(completed_days)}/4 workouts logged.")
