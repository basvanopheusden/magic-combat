import json
from typing import List, Dict, Any, Iterable

from .creature import CombatCreature
from .parsing import (
    parse_colors as _parse_colors,
    parse_protection as _parse_protection,
    parse_value as _parse_value,
    apply_keyword_attributes,
)


import requests

SCRYFALL_API = "https://api.scryfall.com/cards/search"
QUERY = "is:frenchvanilla t:creature"

# Keyword abilities supported by :class:`~magic_combat.creature.CombatCreature`.
ALLOWED_KEYWORDS = {
    "Flying",
    "Reach",
    "Menace",
    "Fear",
    "Shadow",
    "Horsemanship",
    "Skulk",
    "Vigilance",
    "First strike",
    "Double strike",
    "Deathtouch",
    "Trample",
    "Lifelink",
    "Wither",
    "Infect",
    "Toxic",
    "Indestructible",
    "Bushido",
    "Flanking",
    "Rampage",
    "Exalted",
    "Battle cry",
    "Melee",
    "Training",
    "Frenzy",
    "Battalion",
    "Dethrone",
    "Undying",
    "Persist",
    "Intimidate",
    "Defender",
    "Afflict",
    "Provoke",
}


def fetch_french_vanilla_cards() -> List[Dict[str, Any]]:
    """Return a list of creature cards with only keyword abilities.

    Uses the Scryfall API's ``is:frenchvanilla`` query to find cards whose
    rules text contains only keyword abilities and no additional abilities.
    """
    url = SCRYFALL_API
    params = {"q": QUERY}
    cards: List[Dict[str, Any]] = []
    while url:
        resp = requests.get(url, params=params)
        resp.raise_for_status()
        data = resp.json()
        for c in data.get("data", []):
            if c.get("object") != "card":
                continue
            keywords = c.get("keywords", [])
            if not all(k in ALLOWED_KEYWORDS for k in keywords):
                continue
            cards.append(
                {
                    "name": c["name"],
                    "mana_cost": c.get("mana_cost"),
                    "power": c.get("power"),
                    "toughness": c.get("toughness"),
                    "oracle_text": c.get("oracle_text"),
                    "keywords": keywords,
                }
            )
        url = data.get("next_page")
        params = None
    return cards


def save_cards(cards: List[Dict[str, Any]], path: str) -> None:
    """Save ``cards`` to ``path`` as JSON."""
    with open(path, "w", encoding="utf8") as fh:
        json.dump(cards, fh, indent=2, ensure_ascii=False)


def load_cards(path: str) -> List[Dict[str, Any]]:
    """Load card data from ``path``."""
    with open(path, "r", encoding="utf8") as fh:
        return json.load(fh)




def card_to_creature(card: Dict[str, Any], controller: str) -> CombatCreature:
    """Convert a single card dictionary into a :class:`CombatCreature`."""

    name = card.get("name", "")
    try:
        power = int(card.get("power", 0))
    except (TypeError, ValueError):
        power = 0
    try:
        toughness = int(card.get("toughness", 0))
    except (TypeError, ValueError):
        toughness = 0
    mana_cost = card.get("mana_cost") or ""
    oracle_text = card.get("oracle_text") or ""
    keywords = set(card.get("keywords", []))

    kwargs: Dict[str, Any] = {
        "name": name,
        "power": power,
        "toughness": toughness,
        "controller": controller,
        "mana_cost": mana_cost,
        "colors": _parse_colors(mana_cost),
    }

    kwargs.update(apply_keyword_attributes(keywords, oracle_text))

    return CombatCreature(**kwargs)


def cards_to_creatures(cards: Iterable[Dict[str, Any]], controller: str) -> List[CombatCreature]:
    """Convert an iterable of card dicts into :class:`CombatCreature` objects."""

    return [card_to_creature(c, controller) for c in cards]
