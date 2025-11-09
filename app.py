import streamlit as st
import matplotlib.pyplot as plt
from helpers import (
    load_weights, update_weight, generate_day,
    mark_workout_done, check_workout_done,
    load_progress, load_weight_history,
    set_shared_plan, get_shared_plan, save_user_data
)
from exercises import (
    delts, chest, biceps, butt,
    back_lats, back_mids, back_lower, back_combo,
    abs_upper, abs_lower, abs_combo,
    triceps, calf, thighs
)

# --- Streamlit setup ---
st.set_page_config(page_title="Workout Scheduler", page_icon="💪", layout="wide")

# --- Centered Login Section (mobile-friendly) ---
if "user" not in st.session_state:
    st.session_state["user"] = ""

st.title("💪 Workout Scheduler")

if not st.session_state["user"]:
    st.markdown("### 👋 Welcome! Please log in to get started.")
    name_input = st.text_input("Enter your name or nickname:", placeholder="e.g. Katy")

    if name_input:
        st.session_state["user"] = name_input.strip().lower().replace(" ", "_")
        st.success(f"Logged in as: **{st.session_state['user']}**")
        st.rerun()
    else:
        st.warning("Please enter your name to continue.")
        st.stop()

user = st.session_state["user"]
st.sidebar.success(f"Logged in as: {user}")

# --- Workout Buddy Sync ---
st.sidebar.markdown("---")
buddy = st.sidebar.text_input("🏋️ Workout Buddy (optional)", placeholder="Enter their name to sync workouts")
if buddy:
    buddy = buddy.strip().lower().replace(" ", "_")
    st.sidebar.info(f"Syncing workouts with: **{buddy}**")

# --- Persistent schedule ---
if "weekly_schedule" not in st.session_state:
    st.session_state.weekly_schedule = {}

def get_day_plan(week, day):
    """Return or generate a user's workout plan."""
    if week not in st.session_state.weekly_schedule:
        st.session_state.weekly_schedule[week] = {}
    if day not in st.session_state.weekly_schedule[week]:
        st.session_state.weekly_schedule[week][day] = generate_day(week, day)
    return st.session_state.weekly_schedule[week][day]

def get_or_generate_shared_day(owner, week, day, user):
    """Load a shared plan or generate one, syncing for both users."""
    owner = owner.strip().lower()
    user = user.strip().lower()

    shared = get_shared_plan(owner, week, day)
    if shared:
        set_shared_plan(user, week, day, shared)
        return shared

    plan = get_day_plan(week, day)
    set_shared_plan(owner, week, day, plan)
    set_shared_plan(user, week, day, plan)
    return plan

# --- Sidebar Navigation ---
st.sidebar.title("🏋️ Workout Scheduler")
view_mode = st.sidebar.radio("Choose View", ["Daily Workout", "Full 4-Week Schedule", "Progress Tracker"])

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

    # Shared or personal plan
    if buddy:
        st.session_state.day_plan = get_or_generate_shared_day(buddy, week, day, user)
    else:
        st.session_state.day_plan = get_day_plan(week, day)

    st.subheader(f"Week {week} – {phase_names[week - 1]}")
    st.caption(f"Day {day}")
    st.caption(f"👋 Welcome, **{user.title()}** — ready to train?")

    if buddy:
        st.info(f"🤝 Matched with **{buddy.title()}** — you’re sharing workouts!")

    st.write("### Today's Workout")
    for group, text in st.session_state.day_plan.items():
        st.write(f"**{group}:** {text}")

    # --- Workout Completion Section ---
    if check_workout_done(user, week, day):
        st.success("✅ Workout complete! Great job 💪")
        st.button("🎉 I Did It!", disabled=True)
        if st.button("↩️ Undo Completion"):
            progress = load_progress(user)
            key = f"Week {week} Day {day}"
            if key in progress:
                del progress[key]
                save_user_data(user, "progress", progress)
                st.session_state[f"done_{week}_{day}"] = False
                st.warning("Workout unmarked. You can mark it complete again anytime.")
                st.rerun()
    else:
        if st.button("🎉 I Did It!"):
            mark_workout_done(user, week, day)
            st.session_state[f"done_{week}_{day}"] = True
            st.success("✅ Workout complete! Great job 💪")

    # --- Weekly Progress Badge ---
    progress = load_progress(user)
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

        current_weights = load_weights(user)
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
                    update_weight(user, name, val)
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

    st.markdown("### 💪 Weight Progress Over Time")
    weight_history = load_weight_history(user)

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
    progress = load_progress(user)
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
