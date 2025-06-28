"""Utility helpers for parsing card data and abilities."""

from __future__ import annotations

import re
from typing import Any
from typing import Dict
from typing import Set

from .creature import Color
from .keywords import BOOLEAN_KEYWORDS as _BOOLEAN_KEYWORDS
from .keywords import STACKABLE_KEYWORDS as _STACKABLE_KEYWORDS
from .keywords import VALUE_KEYWORDS as _VALUE_KEYWORDS

# Mapping from short mana cost letters to :class:`Color` enums
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


def parse_colors(mana_cost: str) -> Set[Color]:
    """Return the set of colors appearing in ``mana_cost``."""
    colors: Set[Color] = set()
    if not mana_cost:
        return colors
    for symbol in re.findall(r"{([^{}]+)}", mana_cost):
        for part in symbol.split("/"):
            col = _COLOR_MAP.get(part)
            if col:
                colors.add(col)
    return colors


def parse_value(text: str, keyword: str) -> int:
    """Extract the numeric value following ``keyword`` in ``text``."""
    match = re.search(rf"{keyword}\s*(\d+)", text)
    if match:
        return int(match.group(1))
    return 1


def parse_protection(text: str) -> Set[Color]:
    """Return a set of colors from "protection from" clauses."""
    colors: Set[Color] = set()
    for match in re.findall(r"protection from ([^.,\n]+)", text, flags=re.I):
        parts = re.split(r"\s*and from\s*", match)
        for part in parts:
            color = _COLOR_NAME_MAP.get(part.strip().lower())
            if color:
                colors.add(color)
    return colors


# Keyword mappings are shared in :mod:`magic_combat.keywords`


def apply_keyword_attributes(keywords: Set[str], oracle_text: str) -> Dict[str, Any]:
    """Return attribute overrides for ``CombatCreature`` based on keywords."""
    attrs: Dict[str, Any] = {}

    for key in keywords:
        if key in _BOOLEAN_KEYWORDS:
            attrs[_BOOLEAN_KEYWORDS[key]] = True
        elif key in _STACKABLE_KEYWORDS:
            field = _STACKABLE_KEYWORDS[key]
            attrs[field] = attrs.get(field, 0) + 1
        elif key in _VALUE_KEYWORDS:
            attrs[_VALUE_KEYWORDS[key]] = parse_value(oracle_text, key)
    prot = parse_protection(oracle_text)
    if prot:
        attrs["protection_colors"] = prot
    return attrs
