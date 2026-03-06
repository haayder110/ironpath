"""
main_ai_coach_integration.py
────────────────────────────────────────────────────────
Snippets to drop into your existing main.py.
────────────────────────────────────────────────────────
"""

from core.ai_coach import AICoach


# ── 1. Replace your plan generation block with this ──────

def run_ai_plan_generation(user_profile, display):
    display.print_info("\n🤖  AI Coach is analysing your training history...\n")

    try:
        coach = AICoach(user_profile)           # verbose=True by default — prints each tool call
        plan  = coach.generate_plan(verbose=True)

        display.print_success(f"\n✅  {plan['plan_name']}")
        print(f"\n📊  Rationale: {plan['rationale']}\n")

        return plan

    except EnvironmentError:
        display.print_warning("No API key — using built-in plan.")
        from data.workout_plans import get_workout_plan
        return get_workout_plan(user_profile.goal, user_profile.experience_level)


# ── 2. Add an "Ask your coach" option to the main menu ───

def run_coach_qa(user_profile, display):
    """
    Let the user ask the AI coach anything.
    The AI will query the database to give data-backed answers.
    """
    display.print_header("💬  Ask Your AI Coach")
    question = input("  What do you want to know? › ").strip()
    if not question:
        return

    print()
    try:
        coach  = AICoach(user_profile)
        answer = coach.ask(question, verbose=True)
        print(f"\n  🏋️  Coach: {answer}\n")
    except Exception as e:
        display.print_warning(f"Coach unavailable: {e}")


# ── Example terminal output when verbose=True ────────────
#
#  🤖  AI Coach is analysing your training history...
#
#  🔍  Coach is checking: get_recovery_status()
#  🔍  Coach is checking: get_recent_sessions(n=5)
#  🔍  Coach is checking: get_personal_records(exercise_names=['Squat', 'Bench Press', 'Deadlift'])
#  🔍  Coach is checking: get_volume_trend(muscle_group=legs, weeks=4)
#  🔍  Coach is checking: calculate_training_max(exercise_name=Squat, weight_kg=120, reps=5, rpe=8)
#
#  ✅  5/3/1 Strength Block — Week 1
#
#  📊  Rationale: Your squat and deadlift PRs suggest a 1RM around 145kg and
#      165kg respectively. Volume on legs has been flat for 3 weeks and your
#      last 3 sessions averaged RPE 8.4 — so I've reduced frequency to 3 days
#      and built in a dedicated lower day with conservative training maxes.
