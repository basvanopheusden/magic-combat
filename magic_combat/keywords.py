"""Shared keyword ability mappings used for parsing and data loading."""

from __future__ import annotations

# Mapping of Scryfall keyword names to ``CombatCreature`` boolean attributes
BOOLEAN_KEYWORDS = {
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
    "Mentor": "mentor",
    "Battalion": "battalion",
    "Dethrone": "dethrone",
    "Undying": "undying",
    "Persist": "persist",
    "Intimidate": "intimidate",
    "Daunt": "daunt",
    "Defender": "defender",
    "Provoke": "provoke",
}

# Keywords that include an integer value in their rules text
VALUE_KEYWORDS = {
    "Bushido": "bushido",
    "Rampage": "rampage",
    "Frenzy": "frenzy",
    "Toxic": "toxic",
    "Afflict": "afflict",
}

# Keywords that stack when repeated
STACKABLE_KEYWORDS = {
    "Exalted": "exalted_count",
    "Battle cry": "battle_cry_count",
    "Flanking": "flanking",
}

# Convenience set of all supported Scryfall keyword names
ALLOWED_KEYWORDS = (
    set(BOOLEAN_KEYWORDS.keys())
    | set(VALUE_KEYWORDS.keys())
    | set(STACKABLE_KEYWORDS.keys())
)

__all__ = [
    "BOOLEAN_KEYWORDS",
    "VALUE_KEYWORDS",
    "STACKABLE_KEYWORDS",
    "ALLOWED_KEYWORDS",
]
