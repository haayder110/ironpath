"""
core/nutrition.py
=================
Calculates personalised daily macro targets and renders
the nutrition guide screen.

Formula basis:
  - Calories: bodyweight-based multiplier per goal
  - Protein:  high across all goals to preserve/build muscle
  - Carbs:    scaled up for performance goals
  - Fat:      fills remaining calories
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Tuple, TYPE_CHECKING

if TYPE_CHECKING:
    from core.user import UserProfile
    from utils.display import UI


@dataclass(frozen=True)
class MacroTarget:
    calories: int
    protein_g: int
    carbs_g:   int
    fat_g:     int
    note:      str


# Multipliers per goal (calories per kg of bodyweight)
_CALORIE_MULTIPLIERS: Dict[str, float] = {
    "Build Muscle":    33.0,
    "Lose Fat":        26.0,
    "Get Stronger":    35.0,
    "General Fitness": 30.0,
}

# Protein (g per kg)
_PROTEIN_MULTIPLIERS: Dict[str, float] = {
    "Build Muscle":    2.0,
    "Lose Fat":        2.2,
    "Get Stronger":    1.8,
    "General Fitness": 1.6,
}

_GOAL_NOTES: Dict[str, str] = {
    "Build Muscle":
        "Eat in a slight caloric surplus (~300–500 kcal above maintenance). "
        "Prioritise protein at every meal.",
    "Lose Fat":
        "Eat in a moderate caloric deficit (~400–500 kcal below maintenance). "
        "Keep protein high to preserve muscle.",
    "Get Stronger":
        "Eat enough to fuel heavy training. "
        "Carb-load on training days, reduce slightly on rest days.",
    "General Fitness":
        "Maintain a balanced diet. "
        "Focus on whole foods, consistent meal timing, and adequate hydration.",
}

TOP_FOODS: Dict[str, list] = {
    "Protein": ["Chicken breast", "Eggs", "Greek yogurt", "Tuna", "Lean beef"],
    "Carbs":   ["White rice", "Oats", "Sweet potato", "Banana", "Sourdough bread"],
    "Fats":    ["Avocado", "Olive oil", "Almonds", "Salmon", "Whole eggs"],
}

MEAL_TIMING = [
    ("Pre-workout",  "Carbs + protein 60–90 min before training"),
    ("Post-workout", "Protein shake + fast carbs within 30 min after"),
    ("Before bed",   "Casein protein or cottage cheese"),
    ("Hydration",    "{water_target}L of water per day minimum"),
]


def calculate_macros(weight_kg: float, goal: str) -> MacroTarget:
    """
    Pure function: given bodyweight and goal, return macro targets.
    Raises ValueError if goal is unrecognised.
    """
    if goal not in _CALORIE_MULTIPLIERS:
        raise ValueError(f"Unknown goal: '{goal}'")

    calories  = round(weight_kg * _CALORIE_MULTIPLIERS[goal])
    protein_g = round(weight_kg * _PROTEIN_MULTIPLIERS[goal])

    protein_kcal = protein_g * 4
    fat_g        = round(weight_kg * 1.0)
    fat_kcal     = fat_g * 9
    carbs_kcal   = max(0, calories - protein_kcal - fat_kcal)
    carbs_g      = round(carbs_kcal / 4)

    return MacroTarget(
        calories  = calories,
        protein_g = protein_g,
        carbs_g   = carbs_g,
        fat_g     = fat_g,
        note      = _GOAL_NOTES[goal],
    )


class Nutrition:

    def __init__(self, profile: "UserProfile", ui: "UI"):
        self.profile = profile
        self.ui      = ui

    def show_guide(self) -> None:
        p = self.profile
        macros = calculate_macros(p.weight_kg, p.goal)
        water  = round(p.weight_kg * 0.035, 1)

        self.ui.header("NUTRITION GUIDE", f"AI Recommendations for {p.goal}")

        self._render_targets(macros)
        self.ui.line()
        print()
        self._render_note(macros)
        self.ui.line()
        print()
        self._render_timing(water)
        self.ui.line()
        print()
        self._render_foods()

        self.ui.press_enter()

    # ── Private rendering ─────────────────────────────────────────────────────

    def _render_targets(self, m: MacroTarget) -> None:
        from utils.display import _o, _y, _gr
        print(f"  YOUR DAILY TARGETS")
        print()
        print(f"  {_y('🔥')} Calories  : {_o(str(m.calories) + ' kcal/day')}")
        print(f"  {_y('🥩')} Protein   : {_o(str(m.protein_g) + 'g')}  {_gr('(' + str(m.protein_g * 4) + ' kcal)')}")
        print(f"  {_y('🍚')} Carbs     : {_o(str(m.carbs_g) + 'g')}  {_gr('(' + str(m.carbs_g * 4) + ' kcal)')}")
        print(f"  {_y('🥑')} Fat       : {_o(str(m.fat_g) + 'g')}  {_gr('(' + str(m.fat_g * 9) + ' kcal)')}")
        print()

    def _render_note(self, m: MacroTarget) -> None:
        from utils.display import _o
        print(f"  AI TIP")
        print(f"  {m.note}")
        print()

    def _render_timing(self, water: float) -> None:
        from utils.display import _o, _g
        print(f"  MEAL TIMING")
        for label, tip in MEAL_TIMING:
            tip_text = tip.replace("{water_target}", str(water))
            print(f"  {_g('▸')} {label:15s}: {tip_text}")
        print()

    def _render_foods(self) -> None:
        from utils.display import _o, _y
        print(f"  TOP FOOD SOURCES")
        for macro, items in TOP_FOODS.items():
            print(f"  {_y(macro + ':')}  {', '.join(items)}")
        print()
