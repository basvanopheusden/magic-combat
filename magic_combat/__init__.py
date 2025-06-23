"""Core package for the Magic Combat simulator."""

from .creature import CombatCreature, Color

# Default life total used when initializing ``PlayerState`` instances
DEFAULT_STARTING_LIFE = 20

from .simulator import CombatResult, CombatSimulator
from .damage import DamageAssignmentStrategy, OptimalDamageStrategy
from .blocking_ai import decide_optimal_blocks, decide_simple_blocks
from .utils import (
    calculate_mana_value,
    apply_attacker_blocking_bonuses,
    apply_blocker_bushido,
)
from .gamestate import GameState, PlayerState, has_player_lost
from .scryfall_loader import (
    fetch_french_vanilla_cards,
    load_cards,
    save_cards,
    card_to_creature,
    cards_to_creatures,
)
from .random_creature import (
    compute_card_statistics,
    generate_random_creature,
    assign_random_counters,
    assign_random_tapped,
)

__all__ = [
    "CombatCreature",
    "Color",
    "CombatResult",
    "CombatSimulator",
    "DamageAssignmentStrategy",
    "OptimalDamageStrategy",
    "decide_optimal_blocks",
    "decide_simple_blocks",
    "GameState",
    "PlayerState",
    "has_player_lost",
    "calculate_mana_value",
    "DEFAULT_STARTING_LIFE",
    "fetch_french_vanilla_cards",
    "load_cards",
    "save_cards",
    "card_to_creature",
    "cards_to_creatures",
    "compute_card_statistics",
    "generate_random_creature",
    "assign_random_counters",
    "assign_random_tapped",
    "apply_attacker_blocking_bonuses",
    "apply_blocker_bushido",
]
