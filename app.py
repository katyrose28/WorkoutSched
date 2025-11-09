import streamlit as st
import matplotlib.pyplot as plt
import time
import json
from helpers import (
    load_weights, update_weight, generate_base_day, build_user_day_from_base,
    mark_workout_done, check_workout_done, unmark_workout_done,
    load_progress, load_weight_history, load_user_schedule, save_user_schedule,
    get_shared_base_day, set_shared_base_day
)
from exercises import (
    delts, chest, biceps, butt,
    back_lats, back_mids, back_lower, back_combo,
    abs_upper, abs_lower, abs_combo,
    triceps, calf, thighs
)

# --- Streamlit Page Setup ---
st.set_page_config(page_title="Workout Scheduler", page_icon="💪", layout="wide")

# --- User Login ---
st.sidebar.title("👋 Login")
username = st.sidebar.text_input("Enter your name:")
buddy_name = st.sidebar.text_input("Workout Buddy (optional):")

if not username:
    st.warning("Please enter your name to continue.")
    st.stop()

# --- Determine team/sync key ---
schedule_key = buddy_name.strip().lower() if buddy_name else username.strip().lower()

# --- Load user's schedule ---
if "weekly_schedule" not in st.session_state or st.session_state.get("active_user") != schedule_key:
    st.session_state.weekly_schedule = load_user_schedule(schedule_key)
    st.session_state.active_user = schedule_key

# --- Sidebar Navigation ---
st.sidebar.title("🏋️ Workout Scheduler")
view_mode = st.sidebar.radio(
    "Choose View",
    ["Daily Workout", "Full 4-Week Schedule", "Progress Tracker"]
)

phase_names = [
    "Build Phase (4–6 reps)",
    "Strength Phase (6–8 reps)",
    "Hypertrophy Phase (8–10 reps)",
    "Deload / Endurance Phase (12–15 reps)",
]

# --- Helper: Get or create a consistent workout plan ---
def get_day_plan(week, day):
    """Return a consistent day plan for the team or user."""
    if week not in st.session_state.weekly_schedule:
        st.session_state.weekly_schedule[week] = {}

    if day in st.session_state.weekly_schedule[week]:
        return st.session_state.weekly_schedule[week][day]

    # Shared team logic
    base_day = get_shared_base_day(schedule_key, week, day)
    if not base_day:
        base_day = generate_base_day(week, day)
        set_shared_base_day(schedule_key, week, day, base_day)

    # Build user-specific plan (weights, week scaling)
    user_day = build_user_day_from_base(base_day, week, username)
    st.session_state.weekly_schedule[week][day] = user_day
    save_user_schedule(schedule_key, st.session_state.weekly_schedule)
    return user_day


