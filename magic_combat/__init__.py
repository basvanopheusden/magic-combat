"""Core package for the Magic Combat simulator."""

from .creature import Color, CombatCreature

# Default life total used when initializing ``PlayerState`` instances
DEFAULT_STARTING_LIFE = 20
# Poison counter threshold at which a player loses the game
POISON_LOSS_THRESHOLD = 10
# Version tag used in snapshot test files
SNAPSHOT_VERSION = "1"

from .blocking_ai import decide_optimal_blocks, decide_simple_blocks
from .combat_utils import damage_creature, damage_player
from .create_llm_prompt import create_llm_prompt, parse_block_assignments
from .damage import DamageAssignmentStrategy, OptimalDamageStrategy
from .gamestate import GameState, PlayerState, has_player_lost
from .llm_cache import LLMCache, MockLLMCache
from .random_creature import (
    assign_random_counters,
    assign_random_tapped,
    compute_card_statistics,
    generate_random_creature,
)
from .random_scenario import (
    build_value_map,
    ensure_cards,
    generate_balanced_creatures,
    generate_random_scenario,
    sample_balanced,
)
from .rules_text import RULES_TEXT, get_relevant_rules_text
from .scryfall_loader import (
    card_to_creature,
    cards_to_creatures,
    fetch_french_vanilla_cards,
    load_cards,
    save_cards,
)
from .simulator import CombatResult, CombatSimulator
from .utils import (
    apply_attacker_blocking_bonuses,
    apply_blocker_bushido,
    calculate_mana_value,
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
    "POISON_LOSS_THRESHOLD",
    "SNAPSHOT_VERSION",
    "fetch_french_vanilla_cards",
    "load_cards",
    "save_cards",
    "card_to_creature",
    "cards_to_creatures",
    "compute_card_statistics",
    "generate_random_creature",
    "assign_random_counters",
    "assign_random_tapped",
    "ensure_cards",
    "build_value_map",
    "sample_balanced",
    "generate_balanced_creatures",
    "generate_random_scenario",
    "damage_creature",
    "damage_player",
    "apply_attacker_blocking_bonuses",
    "apply_blocker_bushido",
    "parse_block_assignments",
    "create_llm_prompt",
    "LLMCache",
    "MockLLMCache",
    "RULES_TEXT",
    "get_relevant_rules_text",
]
