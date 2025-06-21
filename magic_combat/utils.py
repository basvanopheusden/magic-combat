"""Utility helpers used across the combat simulator."""

def check_non_negative(value: int, name: str) -> None:
    """Validate that ``value`` is not negative.

    Parameters
    ----------
    value:
        The integer value to validate.
    name:
        Human readable name of the value being validated.

    Raises
    ------
    ValueError
        If ``value`` is less than zero.
    """
    if value < 0:
        raise ValueError(f"{name} cannot be negative")


def check_positive(value: int, name: str) -> None:
    """Validate that ``value`` is strictly positive."""
    if value <= 0:
        raise ValueError(f"{name} must be positive")
