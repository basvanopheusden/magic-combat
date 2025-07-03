"""Utilities for fetching and converting Scryfall card data.

Functions in this module retrieve French vanilla creature cards from Scryfall
and convert them into :class:`~magic_combat.creature.CombatCreature` objects.
"""

import json
from typing import Any
from typing import Dict
from typing import Iterable
from typing import List

import requests  # type: ignore[import]

from .creature import CombatCreature
from .keywords import ALLOWED_KEYWORDS
from .parsing import apply_keyword_attributes
from .parsing import parse_colors as _parse_colors

SCRYFALL_API = "https://api.scryfall.com/cards/search"
QUERY = "is:frenchvanilla t:creature"

# Keyword abilities supported by :class:`~magic_combat.creature.CombatCreature`.
# The names come from :mod:`magic_combat.keywords`.


def fetch_french_vanilla_cards(timeout: float = 10.0) -> List[Dict[str, Any]]:
    """Return a list of creature cards with only keyword abilities.

    Uses the Scryfall API's ``is:frenchvanilla`` query to find cards whose
    rules text contains only keyword abilities and no additional abilities.

    Parameters
    ----------
    timeout:
        Maximum number of seconds to wait for each HTTP request.  The default
        of 10 seconds should be suitable for most use cases.
    """
    url = SCRYFALL_API
    params: Dict[str, str] | None = {"q": QUERY}
    cards: List[Dict[str, Any]] = []
    with requests.Session() as session:
        while url:
            resp = session.get(url, params=params, timeout=timeout)
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
        "oracle_text": oracle_text,
        "colors": _parse_colors(mana_cost),
    }

    kwargs.update(apply_keyword_attributes(keywords, oracle_text))

    return CombatCreature(**kwargs)


def cards_to_creatures(
    cards: Iterable[Dict[str, Any]], controller: str
) -> List[CombatCreature]:
    """Convert an iterable of card dicts into :class:`CombatCreature` objects."""
    creatures = []
    for card in cards:
        try:
            creature = card_to_creature(card, controller)
            creatures.append(creature)
        except ValueError as exc:
            print(f"Skipping card {card.get('name', 'unknown')}: {exc}")

    return creatures
