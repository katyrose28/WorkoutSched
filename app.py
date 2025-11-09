import streamlit as st
import matplotlib.pyplot as plt
from helpers import (
    load_weights, update_weight, generate_day,
    mark_workout_done, check_workout_done,
    load_progress, load_weight_history
)
from exercises import (
    delts, chest, biceps, butt,
    back_lats, back_mids, back_lower, back_combo,
    abs_upper, abs_lower, abs_combo,
    triceps, calf, thighs
)

# --- Streamlit Page Setup ---
st.set_page_config(page_title="Workout Scheduler", page_icon="💪", layout="wide")

# --- Persistent Schedule ---
if "weekly_schedule" not in st.session_state:
    st.session_state.weekly_schedule = {}

def get_day_plan(week, day):
    """Return a consistent plan for the given week/day."""
    if week not in st.session_state.weekly_schedule:
        st.session_state.weekly_schedule[week] = {}
    if day not in st.session_state.weekly_schedule[week]:
        st.session_state.weekly_schedule[week][day] = generate_day(week, day)
    return st.session_state.weekly_schedule[week][day]

# --- Sidebar ---
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

# === DAILY WORKOUT ===
if view_mode == "Daily Workout":
    st.title("📅 Daily Workout Mode")

    week = st.selectbox("Select Week", [1, 2, 3, 4], index=0)
    day = st.radio("Select Day", [1, 2, 3, 4], horizontal=True)

    # Always auto-generate the workout when switching week/day
    st.session_state.day_plan = get_day_plan(week, day)

    st.subheader(f"Week {week} – {phase_names[week - 1]}")
    st.caption(f"Day {day}")

    # --- Today's Workout ---
    st.write("### Today's Workout")
    for group, text in st.session_state.day_plan.items():
        st.write(f"**{group}:** {text}")

    # --- Workout Completion with Undo Option ---
    if check_workout_done(week, day):
        st.success("✅ Workout complete! Great job 💪")

        # Disable the "I Did It!" button when done
        st.button("🎉 I Did It!", disabled=True)

        # Add a small undo button
        if st.button("↩️ Undo Completion"):
            progress = load_progress()
            key = f"Week {week} Day {day}"
            if key in progress:
                del progress[key]
                with open("progress_data.json", "w") as f:
                    import json
                    json.dump(progress, f, indent=4)
                st.session_state[f"done_{week}_{day}"] = False
                st.warning("Workout unmarked. You can mark it complete again anytime.")
                st.rerun()
        else:
        # Only show the button if not done
          if st.button("🎉 I Did It!"):
            mark_workout_done(week, day)
            st.session_state[f"done_{week}_{day}"] = True
            st.success("✅ Workout complete! Great job 💪")



    # --- Weekly Progress Badge ---
    progress = load_progress()
    completed_days = [
        d for d in range(1, 5)
        if f"Week {week} Day {d}" in progress
    ]

    if len(completed_days) == 4:
        st.success(f"🎯 Week {week} complete! 4/4 workouts logged.")
    else:
        pct = len(completed_days) / 4
        st.progress(pct)
        st.caption(f"Week {week} progress: {len(completed_days)}/4 workouts logged.")

    # --- Update Weights (Week 1 Only) ---
    if week == 1:
        st.markdown("---")
        st.subheader("🏋️ Update Today's Weights")
        st.caption("If you improved any of today's lifts, enter the new weight below:")

        current_weights = load_weights()
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
                    update_weight(name, val)
                st.success("✅ Updated today's exercise weights!")
        else:
            st.info("No changes yet — adjust a weight above to enable saving.")

# === FULL 4-WEEK SCHEDULE ===
elif view_mode == "Full 4-Week Schedule":
    st.title("🗓 Full 4-Week Schedule")
    for week_num, phase in enumerate(phase_names, start=1):
        st.markdown(f"## 🏋️ Week {week_num} – {phase}")
        with st.expander(f"View Week {week_num} Workouts"):
            if st.button(f"Regenerate Week {week_num}"):
                st.session_state.weekly_schedule[week_num] = {}
                st.success(f"✅ Week {week_num} regenerated!")

            for day_num in range(1, 5):
                day_plan = get_day_plan(week_num, day_num)
                st.markdown(f"### Day {day_num}")
                for group, text in day_plan.items():
                    st.write(f"- **{group}:** {text}")
                st.divider()

# === PROGRESS TRACKER ===
elif view_mode == "Progress Tracker":
    st.title("📈 Progress Tracker")

    # --- 💪 Weight Progress Section ---
    st.markdown("### 💪 Weight Progress Over Time")
    weight_history = load_weight_history()

    # Gather all known exercises
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

            # 🎨 Plot trend line
            fig, ax = plt.subplots(figsize=(6, 3))
            ax.plot(dates, weights, marker="o", linewidth=2, color="deepskyblue")

            # Show trend direction
            trend = "🔺" if weights[-1] > weights[-2] else "🔻"
            ax.set_title(f"{selected} Progress Over Time {trend}")
            ax.set_xlabel("Date")
            ax.set_ylabel("Weight (lbs)")
            plt.xticks(rotation=30, ha="right")
            st.pyplot(fig)

            # Show PR
            pr = max(weights)
            st.success(f"🏆 Personal Record for **{selected}: {pr} lbs**")

        elif selected in weight_history:
            st.info(f"Only one entry for **{selected}** so far — update again to see progress!")
        else:
            st.info("No data yet for this exercise — update it in Week 1 to begin tracking!")
    else:
        st.info("No exercises found — complete a workout to start tracking!")

    st.markdown("---")

    # --- 🗓 Weekly Progress Overview ---
    progress = load_progress()
    if progress:
        st.markdown("### 🏁 Weekly Progress Overview")

        # Count workouts by week
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
