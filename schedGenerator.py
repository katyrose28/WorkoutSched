from exercises import (
    delts, chest, biceps, butt,
    back_lats, back_mids, back_lower, back_combo,
    abs_upper, abs_lower, abs_combo,
    triceps, calf, thighs
)
from helpers import pick_unique_exercise
from helpers import pick_unique_exercise, prompt_weight_updates, load_weights


# a simple helper so we don't repeat all the print lines manually
def print_week(week_num, phase_label):
    print(f"\n\n🏋️‍♀️ Week {week_num} – {phase_label}\n")

    print("DAY 1 - UPPER BODY")
    print("Delts:       ", pick_unique_exercise("Delts", delts, week_num))
    print("Chest:       ", pick_unique_exercise("Chest", chest, week_num))
    print("Biceps:      ", pick_unique_exercise("Biceps", biceps, week_num))
    print("Butt:        ", pick_unique_exercise("Butt", butt, week_num))
    print("Upper Back:  ", pick_unique_exercise("Upper Back", back_lats, week_num))
    print("Abs/Upper:   ", pick_unique_exercise("Abs/Upper", abs_upper, week_num))

    print("\nDAY 2 - FULL BODY")
    print("Triceps:     ", pick_unique_exercise("Triceps", triceps, week_num))
    print("Chest:       ", pick_unique_exercise("Chest", chest, week_num))
    print("Abs/Lower:   ", pick_unique_exercise("Abs/Lower", abs_lower, week_num))
    print("Back:        ", pick_unique_exercise("Back Lower", back_lower, week_num))
    print("Calves:      ", pick_unique_exercise("Calves", calf, week_num))
    print("Thighs:      ", pick_unique_exercise("Thighs", thighs, week_num))

    print("\nDAY 3 - UPPER BODY")
    print("Delts:       ", pick_unique_exercise("Delts", delts, week_num))
    print("Chest:       ", pick_unique_exercise("Chest", chest, week_num))
    print("Biceps:      ", pick_unique_exercise("Biceps", biceps, week_num))
    print("Butt:        ", pick_unique_exercise("Butt", butt, week_num))
    print("Upper Back:  ", pick_unique_exercise("Upper Back", back_mids, week_num))
    print("Abs/Upper:   ", pick_unique_exercise("Abs/Upper", abs_combo, week_num))

    print("\nDAY 4 - FULL BODY")
    print("Triceps:     ", pick_unique_exercise("Triceps", triceps, week_num))
    print("Chest:       ", pick_unique_exercise("Chest", chest, week_num))
    print("Abs/Lower:   ", pick_unique_exercise("Abs/Lower", abs_lower, week_num))
    print("Back:        ", pick_unique_exercise("Back Combo", back_combo, week_num))
    print("Calves:      ", pick_unique_exercise("Calves", calf, week_num))
    print("Thighs:      ", pick_unique_exercise("Thighs", thighs, week_num))


# -----------------------------
# generate all 4 weeks in one run
# -----------------------------
print_week(1, "Build Phase (4–6 reps)")

# ---- Week 1 update ----
prompt_weight_updates()

# 🔁 reload weights after updates
current_weights = load_weights()

print_week(2, "Strength Phase (6–8 reps)")
print_week(3, "Hypertrophy Phase (8–10 reps)")
print_week(4, "Deload / Endurance Phase (12–15 reps)")