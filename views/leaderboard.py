# views/leaderboard.py

import streamlit as st
from helpers import load_progress, get_user_team, get_all_users


def show_leaderboard(current_user: str | None = None):
    st.title("🏆 Leaderboard")

    users = get_all_users()

    if not users:
        st.info("No users found yet. Once someone logs a workout, the leaderboard will appear here.")
        return

    # =========================
    # Build per-user progress snapshot
    # =========================
    weeks = ["Week 1", "Week 2", "Week 3", "Week 4"]

    progress_data = {}  # {user: {"team": str, "completed": int, "weeks": {Week X: count}}}

    for user in users:
        progress = load_progress(user)
        team = get_user_team(user) or "(Individual)"

        # Initialize weekly counts
        week_counts = {w: 0 for w in weeks}
        total_completed = 0

        for key in progress.keys():
            # Expect keys like: "Week 1 Day 3"
            parts = key.split()
            if len(parts) != 4 or parts[0] != "Week" or parts[2] != "Day":
                continue

            try:
                week_num = int(parts[1])
            except ValueError:
                continue

            if 1 <= week_num <= 4:
                week_label = f"Week {week_num}"
                week_counts[week_label] += 1
                total_completed += 1

        progress_data[user] = {
            "team": team,
            "completed": total_completed,
            "weeks": week_counts,
        }

    # =========================
    # Top Performers
    # =========================
    st.subheader("🥇 Top Performers")

    # Sort users by total completed desc, then name
    sorted_users = sorted(
        progress_data.items(),
        key=lambda item: (-item[1]["completed"], item[0].lower()),
    )

    if not sorted_users:
        st.info("No workouts logged yet. Once people start checking in, rankings will show here.")
    else:
        for idx, (user, data) in enumerate(sorted_users):
            total = data["completed"]
            team = data["team"]

            # Choose icon by rank
            if idx == 0:
                icon = "🥇"
            elif idx == 1:
                icon = "🥈"
            elif idx == 2:
                icon = "🥉"
            else:
                icon = "🏋️"

            label = f"**{user}** — {total} workouts completed ({team})"

            # Highlight current user if provided
            if current_user and user.lower() == current_user.lower():
                st.markdown(
                    f"<div style='background-color:#222;padding:6px 10px;border-radius:8px;'>"
                    f"⭐ {label}</div>",
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(f"{icon} {label}")

    # =========================
    # Team Totals
    # =========================
    st.markdown("---")
    st.subheader("👥 Team Totals")

    team_totals = {}  # {team_name: total_workouts}
    for user, data in progress_data.items():
        team = data["team"]
        team_totals[team] = team_totals.get(team, 0) + data["completed"]

    if team_totals:
        # Sort by total desc
        sorted_teams = sorted(team_totals.items(), key=lambda x: -x[1])
        for idx, (team, total) in enumerate(sorted_teams):
            icon = "🥇" if idx == 0 else "🥈" if idx == 1 else "🥉" if idx == 2 else "🏁"
            st.markdown(f"{icon} **{team}** — {total} workouts completed total")
    else:
        st.info("No team data yet.")

    # =========================
    # Detailed Weekly Breakdown (Checklist Grid)
    # =========================
    st.markdown("---")
    st.subheader("🔍 Weekly Progress")

    st.caption("Each block = 1 workout. ✅ = completed, ⬜ = not yet done.")

    # Build HTML table for nicer spacing & alignment
    table_html = """
<style>
table.leaderboard-table {
    border-collapse: collapse;
    width: 100%;
    margin-top: 10px;
    margin-bottom: 20px;
    font-size: 0.95rem;
}
table.leaderboard-table th,
table.leaderboard-table td {
    border-bottom: 1px solid #444;
    padding: 8px 10px;
    text-align: center;
}
table.leaderboard-table th:first-child,
table.leaderboard-table td:first-child {
    text-align: left;
    padding-left: 4px;
}
table.leaderboard-table tr:hover {
    background-color: #222;
}
</style>
<table class="leaderboard-table">
<thead>
<tr>
    <th>Name</th>
    <th>Week 1</th>
    <th>Week 2</th>
    <th>Week 3</th>
    <th>Week 4</th>
    <th>Total</th>
</tr>
</thead>
<tbody>
"""

    for user, data in sorted_users:
        weeks_counts = data["weeks"]
        total = data["completed"]

        table_html += "<tr>"
        table_html += f"<td><strong>{user}</strong></td>"

        # For each week: 4 total possible workouts → 4 blocks
        for w in weeks:
            done = weeks_counts.get(w, 0)
            done = max(0, min(4, done))  # clamp 0-4
            filled = "✅" * done + "⬜" * (4 - done)
            table_html += f"<td style='font-family:monospace;'>{filled}</td>"

        table_html += f"<td><strong>{total}/16</strong></td>"
        table_html += "</tr>"

    table_html += "</tbody></table>"

    st.markdown(table_html, unsafe_allow_html=True)

    # =========================
    # Overall Completion Rate
    # =========================
    total_possible = len(users) * 16  # 4 weeks * 4 workouts
    total_done = sum(d["completed"] for d in progress_data.values())
    completion_rate = round((total_done / total_possible) * 100, 1) if total_possible else 0.0

    # Small visual summary
    st.markdown(
        f"<div style='margin-top:4px;font-weight:600;'>"
        f"🏁 Team Completion Rate: <span style='color:#00FF88;'>{completion_rate}%</span>"
        f"</div>",
        unsafe_allow_html=True,
    )
