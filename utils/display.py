"""
utils/display.py
================
All terminal output, colours, and UI rendering lives here.
Nothing outside this file should call print() directly —
this keeps the rest of the codebase clean and makes it easy
to swap the terminal UI for a web UI later.
"""

import os
import time
from typing import List, Optional
from utils.validators import (
    validate_name, validate_positive_float,
    validate_positive_int, validate_rpe, validate_menu_choice,
)


# ── ANSI colour helpers ───────────────────────────────────────────────────────

class _C:
    ORANGE = "\033[38;5;208m"
    GREEN  = "\033[92m"
    RED    = "\033[91m"
    YELLOW = "\033[93m"
    BLUE   = "\033[94m"
    CYAN   = "\033[96m"
    GREY   = "\033[90m"
    BOLD   = "\033[1m"
    RESET  = "\033[0m"

def _o(t): return f"{_C.ORANGE}{_C.BOLD}{t}{_C.RESET}"
def _g(t): return f"{_C.GREEN}{t}{_C.RESET}"
def _r(t): return f"{_C.RED}{t}{_C.RESET}"
def _y(t): return f"{_C.YELLOW}{t}{_C.RESET}"
def _b(t): return f"{_C.BLUE}{t}{_C.RESET}"
def _gr(t): return f"{_C.GREY}{t}{_C.RESET}"
def _bold(t): return f"{_C.BOLD}{t}{_C.RESET}"
def _cy(t): return f"{_C.CYAN}{t}{_C.RESET}"

LINE = _gr("─" * 56)

LOGO = f"""
{_o('  ██╗██████╗  ██████╗ ███╗  ██╗██████╗  █████╗ ████████╗██╗  ██╗')}
{_o('  ██║██╔══██╗██╔═══██╗████╗ ██║██╔══██╗██╔══██╗╚══██╔══╝██║  ██║')}
{_o('  ██║██████╔╝██║   ██║██╔██╗██║██████╔╝███████║   ██║   ███████║')}
{_o('  ╚═╝╚═════╝  ╚═════╝ ╚═╝ ╚═══╝╚═════╝  ╚════╝   ╚═╝   ╚══════╝')}
{_gr('              Your AI Personal Trainer — v2.0')}
"""


