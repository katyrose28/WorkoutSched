import os
import json
import random
from datetime import datetime

# =========================
# Paths & Setup
# =========================

USER_DIR = "user_data"
os.makedirs(USER_DIR, exist_ok=True)

SHARED_PLAN_FILE = "shared_plans.json"  # team-shared base plans (exercise names only)


# =========================
# Generic per-user JSON helpers
# =========================

def get_user_file(user, file_type):
    """
    Build path for a user's JSON file.
    Example: user='katy', file_type='weights' -> user_data/katy_weights.json
    """
    filename = f"{user}_{file_type}.json"
    return os.path.join(USER_DIR, filename)


def load_user_data(user, file_type):
    path = get_user_file(user, file_type)
    if os.path.exists(path):
        try:
            with open(path, "r") as f:
                data = f.read().strip()
                if not data:
                    return {}
                return json.loads(data)
        except json.JSONDecodeError:
            return {}
    return {}


def save_user_data(user, file_type, data):
    path = get_user_file(user, file_type)
    with open(path, "w") as f:
        json.dump(data, f, indent=4)


# =========================
# Team meta & discovery
# =========================

def get_user_meta(user):
    return load_user_data(user, "meta")


def save_user_meta(user, meta):
    save_user_data(user, "meta", meta)


def get_user_team(user):
    meta = get_user_meta(user)
    return meta.get("team")


def set_user_team(user, team_name):
    meta = get_user_meta(user)
    if team_name:
        meta["team"] = team_name
    else:
        meta.pop("team", None)
    save_user_meta(user, meta)


def get_all_users():
    """Infer all user IDs from filenames in user_data."""
    users = set()
    if not os.path.exists(USER_DIR):
        return []
    for fname in os.listdir(USER_DIR):
        if not fname.endswith(".json"):
            continue
        base = fname[:-5]  # drop .json
        if "_" in base:
            user = base.rsplit("_", 1)[0]
            if user:
                users.add(user)
    return sorted(users)


# =========================
# Shared Team Plans (base exercises only)
# =========================

def load_shared_plans():
    if os.path.exists(SHARED_PLAN_FILE):
        try:
            with open(SHARED_PLAN_FILE, "r") as f:
                data = f.read().strip()
                if not data:
                    return {}
                return json.loads(data)
        except json.JSONDecodeError:
            return {}
    return {}


def save_shared_plans(data):
    with open(SHARED_PLAN_FILE, "w") as f:
        json.dump(data, f, indent=4)


def _shared_key(team, week, day):
    team_key = team.strip().lower().replace(" ", "_")
    return f"{team_key}_week{week}_day{day}"


def get_shared_base_day(team, week, day):
    plans = load_shared_plans()
    key = _shared_key(team, week, day)
    return plans.get(key)


def set_shared_base_day(team, week, day, base_day):
    plans = load_shared_plans()
    key = _shared_key(team, week, day)
    plans[key] = base_day
    save_shared_plans(plans)


# =========================
# Exercises metadata
# =========================

def get_all_exercises():
    from exercises import (
        delts, chest, biceps, butt,
        back_lats, back_mids, back_lower, back_combo,
        abs_upper, abs_lower, abs_combo,
        triceps, calf, thighs
    )
    groups = [
        delts, chest, biceps, butt,
        back_lats, back_mids, back_lower, back_combo,
        abs_upper, abs_lower, abs_combo,
        triceps, calf, thighs
    ]
    all_ex = {}
    for group in groups:
        for name, weight in group:
            all_ex[name] = weight
    return all_ex


def get_base_weight(exercise_name):
    all_ex = get_all_exercises()
    return all_ex.get(exercise_name)


# =========================
# Weights & History (per user)
# =========================

def load_weights(user):
    return load_user_data(user, "weights")


def save_weights(user, data):
    save_user_data(user, "weights", data)


def update_weight(user, exercise_name, new_weight):
    weights = load_weights(user)
    weights[exercise_name] = float(new_weight)
    save_weights(user, weights)
    log_weight_history(user, exercise_name, new_weight)


def load_weight_history(user):
    return load_user_data(user, "weight_history")


def save_weight_history(user, history):
    save_user_data(user, "weight_history", history)


def log_weight_history(user, exercise_name, new_weight):
    """Append a dated weight entry for tracking progression."""
    history = load_weight_history(user)
    entry = {
        "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "weight": float(new_weight),
    }

    if exercise_name not in history:
        history[exercise_name] = []

    # Avoid spam: require >1h between identical logs
    if history[exercise_name]:
        last = history[exercise_name][-1]
        try:
            last_dt = datetime.strptime(last["date"], "%Y-%m-%d %H:%M")
            new_dt = datetime.strptime(entry["date"], "%Y-%m-%d %H:%M")
            if (new_dt - last_dt).total_seconds() <= 3600 and last["weight"] == entry["weight"]:
                return
        except Exception:
            pass

    history[exercise_name].append(entry)
    save_weight_history(user, history)


# =========================
# Unique exercise selection (names only)
# =========================

used_exercises = {}  # {group_key: [names...]}


def pick_unique_exercise_name(group_name, exercise_list):
    key = group_name.strip().lower()
    history = used_exercises.get(key, [])
    recent = set(history[-2:])
    candidates = [name for (name, _) in exercise_list if name not in recent]
    if not candidates:
        candidates = [name for (name, _) in exercise_list]
    choice = random.choice(candidates)
    history.append(choice)
    used_exercises[key] = history
    return choice


