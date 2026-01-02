import streamlit as st
import time
import json
import os
import streamlit.components.v1 as components

from helpers import (
    load_weights,
    update_weight,
    generate_base_day,
    build_user_day_from_base,
    mark_workout_done,
    check_workout_done,
    unmark_workout_done,
    load_progress,
    load_user_schedule,
    save_user_schedule,
    get_shared_base_day,
    set_shared_base_day,
)

from exercises import all_groups


def show_daily_workout(username, schedule_key):
    """Display daily workout view with timer and set tracking."""
    st.title(f"📅 Daily Workout — {username.title()}")

    # --- Normalize schedule key ---
    # IMPORTANT FIX:
    # Individual mode should use username, not "(Individual)"
    shared_key = username.strip().lower() if schedule_key.lower() == "(individual)" else schedule_key

    # --- Team info ---
    if shared_key != username.strip().lower():
        st.info(f"🤝 You're training with team: **{shared_key.title()}**")

    phase_names = [
        "Build Phase (4–6 reps)",
        "Strength Phase (6–8 reps)",
        "Hypertrophy Phase (8–10 reps)",
        "Deload / Endurance Phase (12–15 reps)",
    ]

    # --- Load weekly schedule ---
    if "weekly_schedule" not in st.session_state or st.session_state.get("active_user") != shared_key:
        st.session_state.weekly_schedule = load_user_schedule(shared_key)
        st.session_state.active_user = shared_key

    # --- Helper: get or build a day plan ---
    def get_day_plan(week, day):
        # Ensure week exists
        st.session_state.weekly_schedule.setdefault(week, {})

        # If the day already exists (from Full Schedule), USE IT
        if day in st.session_state.weekly_schedule[week]:
            return st.session_state.weekly_schedule[week][day]

        # Otherwise generate JUST this day
        base_day = generate_base_day(week, day)
        user_day = build_user_day_from_base(base_day, week, username)

        st.session_state.weekly_schedule[week][day] = user_day
        save_user_schedule(shared_key, st.session_state.weekly_schedule)

        return user_day


    # --- Selectors ---
    week = st.selectbox("Select Week", [1, 2, 3, 4], index=0)
    day = st.radio("Select Day", [1, 2, 3, 4], horizontal=True)

    st.subheader(f"Week {week} – {phase_names[week - 1]}")
    st.caption(f"Day {day}")

    st.session_state.day_plan = get_day_plan(week, day)

    # --- Initialize user-added exercises ---
    if "user_exercises" not in st.session_state:
        st.session_state.user_exercises = {}

    st.session_state.user_exercises.setdefault(week, {})
    st.session_state.user_exercises[week].setdefault(day, [])

    # =========================
    # 🕒 Rest Timer
    # =========================
    st.markdown("### 🕒 Rest Timer")

    minutes = st.number_input("Minutes", min_value=0, value=1, step=1)
    seconds = st.number_input("Seconds", min_value=0, value=0, step=5)
    total_seconds = minutes * 60 + seconds

    if st.button("▶️ Start Rest Timer"):
        placeholder = st.empty()
        end_time = time.time() + total_seconds

        while time.time() < end_time:
            remaining = int(end_time - time.time())
            mins, secs = divmod(remaining, 60)
            placeholder.markdown(f"⏳ **{mins:02d}:{secs:02d} remaining...**")
            time.sleep(1)

        placeholder.markdown("✅ **Time’s up!** ⏰")

        components.html(
            """
            <script>
            function playBeep(freq, duration) {
                const ctx = new (window.AudioContext || window.webkitAudioContext)();
                const osc = ctx.createOscillator();
                const gain = ctx.createGain();
                osc.connect(gain);
                gain.connect(ctx.destination);
                osc.frequency.value = freq;
                osc.start();
                gain.gain.setValueAtTime(1, ctx.currentTime);
                gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + duration / 1000);
                osc.stop(ctx.currentTime + duration / 1000);
            }

            async function beepSequence() {
                for (let i = 0; i < 3; i++) {
                    playBeep(1000, 300);
                    await new Promise(r => setTimeout(r, 500));
                }
            }
            beepSequence();
            </script>
            """,
            height=0,
        )

    # =========================
    # 🏋️ Today's Workout (Base)
    # =========================
    st.markdown("### 🏋️ Today's Workout")

    if not st.session_state.day_plan:
        st.warning("No workout generated for this day.")
    else:
        for group, text in st.session_state.day_plan.items():
            st.write(f"**{group}:** {text}")

    # =========================
    # ➕ Add Exercise
    # =========================
    st.markdown("### ➕ Add Exercise")

    muscle_group = st.selectbox("Muscle Group", list(all_groups.keys()))
    exercise_names = [e[0] for e in all_groups[muscle_group]]
    exercise_name = st.selectbox("Exercise", exercise_names)

    default_weight = dict(all_groups[muscle_group]).get(exercise_name, 0)

    weight = st.number_input("Weight", value=float(default_weight))
    sets = st.number_input("Sets", min_value=1, max_value=10, value=3)
    reps = st.text_input("Reps", "6–8")

    if st.button("Add Exercise"):
        st.session_state.user_exercises[week][day].append(
            {
                "name": exercise_name,
                "muscle_group": muscle_group,
                "weight": weight,
                "sets": sets,
                "reps": reps,
            }
        )
        st.success(f"Added {exercise_name}")

    # =========================
    # 🏋️ User Added Exercises
    # =========================
    if st.session_state.user_exercises[week][day]:
        st.markdown("### 🏋️ Your Added Exercises")
        for ex in st.session_state.user_exercises[week][day]:
            st.markdown(
                f"""
                **{ex['name']}**  
                *{ex['muscle_group']}*  
                {ex['sets']} × {ex['reps']} @ {ex['weight']}
                """
            )

    # =========================
    # 📊 Set Tracking
    # =========================
    SET_PROGRESS_DIR = "user_data"
    os.makedirs(SET_PROGRESS_DIR, exist_ok=True)

    def get_set_progress_file(user):
        return os.path.join(SET_PROGRESS_DIR, f"{user}_setprogress.json")

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

    set_progress = load_set_progress(username)
    progress_key = f"week{week}_day{day}"
    set_progress.setdefault(progress_key, {})

    total_sets = total_done = 0

    for group, text in st.session_state.day_plan.items():
        exercise_name = text.split("—")[0].strip()

        if exercise_name not in set_progress[progress_key]:
            set_progress[progress_key][exercise_name] = [False, False, False]

        cols = st.columns(3)
        for i in range(3):
            with cols[i]:
                done = st.checkbox(
                    f"Set {i + 1}",
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

    # =========================
    # ✅ Workout Completion
    # =========================
    if check_workout_done(username, week, day):
        st.success("✅ Workout complete! Great job 💪")
        if st.button("↩️ Undo Completion"):
            unmark_workout_done(username, week, day)
            st.rerun()
    else:
        if st.button("🎉 I Did It!"):
            mark_workout_done(username, week, day)
            st.rerun()

    # =========================
    # 📈 Weekly Progress
    # =========================
    progress = load_progress(username)
    completed_days = [d for d in range(1, 5) if f"Week {week} Day {d}" in progress]
    pct = len(completed_days) / 4
    st.progress(pct)

    if len(completed_days) == 4:
        st.success("🎯 Week complete!")
    else:
        st.caption(f"Week {week} progress: {len(completed_days)}/4 workouts logged.")
