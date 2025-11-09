import streamlit as st
from helpers import generate_base_day, build_user_day_from_base, load_user_schedule, save_user_schedule

def show_full_schedule(username, schedule_key):
    """Display all 4 weeks of workouts."""
    st.title(f"🗓 Full 4-Week Schedule — {username.title()}")

    phase_names = [
        "Build Phase (4–6 reps)",
        "Strength Phase (6–8 reps)",
        "Hypertrophy Phase (8–10 reps)",
        "Deload / Endurance Phase (12–15 reps)",
    ]

    if "weekly_schedule" not in st.session_state:
        st.session_state.weekly_schedule = load_user_schedule(schedule_key)

    for week_num, phase in enumerate(phase_names, start=1):
        st.markdown(f"## 🏋️ Week {week_num} – {phase}")
        with st.expander(f"View Week {week_num} Workouts"):
            if st.button(f"Regenerate Week {week_num}"):
                st.session_state.weekly_schedule[week_num] = {}
                save_user_schedule(schedule_key, st.session_state.weekly_schedule)
                st.success(f"✅ Week {week_num} regenerated!")

            for day_num in range(1, 5):
                base_day = generate_base_day(week_num, day_num)
                user_day = build_user_day_from_base(base_day, week_num, username)
                st.markdown(f"### Day {day_num}")
                for group, text in user_day.items():
                    st.write(f"- **{group}:** {text}")
                st.divider()