# =========================
# Base day generation (shared template)
# =========================

def generate_base_day(week_num: int, day_num: int):
    """
    Returns a dict of {muscle_group: exercise_name} for a given week/day.
    This is the shared *template* across a team.
    """
    from exercises import (
        delts, chest, biceps, butt,
        back_lats, back_mids, back_lower, back_combo,
        abs_upper, abs_lower, abs_combo,
        triceps, calf, thighs
    )

    if day_num == 1:
        return {
            "Delts":      pick_unique_exercise_name("Delts", delts),
            "Chest":      pick_unique_exercise_name("Chest", chest),
            "Biceps":     pick_unique_exercise_name("Biceps", biceps),
            "Butt":       pick_unique_exercise_name("Butt", butt),
            "Upper Back": pick_unique_exercise_name("Upper Back", back_lats),
            "Abs/Upper":  pick_unique_exercise_name("Abs/Upper", abs_upper),
        }
    elif day_num == 2:
        return {
            "Triceps":   pick_unique_exercise_name("Triceps", triceps),
            "Chest":     pick_unique_exercise_name("Chest", chest),
            "Abs/Lower": pick_unique_exercise_name("Abs/Lower", abs_lower),
            "Back":      pick_unique_exercise_name("Back", back_lower),
            "Calves":    pick_unique_exercise_name("Calves", calf),
            "Thighs":    pick_unique_exercise_name("Thighs", thighs),
        }
    elif day_num == 3:
        return {
            "Delts":      pick_unique_exercise_name("Delts", delts),
            "Chest":      pick_unique_exercise_name("Chest", chest),
            "Biceps":     pick_unique_exercise_name("Biceps", biceps),
            "Butt":       pick_unique_exercise_name("Butt", butt),
            "Upper Back": pick_unique_exercise_name("Upper Back", back_mids),
            "Abs/Upper":  pick_unique_exercise_name("Abs/Upper", abs_combo),
        }
    elif day_num == 4:
        return {
            "Triceps":   pick_unique_exercise_name("Triceps", triceps),
            "Chest":     pick_unique_exercise_name("Chest", chest),
            "Abs/Lower": pick_unique_exercise_name("Abs/Lower", abs_lower),
            "Back":      pick_unique_exercise_name("Back", back_combo),
            "Calves":    pick_unique_exercise_name("Calves", calf),
            "Thighs":    pick_unique_exercise_name("Thighs", thighs),
        }
    return {}


# =========================
# User-specific formatting
# =========================

def format_exercise_for_user(exercise_name, week_num, user):
    """
    Convert exercise name into text with proper weight for this user + phase.
    """
    base = get_base_weight(exercise_name)
    user_weights = load_weights(user)
    weight = user_weights.get(exercise_name, base)

    # Non-numeric gear (bands, cables, ankle weights, etc.)
    if not isinstance(weight, (int, float)):
        if base is None:
            return f"{exercise_name} — Bodyweight"
        return f"{exercise_name} — {str(weight).capitalize()}"

    # Bodyweight
    if weight == 0:
        return f"{exercise_name} — Bodyweight"

    # Week/phase logic
    if week_num == 1:
        return f"{exercise_name} — {weight} lbs, try {weight + 5} lbs"
    elif week_num == 4:
        return f"{exercise_name} — {round(weight / 2, 1)} lbs (deload)"
    else:
        return f"{exercise_name} — {weight} lbs"


def build_user_day_from_base(base_day, week_num, user):
    """
    Given {group: exercise_name}, return {group: formatted_text} for that user.
    """
    return {
        group: format_exercise_for_user(ex_name, week_num, user)
        for group, ex_name in base_day.items()
    }


# =========================
# Progress Tracking (per user)
# =========================

def load_progress(user):
    return load_user_data(user, "progress")


def save_progress(user, progress):
    save_user_data(user, "progress", progress)


def mark_workout_done(user, week, day):
    progress = load_progress(user)
    key = f"Week {week} Day {day}"
    progress[key] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    save_progress(user, progress)


def unmark_workout_done(user, week, day):
    progress = load_progress(user)
    key = f"Week {week} Day {day}"
    if key in progress:
        del progress[key]
        save_progress(user, progress)


def check_workout_done(user, week, day):
    progress = load_progress(user)
    return f"Week {week} Day {day}" in progress

USER_SCHEDULES_DIR = "user_schedules"

def load_user_schedule(username):
    """Load a user's saved workout schedule or return an empty one."""
    if not os.path.exists(USER_SCHEDULES_DIR):
        os.makedirs(USER_SCHEDULES_DIR)
    file_path = os.path.join(USER_SCHEDULES_DIR, f"{username}_schedule.json")
    if os.path.exists(file_path):
        with open(file_path, "r") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return {}
    return {}

def save_user_schedule(username, schedule):
    """Save the workout schedule for a specific user."""
    if not os.path.exists(USER_SCHEDULES_DIR):
        os.makedirs(USER_SCHEDULES_DIR)
    file_path = os.path.join(USER_SCHEDULES_DIR, f"{username}_schedule.json")
    with open(file_path, "w") as f:
        json.dump(schedule, f, indent=4)
