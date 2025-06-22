import os
import random
from typing import List, Dict, Any, Tuple

from .creature import CombatCreature
from .gamestate import GameState, PlayerState
from .scryfall_loader import fetch_french_vanilla_cards, load_cards, save_cards
from . import DEFAULT_STARTING_LIFE

__all__ = ["load_or_fetch_cards", "card_to_creature", "create_random_combat"]


def load_or_fetch_cards(path: str) -> List[Dict[str, Any]]:
    """Load card data from ``path`` or download it if missing."""
    if os.path.exists(path):
        return load_cards(path)

    cards = fetch_french_vanilla_cards()
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    save_cards(cards, path)
    return cards


# Mapping from Scryfall keyword strings to :class:`CombatCreature` attributes
_SIMPLE_KEYWORDS = {
    "Flying": "flying",
    "Reach": "reach",
    "Menace": "menace",
    "Fear": "fear",
    "Shadow": "shadow",
    "Horsemanship": "horsemanship",
    "Skulk": "skulk",
    "Vigilance": "vigilance",
    "First strike": "first_strike",
    "Double strike": "double_strike",
    "Deathtouch": "deathtouch",
    "Trample": "trample",
    "Lifelink": "lifelink",
    "Wither": "wither",
    "Infect": "infect",
    "Indestructible": "indestructible",
    "Melee": "melee",
    "Training": "training",
    "Battalion": "battalion",
    "Dethrone": "dethrone",
    "Undying": "undying",
    "Persist": "persist",
    "Intimidate": "intimidate",
    "Defender": "defender",
}

_NUMERIC_KEYWORDS = {
    "Toxic": "toxic",
    "Bushido": "bushido",
    "Flanking": "flanking",
    "Rampage": "rampage",
    "Exalted": "exalted_count",
    "Battle cry": "battle_cry_count",
    "Frenzy": "frenzy",
    "Afflict": "afflict",
}


def _parse_numeric(keyword: str, card: Dict[str, Any]) -> int:
    """Return numeric value for ``keyword`` using the card's oracle text."""
    text = card.get("oracle_text", "")
    for line in text.splitlines():
        if line.startswith(f"{keyword} "):
            try:
                return int(line.split()[1])
            except (IndexError, ValueError):
                return 1
    return 1


def card_to_creature(card: Dict[str, Any], controller: str) -> CombatCreature:
    """Convert a Scryfall card dictionary to a :class:`CombatCreature`."""
    try:
        power = int(card.get("power", 0))
    except (TypeError, ValueError):
        power = 0
    try:
        toughness = int(card.get("toughness", 1))
    except (TypeError, ValueError):
        toughness = 1

    kwargs: Dict[str, Any] = {}
    for kw in card.get("keywords", []):
        if kw in _SIMPLE_KEYWORDS:
            kwargs[_SIMPLE_KEYWORDS[kw]] = True
        elif kw in _NUMERIC_KEYWORDS:
            kwargs[_NUMERIC_KEYWORDS[kw]] = _parse_numeric(kw, card)
        elif kw == "Provoke":
            kwargs["provoke_target"] = None

    return CombatCreature(
        name=card.get("name", "Unknown"),
        power=power,
        toughness=toughness,
        controller=controller,
        mana_cost=card.get("mana_cost", ""),
        **kwargs,
    )


def create_random_combat(
    num_attackers: int,
    num_blockers: int,
    card_path: str,
) -> Tuple[List[CombatCreature], List[CombatCreature], GameState]:
    """Generate a random combat scenario.

    The returned tuple contains the attackers, blockers and a ``GameState`` with
    both players starting at :data:`DEFAULT_STARTING_LIFE`.
    """
    cards = load_or_fetch_cards(card_path)
    if len(cards) < num_attackers + num_blockers:
        raise ValueError("Not enough cards to create scenario")

    atk_cards = random.sample(cards, num_attackers)
    blk_cards = random.sample(cards, num_blockers)

    attackers = [card_to_creature(c, "A") for c in atk_cards]
    blockers = [card_to_creature(c, "B") for c in blk_cards]

    state = GameState(
        players={
            "A": PlayerState(life=DEFAULT_STARTING_LIFE, creatures=attackers),
            "B": PlayerState(life=DEFAULT_STARTING_LIFE, creatures=blockers),
        }
    )
    return attackers, blockers, state
