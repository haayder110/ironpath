"""
data/database.py
================
Handles all reading and writing of user data.
Uses a local JSON file as a simple persistent store.

In a production app this would be swapped for a real
database (PostgreSQL, Firebase, etc.) without touching
any other part of the codebase — that is the point of
isolating data access here.
"""

import json
import os
import shutil
from datetime import datetime
from typing import Optional


DATA_FILE = "ironpath_save.json"
BACKUP_FILE = "ironpath_save.backup.json"


class Database:
    """Simple JSON-based persistence layer."""

    def __init__(self, filepath: str = DATA_FILE):
        self.filepath = filepath

    # ── Public API ────────────────────────────────────────────────────────────

    def load(self) -> Optional[dict]:
        """
        Load user data from disk.
        Returns None if no save file exists (first-time user).
        Raises RuntimeError if the file is corrupted.
        """
        if not os.path.exists(self.filepath):
            return None

        try:
            with open(self.filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
            self._validate(data)
            return data

        except json.JSONDecodeError as e:
            raise RuntimeError(
                f"Save file is corrupted ({e}). "
                f"Delete '{self.filepath}' to start fresh."
            )

    def save(self, data: dict) -> None:
        """
        Save user data to disk.
        Writes to a temp file first, then renames — prevents
        data loss if the process is killed mid-write.
        """
        self._validate(data)

        # Backup previous save
        if os.path.exists(self.filepath):
            shutil.copy2(self.filepath, BACKUP_FILE)

        # Atomic write
        tmp = self.filepath + ".tmp"
        try:
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            os.replace(tmp, self.filepath)
        except OSError as e:
            raise RuntimeError(f"Could not save data: {e}")
        finally:
            if os.path.exists(tmp):
                os.remove(tmp)

    def exists(self) -> bool:
        """Return True if a save file already exists."""
        return os.path.exists(self.filepath)

    def delete(self) -> None:
        """Delete save file (used in tests or reset flow)."""
        if os.path.exists(self.filepath):
            os.remove(self.filepath)

    # ── Private helpers ───────────────────────────────────────────────────────

    @staticmethod
    def _validate(data: dict) -> None:
        """
        Lightweight schema check.
        Raises ValueError with a clear message if required
        top-level keys are missing.
        """
        required = {"name", "goal", "xp", "streak", "total_workouts",
                    "workout_history", "prs", "badges"}
        missing = required - data.keys()
        if missing:
            raise ValueError(
                f"Save data is missing required fields: {missing}"
            )
