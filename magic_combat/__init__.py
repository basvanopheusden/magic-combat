"""Core package for the Magic Combat simulator."""

from .creature import CombatCreature, Color

# Default life total used when initializing ``PlayerState`` instances
DEFAULT_STARTING_LIFE = 20

from .simulator import CombatResult, CombatSimulator
from .damage import DamageAssignmentStrategy, MostCreaturesKilledStrategy
from .blocking_ai import decide_optimal_blocks
from .utils import calculate_mana_value
from .gamestate import GameState, PlayerState, has_player_lost

__all__ = [
    "CombatCreature",
    "Color",
    "CombatResult",
    "CombatSimulator",
    "DamageAssignmentStrategy",
    "MostCreaturesKilledStrategy",
    "decide_optimal_blocks",
    "GameState",
    "PlayerState",
    "has_player_lost",
    "calculate_mana_value",
    "DEFAULT_STARTING_LIFE",
]
