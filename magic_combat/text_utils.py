"""Utility helpers for generating descriptive text."""

from typing import List

from .creature import CombatCreature
from .rules_text import describe_abilities


def summarize_creature(
    creature: CombatCreature, *, include_colors: bool = False
) -> str:
    """Return a readable one-line summary of ``creature``."""
    extra: List[str] = []
    if creature.plus1_counters:
        extra.append(f"+1/+1 x{creature.plus1_counters}")
    if creature.minus1_counters:
        extra.append(f"-1/-1 x{creature.minus1_counters}")
    if creature.damage_marked:
        extra.append(f"{creature.damage_marked} dmg")
    if creature.tapped:
        extra.append("tapped")
    extras = f" [{', '.join(extra)}]" if extra else ""
    color_info = ""
    if include_colors and creature.colors:
        joined = "/".join(
            c.name.capitalize() for c in sorted(creature.colors, key=lambda x: x.name)
        )
        color_info = f" [{joined}]"
    elif include_colors:
        color_info = " [Colorless]"

    stats = f"{creature.name}"
    if creature.mana_cost:
        stats += f" {creature.mana_cost}"
    stats += f" ({creature.power}/{creature.toughness})"

    return f"{stats}{color_info}{extras} -- {describe_abilities(creature)}"
