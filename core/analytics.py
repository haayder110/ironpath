"""
core/analytics.py
=================
Progress tracking, personal record detection, and the
AI progressive overload recommendation engine.

PR Detection logic:
  - A new PR is set when the estimated 1RM for a set
    exceeds the stored best estimated 1RM for that lift.
  - We store the raw weight + reps (not just the 1RM)
    so the actual numbers are always shown to the user.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Tuple, TYPE_CHECKING

if TYPE_CHECKING:
    from core.user import UserProfile
    from data.database import Database
    from utils.display import UI


class Analytics:

    def __init__(self, profile: "UserProfile", db: "Database", ui: "UI"):
        self.profile = profile
        self.db      = db
        self.ui      = ui

    # ── PR detection ──────────────────────────────────────────────────────────

    def is_new_pr(self, exercise_name: str, weight: float, reps: int) -> bool:
        """
        Return True if this set is a new personal record for the exercise.
        Uses estimated 1RM (Epley formula) as the comparison metric.
        """
        if weight <= 0 or reps <= 0:
            return False

        from core.user import UserProfile
        new_1rm = UserProfile.estimate_1rm(weight, reps)
        prev    = self.profile.prs.get(exercise_name)

        if prev is None:
            return True

        prev_1rm = UserProfile.estimate_1rm(prev["weight"], prev["reps"])
        return new_1rm > prev_1rm

    def record_pr(self, exercise_name: str, weight: float,
                  reps: int, session_date: str) -> None:
        """Persist a new PR to the user profile."""
        from core.user import UserProfile
        self.profile.prs[exercise_name] = {
            "weight": weight,
            "reps":   reps,
            "est_1rm": UserProfile.estimate_1rm(weight, reps),
            "date":   session_date,
        }

    # ── Progressive overload suggestions ─────────────────────────────────────

    def overload_suggestion(self, exercise_name: str) -> Optional[Tuple[float, float]]:
        """
        Return (current_weight, suggested_weight) for a given exercise.
        Applies a 2.5% increase rounded to nearest 1.25 kg increment.
        Returns None if no PR exists for the exercise.
        """
        pr = self.profile.prs.get(exercise_name)
        if pr is None:
            return None

        current    = pr["weight"]
        raw_target = current * 1.025
        # Round to nearest 1.25 kg (smallest standard plate pair)
        suggested  = round(raw_target / 1.25) * 1.25
        return current, suggested

    # ── Dashboard ─────────────────────────────────────────────────────────────

    def show_dashboard(self) -> None:
        p = self.profile
        history = p.workout_history

        self.ui.header("PROGRESS & ANALYTICS", f"{p.name}'s Stats")

        if not history:
            self.ui.info("No workouts logged yet. Complete your first workout to see analytics!")
            self.ui.press_enter()
            return

        self._show_overview(history)
        self.ui.line()
        print()
        self._show_recent_workouts(history)
        self.ui.line()
        print()
        self._show_personal_records()
        self.ui.line()
        print()
        self._show_overload_tips()

        self.ui.press_enter()

    # ── Private rendering ─────────────────────────────────────────────────────

    def _show_overview(self, history: list) -> None:
        from utils.display import _o, _y, _gr
        total_volume   = sum(w.get("volume", 0)   for w in history)
        total_duration = sum(w.get("duration", 0) for w in history)
        total_prs      = sum(w.get("new_prs", 0)  for w in history)

        print(f"  OVERVIEW")
        print(f"  {_y('🏋️')} Total Workouts  : {_o(str(self.profile.total_workouts))}")
        print(f"  {_y('📦')} Total Volume    : {_o(f'{total_volume:,.0f} kg lifted')}")
        print(f"  {_y('⏱')}  Total Time      : {_o(str(total_duration) + ' minutes')}")
        print(f"  {_y('🏅')} Personal Records: {_o(str(len(self.profile.prs)) + ' PRs set')}")
        print(f"  {_y('🔥')} Current Streak  : {_o(str(self.profile.streak) + ' days')}")
        print()

    def _show_recent_workouts(self, history: list) -> None:
        from utils.display import _o, _y, _gr, _bold
        print(f"  RECENT WORKOUTS  {_gr('(last 5)')}")
        for entry in reversed(history[-5:]):
            vol = entry.get("volume", 0)
            dur = entry.get("duration", 0)
            print(
                f"  {_y('·')} {entry['date']}  "
                f"{_bold(entry['workout'])}  "
                f"{_gr(f'{vol:,.0f} kg · {dur} min')}"
            )
        print()

    def _show_personal_records(self) -> None:
        from utils.display import _o, _y, _gr, _bold
        if not self.profile.prs:
            print(f"  No PRs yet — keep lifting!")
            print()
            return

        print(f"  PERSONAL RECORDS")
        for lift, pr in sorted(self.profile.prs.items()):
            est = pr.get("est_1rm", 0)
            print(
                f"  {_y('🏅')} {_bold(lift)}\n"
                f"     {_o(str(pr['weight']) + ' kg × ' + str(pr['reps']) + ' reps')}  "
                f"{_gr('est. 1RM: ' + str(est) + ' kg · ' + pr['date'])}"
            )
        print()

    def _show_overload_tips(self) -> None:
        from utils.display import _o, _g, _gr
        print(f"  AI PROGRESSIVE OVERLOAD TIPS")
        if not self.profile.prs:
            print(f"  {_gr('Log workouts with weights to get AI suggestions.')}")
            print()
            return

        shown = 0
        for lift in list(self.profile.prs.keys())[:5]:
            result = self.overload_suggestion(lift)
            if result:
                current, suggested = result
                print(f"  {_g('▸')} {lift}: Try {_o(str(suggested) + ' kg')} {_gr('(currently ' + str(current) + ' kg, +2.5% overload)')}")
                shown += 1

        if shown == 0:
            print(f"  {_gr('No suggestions available yet.')}")
        print()
