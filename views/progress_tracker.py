import streamlit as st
import matplotlib.pyplot as plt
from helpers import load_weight_history, load_progress
from exercises import (
    delts, chest, biceps, butt,
    back_lats, back_mids, back_lower, back_combo,
    abs_upper, abs_lower, abs_combo,
    triceps, calf, thighs
)

def show_progress_tracker(username):
    """Show charts and weekly progress summary."""
    st.title(f"📈 Progress Tracker — {username.title()}")

    st.markdown("### 💪 Weight Progress Over Time")
    weight_history = load_weight_history(username)

    # Collect all exercise names
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

    # --- Weekly Completion Progress ---
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
