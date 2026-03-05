"""
utils/validators.py
===================
Pure input-validation functions.
All functions raise ValueError with a human-readable message
on bad input, and return the cleaned value on success.
"""


def validate_positive_float(raw: str, field_name: str = "value") -> float:
    """
    Parse a string as a positive float.
    Accepts both '80' and '80.5'.
    Raises ValueError with a clear message on failure.
    """
    try:
        value = float(raw.strip())
    except ValueError:
        raise ValueError(f"{field_name} must be a number (e.g. 80 or 80.5).")

    if value <= 0:
        raise ValueError(f"{field_name} must be greater than zero.")

    return value


def validate_positive_int(raw: str, field_name: str = "value") -> int:
    """Parse a string as a positive integer."""
    try:
        value = int(raw.strip())
    except ValueError:
        raise ValueError(f"{field_name} must be a whole number (e.g. 5).")

    if value <= 0:
        raise ValueError(f"{field_name} must be greater than zero.")

    return value


def validate_rpe(raw: str) -> int:
    """
    Parse an RPE (Rate of Perceived Exertion) value.
    Must be an integer between 1 and 10.
    Returns -1 if the user skipped (empty input).
    """
    if raw.strip() == "":
        return -1  # sentinel for "skipped"

    try:
        value = int(raw.strip())
    except ValueError:
        raise ValueError("RPE must be a whole number between 1 and 10.")

    if not 1 <= value <= 10:
        raise ValueError("RPE must be between 1 and 10.")

    return value


def validate_menu_choice(raw: str, min_val: int, max_val: int) -> int:
    """Validate a numeric menu selection within a given range."""
    try:
        value = int(raw.strip())
    except ValueError:
        raise ValueError(f"Please enter a number between {min_val} and {max_val}.")

    if not min_val <= value <= max_val:
        raise ValueError(f"Please enter a number between {min_val} and {max_val}.")

    return value


def validate_name(raw: str) -> str:
    """Validate a user-supplied name. Returns stripped title-cased name."""
    name = raw.strip()
    if not name:
        raise ValueError("Name cannot be empty.")
    if len(name) > 50:
        raise ValueError("Name is too long (max 50 characters).")
    if not all(c.isalpha() or c in " '-" for c in name):
        raise ValueError("Name can only contain letters, spaces, hyphens, or apostrophes.")
    return name.title()
