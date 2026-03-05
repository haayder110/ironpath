"""
core/workout.py
===============
WorkoutSession — orchestrates a single live workout.

Responsibilities:
  - Present each exercise card in sequence
  - Collect set logs (weight, reps, RPE) via the UI
  - Detect PRs via Analytics
  - Award XP and badges via Gamification
  - Persist the completed session to the database

This class is intentionally the thickest in the project
because a workout session is the core user interaction.
All rendering still delegates to UI; all data mutations
go through the profile and then db.save().
"""

from __future__ import annotations

import time
from datetime import date
from typing import List, Dict, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from core.user import UserProfile
    from core.analytics import Analytics
    from core.gamification import Gamification
    from data.database import Database
    from utils.display import UI


class WorkoutSession:

    def __init__(
        self,
        profile:      "UserProfile",
        db:           "Database",
        ui:           "UI",
        analytics:    "Analytics",
        gamification: "Gamification",
    ):
        self.profile      = profile
        self.db           = db
        self.ui           = ui
        self.analytics    = analytics
        self.gamification = gamification

    # ── Entry point ───────────────────────────────────────────────────────────

    def run(self) -> None:
        """Run a complete workout session end-to-end."""
        from data.workout_plans import PLANS

        sessions     = list(PLANS[self.profile.goal].keys())
        session_name = sessions[self.profile.total_workouts % len(sessions)]
        exercises    = PLANS[self.profile.goal][session_name]

        self.ui.header(
            f"WORKOUT: {session_name.upper()}",
            f"{self.profile.goal} · {len(exercises)} exercises",
        )
        self.ui.info("Log each set. Press ENTER on weight to reuse your last weight.")
        print()
        self.ui.press_enter("Press ENTER to start your workout...")

        start_time   = time.time()
        session_log  = []
        total_volume = 0.0
        all_new_prs  = []

        for idx, exercise in enumerate(exercises, 1):
            ex_log, ex_prs, ex_volume = self._run_exercise(
                exercise, idx, len(exercises)
            )
            session_log.append(ex_log)
            all_new_prs.extend(ex_prs)
            total_volume += ex_volume

        duration_mins = int((time.time() - start_time) / 60)

        # ── Post-session updates ──────────────────────────────────────────────
        xp_earned = self.gamification.award_workout_xp(len(all_new_prs))
        self.profile.total_workouts  += 1
        self.profile.record_workout_today()

        # Append history entry
        self.profile.workout_history.append({
            "date":     str(date.today()),
            "workout":  session_name,
            "volume":   round(total_volume, 1),
            "duration": duration_mins,
            "exercises": session_log,
            "new_prs":  len(all_new_prs),
        })

        new_badges = self.gamification.check_and_award()
        self.db.save(self.profile.to_dict())

        self._show_summary(session_name, duration_mins, total_volume,
                           session_log, all_new_prs, xp_earned, new_badges)

    # ── Exercise loop ─────────────────────────────────────────────────────────

    def _run_exercise(
        self, exercise: dict, ex_num: int, total_exercises: int
    ) -> tuple:
        """
        Run one exercise through all its sets.
        Returns (ex_log dict, list of new PR dicts, total volume float).
        """
        from data.workout_plans import COACHING_CUES
        from utils.display import _o, _y, _b, _gr, _g

        self.ui.header(
            f"EXERCISE {ex_num}/{total_exercises}: {exercise['name'].upper()}",
            f"{exercise['muscle']} · {exercise['sets']} sets × {exercise['reps']} reps",
        )

        # Coaching cue
        cue = COACHING_CUES.get(exercise["muscle"], "Focus on form. Control every rep.")
        self.ui.tip(cue)
        print()

        # Show previous PR if exists
        prev_pr = self.profile.prs.get(exercise["name"])
        if prev_pr:
            from core.user import UserProfile
            est = UserProfile.estimate_1rm(prev_pr["weight"], prev_pr["reps"])
            print(
                f"  {_gr('Previous best:')} "
                f"{_o(str(prev_pr['weight']) + ' kg × ' + str(prev_pr['reps']) + ' reps')}  "
                f"{_gr('(est. 1RM: ' + str(est) + ' kg)')}"
            )
            print()

        default_weight = prev_pr["weight"] if prev_pr else 0.0
        ex_log  = {"name": exercise["name"], "sets": []}
        new_prs = []
        volume  = 0.0
        best_set_for_pr: Optional[dict] = None

        for s in range(1, exercise["sets"] + 1):
            set_data, is_pr = self._run_set(
                s, exercise["sets"], exercise["reps"],
                default_weight, exercise["name"]
            )
            ex_log["sets"].append(set_data)
            volume += set_data["weight"] * set_data["reps"]

            if is_pr:
                # Track the best set of this exercise for PR storage
                from core.user import UserProfile
                if best_set_for_pr is None or (
                    UserProfile.estimate_1rm(set_data["weight"], set_data["reps"]) >
                    UserProfile.estimate_1rm(best_set_for_pr["weight"], best_set_for_pr["reps"])
                ):
                    best_set_for_pr = set_data

            # Update default weight for next set
            if set_data["weight"] > 0:
                default_weight = set_data["weight"]

            # Rest indicator (not a blocking timer — keeps the app fast)
            if s < exercise["sets"]:
                rest = exercise["rest"]
                print(
                    f"  {_g('✓ Set logged!')}  "
                    f"{_gr('Recommended rest: ' + str(rest // 60) + 'm ' + str(rest % 60) + 's')}"
                )
            else:
                print(f"  {_g('✓ Exercise complete!')}")
            print()

        # Persist PR if a new one was set this exercise
        if best_set_for_pr and best_set_for_pr["weight"] > 0:
            from core.user import UserProfile
            new_1rm = UserProfile.estimate_1rm(best_set_for_pr["weight"], best_set_for_pr["reps"])
            new_prs.append({
                "name":    exercise["name"],
                "weight":  best_set_for_pr["weight"],
                "reps":    best_set_for_pr["reps"],
                "est_1rm": new_1rm,
            })
            self.analytics.record_pr(
                exercise["name"],
                best_set_for_pr["weight"],
                best_set_for_pr["reps"],
                str(date.today()),
            )

        return ex_log, new_prs, volume

    def _run_set(
        self,
        set_num:        int,
        total_sets:     int,
        target_reps:    str,
        default_weight: float,
        exercise_name:  str,
    ) -> tuple:
        """
        Prompt the user to log a single set.
        Returns (set_data dict, is_new_pr bool).
        """
        from utils.display import _o, _gr, _y

        print(f"  {_o('Set ' + str(set_num) + '/' + str(total_sets))}  {_gr('Target: ' + target_reps + ' reps')}")

        weight = self.ui.ask_float_optional("  Weight (kg):", default_weight)
        reps   = self.ui.ask_int("  Reps completed:")
        rpe    = self.ui.ask_rpe()

        is_pr = self.analytics.is_new_pr(exercise_name, weight, reps)
        if is_pr and weight > 0:
            from core.user import UserProfile
            est_1rm = UserProfile.estimate_1rm(weight, reps)
            print(f"  {_y('🏅 NEW PR!')} Est. 1RM: {_o(str(est_1rm) + ' kg')}")

        set_data = {
            "set":    set_num,
            "weight": weight,
            "reps":   reps,
            "rpe":    rpe if rpe != -1 else None,
        }
        return set_data, is_pr

    # ── Summary screen ────────────────────────────────────────────────────────

    def _show_summary(
        self,
        session_name:  str,
        duration_mins: int,
        total_volume:  float,
        session_log:   list,
        new_prs:       list,
        xp_earned:     int,
        new_badges:    list,
    ) -> None:
        from utils.display import _o, _y, _g, _gr
        from core.gamification import ALL_BADGES

        total_sets = sum(len(ex["sets"]) for ex in session_log)

        self.ui.header("WORKOUT COMPLETE!", f"Great work, {self.profile.name}!")

        print(f"  {_o('SESSION STATS')}")
        print(f"  {_y('⏱')}  Duration    : {_o(str(duration_mins) + ' minutes')}")
        print(f"  {_y('📦')} Total Volume : {_o(f'{total_volume:,.0f} kg lifted')}")
        print(f"  {_y('✅')} Sets Done    : {_o(str(total_sets))}")
        print(f"  {_y('⚡')} XP Earned    : {_o('+' + str(xp_earned) + ' XP')}")
        print()

        if new_prs:
            print(f"  {_y('🏅 NEW PERSONAL RECORDS:')}")
            for pr in new_prs:
                print(
                    f"     {_g('▸')} {pr['name']}: "
                    f"{_o(str(pr['weight']) + ' kg × ' + str(pr['reps']) + ' reps')}  "
                    f"{_gr('(est. 1RM: ' + str(pr['est_1rm']) + ' kg)')}"
                )
            print()

        if new_badges:
            print(f"  {_y('🎖️  BADGES UNLOCKED:')}")
            for badge in new_badges:
                print(f"     {badge.emoji}  {_o(badge.name)} — {badge.desc}")
            print()

        level, level_xp, needed_xp, level_name = self.profile.level_info()
        print(f"  {_o('🔥 Streak: ' + str(self.profile.streak) + ' day' + ('s' if self.profile.streak != 1 else ''))}")
        print()
        self.ui.xp_bar(self.profile.xp, level, level_xp, needed_xp, level_name)

        self.ui.press_enter()
