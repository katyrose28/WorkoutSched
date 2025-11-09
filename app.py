import streamlit as st
import matplotlib.pyplot as plt

from helpers import (
    generate_base_day,
    build_user_day_from_base,
    get_shared_base_day,
    set_shared_base_day,
    load_weights,
    update_weight,
    mark_workout_done,
    unmark_workout_done,
    check_workout_done,
    load_progress,
    load_weight_history,
    set_user_team,
    get_user_team,
    get_all_users,
)

from exercises import (
    delts, chest, biceps, butt,
    back_lats, back_mids, back_lower, back_combo,
    abs_upper, abs_lower, abs_combo,
    triceps, calf, thighs
)

# =========================
# Page Setup
# =========================

st.set_page_config(page_title="Workout Scheduler", page_icon="💪", layout="wide")

# =========================
# Login (centered, mobile-friendly)
# =========================

if "user" not in st.session_state:
    st.session_state["user"] = ""

st.title("💪 Workout Scheduler")

if not st.session_state["user"]:
    st.markdown("### 👋 Welcome! Please log in to get started.")
    name_input = st.text_input("Enter your name or nickname:", placeholder="e.g. katy")

    if name_input:
        st.session_state["user"] = name_input.strip().lower().replace(" ", "_")
        st.success(f"Logged in as **{st.session_state['user']}**")
        st.rerun()
    else:
        st.warning("Please enter your name to continue.")
        st.stop()

user = st.session_state["user"]
st.sidebar.success(f"Logged in as: {user}")

# =========================
# Team Name (Open Sync)
# =========================

st.sidebar.markdown("---")
team_name_input = st.sidebar.text_input(
    "👥 Team Name (optional)",
    placeholder="Share this name to sync workouts"
)

team_name = None
if team_name_input:
    team_name = team_name_input.strip().lower().replace(" ", "_")
    set_user_team(user, team_name)
    st.sidebar.info(f"You're part of team: **{team_name}**")
else:
    existing_team = get_user_team(user)
    if existing_team:
        team_name = existing_team
        st.sidebar.info(f"You're part of team: **{team_name}**")

# =========================
# Base schedule caching
# =========================

if "personal_base_schedule" not in st.session_state:
    st.session_state.personal_base_schedule = {}  # {week: {day: base_day}}


def get_personal_base_day(week, day):
    if week not in st.session_state.personal_base_schedule:
        st.session_state.personal_base_schedule[week] = {}
    if day not in st.session_state.personal_base_schedule[week]:
        st.session_state.personal_base_schedule[week][day] = generate_base_day(week, day)
    return st.session_state.personal_base_schedule[week][day]


def get_team_base_day(team, week, day):
    base = get_shared_base_day(team, week, day)
    if base:
        return base
    base = generate_base_day(week, day)
    set_shared_base_day(team, week, day, base)
    return base


# =========================
# Sidebar Navigation
# =========================

st.sidebar.title("🏋️ Navigation")
view_mode = st.sidebar.radio(
    "Choose View",
    ["Daily Workout", "Full 4-Week Schedule", "Progress Tracker", "🏆 Team Dashboard"]
)

phase_names = [
    "Build Phase (4–6 reps)",
    "Strength Phase (6–8 reps)",
    "Hypertrophy Phase (8–10 reps)",
    "Deload / Endurance Phase (12–15 reps)",
]

# =========================
# DAILY WORKOUT
# =========================