class UI:
    """All terminal rendering and user input collection."""

    # ── Layout helpers ────────────────────────────────────────────────────────

    def clear(self) -> None:
        os.system("cls" if os.name == "nt" else "clear")

    def header(self, title: str, subtitle: str = "") -> None:
        self.clear()
        print(LOGO)
        print(LINE)
        print(f"  {_bold(title)}")
        if subtitle:
            print(f"  {_gr(subtitle)}")
        print(LINE)
        print()

    def line(self) -> None:
        print(LINE)

    def blank(self) -> None:
        print()

    def success(self, msg: str) -> None:
        print(f"  {_g('✓')} {msg}")

    def error(self, msg: str) -> None:
        print(f"  {_r('✗')} {_r(msg)}")

    def info(self, msg: str) -> None:
        print(f"  {_b('ℹ')} {msg}")

    def tip(self, msg: str) -> None:
        print(f"  {_b('💡 TIP:')} {msg}")

    def press_enter(self, msg: str = "Press ENTER to continue...") -> None:
        print()
        print(_gr(f"  {msg}"))
        try:
            input()
        except (KeyboardInterrupt, EOFError):
            pass

    def xp_bar(self, current_xp: int, level: int,
               level_xp: int, needed_xp: int, level_name: str) -> None:
        pct = min(int((level_xp / needed_xp) * 30), 30)
        bar = _o("█" * pct) + _gr("░" * (30 - pct))
        print(f"  {_y('⚡')} Level {level} — {_o(level_name)}")
        print(f"  [{bar}] {level_xp}/{needed_xp} XP")

    # ── Input collection ──────────────────────────────────────────────────────

    def ask(self, prompt: str, allow_empty: bool = False) -> str:
        """Read a line of input. Ctrl+C exits gracefully."""
        while True:
            try:
                raw = input(f"  {_cy('▸')} {prompt} ").strip()
            except (KeyboardInterrupt, EOFError):
                print("\n\n  See you at the gym. 💪")
                raise SystemExit(0)
            if raw or allow_empty:
                return raw
            self.error("Please enter a value.")

    def ask_choice(self, prompt: str, options: List[str]) -> str:
        """Present a numbered list and return the chosen option string."""
        for i, opt in enumerate(options, 1):
            print(f"  {_o(str(i) + '.')} {opt}")
        print()
        while True:
            raw = self.ask(prompt)
            try:
                idx = validate_menu_choice(raw, 1, len(options))
                return options[idx - 1]
            except ValueError as e:
                self.error(str(e))

    def ask_float(self, prompt: str, field: str = "Value") -> float:
        """Ask for a positive float, re-prompting on bad input."""
        while True:
            raw = self.ask(prompt)
            try:
                return validate_positive_float(raw, field)
            except ValueError as e:
                self.error(str(e))

    def ask_int(self, prompt: str, field: str = "Value") -> int:
        """Ask for a positive integer, re-prompting on bad input."""
        while True:
            raw = self.ask(prompt)
            try:
                return validate_positive_int(raw, field)
            except ValueError as e:
                self.error(str(e))

    def ask_float_optional(self, prompt: str, default: float) -> float:
        """Ask for a float; return default on empty input."""
        while True:
            raw = self.ask(prompt + f" (ENTER = {default}kg)", allow_empty=True)
            if raw == "":
                return default
            try:
                return validate_positive_float(raw, "Weight")
            except ValueError as e:
                self.error(str(e))

    def ask_rpe(self) -> int:
        """Ask for an RPE rating (1-10). Returns -1 if skipped."""
        while True:
            raw = self.ask("How hard? Rate 1–10 (ENTER to skip):", allow_empty=True)
            try:
                return validate_rpe(raw)
            except ValueError as e:
                self.error(str(e))

    def ask_name(self) -> str:
        while True:
            raw = self.ask("Your first name:")
            try:
                return validate_name(raw)
            except ValueError as e:
                self.error(str(e))

    # ── Screens ───────────────────────────────────────────────────────────────

    def splash_screen(self) -> None:
        self.clear()
        print(LOGO)
        time.sleep(1)

    def welcome_back(self, name: str) -> None:
        self.header(f"WELCOME BACK, {name.upper()}!", "Loading your profile...")
        time.sleep(0.6)

    def goodbye(self, name: str) -> None:
        self.header("SEE YOU AT THE GYM!", "")
        print(f"  {_o('Keep grinding, ' + name + '. Gains do not take days off.')}")
        print()

    def main_menu(self, profile) -> str:
        from data.workout_plans import PLANS
        sessions = list(PLANS[profile.goal].keys())
        next_session = sessions[profile.total_workouts % len(sessions)]

        self.header(f"HOME — {profile.name.upper()}", "IronPath Dashboard")

        # Stats row
        streak_icon = "🔥" if profile.streak > 0 else "💤"
        print(f"  {streak_icon}  Streak     : {_o(str(profile.streak) + ' day' + ('s' if profile.streak != 1 else ''))}")
        print(f"  {_y('🎯')} Goal       : {_o(profile.goal)}")
        print(f"  {_y('🏋️')} Workouts   : {_o(str(profile.total_workouts) + ' total')}")
        print()
        self.xp_bar(profile.xp, *profile.level_info())
        print()
        self.line()
        print()

        # Next workout preview
        from data.workout_plans import PLANS
        exercises = PLANS[profile.goal][next_session]
        print(f"  {_o('TODAYS WORKOUT:')} {_bold(next_session)}")
        print(f"  {_gr(str(len(exercises)) + ' exercises · ' + profile.goal)}")
        print()

        options = [
            "Start Today's Workout",
            "View Full Workout Plan",
            "Progress & Analytics",
            "My Profile & Badges",
            "Nutrition Guide",
            "Exit",
        ]
        return self.ask_choice("Choose an option:", options)

    def show_workout_plan(self, profile) -> None:
        from data.workout_plans import PLANS
        sessions = PLANS[profile.goal]
        session_names = list(sessions.keys())
        current_idx = profile.total_workouts % len(session_names)

        self.header("YOUR WORKOUT PLAN", f"Goal: {profile.goal}")
        for i, (name, exercises) in enumerate(sessions.items()):
            marker = _o("◀ NEXT") if i == current_idx else _gr("      ")
            print(f"  {_o(str(i+1)+'.')} {_bold(name)}  {marker}")
            for ex in exercises:
                print(f"      {_gr('·')} {ex['name']}  {_gr(str(ex['sets']) + ' × ' + ex['reps'] + '  [' + ex['muscle'] + ']')}")
            print()
        self.press_enter()
