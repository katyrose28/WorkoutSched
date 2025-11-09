import os
import streamlit as st
import json
from helpers import load_progress, get_all_users, get_user_team

def show_leaderboard():
    st.title("🏆 Leaderboard")

    users = get_all_users()
    progress_data = {}
    team_totals = {}

    # Collect all users' progress
    for user in users:
        data = load_progress(user)
        team = get_user_team(user) or "(Individual)"
        completed = len(data)
        progress_data[user] = {
            "completed": completed,
            "team": team,
            "weeks": {f"Week {w}": 0 for w in range(1, 5)},
        }

        # Count per week
        for key in data.keys():
            try:
                week_num = int(key.split()[1])
                progress_data[user]["weeks"][f"Week {week_num}"] += 1
            except Exception:
                continue

        # Update team totals
        team_totals.setdefault(team, 0)
        team_totals[team] += completed

    # --- Sort by total completions ---
    leaderboard = sorted(progress_data.items(), key=lambda x: x[1]["completed"], reverse=True)

    st.subheader("🥇 Top Performers")
    for i, (user, data) in enumerate(leaderboard):
        medal = ["🥇", "🥈", "🥉"][i] if i < 3 else "🏅"
        name = user
        current_user = st.session_state.get("username", "").lower()

        # Highlight your own row
        if user.lower() == current_user:
            st.markdown(
                f"<div style='background-color:#222;padding:6px;border-radius:8px;'>"
                f"⭐ **You ({user})** — {data['completed']} workouts completed ({data['team']})</div>",
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                f"{medal} **{name}** — {data['completed']} workouts completed ({data['team']})"
            )

    # --- Team Totals ---
    st.divider()
    st.subheader("👥 Team Totals")
    for i, (team, total) in enumerate(sorted(team_totals.items(), key=lambda x: x[1], reverse=True)):
        medal = ["🥇", "🥈", "🥉"][i] if i < 3 else "🏅"
        st.markdown(f"{medal} **{team}** — {total} workouts completed total")

    # --- Detailed Weekly Breakdown ---
    st.divider()
    st.subheader("🔍 Weekly Progress")

    st.caption("Each block = 1 workout. ✅ = completed, ⬜ = not yet done.")

    weeks = ["Week 1", "Week 2", "Week 3", "Week 4"]
    cols = ["Name"] + weeks + ["Total"]
    table = []

    for user, data in progress_data.items():
        week_counts = [data["weeks"][w] for w in weeks]
        row = [user]
        total = data["completed"]
        for count in week_counts:
            filled = "✅" * count + "⬜" * (4 - count)
            row.append(filled)
        row.append(f"{total}/16")
        table.append(row)

    # Display table
    st.write("| " + " | ".join(cols) + " |")
    st.write("|" + " --- |" * len(cols))
    for row in table:
        st.write("| " + " | ".join(row) + " |")

    # --- Team Completion Rate ---
    total_possible = len(users) * 16
    total_done = sum(d["completed"] for d in progress_data.values())
    completion_rate = round((total_done / total_possible) * 100, 1) if total_possible else 0
    st.markdown(f"🏁 **Team Completion Rate:** {completion_rate}%")
