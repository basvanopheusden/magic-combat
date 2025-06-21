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


def ensure_player_state(state, player: str):
    """Return existing :class:`PlayerState` for ``player`` or create one."""
    if state is None:
        raise ValueError("state cannot be None")

    # Import inside the function to avoid circular imports at module load time.
    from . import DEFAULT_STARTING_LIFE
    from .gamestate import PlayerState

    return state.players.setdefault(
        player, PlayerState(life=DEFAULT_STARTING_LIFE, creatures=[], poison=0)
    )
