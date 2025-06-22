"""Shared ability name mappings for random generation and display."""

from __future__ import annotations

# Mapping from attribute names on :class:`CombatCreature` to human readable names
BOOL_NAMES = {
    "flying": "Flying",
    "reach": "Reach",
    "menace": "Menace",
    "fear": "Fear",
    "shadow": "Shadow",
    "horsemanship": "Horsemanship",
    "skulk": "Skulk",
    "unblockable": "Unblockable",
    "daunt": "Daunt",
    "vigilance": "Vigilance",
    "first_strike": "First strike",
    "double_strike": "Double strike",
    "deathtouch": "Deathtouch",
    "trample": "Trample",
    "lifelink": "Lifelink",
    "wither": "Wither",
    "infect": "Infect",
    "indestructible": "Indestructible",
    "melee": "Melee",
    "training": "Training",
    "mentor": "Mentor",
    "battalion": "Battalion",
    "dethrone": "Dethrone",
    "undying": "Undying",
    "persist": "Persist",
    "intimidate": "Intimidate",
    "defender": "Defender",
    "provoke": "Provoke",
}

INT_NAMES = {
    "toxic": "Toxic",
    "bushido": "Bushido",
    "flanking": "Flanking",
    "rampage": "Rampage",
    "exalted_count": "Exalted",
    "battle_cry_count": "Battle cry",
    "frenzy": "Frenzy",
    "afflict": "Afflict",
}

# Convenience sets of ability attribute names used for random generation
BOOL_ATTRIBUTES = set(BOOL_NAMES.keys())
INT_ATTRIBUTES = set(INT_NAMES.keys())

__all__ = [
    "BOOL_NAMES",
    "INT_NAMES",
    "BOOL_ATTRIBUTES",
    "INT_ATTRIBUTES",
]
