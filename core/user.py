"""
core/user.py
============
UserProfile — the central data model for a single user.

Responsibilities:
  - Hold all user state (name, goal, XP, streak, etc.)
  - Serialise to / deserialise from a plain dict (for JSON storage)
  - Expose helper methods for level calculation and streak logic
  - Run the first-time onboarding flow

Intentionally contains NO terminal I/O — that all lives in utils/display.py.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Dict, List, Optional, Tuple


# ── Constants ─────────────────────────────────────────────────────────────────

XP_PER_LEVEL = 500   # XP needed per level

LEVEL_NAMES: Dict[int, str] = {
    1:  "Rookie",
    2:  "Beginner",
    3:  "Trainee",
    4:  "Athlete",
    5:  "Iron Warrior",
    6:  "Iron Beast",
    7:  "Iron Elite",
    8:  "Iron Legend",
    9:  "Iron God",
    10: "IronPath Champion",
}

GOALS     = ["Build Muscle", "Lose Fat", "Get Stronger", "General Fitness"]
EXPERIENCE = [
    "Beginner (under 1 year)",
    "Intermediate (1–3 years)",
    "Advanced (3+ years)",
]


# ── Data model ────────────────────────────────────────────────────────────────

@dataclass
class UserProfile:
    name:               str
    goal:               str
    experience:         str
    weight_kg:          float
    xp:                 int                     = 0
    streak:             int                     = 0
    last_workout_date:  Optional[str]           = None
    total_workouts:     int                     = 0
    workout_history:    List[dict]              = field(default_factory=list)
    prs:                Dict[str, dict]         = field(default_factory=dict)
    badges:             List[str]               = field(default_factory=list)
    created:            str                     = field(default_factory=lambda: str(date.today()))

    # ── Level helpers ──────────────────────────────────────────────────────────

    def level_info(self) -> Tuple[int, int, int, str]:
        """
        Return (level, xp_into_level, xp_needed_for_level, level_name).
        Level is capped at 10.
        """
        level = min(10, max(1, self.xp // XP_PER_LEVEL + 1))
        xp_into = self.xp % XP_PER_LEVEL
        needed  = XP_PER_LEVEL
        name    = LEVEL_NAMES.get(level, "Champion")
        return level, xp_into, needed, name

    @property
    def level(self) -> int:
        return self.level_info()[0]

    # ── Streak helpers ─────────────────────────────────────────────────────────

    def record_workout_today(self) -> None:
        """Update streak based on today's date."""
        today = str(date.today())
        yesterday = str(date.today() - timedelta(days=1))

        if self.last_workout_date == today:
            return  # already logged today — streak unchanged

        if self.last_workout_date == yesterday:
            self.streak += 1
        else:
            self.streak = 1

        self.last_workout_date = today

    def check_streak_broken(self) -> bool:
        """
        Return True if the streak was broken since the last session.
        Call this on app load to reset a dead streak before showing it.
        """
        if self.last_workout_date is None:
            return False
        yesterday = str(date.today() - timedelta(days=1))
        if self.last_workout_date < yesterday:
            self.streak = 0
            return True
        return False

    # ── 1RM estimate ──────────────────────────────────────────────────────────

    @staticmethod
    def estimate_1rm(weight: float, reps: int) -> float:
        """Epley formula. Returns 0 if weight or reps are 0."""
        if weight <= 0 or reps <= 0:
            return 0.0
        if reps == 1:
            return weight
        return round(weight * (1 + reps / 30), 1)

    # ── Serialisation ─────────────────────────────────────────────────────────

    def to_dict(self) -> dict:
        return {
            "name":               self.name,
            "goal":               self.goal,
            "experience":         self.experience,
            "weight_kg":          self.weight_kg,
            "xp":                 self.xp,
            "streak":             self.streak,
            "last_workout_date":  self.last_workout_date,
            "total_workouts":     self.total_workouts,
            "workout_history":    self.workout_history,
            "prs":                self.prs,
            "badges":             self.badges,
            "created":            self.created,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "UserProfile":
        return cls(
            name              = data["name"],
            goal              = data["goal"],
            experience        = data.get("experience", ""),
            weight_kg         = data.get("weight_kg", 0.0),
            xp                = data.get("xp", 0),
            streak            = data.get("streak", 0),
            last_workout_date = data.get("last_workout_date"),
            total_workouts    = data.get("total_workouts", 0),
            workout_history   = data.get("workout_history", []),
            prs               = data.get("prs", {}),
            badges            = data.get("badges", []),
            created           = data.get("created", str(date.today())),
        )

    # ── Onboarding factory ────────────────────────────────────────────────────

    @classmethod
    def onboard(cls, ui) -> "UserProfile":
        """
        Run the first-time setup wizard.
        Returns a fully initialised UserProfile.
        ui is a utils.display.UI instance.
        """
        ui.header("WELCOME TO IRONPATH", "Your AI Personal Trainer")
        print("  Let's build your profile. This takes about 60 seconds.\n")

        name = ui.ask_name()

        ui.header(f"HEY {name.upper()}!", "Step 1 of 4 — Your Goal")
        print("  What is your main goal?\n")
        goal = ui.ask_choice("Choose your goal:", GOALS)

        ui.header("YOUR EXPERIENCE", "Step 2 of 4")
        print("  How long have you been training consistently?\n")
        experience = ui.ask_choice("Choose your level:", EXPERIENCE)

        ui.header("BODY STATS", "Step 3 of 4")
        print("  Your bodyweight helps calculate macros and strength targets.\n")
        weight = ui.ask_float("Your current bodyweight in kg:", "Bodyweight")

        profile = cls(
            name=name,
            goal=goal,
            experience=experience,
            weight_kg=weight,
            xp=100,   # welcome bonus
        )

        ui.header("YOUR IRONPATH PROFILE", "Step 4 of 4 — All set!")
        print(f"  👤 Name        : {name}")
        print(f"  🎯 Goal        : {goal}")
        print(f"  💪 Experience  : {experience}")
        print(f"  ⚖️  Weight      : {weight} kg")
        print()
        ui.success("Your AI trainer has built your first workout plan!")
        ui.press_enter("Press ENTER to enter IronPath...")

        return profile
