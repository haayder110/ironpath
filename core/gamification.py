"""
core/gamification.py
====================
XP rewards, badge definitions, badge checking, and profile display.

Badge checking is intentionally decoupled from the workout logic —
WorkoutSession calls gamification.check_and_award() after a session,
passing the updated profile. This module never modifies profile data
directly; it returns lists of newly earned badges for the caller to display.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, TYPE_CHECKING

if TYPE_CHECKING:
    from core.user import UserProfile
    from data.database import Database
    from utils.display import UI


# ── Badge definitions ─────────────────────────────────────────────────────────

@dataclass(frozen=True)
class Badge:
    id:    str
    name:  str
    emoji: str
    desc:  str
    xp:    int   # bonus XP awarded on unlock (0 = no XP bonus)


ALL_BADGES: List[Badge] = [
    Badge("first_workout", "First Step",       "👟", "Complete your first workout",    50),
    Badge("5_workouts",    "Getting Warmed Up", "🔥", "Complete 5 workouts",           100),
    Badge("10_workouts",   "Dedicated",         "💪", "Complete 10 workouts",          150),
    Badge("25_workouts",   "Iron Habit",        "🦾", "Complete 25 workouts",          300),
    Badge("50_workouts",   "Century Club",      "💯", "Complete 50 workouts",          500),
    Badge("streak_3",      "Hat Trick",         "🎩", "Maintain a 3-day streak",        75),
    Badge("streak_7",      "Iron Week",         "📅", "Maintain a 7-day streak",       200),
    Badge("streak_30",     "Iron Monk",         "🧘", "Maintain a 30-day streak",     1000),
    Badge("first_pr",      "Personal Best",     "🏅", "Log your first PR",             100),
    Badge("10_prs",        "PR Machine",        "🚀", "Hit 10 personal records",       250),
    Badge("level_5",       "Iron Warrior",      "⚔️", "Reach Level 5",                  0),
    Badge("level_10",      "IronPath Champion", "🏆", "Reach Level 10",                 0),
]

# Map badge id → Badge for O(1) lookup
_BADGE_MAP = {b.id: b for b in ALL_BADGES}


# ── XP reward values ──────────────────────────────────────────────────────────

XP_WORKOUT_BASE = 150
XP_PER_PR       = 50


# ── Gamification service ──────────────────────────────────────────────────────

class Gamification:

    def __init__(self, profile: "UserProfile", db: "Database", ui: "UI"):
        self.profile = profile
        self.db      = db
        self.ui      = ui

    # ── Public API ─────────────────────────────────────────────────────────────

    def award_workout_xp(self, pr_count: int) -> int:
        """
        Calculate and apply XP for a completed workout.
        Returns total XP awarded.
        """
        earned = XP_WORKOUT_BASE + (pr_count * XP_PER_PR)
        self.profile.xp += earned
        return earned

    def check_and_award(self) -> List[Badge]:
        """
        Check all badge conditions and award any not yet earned.
        Returns a list of newly awarded Badge objects.
        Bonus XP for each badge is applied to profile.xp.
        """
        newly_earned: List[Badge] = []

        conditions = self._build_conditions()
        for badge_id, condition_met in conditions:
            if condition_met and badge_id not in self.profile.badges:
                badge = _BADGE_MAP[badge_id]
                self.profile.badges.append(badge_id)
                if badge.xp > 0:
                    self.profile.xp += badge.xp
                newly_earned.append(badge)

        return newly_earned

    # ── Profile screen ────────────────────────────────────────────────────────

    def show_profile(self) -> None:
        p = self.profile
        level, level_xp, needed_xp, level_name = p.level_info()

        self.ui.header(f"{p.name.upper()}'S PROFILE", "IronPath Athlete")

        # Stats
        from utils.display import _o, _y, _gr
        print(f"  {_y('👤')} Name        : {_o(p.name)}")
        print(f"  {_y('🎯')} Goal        : {_o(p.goal)}")
        print(f"  {_y('💪')} Experience  : {_o(p.experience)}")
        print(f"  {_y('⚖️')} Weight      : {_o(str(p.weight_kg) + ' kg')}")
        print(f"  {_y('📅')} Member Since: {_o(p.created)}")
        print()
        self.ui.line()
        print()

        # XP bar
        print(f"  LEVEL & XP")
        self.ui.xp_bar(p.xp, level, level_xp, needed_xp, level_name)
        print()
        self.ui.line()
        print()

        # Badges
        earned_count = len(p.badges)
        total_count  = len(ALL_BADGES)
        print(f"  BADGES  {_gr('(' + str(earned_count) + '/' + str(total_count) + ' unlocked)')}")
        print()
        for badge in ALL_BADGES:
            if badge.id in p.badges:
                print(f"  {badge.emoji}  {_o(badge.name)}  {_gr(badge.desc)}")
            else:
                print(f"  {_gr('🔒  ' + badge.name)}  {_gr(badge.desc)}")
        print()

        self.ui.press_enter()

    # ── Private helpers ───────────────────────────────────────────────────────

    def _build_conditions(self) -> List[tuple]:
        p = self.profile
        total    = p.total_workouts
        streak   = p.streak
        pr_count = len(p.prs)
        level    = p.level

        return [
            ("first_workout", total >= 1),
            ("5_workouts",    total >= 5),
            ("10_workouts",   total >= 10),
            ("25_workouts",   total >= 25),
            ("50_workouts",   total >= 50),
            ("streak_3",      streak >= 3),
            ("streak_7",      streak >= 7),
            ("streak_30",     streak >= 30),
            ("first_pr",      pr_count >= 1),
            ("10_prs",        pr_count >= 10),
            ("level_5",       level >= 5),
            ("level_10",      level >= 10),
        ]
