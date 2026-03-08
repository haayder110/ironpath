import json
import os
import anthropic
from data.database import Database

MODEL = "claude-3-sonnet-20240229"
MAX_TOKENS = 2000
MAX_ROUNDS = 6

TOOLS = [
    {
        "name": "get_personal_records",
        "description": "Fetch the athlete's all-time personal records.",
        "input_schema": {
            "type": "object",
            "properties": {
                "exercise_names": {
                    "type": "array",
                    "items": {"type": "string"}
                }
            },
            "required": ["exercise_names"]
        }
    },
    {
        "name": "get_recent_sessions",
        "description": "Fetch recent workout sessions.",
        "input_schema": {
            "type": "object",
            "properties": {
                "n": {"type": "integer"}
            }
        }
    },
    {
        "name": "get_volume_trend",
        "description": "Get weekly training volume trend.",
        "input_schema": {
            "type": "object",
            "properties": {
                "muscle_group": {"type": "string"},
                "weeks": {"type": "integer"}
            },
            "required": ["muscle_group"]
        }
    },
    {
        "name": "calculate_training_max",
        "description": "Calculate training max using Epley formula.",
        "input_schema": {
            "type": "object",
            "properties": {
                "exercise_name": {"type": "string"},
                "weight_kg": {"type": "number"},
                "reps": {"type": "integer"},
                "rpe": {"type": "number"}
            },
            "required": ["exercise_name", "weight_kg", "reps"]
        }
    },
    {
        "name": "get_recovery_status",
        "description": "Estimate athlete recovery status.",
        "input_schema": {"type": "object", "properties": {}}
    }
]

COACH_SYSTEM_PROMPT = """
You are an elite strength coach.

Return ONLY JSON workout plan.
"""

QA_SYSTEM_PROMPT = """
Answer athlete questions using training data.
"""

class AICoach:
    def __init__(self, user_profile, api_key=None):
        key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not key:
            raise EnvironmentError("Set ANTHROPIC_API_KEY environment variable.")
        self.client = anthropic.Anthropic(api_key=key)
        self.profile = user_profile
        self.db = Database()
        self.username = getattr(user_profile, "name", "athlete")
        self._tool_router = {
            "get_personal_records": self._tool_get_prs,
            "get_recent_sessions": self._tool_get_sessions,
            "get_volume_trend": self._tool_get_volume_trend,
            "calculate_training_max": self._tool_calculate_training_max,
            "get_recovery_status": self._tool_get_recovery_status,
        }

    def generate_plan(self):
        messages = [
            {"role": "user", "content": self._build_user_message()}
        ]
        for _ in range(MAX_ROUNDS):
            response = self.client.messages.create(
                model=MODEL,
                max_tokens=MAX_TOKENS,
                system=COACH_SYSTEM_PROMPT,
                tools=TOOLS,
                messages=messages,
            )
            if response.stop_reason == "end_turn":
                for block in response.content:
                    if hasattr(block, "text"):
                        text = block.text.strip()
                        clean = text.replace("```json", "").replace("```", "").strip()
                        return json.loads(clean)
            if response.stop_reason == "tool_use":
                messages.append({"role": "assistant", "content": response.content})
                tool_results = []
                for block in response.content:
                    if block.type == "tool_use":
                        fn_name = block.name
                        fn_args = block.input
                        result = self._execute_tool(fn_name, fn_args)
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": json.dumps(result)
                        })
                # Append serialized tool results
                messages.append({"role": "user", "content": json.dumps(tool_results)})
        raise RuntimeError("AI coach did not produce a plan.")

    def ask(self, question):
        messages = [
            {"role": "user", "content": question}
        ]
        for _ in range(MAX_ROUNDS):
            response = self.client.messages.create(
                model=MODEL,
                max_tokens=500,
                system=QA_SYSTEM_PROMPT,
                tools=TOOLS,
                messages=messages,
            )
            if response.stop_reason == "end_turn":
                for block in response.content:
                    if hasattr(block, "text"):
                        return block.text.strip()
            if response.stop_reason == "tool_use":
                messages.append({"role": "assistant", "content": response.content})
                tool_results = []
                for block in response.content:
                    if block.type == "tool_use":
                        result = self._execute_tool(block.name, block.input)
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": json.dumps(result)
                        })
                messages.append({"role": "user", "content": json.dumps(tool_results)})
        return "Unable to answer."

    def _tool_get_prs(self, exercise_names):
        prs = {}
        for name in exercise_names:
            record = self.db.get_pr(self.username, name)
            prs[name] = record if record else None
        return {"personal_records": prs}

    def _tool_get_sessions(self, n=5):
        history = self.db.get_workout_history(self.username)
        return {"sessions": history[-n:]}

    def _tool_get_volume_trend(self, muscle_group, weeks=4):
        history = self.db.get_workout_history(self.username)
        volume = {}
        for session in history:
            week = session.get("date", "")[:7]
            for ex in session.get("exercises", []):
                if muscle_group.lower() in ex.get("name", "").lower():
                    v = ex["sets"] * ex["reps"] * ex["weight_kg"]
                    volume[week] = volume.get(week, 0) + v
        return {"trend": volume}

    def _tool_calculate_training_max(self, exercise_name, weight_kg, reps, rpe=8):
        est = self._epley(weight_kg, reps)
        training_max = round(est * 0.9, 1)
        return {
            "exercise": exercise_name,
            "training_max": training_max
        }

    def _tool_get_recovery_status(self):
        history = self.db.get_workout_history(self.username)
        recent = history[-7:]
        return {"sessions_last_week": len(recent)}

    def _execute_tool(self, name, args):
        handler = self._tool_router.get(name)
        if not handler:
            return {"error": "Unknown tool"}
        try:
            return handler(**args)
        except Exception as e:
            return {"error": str(e)}

    def _epley(self, weight, reps):
        return round(weight * (1 + reps / 30), 1)

    def _build_user_message(self):
        p = self.profile
        return f"""
Generate workout plan.

Name: {getattr(p,'name','Athlete')}
Goal: {getattr(p,'goal','fitness')}
Experience: {getattr(p,'experience_level','intermediate')}
Days/week: {getattr(p,'days_per_week',4)}
"""
