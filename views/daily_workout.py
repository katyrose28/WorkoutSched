import streamlit as st
import time
import json
import os
import streamlit.components.v1 as components

from helpers import (
    generate_base_day,
    build_user_day_from_base,
    mark_workout_done,
    check_workout_done,
    unmark_workout_done,
    load_progress,
    load_user_schedule,
    save_user_schedule,
)

from exercises import all_groups


def show_daily_workout(username, schedule_key):
    st.title(f"📅 Daily Workout — {username.title()}")

    # =========================
    # 🔑 Normalize schedule key
    # =========================
    mode = schedule_key.strip().lower()
    shared_key = username.strip().lower() if "individual" in mode else schedule_key.strip().lower()

    if shared_key != username.strip().lower():
        st.info(f"🤝 You're training with team: **{shared_key.title()}**")

    phase_names = [
        "Build Phase (4–6 reps)",
        "Strength Phase (6–8 reps)",
        "Hypertrophy Phase (8–10 reps)",
        "Deload / Endurance Phase (12–15 reps)",
    ]

    # =========================
    # 📂 Load & normalize schedule
    # =========================
    if "weekly_schedule" not in st.session_state or st.session_state.get("active_user") != shared_key:
        raw = load_user_schedule(shared_key) or {}
        normalized = {}

        # Normalize JSON keys (strings → ints)
        for w_key, days in raw.items():
            try:
                w = int(w_key)
            except (TypeError, ValueError):
                continue
            normalized[w] = {}
            if isinstance(days, dict):
                for d_key, plan in days.items():
                    try:
                        d = int(d_key)
                    except (TypeError, ValueError):
                        continue
                    normalized[w][d] = plan

        st.session_state.weekly_schedule = normalized
        st.session_state.active_user = shared_key

    # =========================
    # 📅 Selectors
    # =========================
    week = st.selectbox("Select Week", [1, 2, 3, 4], index=0)
    day = st.radio("Select Day", [1, 2, 3, 4], horizontal=True)

    st.subheader(f"Week {week} – {phase_names[week - 1]}")
    st.caption(f"Day {day}")

    # =========================
    # 🧠 Get or generate day plan
    # =========================
    st.session_state.weekly_schedule.setdefault(week, {})

    if day not in st.session_state.weekly_schedule[week]:
        base_day = generate_base_day(week, day)
        user_day = build_user_day_from_base(base_day, week, username)
        st.session_state.weekly_schedule[week][day] = user_day
        save_user_schedule(shared_key, st.session_state.weekly_schedule)

    day_plan = st.session_state.weekly_schedule[week][day]

    # =========================
    # 🕒 Rest Timer
    # =========================
    st.markdown("### 🕒 Rest Timer")

    minutes = st.number_input("Minutes", min_value=0, value=1)
    seconds = st.number_input("Seconds", min_value=0, value=0, step=5)
    total_seconds = minutes * 60 + seconds

    if st.button("▶️ Start Rest Timer"):
        placeholder = st.empty()
        end_time = time.time() + total_seconds

        while time.time() < end_time:
            remaining = int(end_time - time.time())
            m, s = divmod(remaining, 60)
            placeholder.markdown(f"⏳ **{m:02d}:{s:02d} remaining...**")
            time.sleep(1)

        placeholder.markdown("✅ **Time’s up!** ⏰")

        components.html(
            """
            <script>
            function beep(freq, duration) {
              const ctx = new (window.AudioContext || window.webkitAudioContext)();
              const osc = ctx.createOscillator();
              const gain = ctx.createGain();
              osc.connect(gain);
              gain.connect(ctx.destination);
              osc.frequency.value = freq;
              osc.start();
              gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + duration/1000);
              osc.stop(ctx.currentTime + duration/1000);
            }
            async function seq() {
              for (let i=0;i<3;i++){ beep(1000,300); await new Promise(r=>setTimeout(r,500)); }
            }
            seq();
            </script>
            """,
            height=0,
        )

    # =========================
    # 🏋️ Today's Workout
    # =========================
    st.markdown("### 🏋️ Today's Workout")

    if not day_plan:
        st.warning("No workout found for this day.")
    else:
        for group, text in day_plan.items():
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
        day_plan[f"{muscle_group} (Custom)"] = (
            f"{exercise_name} — {weight} lbs, {sets}×{reps}"
        )
        save_user_schedule(shared_key, st.session_state.weekly_schedule)
        st.success(f"Added {exercise_name}")
        st.rerun()

    # =========================
    # 📊 Set Tracking
    # =========================
    SET_PROGRESS_DIR = "user_data"
    os.makedirs(SET_PROGRESS_DIR, exist_ok=True)

    def progress_file(user):
        return os.path.join(SET_PROGRESS_DIR, f"{user}_setprogress.json")

    if os.path.exists(progress_file(username)):
        with open(progress_file(username), "r") as f:
            set_progress = json.load(f)
    else:
        set_progress = {}

    key = f"week{week}_day{day}"
    set_progress.setdefault(key, {})

    total_sets = total_done = 0

    for group, text in day_plan.items():
        exercise = text.split("—")[0].strip()
        set_progress[key].setdefault(exercise, [False, False, False])

        cols = st.columns(3)
        for i in range(3):
            with cols[i]:
                done = st.checkbox(
                    f"{exercise} – Set {i+1}",
                    value=set_progress[key][exercise][i],
                    key=f"{exercise}_{week}_{day}_{i}",
                )
                set_progress[key][exercise][i] = done

        done_count = sum(set_progress[key][exercise])
        total_sets += 3
        total_done += done_count
        st.caption(f"Sets complete: {done_count}/3")
        st.markdown("---")

    with open(progress_file(username), "w") as f:
        json.dump(set_progress, f, indent=2)

    st.markdown(f"### 🔥 Overall Progress: {total_done}/{total_sets} sets complete")

    # =========================
    # ✅ Completion
    # =========================
    if check_workout_done(username, week, day):
        st.success("✅ Workout complete!")
        if st.button("↩️ Undo"):
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
    completed = [d for d in range(1, 5) if f"Week {week} Day {d}" in progress]
    st.progress(len(completed) / 4)
    st.caption(f"Week {week} progress: {len(completed)}/4 workouts logged.")
