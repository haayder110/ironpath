"""
IronPath — AI Personal Trainer
================================
Entry point. Run this file to start the app.

    python main.py

Project Structure:
    main.py              — Entry point
    core/
        user.py          — User profile, XP, levels, streaks
        workout.py       — Workout session logic
        analytics.py     — Progress tracking and PR detection
        nutrition.py     — Macro and calorie calculations
        gamification.py  — Badges, XP rewards, level system
    data/
        database.py      — Load/save all data to JSON
        workout_plans.py — All workout exercise data
    utils/
        display.py       — Terminal colors, UI helpers
        validators.py    — Input validation helpers
"""

from core.user import UserProfile
from data.database import Database
from utils.display import UI
from core.workout import WorkoutSession
from core.analytics import Analytics
from core.nutrition import Nutrition
from core.gamification import Gamification
from core.ai_coach import AICoach
from main_ai_coach_integration import run_ai_plan_generation, run_coach_qa

def main():
    db = Database()
    ui = UI()

    ui.splash_screen()

    # Load existing user or run onboarding
    user_data = db.load()
    if user_data is None:
        profile = UserProfile.onboard(ui)
        db.save(profile.to_dict())
    else:
        profile = UserProfile.from_dict(user_data)
        ui.welcome_back(profile.name)

    # Core module instances
    analytics    = Analytics(profile, db, ui)
    nutrition    = Nutrition(profile, ui)
    gamification = Gamification(profile, db, ui)

    # Main app loop
    while True:
        choice = ui.main_menu(profile)

        if choice == "1":
            session = WorkoutSession(profile, db, ui, analytics, gamification)
            session.run()

        elif choice == "2":
            ui.show_workout_plan(profile)

        elif choice == "3":
            analytics.show_dashboard()

        elif choice == "4":
            gamification.show_profile()

        elif choice == "5":
            nutrition.show_guide()
        elif choice == "6":
            run_coach_qa(profile, ui)

        elif choice == "7":
            ui.goodbye(profile.name)
            break


if __name__ == "__main__":
    main()