if view_mode == "Daily Workout":
    st.title("📅 Daily Workout Mode")

    week = st.selectbox("Select Week", [1, 2, 3, 4], index=0)
    day = st.radio("Select Day", [1, 2, 3, 4], horizontal=True)

    # Decide which template to use
    if team_name:
        base_day = get_team_base_day(team_name, week, day)
    else:
        base_day = get_personal_base_day(week, day)

    day_plan = build_user_day_from_base(base_day, week, user)

    st.subheader(f"Week {week} – {phase_names[week - 1]}")
    st.caption(f"Day {day}")
    st.caption(f"👋 Welcome, **{user.title()}** — ready to train?")

    if team_name:
        st.info(f"🤝 You're synced with **Team {team_name}** — everyone on this team shares the same exercises.")

    st.write("### Today's Workout")
    for group, text in day_plan.items():
        st.write(f"**{group}:** {text}")

    # --- Completion + Undo ---
    if check_workout_done(user, week, day):
        st.success("✅ Workout complete! Great job 💪")
        col1, col2 = st.columns(2)
        with col1:
            st.button("🎉 I Did It!", disabled=True)
        with col2:
            if st.button("↩️ Undo Completion"):
                unmark_workout_done(user, week, day)
                st.warning("Workout unmarked. You can mark it again anytime.")
                st.rerun()
    else:
        if st.button("🎉 I Did It!"):
            mark_workout_done(user, week, day)
            st.success("✅ Workout complete! Great job 💪")
            st.rerun()

    # --- Weekly badge / progress bar ---
    progress = load_progress(user)
    completed_days = [d for d in range(1, 5) if f"Week {week} Day {d}" in progress]
    if len(completed_days) == 4:
        st.success(f"🎯 Week {week} complete! 4/4 workouts logged.")
    else:
        pct = len(completed_days) / 4
        st.progress(pct)
        st.caption(f"Week {week} progress: {len(completed_days)}/4 workouts logged.")

    # --- Update weights (Week 1 only) ---
    if week == 1:
        st.markdown("---")
        st.subheader("🏋️ Update Today's Weights")
        st.caption("If you improved any of today's lifts, enter the new weight below:")

        current_weights = load_weights(user)
        updates = {}

        for group, text in day_plan.items():
            exercise_name = text.split("—")[0].strip()

            # Try to parse current numeric weight (ignore 'try' and 'deload')
            try:
                right = text.split("—", 1)[1]
                if "deload" in right.lower():
                    raise ValueError
                # before any comma / 'try'
                num_str = right.split("lbs")[0].split(",")[0].replace("try", "").strip()
                current_display_weight = float(num_str)
            except Exception:
                current_display_weight = None

            if current_display_weight:
                new_val = st.number_input(
                    f"{exercise_name}",
                    value=float(current_weights.get(exercise_name, current_display_weight)),
                    step=2.5,
                    key=f"update_{exercise_name}"
                )
                if new_val != current_weights.get(exercise_name, current_display_weight):
                    updates[exercise_name] = new_val

        if updates:
            if st.button("💾 Save Today's Updates"):
                for name, val in updates.items():
                    update_weight(user, name, val)
                st.success("✅ Updated today's exercise weights & logged history!")
        else:
            st.info("No changes yet — tweak a value above to enable saving.")

# =========================
# FULL 4-WEEK SCHEDULE
# =========================

elif view_mode == "Full 4-Week Schedule":
    st.title("🗓 Full 4-Week Schedule")

    for week_num, phase in enumerate(phase_names, start=1):
        st.markdown(f"## 🏋️ Week {week_num} – {phase}")
        with st.expander(f"View Week {week_num} Workouts"):
            for day_num in range(1, 5):
                if team_name:
                    base_day = get_team_base_day(team_name, week_num, day_num)
                else:
                    base_day = get_personal_base_day(week_num, day_num)

                day_plan = build_user_day_from_base(base_day, week_num, user)

                st.markdown(f"### Day {day_num}")
                for group, text in day_plan.items():
                    st.write(f"- **{group}:** {text}")
                st.divider()

# =========================
# PROGRESS TRACKER
# =========================

