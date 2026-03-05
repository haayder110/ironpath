# IronPath 🏋️ — AI Personal Trainer

A terminal-based fitness application built in Python.  
Designed as a working prototype to validate the IronPath product concept.

---

## Features

- **AI Workout Generator** — personalised plans based on goal, experience, and equipment
- **Live Workout Logging** — log every set, weight, reps, and RPE in real time
- **PR Detection** — automatic personal record tracking using the Epley 1RM formula
- **Progressive Overload Engine** — AI suggests next-session weights per lift
- **Progress Analytics** — full history, volume stats, and all-time PRs
- **Gamification** — XP system, 10 levels, 12 unlockable badges, daily streaks
- **Nutrition Guide** — personalised daily macro targets (calories, protein, carbs, fat)
- **Persistent Data** — all progress saved locally between sessions

---

## Project Structure

```
ironpath/
├── main.py                  # Entry point
├── core/
│   ├── user.py              # UserProfile data model + onboarding
│   ├── workout.py           # Live workout session logic
│   ├── analytics.py         # PR detection + overload recommendations
│   ├── nutrition.py         # Macro calculations
│   └── gamification.py      # XP, badges, levels
├── data/
│   ├── database.py          # JSON persistence layer
│   └── workout_plans.py     # All exercise data + coaching cues
└── utils/
    ├── display.py           # All terminal rendering + UI helpers
    └── validators.py        # Input validation functions
```

---

## Getting Started

**Requirements:** Python 3.8+

```bash
# Clone the repo
git clone https://github.com/haayder110/ironpath.git
cd ironpath

# Run the app
python main.py
```

No third-party dependencies. Uses Python standard library only.

---

## Architecture Notes

- **Separation of concerns** — UI, data, business logic, and validation are fully decoupled into separate modules
- **No global state** — all state is owned by `UserProfile` and passed explicitly
- **Swappable storage** — `Database` is an isolated class; replacing JSON with PostgreSQL or Firebase requires changing only `data/database.py`
- **Validated input** — all user input goes through `utils/validators.py` before touching business logic
- **Atomic writes** — the save function writes to a temp file first, then renames, preventing data corruption on interrupted saves

---

## Roadmap

This terminal prototype is the foundation for a full mobile app.

| Phase | Feature |
|-------|---------|
| v2    | REST API backend (FastAPI) |
| v2    | React Native mobile app |
| v3    | Real AI workout generation (OpenAI API) |
| v3    | Cloud database (PostgreSQL) |
| v4    | AI form analysis via camera |
| v4    | Apple Watch / Garmin integration |

---

## Built By

**IronPath** — concept, product design, and vision by the founding team.  
Terminal prototype built to validate core user flows before mobile development.
