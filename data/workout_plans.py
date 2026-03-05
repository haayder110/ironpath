"""
data/workout_plans.py
=====================
All workout exercise data organised by goal and session name.
Each exercise is a typed dict for clarity and easy extension.

Adding a new goal:  add a new key to PLANS
Adding an exercise: append to the relevant session list
"""

from typing import TypedDict, List, Dict


class Exercise(TypedDict):
    name:   str
    sets:   int
    reps:   str   # e.g. "8-10" or "45sec"
    muscle: str
    rest:   int   # seconds


# All plans keyed by goal name
PLANS: Dict[str, Dict[str, List[Exercise]]] = {

    "Build Muscle": {
        "Upper A": [
            {"name": "Barbell Bench Press",    "sets": 4, "reps": "8-10",  "muscle": "Chest",     "rest": 180},
            {"name": "Barbell Row",            "sets": 4, "reps": "8-10",  "muscle": "Back",      "rest": 180},
            {"name": "Overhead Press",         "sets": 3, "reps": "8-12",  "muscle": "Shoulders", "rest": 120},
            {"name": "Pull-Ups",               "sets": 3, "reps": "6-10",  "muscle": "Back",      "rest": 120},
            {"name": "Dumbbell Curl",          "sets": 3, "reps": "10-12", "muscle": "Biceps",    "rest": 90},
            {"name": "Tricep Pushdown",        "sets": 3, "reps": "10-12", "muscle": "Triceps",   "rest": 90},
        ],
        "Lower A": [
            {"name": "Barbell Squat",          "sets": 4, "reps": "6-8",   "muscle": "Quads",     "rest": 240},
            {"name": "Romanian Deadlift",      "sets": 3, "reps": "8-10",  "muscle": "Hamstrings","rest": 180},
            {"name": "Leg Press",              "sets": 3, "reps": "10-12", "muscle": "Quads",     "rest": 120},
            {"name": "Leg Curl",               "sets": 3, "reps": "10-12", "muscle": "Hamstrings","rest": 90},
            {"name": "Calf Raise",             "sets": 4, "reps": "12-15", "muscle": "Calves",    "rest": 60},
            {"name": "Plank",                  "sets": 3, "reps": "45sec", "muscle": "Core",      "rest": 60},
        ],
        "Upper B": [
            {"name": "Incline Dumbbell Press", "sets": 4, "reps": "8-12",  "muscle": "Chest",     "rest": 120},
            {"name": "Cable Row",              "sets": 4, "reps": "10-12", "muscle": "Back",      "rest": 120},
            {"name": "Lateral Raise",          "sets": 3, "reps": "12-15", "muscle": "Shoulders", "rest": 90},
            {"name": "Lat Pulldown",           "sets": 3, "reps": "10-12", "muscle": "Back",      "rest": 120},
            {"name": "Hammer Curl",            "sets": 3, "reps": "10-12", "muscle": "Biceps",    "rest": 90},
            {"name": "Skull Crushers",         "sets": 3, "reps": "10-12", "muscle": "Triceps",   "rest": 90},
        ],
        "Lower B": [
            {"name": "Deadlift",               "sets": 4, "reps": "5-6",   "muscle": "Back",      "rest": 240},
            {"name": "Hack Squat",             "sets": 3, "reps": "8-10",  "muscle": "Quads",     "rest": 180},
            {"name": "Walking Lunges",         "sets": 3, "reps": "12/leg","muscle": "Quads",     "rest": 120},
            {"name": "Leg Curl",               "sets": 3, "reps": "12-15", "muscle": "Hamstrings","rest": 90},
            {"name": "Seated Calf Raise",      "sets": 4, "reps": "15-20", "muscle": "Calves",    "rest": 60},
            {"name": "Ab Wheel Rollout",       "sets": 3, "reps": "8-12",  "muscle": "Core",      "rest": 60},
        ],
    },

    "Lose Fat": {
        "Full Body A": [
            {"name": "Goblet Squat",           "sets": 3, "reps": "12-15", "muscle": "Quads",     "rest": 60},
            {"name": "Dumbbell Row",           "sets": 3, "reps": "12-15", "muscle": "Back",      "rest": 60},
            {"name": "Push-Ups",               "sets": 3, "reps": "15-20", "muscle": "Chest",     "rest": 60},
            {"name": "Dumbbell Lunge",         "sets": 3, "reps": "12/leg","muscle": "Quads",     "rest": 60},
            {"name": "Dumbbell Shoulder Press","sets": 3, "reps": "12-15", "muscle": "Shoulders", "rest": 60},
            {"name": "Mountain Climbers",      "sets": 3, "reps": "30sec", "muscle": "Core",      "rest": 45},
        ],
        "Full Body B": [
            {"name": "Deadlift",               "sets": 3, "reps": "10-12", "muscle": "Back",      "rest": 90},
            {"name": "Incline Push-Up",        "sets": 3, "reps": "15-20", "muscle": "Chest",     "rest": 60},
            {"name": "Dumbbell Curl",          "sets": 3, "reps": "12-15", "muscle": "Biceps",    "rest": 60},
            {"name": "Tricep Dips",            "sets": 3, "reps": "12-15", "muscle": "Triceps",   "rest": 60},
            {"name": "Bulgarian Split Squat",  "sets": 3, "reps": "10/leg","muscle": "Quads",     "rest": 90},
            {"name": "Burpees",                "sets": 3, "reps": "10-12", "muscle": "Full Body", "rest": 60},
        ],
        "Full Body C": [
            {"name": "Barbell Squat",          "sets": 3, "reps": "10-12", "muscle": "Quads",     "rest": 90},
            {"name": "Pull-Ups / Assisted",    "sets": 3, "reps": "8-10",  "muscle": "Back",      "rest": 90},
            {"name": "Dumbbell Bench Press",   "sets": 3, "reps": "12-15", "muscle": "Chest",     "rest": 60},
            {"name": "Kettlebell Swing",       "sets": 4, "reps": "15-20", "muscle": "Full Body", "rest": 60},
            {"name": "Plank",                  "sets": 3, "reps": "45sec", "muscle": "Core",      "rest": 45},
            {"name": "Jump Rope",              "sets": 3, "reps": "60sec", "muscle": "Cardio",    "rest": 30},
        ],
    },

    "Get Stronger": {
        "Squat Day": [
            {"name": "Barbell Squat",          "sets": 5, "reps": "3-5",   "muscle": "Quads",     "rest": 300},
            {"name": "Pause Squat",            "sets": 3, "reps": "3",     "muscle": "Quads",     "rest": 240},
            {"name": "Leg Press",              "sets": 3, "reps": "8-10",  "muscle": "Quads",     "rest": 180},
            {"name": "Leg Curl",               "sets": 3, "reps": "10-12", "muscle": "Hamstrings","rest": 90},
            {"name": "Plank",                  "sets": 3, "reps": "45sec", "muscle": "Core",      "rest": 60},
        ],
        "Bench Day": [
            {"name": "Barbell Bench Press",    "sets": 5, "reps": "3-5",   "muscle": "Chest",     "rest": 300},
            {"name": "Paused Bench Press",     "sets": 3, "reps": "3",     "muscle": "Chest",     "rest": 240},
            {"name": "Overhead Press",         "sets": 3, "reps": "6-8",   "muscle": "Shoulders", "rest": 180},
            {"name": "Dumbbell Row",           "sets": 4, "reps": "8-10",  "muscle": "Back",      "rest": 120},
            {"name": "Tricep Pushdown",        "sets": 3, "reps": "10-12", "muscle": "Triceps",   "rest": 90},
        ],
        "Deadlift Day": [
            {"name": "Deadlift",               "sets": 5, "reps": "1-3",   "muscle": "Back",      "rest": 360},
            {"name": "Romanian Deadlift",      "sets": 3, "reps": "5-6",   "muscle": "Hamstrings","rest": 240},
            {"name": "Barbell Row",            "sets": 4, "reps": "6-8",   "muscle": "Back",      "rest": 180},
            {"name": "Pull-Ups",               "sets": 3, "reps": "5-8",   "muscle": "Back",      "rest": 120},
            {"name": "Face Pulls",             "sets": 3, "reps": "15-20", "muscle": "Shoulders", "rest": 60},
        ],
    },

    "General Fitness": {
        "Push Day": [
            {"name": "Push-Ups",               "sets": 4, "reps": "10-15", "muscle": "Chest",     "rest": 60},
            {"name": "Dumbbell Shoulder Press","sets": 3, "reps": "10-12", "muscle": "Shoulders", "rest": 90},
            {"name": "Incline Dumbbell Press", "sets": 3, "reps": "10-12", "muscle": "Chest",     "rest": 90},
            {"name": "Lateral Raise",          "sets": 3, "reps": "12-15", "muscle": "Shoulders", "rest": 60},
            {"name": "Tricep Dips",            "sets": 3, "reps": "10-15", "muscle": "Triceps",   "rest": 60},
        ],
        "Pull Day": [
            {"name": "Pull-Ups / Assisted",    "sets": 4, "reps": "6-10",  "muscle": "Back",      "rest": 90},
            {"name": "Dumbbell Row",           "sets": 3, "reps": "10-12", "muscle": "Back",      "rest": 90},
            {"name": "Face Pulls",             "sets": 3, "reps": "15-20", "muscle": "Shoulders", "rest": 60},
            {"name": "Dumbbell Curl",          "sets": 3, "reps": "10-12", "muscle": "Biceps",    "rest": 60},
            {"name": "Hammer Curl",            "sets": 3, "reps": "10-12", "muscle": "Biceps",    "rest": 60},
        ],
        "Legs Day": [
            {"name": "Bodyweight Squat",       "sets": 4, "reps": "15-20", "muscle": "Quads",     "rest": 60},
            {"name": "Dumbbell Lunge",         "sets": 3, "reps": "12/leg","muscle": "Quads",     "rest": 90},
            {"name": "Glute Bridge",           "sets": 3, "reps": "15-20", "muscle": "Glutes",    "rest": 60},
            {"name": "Calf Raise",             "sets": 4, "reps": "20-25", "muscle": "Calves",    "rest": 45},
            {"name": "Plank",                  "sets": 3, "reps": "45sec", "muscle": "Core",      "rest": 45},
        ],
    },
}

# Coaching cues per muscle group
COACHING_CUES: Dict[str, str] = {
    "Chest":     "Retract shoulder blades. Control the descent. Full stretch at bottom.",
    "Back":      "Drive elbows, not hands. Squeeze shoulder blades at the top.",
    "Quads":     "Knees track over toes. Chest up, core braced. Full depth.",
    "Hamstrings":"Hip hinge — push hips back. Neutral spine throughout.",
    "Shoulders": "Avoid shrugging. Brace core. Control the descent.",
    "Biceps":    "Full range of motion. Supinate at the top. Control the lowering.",
    "Triceps":   "Lock out at the top. Keep elbows tucked. Slow the negative.",
    "Calves":    "Full stretch at the bottom. Pause and squeeze at the top.",
    "Core":      "Brace like taking a punch. Breathe steadily. No sagging hips.",
    "Full Body": "Stay explosive. Prioritise form even when fatigued.",
    "Cardio":    "Maintain a pace you can sustain. Breathe rhythmically.",
    "Glutes":    "Drive through heels. Squeeze hard at the top of every rep.",
}
