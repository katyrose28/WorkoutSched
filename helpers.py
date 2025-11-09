import os
import json
import random
from datetime import datetime

# --- Per-User Data Directory ---
USER_DIR = "user_data"
os.makedirs(USER_DIR, exist_ok=True)

# --- Shared Plans File (for Workout Buddies) ---
SHARED_PLAN_FILE = "shared_plans.json"

# --- Generic File Helpers ---
def get_user_file(user, file_type):
    """Return a user-specific JSON path (e.g., katy_progress.json)."""
    filename = f"{user}_{file_type}.json"
    return os.path.join(USER_DIR, filename)

def load_user_data(user, file_type):
    """Load JSON data for a given user and file type."""
    path = get_user_file(user, file_type)
    if os.path.exists(path):
        with open(path, "r") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return {}
    return {}

def save_user_data(user, file_type, data):
    """Save JSON data for a given user and file type."""
    with open(get_user_file(user, file_type), "w") as f:
        json.dump(data, f, indent=4)

# --- Shared Plan Helpers ---
def load_shared_plans():
    if os.path.exists(SHARED_PLAN_FILE):
        with open(SHARED_PLAN_FILE, "r") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return {}
    return {}

def save_shared_plans(data):
    with open(SHARED_PLAN_FILE, "w") as f:
        json.dump(data, f, indent=4)

def get_shared_plan(owner, week, day):
    """Get a shared plan by normalized owner key."""
    owner_key = owner.strip().lower()
    plans = load_shared_plans()
    key = f"{owner_key}_week{week}_day{day}"
    return plans.get(key)

def set_shared_plan(owner, week, day, plan):
    """Save a shared plan by normalized owner key."""
    owner_key = owner.strip().lower()
    plans = load_shared_plans()
    key = f"{owner_key}_week{week}_day{day}"
    plans[key] = plan
    save_shared_plans(plans)

# --- Weights Management ---
def load_weights(user):
    return load_user_data(user, "weights")

def save_weights(user, data):
    save_user_data(user, "weights", data)

def update_weight(user, exercise_name, new_weight):
    data = load_weights(user)
    data[exercise_name] = new_weight
    save_weights(user, data)
    log_weight_history(user, exercise_name, new_weight)
    print(f"✅ Updated {exercise_name} to {new_weight} lbs for {user}")

# --- Weight History Tracking ---
def load_weight_history(user):
    return load_user_data(user, "weight_history")

def save_weight_history(user, data):
    save_user_data(user, "weight_history", data)

def log_weight_history(user, exercise_name, new_weight):
    """Append a dated weight entry for tracking progression."""
    history = load_weight_history(user)
    entry = {"date": datetime.now().strftime("%Y-%m-%d %H:%M"), "weight": new_weight}

    if exercise_name not in history:
        history[exercise_name] = []

    # Prevent duplicates within 1 hour
    if not history[exercise_name] or abs(
        datetime.strptime(entry["date"], "%Y-%m-%d %H:%M") -
        datetime.strptime(history[exercise_name][-1]["date"], "%Y-%m-%d %H:%M")
    ).total_seconds() > 3600:
        history[exercise_name].append(entry)
        save_weight_history(user, history)

# --- Exercise Formatting ---
def format_exercise(exercise_tuple):
    exercise, weight = exercise_tuple
    if isinstance(weight, (int, float)):
        return f"{exercise} — {weight} lbs" if weight > 0 else f"{exercise} — Bodyweight"
    else:
        return f"{exercise} — {str(weight).capitalize()}"

# --- Unique Exercise Selection ---
used_exercises = {}

def pick_unique_exercise(group_name, exercise_list, week_num):
    key = group_name.strip().lower()
    history = used_exercises.get(key, [])
    recent = set(history[-2:])
    available = [ex for ex in exercise_list if ex[0] not in recent]
    if not available:
        available = exercise_list

    choice = random.choice(available)
    history.append(choice[0])
    used_exercises[key] = history
    return adjust_weight_display(choice, week_num)

# --- Weight Display Adjustments per Phase ---
def adjust_weight_display(exercise_tuple, week_num):
    exercise, weight = exercise_tuple
    updated_weights = load_weights("default")
    if exercise in updated_weights:
        try:
            weight = float(updated_weights[exercise])
        except (ValueError, TypeError):
            pass

    if not isinstance(weight, (int, float)) or weight == 0:
        return f"{exercise} — {format_exercise((exercise, weight)).split('—')[1].strip()}"

    if week_num == 1:
        return f"{exercise} — {weight} lbs, try {weight + 5} lbs"
    elif week_num == 4:
        return f"{exercise} — {round(weight / 2, 1)} lbs (deload)"
    else:
        return f"{exercise} — {weight} lbs"

# --- Workout Generation ---
def generate_day(week_num: int, day_num: int):
    from exercises import (
        delts, chest, biceps, butt,
        back_lats, back_mids, back_lower, back_combo,
        abs_upper, abs_lower, abs_combo,
        triceps, calf, thighs
    )

    if day_num == 1:
        return {
            "Delts": pick_unique_exercise("Delts", delts, week_num),
            "Chest": pick_unique_exercise("Chest", chest, week_num),
            "Biceps": pick_unique_exercise("Biceps", biceps, week_num),
            "Butt": pick_unique_exercise("Butt", butt, week_num),
            "Upper Back": pick_unique_exercise("Upper Back", back_lats, week_num),
            "Abs/Upper": pick_unique_exercise("Abs/Upper", abs_upper, week_num),
        }
    elif day_num == 2:
        return {
            "Triceps": pick_unique_exercise("Triceps", triceps, week_num),
            "Chest": pick_unique_exercise("Chest", chest, week_num),
            "Abs/Lower": pick_unique_exercise("Abs/Lower", abs_lower, week_num),
            "Back": pick_unique_exercise("Back", back_lower, week_num),
            "Calves": pick_unique_exercise("Calves", calf, week_num),
            "Thighs": pick_unique_exercise("Thighs", thighs, week_num),
        }
    elif day_num == 3:
        return {
            "Delts": pick_unique_exercise("Delts", delts, week_num),
            "Chest": pick_unique_exercise("Chest", chest, week_num),
            "Biceps": pick_unique_exercise("Biceps", biceps, week_num),
            "Butt": pick_unique_exercise("Butt", butt, week_num),
            "Upper Back": pick_unique_exercise("Upper Back", back_mids, week_num),
            "Abs/Upper": pick_unique_exercise("Abs/Upper", abs_combo, week_num),
        }
    elif day_num == 4:
        return {
            "Triceps": pick_unique_exercise("Triceps", triceps, week_num),
            "Chest": pick_unique_exercise("Chest", chest, week_num),
            "Abs/Lower": pick_unique_exercise("Abs/Lower", abs_lower, week_num),
            "Back": pick_unique_exercise("Back", back_combo, week_num),
            "Calves": pick_unique_exercise("Calves", calf, week_num),
            "Thighs": pick_unique_exercise("Thighs", thighs, week_num),
        }
    return {}

# --- Progress Tracking (per User) ---
def load_progress(user):
    return load_user_data(user, "progress")

def save_progress(user, progress):
    save_user_data(user, "progress", progress)

def mark_workout_done(user, week, day):
    progress = load_progress(user)
    key = f"Week {week} Day {day}"
    progress[key] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    save_progress(user, progress)

def check_workout_done(user, week, day):
    progress = load_progress(user)
    return f"Week {week} Day {day}" in progress
