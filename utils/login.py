import streamlit as st
from helpers import get_all_users

def login_user():
    """Simple login + team selection dropdown."""
    st.sidebar.title("👋 Login")

    username = st.sidebar.text_input("Your Name:")

    # Get existing teams/users
    all_users = get_all_users()
    all_users = sorted(set(all_users)) if all_users else []

    team_choice = st.sidebar.selectbox(
        "Select Team or Mode:",
        ["(Individual)"] + all_users + ["Create New Team"],
        index=0,
    )

    if team_choice == "(Individual)":
        schedule_key = username.strip().lower()
    elif team_choice == "Create New Team":
        new_team = st.sidebar.text_input("Enter new team name:")
        schedule_key = new_team.strip().lower() if new_team else username.strip().lower()
    else:
        schedule_key = team_choice.strip().lower()

    if not username:
        st.warning("Please enter your name to continue.")
        return None, None

    return username, schedule_key
