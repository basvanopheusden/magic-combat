"""Core package for the Magic Combat simulator."""

from .blocking_ai import decide_optimal_blocks
from .blocking_ai import decide_simple_blocks
from .combat_utils import damage_creature
from .combat_utils import damage_player
from .constants import DEFAULT_STARTING_LIFE
from .constants import POISON_LOSS_THRESHOLD
from .constants import SNAPSHOT_VERSION
from .create_llm_prompt import create_llm_prompt
from .create_llm_prompt import parse_block_assignments
from .creature import Color
from .creature import CombatCreature
from .damage import optimal_damage_order
from .dataset import ReferenceAnswer
from .exceptions import CardDataError
from .exceptions import IllegalBlockError
from .exceptions import InvalidBlockScenarioError
from .exceptions import IterationLimitError
from .exceptions import MissingStatisticsError
from .exceptions import ScenarioGenerationError
from .exceptions import UnparsableLLMOutputError
from .gamestate import GameState
from .gamestate import PlayerState
from .llm_cache import LLMCache
from .llm_cache import MockLLMCache
from .random_creature import assign_random_counters
from .random_creature import assign_random_tapped
from .random_creature import compute_card_statistics
from .random_creature import generate_random_creature
from .random_scenario import build_value_map
from .random_scenario import ensure_cards
from .random_scenario import generate_balanced_creatures
from .random_scenario import generate_random_scenario
from .random_scenario import sample_balanced
from .rules_text import RULES_TEXT
from .rules_text import get_relevant_rules_text
from .scryfall_loader import card_to_creature
from .scryfall_loader import cards_to_creatures
from .scryfall_loader import fetch_french_vanilla_cards
from .scryfall_loader import load_cards
from .scryfall_loader import save_cards
from .simulator import CombatResult
from .simulator import CombatSimulator
from .snapshot import creature_from_dict
from .snapshot import creature_to_dict
from .snapshot import decode_mapping
from .snapshot import decode_mentor
from .snapshot import decode_provoke
from .snapshot import encode_map
from .snapshot import state_from_dict
from .snapshot import state_to_dict
from .utils import apply_attacker_blocking_bonuses
from .utils import apply_blocker_bushido
from .utils import calculate_mana_value

__all__ = [
    "CombatCreature",
    "Color",
    "CombatResult",
    "CombatSimulator",
    "optimal_damage_order",
    "decide_optimal_blocks",
    "decide_simple_blocks",
    "GameState",
    "PlayerState",
    "calculate_mana_value",
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
    "IllegalBlockError",
    "InvalidBlockScenarioError",
    "IterationLimitError",
    "CardDataError",
    "ScenarioGenerationError",
    "MissingStatisticsError",
    "UnparsableLLMOutputError",
    "parse_block_assignments",
    "create_llm_prompt",
    "LLMCache",
    "MockLLMCache",
    "RULES_TEXT",
    "get_relevant_rules_text",
    "DEFAULT_STARTING_LIFE",
    "POISON_LOSS_THRESHOLD",
    "SNAPSHOT_VERSION",
    "creature_to_dict",
    "creature_from_dict",
    "state_to_dict",
    "state_from_dict",
    "encode_map",
    "decode_mapping",
    "decode_provoke",
    "decode_mentor",
    "ReferenceAnswer",
]
