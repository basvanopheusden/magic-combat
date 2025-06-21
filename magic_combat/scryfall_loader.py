import json
from typing import List, Dict, Any

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
