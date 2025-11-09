import random
import json
import os
from datetime import datetime


# --- File paths ---
WEIGHTS_FILE = "weights_data.json"
PROGRESS_FILE = "progress_data.json"

# --- Load or initialize weights file ---
def load_weights():
    if os.path.exists(WEIGHTS_FILE):
        try:
            with open(WEIGHTS_FILE, "r") as f:
                data = f.read().strip()
                if not data:
                    return {}
                return json.loads(data)
        except json.JSONDecodeError:
            return {}
    return {}

# --- Save updated weights ---
def save_weights(data):
    with open(WEIGHTS_FILE, "w") as f:
        json.dump(data, f, indent=4)

# --- Update a specific exercise weight ---
def update_weight(exercise_name, new_weight):
    data = load_weights()
    data[exercise_name] = new_weight
    save_weights(data)
    print(f"✅ Updated {exercise_name} to {new_weight} lbs.")


WEIGHT_HISTORY_FILE = "weight_history.json"

def load_weight_history():
    if os.path.exists(WEIGHT_HISTORY_FILE):
        with open(WEIGHT_HISTORY_FILE, "r") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return {}
    return {}

def save_weight_history(data):
    with open(WEIGHT_HISTORY_FILE, "w") as f:
        json.dump(data, f, indent=4)

def log_weight_history(exercise_name, new_weight):
    """Append a dated weight entry for tracking progression."""
    history = load_weight_history()
    entry = {"date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), "weight": new_weight}

    if exercise_name not in history:
        history[exercise_name] = []

    # Prevent duplicate entries if same weight logged within 1 hour
    if not history[exercise_name] or abs(
        datetime.datetime.strptime(entry["date"], "%Y-%m-%d %H:%M") -
        datetime.datetime.strptime(history[exercise_name][-1]["date"], "%Y-%m-%d %H:%M")
    ).total_seconds() > 3600:
        history[exercise_name].append(entry)
        save_weight_history(history)

# --- Format weight display ---
def format_exercise(exercise_tuple):
    exercise, weight = exercise_tuple
    if isinstance(weight, (int, float)):
        return f"{exercise} — {weight} lbs" if weight > 0 else f"{exercise} — Bodyweight"
    else:
        return f"{exercise} — {str(weight).capitalize()}"

# --- Track used exercises to reduce repeats ---
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

# --- Adjust displayed weight depending on phase ---
def adjust_weight_display(exercise_tuple, week_num):
    exercise, weight = exercise_tuple
    updated_weights = load_weights()
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

# --- Generate a single day's workout ---
def generate_day(week_num: int, day_num: int):
    from exercises import (
        delts, chest, biceps, butt,
        back_lats, back_mids, back_lower, back_combo,
        abs_upper, abs_lower, abs_combo,
        triceps, calf, thighs
    )
    day_plan = {}
    if day_num == 1:
        day_plan = {
            "Delts": pick_unique_exercise("Delts", delts, week_num),
            "Chest": pick_unique_exercise("Chest", chest, week_num),
            "Biceps": pick_unique_exercise("Biceps", biceps, week_num),
            "Butt": pick_unique_exercise("Butt", butt, week_num),
            "Upper Back": pick_unique_exercise("Upper Back", back_lats, week_num),
            "Abs/Upper": pick_unique_exercise("Abs/Upper", abs_upper, week_num),
        }
    elif day_num == 2:
        day_plan = {
            "Triceps": pick_unique_exercise("Triceps", triceps, week_num),
            "Chest": pick_unique_exercise("Chest", chest, week_num),
            "Abs/Lower": pick_unique_exercise("Abs/Lower", abs_lower, week_num),
            "Back": pick_unique_exercise("Back", back_lower, week_num),
            "Calves": pick_unique_exercise("Calves", calf, week_num),
            "Thighs": pick_unique_exercise("Thighs", thighs, week_num),
        }
    elif day_num == 3:
        day_plan = {
            "Delts": pick_unique_exercise("Delts", delts, week_num),
            "Chest": pick_unique_exercise("Chest", chest, week_num),
            "Biceps": pick_unique_exercise("Biceps", biceps, week_num),
            "Butt": pick_unique_exercise("Butt", butt, week_num),
            "Upper Back": pick_unique_exercise("Upper Back", back_mids, week_num),
            "Abs/Upper": pick_unique_exercise("Abs/Upper", abs_combo, week_num),
        }
    elif day_num == 4:
        day_plan = {
            "Triceps": pick_unique_exercise("Triceps", triceps, week_num),
            "Chest": pick_unique_exercise("Chest", chest, week_num),
            "Abs/Lower": pick_unique_exercise("Abs/Lower", abs_lower, week_num),
            "Back": pick_unique_exercise("Back", back_combo, week_num),
            "Calves": pick_unique_exercise("Calves", calf, week_num),
            "Thighs": pick_unique_exercise("Thighs", thighs, week_num),
        }
    return day_plan

# --- Progress tracking (for “I did it!” button) ---
def load_progress():
    if os.path.exists(PROGRESS_FILE):
        try:
            with open(PROGRESS_FILE, "r") as f:
                data = f.read().strip()
                if not data:
                    return {}
                return json.loads(data)
        except (json.JSONDecodeError, ValueError):
            return {}
    return {}

def save_progress(progress):
    with open(PROGRESS_FILE, "w") as f:
        json.dump(progress, f, indent=4)

def mark_workout_done(week, day):
    progress = load_progress()
    key = f"Week {week} Day {day}"
    progress[key] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    save_progress(progress)

def check_workout_done(week, day):
    progress = load_progress()
    return f"Week {week} Day {day}" in progress