# === DAILY WORKOUT ===
if view_mode == "Daily Workout":
    st.title(f"📅 Daily Workout — {username.title()}")
    if buddy_name:
        st.info(f"🤝 Matched with {buddy_name.title()} — you're sharing workouts!")

    week = st.selectbox("Select Week", [1, 2, 3, 4], index=0)
    day = st.radio("Select Day", [1, 2, 3, 4], horizontal=True)

    st.session_state.day_plan = get_day_plan(week, day)

    st.subheader(f"Week {week} – {phase_names[week - 1]}")
    st.caption(f"Day {day}")
    st.write(f"👋 Welcome, {username.title()} — ready to train?")

    # --- 🕒 Global Rest Timer ---
    st.markdown("### 🕒 Rest Timer")
    duration = st.slider("Select rest duration (seconds)", 30, 180, 60, step=30)

    if "timer_running" not in st.session_state:
        st.session_state.timer_running = False
    if "timer_end_time" not in st.session_state:
        st.session_state.timer_end_time = None

    col1, col2 = st.columns(2)
    with col1:
        if st.button("▶️ Start Rest Timer"):
            st.session_state.timer_running = True
            st.session_state.timer_end_time = time.time() + duration
            st.rerun()
    with col2:
        if st.session_state.timer_running:
            if st.button("⏹ Cancel Timer"):
                st.session_state.timer_running = False
                st.session_state.timer_end_time = None
                st.rerun()

    if st.session_state.timer_running:
        remaining = int(st.session_state.timer_end_time - time.time())
        if remaining > 0:
            mins, secs = divmod(remaining, 60)
            st.markdown(
                f"<h2 style='text-align:center; color:deepskyblue;'>⏳ {mins:02d}:{secs:02d}</h2>",
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
    for group, text in st.session_state.day_plan.items():
        st.write(f"**{group}:** {text}")

    # --- Workout Completion ---
    if check_workout_done(username, week, day):
        st.success("✅ Workout complete! Great job 💪")
        st.button("🎉 I Did It!", disabled=True)

        if st.button("↩️ Undo Completion"):
            unmark_workout_done(username, week, day)
            st.warning("Workout unmarked. You can mark it complete again anytime.")
            st.rerun()
    else:
        if st.button("🎉 I Did It!"):
            mark_workout_done(username, week, day)
            st.success("✅ Workout complete! Great job 💪")
            st.rerun()

    # --- Weekly Progress Badge ---
    progress = load_progress(username)
    completed_days = [d for d in range(1, 5) if f"Week {week} Day {d}" in progress]
    if len(completed_days) == 4:
        st.success(f"🎯 Week {week} complete! 4/4 workouts logged.")
    else:
        pct = len(completed_days) / 4
        st.progress(pct)
        st.caption(f"Week {week} progress: {len(completed_days)}/4 workouts logged.")

    # --- Update Weights (Week 1 only) ---
    if week == 1:
        st.markdown("---")
        st.subheader("🏋️ Update Today's Weights")
        st.caption("If you improved any of today's lifts, enter the new weight below:")

        current_weights = load_weights(username)
        updates = {}

        for group, details in st.session_state.day_plan.items():
            exercise_name = details.split("—")[0].strip()
            try:
                current_weight = float(details.split("—")[1].split("lbs")[0].strip())
            except:
                current_weight = None

            if current_weight:
                new_val = st.number_input(
                    f"{exercise_name}",
                    value=current_weights.get(exercise_name, current_weight),
                    step=2.5,
                    key=f"update_{exercise_name}"
                )
                if new_val != current_weights.get(exercise_name, current_weight):
                    updates[exercise_name] = new_val

        if updates:
            if st.button("💾 Save Today's Updates"):
                for name, val in updates.items():
                    update_weight(username, name, val)
                st.success("✅ Updated today's exercise weights!")
        else:
            st.info("No changes yet — adjust a weight above to enable saving.")

# === FULL 4-WEEK SCHEDULE ===
elif view_mode == "Full 4-Week Schedule":
    st.title(f"🗓 Full 4-Week Schedule — {username.title()}")
    for week_num, phase in enumerate(phase_names, start=1):
        st.markdown(f"## 🏋️ Week {week_num} – {phase}")
        with st.expander(f"View Week {week_num} Workouts"):
            if st.button(f"Regenerate Week {week_num}"):
                st.session_state.weekly_schedule[week_num] = {}
                save_user_schedule(schedule_key, st.session_state.weekly_schedule)
                st.success(f"✅ Week {week_num} regenerated!")

            for day_num in range(1, 5):
                day_plan = get_day_plan(week_num, day_num)
                st.markdown(f"### Day {day_num}")
                for group, text in day_plan.items():
                    st.write(f"- **{group}:** {text}")
                st.divider()

# === PROGRESS TRACKER ===
elif view_mode == "Progress Tracker":
    st.title(f"📈 Progress Tracker — {username.title()}")

    st.markdown("### 💪 Weight Progress Over Time")
    weight_history = load_weight_history(username)

    # Collect all exercises
    all_exercises = set()
    for group in [
        delts, chest, biceps, butt, back_lats, back_mids, back_lower,
        back_combo, abs_upper, abs_lower, abs_combo, triceps, calf, thighs
    ]:
        for ex, _ in group:
            all_exercises.add(ex)
    all_exercises.update(weight_history.keys())

    exercise_names = sorted(all_exercises)

    if exercise_names:
        selected = st.selectbox("Choose an exercise to track", exercise_names)

        if selected in weight_history and len(weight_history[selected]) > 1:
            dates = [entry["date"] for entry in weight_history[selected]]
            weights = [entry["weight"] for entry in weight_history[selected]]

            fig, ax = plt.subplots(figsize=(6, 3))
            ax.plot(dates, weights, marker="o", linewidth=2, color="deepskyblue")

            trend = "🔺" if weights[-1] > weights[-2] else "🔻"
            ax.set_title(f"{selected} Progress Over Time {trend}")
            ax.set_xlabel("Date")
            ax.set_ylabel("Weight (lbs)")
            plt.xticks(rotation=30, ha="right")
            st.pyplot(fig)

            pr = max(weights)
            st.success(f"🏆 Personal Record for **{selected}: {pr} lbs**")

        elif selected in weight_history:
            st.info(f"Only one entry for **{selected}** so far — update again to see progress!")
        else:
            st.info("No data yet for this exercise — update it in Week 1 to begin tracking!")
    else:
        st.info("No exercises found — complete a workout to start tracking!")

    st.markdown("---")

    progress = load_progress(username)
    if progress:
        st.markdown("### 🏁 Weekly Progress Overview")

        week_counts = {}
        for key in progress.keys():
            week_num = int(key.split()[1])
            week_counts[week_num] = week_counts.get(week_num, 0) + 1

        for week_num in range(1, 5):
            completed = week_counts.get(week_num, 0)
            pct = completed / 4
            st.progress(pct)
            st.write(f"**Week {week_num}:** {completed}/4 workouts")

    else:
        st.info("No workouts logged yet. Go smash one! 💪")