elif view_mode == "Progress Tracker":
    st.title("📈 Progress Tracker")

    st.markdown("### 💪 Weight Progress Over Time")
    weight_history = load_weight_history(user)

    # Build exercise list from library + history keys
    all_exercises = set()
    for group in [
        delts, chest, biceps, butt,
        back_lats, back_mids, back_lower, back_combo,
        abs_upper, abs_lower, abs_combo,
        triceps, calf, thighs
    ]:
        for ex, _ in group:
            all_exercises.add(ex)
    all_exercises.update(weight_history.keys())
    exercise_names = sorted(all_exercises)

    if exercise_names:
        selected = st.selectbox("Choose an exercise to track", exercise_names)

        if selected in weight_history and len(weight_history[selected]) > 1:
            dates = [e["date"] for e in weight_history[selected]]
            weights = [e["weight"] for e in weight_history[selected]]

            fig, ax = plt.subplots(figsize=(6, 3))
            ax.plot(dates, weights, marker="o")
            trend = "🔺" if weights[-1] > weights[-2] else "🔻"
            ax.set_title(f"{selected} Progress Over Time {trend}")
            ax.set_xlabel("Date")
            ax.set_ylabel("Weight (lbs)")
            plt.xticks(rotation=30, ha="right")
            st.pyplot(fig)

            pr = max(weights)
            st.success(f"🏆 Personal Record for **{selected}: {pr} lbs**")
        elif selected in weight_history:
            st.info(f"Only one entry for **{selected}** so far — log more to see a trend!")
        else:
            st.info("No history yet for this exercise — update it in Week 1 to start tracking.")
    else:
        st.info("No exercises found in history — complete workouts & log weights to see progress.")

    st.markdown("---")

    # Weekly overview
    progress = load_progress(user)
    if progress:
        st.markdown("### 🏁 Weekly Progress Overview")
        week_counts = {}
        for key in progress.keys():
            try:
                parts = key.split()
                w = int(parts[1])
            except Exception:
                continue
            week_counts[w] = week_counts.get(w, 0) + 1

        for w in range(1, 5):
            completed = week_counts.get(w, 0)
            pct = completed / 4
            st.progress(pct)
            st.write(f"**Week {w}:** {completed}/4 workouts")
    else:
        st.info("No workouts logged yet. Go smash one! 💪")

# =========================
# TEAM DASHBOARD (This Week + Leaderboard)
# =========================

elif view_mode == "🏆 Team Dashboard":
    st.title("🏆 Team Dashboard")

    current_team = team_name or get_user_team(user)
    if not current_team:
        st.info("Set a Team Name in the sidebar to see team stats.")
    else:
        st.markdown(f"### Team: **{current_team}**")

        # Collect team members
        members = [
            u for u in get_all_users()
            if get_user_team(u) == current_team
        ]

        if not members:
            st.info("No other members on this team yet. Share your Team Name so others can join.")
        else:
            tab_week, tab_leader = st.tabs(["📅 This Week Only", "🥇 Leaderboard"])

            # ---------- This Week Only ----------
            with tab_week:
                week_choice = st.selectbox("Select Program Week", [1, 2, 3, 4], index=0)
                st.markdown(f"#### Week {week_choice} Check-ins")

                for m in members:
                    progress = load_progress(m)
                    days = [f"Week {week_choice} Day {d}" for d in range(1, 5)]
                    status = ["✅" if key in progress else "⬜" for key in days]
                    completed = status.count("✅")

                    st.write(f"**{m}**: {' '.join(status)}  ({completed}/4)")
                    pct = completed / 4
                    st.progress(pct)

            # ---------- Leaderboard (All-time over 4 weeks) ----------
            with tab_leader:
                st.markdown("#### Overall Leaderboard (Weeks 1–4)")

                leaderboard = []
                for m in members:
                    progress = load_progress(m)
                    count = 0
                    for key in progress.keys():
                        try:
                            parts = key.split()
                            w = int(parts[1])
                            d = int(parts[3])
                            if 1 <= w <= 4 and 1 <= d <= 4:
                                count += 1
                        except Exception:
                            continue
                    pct = count / 16  # 4 weeks * 4 days
                    leaderboard.append((m, count, pct))

                # Sort by pct desc, then name
                leaderboard.sort(key=lambda x: (-x[2], x[0]))

                if not leaderboard:
                    st.info("No team workouts logged yet. Get moving! 💪")
                else:
                    total_completed = sum(x[1] for x in leaderboard)
                    total_possible = len(leaderboard) * 16

                    # Medals map
                    medals = ["🥇", "🥈", "🥉"]

                    for idx, (m, count, pct) in enumerate(leaderboard, start=1):
                        medal = medals[idx - 1] if idx <= 3 else "⭐"
                        st.write(f"{medal} **{m}** — {count}/16 workouts ({round(pct*100)}%)")
                        st.progress(pct)

                    if total_possible > 0:
                        team_pct = total_completed / total_possible
                        st.markdown("---")
                        st.success(
                            f"🏁 Team Completion Rate: **{round(team_pct * 100)}%** "
                            f"({total_completed}/{total_possible} workouts logged)"
                        )
