import streamlit as st
import os
from helpers import load_progress, get_all_users, get_user_team


def show_leaderboard():
    """Display leaderboard ranking by total workouts completed."""
    st.title("🏆 Leaderboard")

    users = get_all_users()
    leaderboard_data = []

    # --- Gather data per user ---
    for user in users:
        progress = load_progress(user)
        total_done = len(progress)
        team = get_user_team(user) or "(Individual)"

        leaderboard_data.append({
            "user": user,
            "team": team,
            "total": total_done
        })

    # --- Sort: total workouts descending ---
    leaderboard_data.sort(key=lambda x: x["total"], reverse=True)

    if not leaderboard_data:
        st.info("No progress data available yet.")
        return

    # --- Display leaderboard ---
    st.markdown("### 🥇 Top Performers")

    medal_emojis = ["🥇", "🥈", "🥉"]
    current_user = st.session_state.get("username", "").lower()

    for idx, entry in enumerate(leaderboard_data, start=1):
        medal = medal_emojis[idx - 1] if idx <= len(medal_emojis) else "🏋️"

        # Highlight the logged-in user
        if entry["user"].lower() == current_user:
            st.markdown(
                f"<div style='background-color:#222;padding:6px;border-radius:8px;'>"
                f"⭐ **You ({entry['user']})** — {entry['total']} workouts completed "
                f"({entry['team']})</div>",
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                f"{medal} **{entry['user']}** — {entry['total']} workouts completed "
                f"({entry['team']})"
            )

    # --- Team Totals ---
    st.divider()
    st.markdown("### 👥 Team Totals")

    team_totals = {}
    for entry in leaderboard_data:
        team = entry["team"]
        team_totals[team] = team_totals.get(team, 0) + entry["total"]

    sorted_teams = sorted(team_totals.items(), key=lambda x: x[1], reverse=True)

    for idx, (team, total) in enumerate(sorted_teams, start=1):
        medal = medal_emojis[idx - 1] if idx <= len(medal_emojis) else "💪"
        st.markdown(f"{medal} **{team}** — {total} workouts completed total")
