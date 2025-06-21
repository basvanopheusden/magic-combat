"""Core package for the Magic Combat simulator."""

from .creature import CombatCreature, Color
from .simulator import CombatResult, CombatSimulator
from .damage import DamageAssignmentStrategy, MostCreaturesKilledStrategy
from .gamestate import (
    GameState,
    PlayerState,
    STARTING_LIFE_TOTAL,
    has_player_lost,
)

__all__ = [
    "CombatCreature",
    "Color",
    "CombatResult",
    "CombatSimulator",
    "DamageAssignmentStrategy",
    "MostCreaturesKilledStrategy",
    "GameState",
    "PlayerState",
    "STARTING_LIFE_TOTAL",
    "has_player_lost",
]
