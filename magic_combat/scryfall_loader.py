import json
from typing import List, Dict, Any, Iterable

import re

from .creature import CombatCreature, Color


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


_COLOR_MAP = {
    "W": Color.WHITE,
    "U": Color.BLUE,
    "B": Color.BLACK,
    "R": Color.RED,
    "G": Color.GREEN,
}

_COLOR_NAME_MAP = {
    "white": Color.WHITE,
    "blue": Color.BLUE,
    "black": Color.BLACK,
    "red": Color.RED,
    "green": Color.GREEN,
}


def _parse_colors(mana_cost: str) -> set[Color]:
    """Extract the set of colors appearing in ``mana_cost``."""
    colors: set[Color] = set()
    if not mana_cost:
        return colors
    for symbol in re.findall(r"{([^{}]+)}", mana_cost):
        for part in symbol.split("/"):
            col = _COLOR_MAP.get(part)
            if col:
                colors.add(col)
    return colors


def _parse_value(text: str, keyword: str) -> int:
    match = re.search(rf"{keyword}\\s*(\d+)", text)
    if match:
        return int(match.group(1))
    return 1


def _parse_protection(text: str) -> set[Color]:
    """Return a set of colors from "protection from" clauses."""
    colors: set[Color] = set()
    for match in re.findall(r"protection from ([^.,\n]+)", text, flags=re.I):
        parts = re.split(r"\s*and from\s*", match)
        for part in parts:
            color = _COLOR_NAME_MAP.get(part.strip().lower())
            if color:
                colors.add(color)
    return colors


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

    if "Flying" in keywords:
        kwargs["flying"] = True
    if "Reach" in keywords:
        kwargs["reach"] = True
    if "Menace" in keywords:
        kwargs["menace"] = True
    if "Fear" in keywords:
        kwargs["fear"] = True
    if "Shadow" in keywords:
        kwargs["shadow"] = True
    if "Horsemanship" in keywords:
        kwargs["horsemanship"] = True
    if "Skulk" in keywords:
        kwargs["skulk"] = True
    if "Vigilance" in keywords:
        kwargs["vigilance"] = True
    if "First strike" in keywords:
        kwargs["first_strike"] = True
    if "Double strike" in keywords:
        kwargs["double_strike"] = True
    if "Deathtouch" in keywords:
        kwargs["deathtouch"] = True
    if "Trample" in keywords:
        kwargs["trample"] = True
    if "Lifelink" in keywords:
        kwargs["lifelink"] = True
    if "Wither" in keywords:
        kwargs["wither"] = True
    if "Infect" in keywords:
        kwargs["infect"] = True
    if "Indestructible" in keywords:
        kwargs["indestructible"] = True

    if "Bushido" in keywords:
        kwargs["bushido"] = _parse_value(oracle_text, "Bushido")
    if "Flanking" in keywords:
        kwargs["flanking"] = kwargs.get("flanking", 0) + 1
    if "Rampage" in keywords:
        kwargs["rampage"] = _parse_value(oracle_text, "Rampage")
    if "Exalted" in keywords:
        kwargs["exalted_count"] = kwargs.get("exalted_count", 0) + 1
    if "Battle cry" in keywords:
        kwargs["battle_cry_count"] = kwargs.get("battle_cry_count", 0) + 1
    if "Melee" in keywords:
        kwargs["melee"] = True
    if "Training" in keywords:
        kwargs["training"] = True
    if "Mentor" in keywords:
        kwargs["mentor"] = True
    if "Frenzy" in keywords:
        kwargs["frenzy"] = _parse_value(oracle_text, "Frenzy")
    if "Battalion" in keywords:
        kwargs["battalion"] = True
    if "Dethrone" in keywords:
        kwargs["dethrone"] = True
    if "Undying" in keywords:
        kwargs["undying"] = True
    if "Persist" in keywords:
        kwargs["persist"] = True
    if "Intimidate" in keywords:
        kwargs["intimidate"] = True
    if "Daunt" in keywords:
        kwargs["daunt"] = True
    if "Defender" in keywords:
        kwargs["defender"] = True
    if "Afflict" in keywords:
        kwargs["afflict"] = _parse_value(oracle_text, "Afflict")
    if "Toxic" in keywords:
        kwargs["toxic"] = _parse_value(oracle_text, "Toxic")
    if "Provoke" in keywords:
        kwargs["provoke"] = True

    prot_colors = _parse_protection(oracle_text)
    if prot_colors:
        kwargs["protection_colors"] = prot_colors

    return CombatCreature(**kwargs)


def cards_to_creatures(cards: Iterable[Dict[str, Any]], controller: str) -> List[CombatCreature]:
    """Convert an iterable of card dicts into :class:`CombatCreature` objects."""

    return [card_to_creature(c, controller) for c in cards]
