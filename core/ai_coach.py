"""
core/ai_coach.py
IronPath — Agentic AI Coach with Function Calling

The AI doesn't just receive data — it autonomously decides WHAT to query
and WHEN, mid-reasoning. It behaves like a real coach who pulls up your
history before prescribing anything.

Drop into core/. Requires: pip install openai
"""

import json
import os
from openai import OpenAI
from data.database import Database

MODEL       = "gpt-4o"   # Must be gpt-4o or gpt-4-turbo for reliable function calling
MAX_TOKENS  = 2000
MAX_ROUNDS  = 6          # Max tool-call rounds before forcing a final answer


# ─────────────────────────────────────────────────────────
# Tool Definitions  (what the AI is allowed to call)
# ─────────────────────────────────────────────────────────

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_personal_records",
            "description": (
                "Fetch the athlete's all-time personal records for one or more lifts. "
                "Use this before programming any compound movement to understand "
                "their true strength baseline."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "exercise_names": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of exercise names, e.g. ['Bench Press', 'Squat', 'Deadlift']",
                    }
                },
                "required": ["exercise_names"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_recent_sessions",
            "description": (
                "Fetch the athlete's last N workout sessions. "
                "Use this to identify fatigue patterns, training frequency, "
                "and whether progressive overload has stalled."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "n": {
                        "type": "integer",
                        "description": "Number of recent sessions to retrieve. Default 5, max 12.",
                    }
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_volume_trend",
            "description": (
                "Get weekly training volume trend for a specific muscle group or lift "
                "over the last N weeks. Use this to detect overtraining or undertraining "
                "before prescribing volume."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "muscle_group": {
                        "type": "string",
                        "description": "e.g. 'chest', 'legs', 'back', or a specific lift like 'Deadlift'",
                    },
                    "weeks": {
                        "type": "integer",
                        "description": "Number of weeks to look back. Default 4.",
                    },
                },
                "required": ["muscle_group"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "calculate_training_max",
            "description": (
                "Calculate a conservative training max (90% of 1RM) using the Epley formula "
                "from a recent performance. Use this to set working weights for strength blocks."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "exercise_name": {"type": "string"},
                    "weight_kg":     {"type": "number", "description": "Weight used in the set"},
                    "reps":          {"type": "integer", "description": "Reps completed"},
                    "rpe":           {"type": "number",  "description": "RPE of the set (1-10)"},
                },
                "required": ["exercise_name", "weight_kg", "reps"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_recovery_status",
            "description": (
                "Estimate the athlete's current recovery status based on "
                "session frequency, average RPE trend, and rest days in the last 7 days. "
                "Use this before prescribing intensity."
            ),
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        },
    },
]


# ─────────────────────────────────────────────────────────
# Agentic AI Coach
# ─────────────────────────────────────────────────────────

class AICoach:
    """
    An agentic AI coach that autonomously queries IronPath's database
    using OpenAI function calling before generating any workout plan.

    The AI decides WHAT to look up and WHEN — you don't pre-fetch anything.
    """

    def __init__(self, user_profile, api_key: str | None = None):
        key = api_key or os.getenv("OPENAI_API_KEY")
        if not key:
            raise EnvironmentError(
                "Set OPENAI_API_KEY env variable to use the AI coach."
            )
        self.client   = OpenAI(api_key=key)
        self.profile  = user_profile
        self.db       = Database()
        self.username = getattr(user_profile, "name", "athlete")

        # Tool router — maps function name → actual method
        self._tool_router = {
            "get_personal_records":   self._tool_get_prs,
            "get_recent_sessions":    self._tool_get_sessions,
            "get_volume_trend":       self._tool_get_volume_trend,
            "calculate_training_max": self._tool_calculate_training_max,
            "get_recovery_status":    self._tool_get_recovery_status,
        }

    # ── Public API ─────────────────────────────────────────

    def generate_plan(self, verbose: bool = True) -> dict:
        """
        Run the agentic loop:
          1. AI receives user profile
          2. AI calls whatever tools it needs (PRs, history, volume trends...)
          3. We execute the tools against the real database
          4. AI reasons over the results and generates the final plan

        Args:
            verbose: If True, prints each tool call the AI makes (great for terminal UX)

        Returns:
            Full workout plan dict (same schema as before)
        """
        messages = [
            {"role": "system", "content": COACH_SYSTEM_PROMPT},
            {"role": "user",   "content": self._build_user_message()},
        ]

        # ── Agentic loop ──────────────────────────────────
        for round_n in range(MAX_ROUNDS):
            response = self.client.chat.completions.create(
                model=MODEL,
                max_tokens=MAX_TOKENS,
                tools=TOOLS,
                tool_choice="auto",           # AI decides when it's done querying
                response_format={"type": "json_object"} if self._is_final_round(round_n) else None,
                messages=messages,
            )

            message = response.choices[0].message

            # ── No tool calls → AI is done reasoning, return plan ──
            if not message.tool_calls:
                try:
                    return json.loads(message.content)
                except (json.JSONDecodeError, TypeError):
                    # Sometimes the AI wraps JSON in markdown — strip it
                    clean = (message.content or "").replace("```json", "").replace("```", "").strip()
                    return json.loads(clean)

            # ── AI wants to call tools ──
            messages.append(message)   # Append assistant's tool-call message

            for tool_call in message.tool_calls:
                fn_name = tool_call.function.name
                fn_args = json.loads(tool_call.function.arguments)

                if verbose:
                    print(f"  🔍  Coach is checking: {fn_name}({self._pretty_args(fn_args)})")

                # Execute the tool against the real database
                result = self._execute_tool(fn_name, fn_args)

                # Feed result back into the conversation
                messages.append({
                    "role":         "tool",
                    "tool_call_id": tool_call.id,
                    "content":      json.dumps(result),
                })

        raise RuntimeError("AI coach did not produce a plan within the allowed rounds.")

    def ask(self, question: str, verbose: bool = True) -> str:
        """
        Free-form Q&A with the AI coach. It can still call tools to answer.
        e.g. "Am I overtraining legs?" or "What weight should I squat today?"

        Args:
            question: Natural language question from the user
            verbose:  Print tool calls to terminal

        Returns:
            Plain text answer from the coach
        """
        messages = [
            {"role": "system", "content": QA_SYSTEM_PROMPT},
            {"role": "user",   "content": f"Athlete profile: {self._profile_summary()}\n\nQuestion: {question}"},
        ]

        for _ in range(MAX_ROUNDS):
            response = self.client.chat.completions.create(
                model=MODEL,
                max_tokens=500,
                tools=TOOLS,
                tool_choice="auto",
                messages=messages,
            )
            message = response.choices[0].message

            if not message.tool_calls:
                return message.content.strip()

            messages.append(message)

            for tool_call in message.tool_calls:
                fn_name = tool_call.function.name
                fn_args = json.loads(tool_call.function.arguments)

                if verbose:
                    print(f"  🔍  {fn_name}({self._pretty_args(fn_args)})")

                result = self._execute_tool(fn_name, fn_args)
                messages.append({
                    "role":         "tool",
                    "tool_call_id": tool_call.id,
                    "content":      json.dumps(result),
                })

        return "I wasn't able to fully analyse your data. Please try again."

    # ── Tool Implementations ───────────────────────────────
    # Each method hits your real Database and returns clean data
    # the AI can reason over.

    def _tool_get_prs(self, exercise_names: list) -> dict:
        """Fetch PRs from your existing database."""
        prs = {}
        for name in exercise_names:
            record = self.db.get_pr(self.username, name)   # adjust to your DB API
            if record:
                prs[name] = {
                    "weight_kg":  record.get("weight_kg"),
                    "reps":       record.get("reps"),
                    "estimated_1rm": self._epley(
                        record.get("weight_kg", 0),
                        record.get("reps", 1)
                    ),
                    "date": record.get("date"),
                }
            else:
                prs[name] = None   # AI will know there's no PR yet
        return {"personal_records": prs}

    def _tool_get_sessions(self, n: int = 5) -> dict:
        """Fetch recent sessions from your existing database."""
        n = min(max(n, 1), 12)
        history = self.db.get_workout_history(self.username)
        recent  = history[-(n):]
        return {
            "sessions_retrieved": len(recent),
            "sessions": recent,
        }

    def _tool_get_volume_trend(self, muscle_group: str, weeks: int = 4) -> dict:
        """
        Compute weekly volume (sets × reps × weight) for a muscle group.
        Returns a week-by-week breakdown the AI can interpret.
        """
        history = self.db.get_workout_history(self.username)

        # Map muscle group keyword to exercise names
        # Adjust this mapping to match your exercise database
        muscle_map = {
            "chest":      ["Bench Press", "Incline Bench", "Dumbbell Fly", "Push Up"],
            "back":       ["Deadlift", "Pull Up", "Barbell Row", "Lat Pulldown"],
            "legs":       ["Squat", "Leg Press", "Romanian Deadlift", "Lunge"],
            "shoulders":  ["Overhead Press", "Lateral Raise", "Face Pull"],
            "triceps":    ["Tricep Dip", "Skull Crusher", "Tricep Pushdown"],
            "biceps":     ["Barbell Curl", "Dumbbell Curl", "Hammer Curl"],
        }
        target_exercises = muscle_map.get(
            muscle_group.lower(),
            [muscle_group]   # If not a muscle group, treat as a specific lift
        )

        weekly_volume = {}
        for session in history:
            week = session.get("week_number") or session.get("date", "")[:7]
            for ex in session.get("exercises", []):
                if ex.get("name") in target_exercises:
                    vol = ex.get("sets", 0) * ex.get("reps", 0) * ex.get("weight_kg", 0)
                    weekly_volume[week] = weekly_volume.get(week, 0) + vol

        sorted_weeks = sorted(weekly_volume.items())[-weeks:]
        trend = "increasing" if len(sorted_weeks) > 1 and sorted_weeks[-1][1] > sorted_weeks[0][1] else "decreasing or flat"

        return {
            "muscle_group":   muscle_group,
            "weeks_analysed": len(sorted_weeks),
            "weekly_volume":  dict(sorted_weeks),
            "trend":          trend,
        }

    def _tool_calculate_training_max(
        self, exercise_name: str, weight_kg: float, reps: int, rpe: float = 8.0
    ) -> dict:
        """Calculate estimated 1RM and training max (90%) using Epley formula."""
        estimated_1rm    = self._epley(weight_kg, reps)
        rpe_adjustment   = 1 + (10 - rpe) * 0.03   # Add ~3% per RPE point below 10
        adjusted_1rm     = estimated_1rm * rpe_adjustment
        training_max     = round(adjusted_1rm * 0.90, 1)

        return {
            "exercise":       exercise_name,
            "estimated_1rm":  round(adjusted_1rm, 1),
            "training_max":   training_max,
            "week_1_weight":  round(training_max * 0.65, 1),   # 531-style week 1
            "week_2_weight":  round(training_max * 0.75, 1),
            "week_3_weight":  round(training_max * 0.85, 1),
        }

    def _tool_get_recovery_status(self) -> dict:
        """
        Estimate recovery by looking at sessions in last 7 days
        and average RPE trend.
        """
        history  = self.db.get_workout_history(self.username)
        recent   = history[-7:]
        sessions_last_7 = len(recent)

        rpes = [
            ex.get("rpe", 7)
            for s in recent
            for ex in s.get("exercises", [])
            if ex.get("rpe")
        ]
        avg_rpe  = round(sum(rpes) / len(rpes), 1) if rpes else 7.0
        rest_days = 7 - sessions_last_7

        if avg_rpe >= 9 or rest_days <= 1:
            status = "fatigued"
            recommendation = "Reduce intensity this session. Consider a deload."
        elif avg_rpe <= 6.5 and rest_days >= 3:
            status = "fresh"
            recommendation = "athlete is well rested — push intensity today."
        else:
            status = "normal"
            recommendation = "Standard training load is appropriate."

        return {
            "status":             status,
            "sessions_last_7_days": sessions_last_7,
            "rest_days":          rest_days,
            "average_rpe":        avg_rpe,
            "recommendation":     recommendation,
        }

    # ── Private helpers ────────────────────────────────────

    def _execute_tool(self, fn_name: str, fn_args: dict):
        handler = self._tool_router.get(fn_name)
        if not handler:
            return {"error": f"Unknown tool: {fn_name}"}
        try:
            return handler(**fn_args)
        except Exception as e:
            return {"error": str(e), "tool": fn_name}

    def _epley(self, weight: float, reps: int) -> float:
        """Epley 1RM formula."""
        if reps == 1:
            return weight
        return round(weight * (1 + reps / 30), 1)

    def _build_user_message(self) -> str:
        p = self.profile
        return (
            f"Generate a complete workout plan for this athlete.\n\n"
            f"Profile:\n"
            f"- Name: {getattr(p, 'name', 'Athlete')}\n"
            f"- Goal: {getattr(p, 'goal', 'general fitness')}\n"
            f"- Experience: {getattr(p, 'experience_level', 'intermediate')}\n"
            f"- Equipment: {', '.join(getattr(p, 'equipment', ['barbell', 'dumbbells']))}\n"
            f"- Training days/week: {getattr(p, 'days_per_week', 4)}\n"
            f"- Age: {getattr(p, 'age', 25)}, Weight: {getattr(p, 'weight_kg', 80)}kg\n"
            f"- Injuries: {', '.join(getattr(p, 'injuries', [])) or 'none'}\n\n"
            f"Before writing the plan, query the athlete's PRs, recent sessions, "
            f"recovery status, and any relevant volume trends. "
            f"Use what you find to justify every programming decision."
        )

    def _profile_summary(self) -> str:
        p = self.profile
        return (
            f"Goal={getattr(p,'goal','unknown')}, "
            f"Experience={getattr(p,'experience_level','unknown')}, "
            f"Days/week={getattr(p,'days_per_week',4)}"
        )

    def _pretty_args(self, args: dict) -> str:
        return ", ".join(f"{k}={v}" for k, v in args.items())

    def _is_final_round(self, round_n: int) -> bool:
        return round_n == MAX_ROUNDS - 1


# ─────────────────────────────────────────────────────────
# System Prompts
# ─────────────────────────────────────────────────────────

COACH_SYSTEM_PROMPT = """
You are an elite strength and conditioning coach with 20 years of experience.
You have access to the athlete's full training database via tools.

MANDATORY BEHAVIOUR:
1. ALWAYS call get_recovery_status before prescribing intensity.
2. ALWAYS call get_personal_records for any compound lift you plan to programme.
3. ALWAYS call get_recent_sessions to check training frequency and fatigue.
4. Call get_volume_trend if you suspect overtraining in a muscle group.
5. Call calculate_training_max if you're writing a strength block.
6. Only generate the plan AFTER you've gathered sufficient data.

Your final response MUST be a single valid JSON object:
{
  "plan_name": "string",
  "rationale": "2-3 sentences explaining WHY this specific plan, referencing what you found in the data",
  "days_per_week": integer,
  "coaching_notes": "string",
  "sessions": [
    {
      "day_label": "string",
      "focus": "string",
      "exercises": [
        {
          "name": "string",
          "sets": integer,
          "reps": "string",
          "suggested_weight_kg": number or null,
          "rest_seconds": integer,
          "rpe_target": integer,
          "coaching_cue": "string"
        }
      ]
    }
  ]
}

Return ONLY the JSON. No markdown. No explanation outside the JSON.
""".strip()

QA_SYSTEM_PROMPT = """
You are an IronPath AI coach answering a direct question from an athlete.
Use your tools to look up their actual data before answering.
Be direct, specific, and data-driven. Reference exact numbers from their history.
Keep answers under 150 words.
""".strip()
