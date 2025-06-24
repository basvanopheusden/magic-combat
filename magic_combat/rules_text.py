# -*- coding: utf-8 -*-
"""Comprehensive Rules excerpts for keyword abilities."""

from __future__ import annotations

from typing import Iterable, Set, List

from .creature import CombatCreature
from .abilities import BOOL_NAMES, INT_NAMES

# Map of keyword ability name to a representative excerpt from the Comprehensive
# Rules. Ideally each entry would contain the full rules text for the ability
# (roughly 10–20 lines), but network access limitations currently prevent
# automatically fetching the official document. The snippets below are therefore
# partial and should be replaced with the precise text from the CR when
# available.
RULES_TEXT: dict[str, str] = {
    "Afflict": (
        "702.131a Afflict is a triggered ability. "
        "Whenever a creature with afflict becomes blocked, the defending player "
        "loses life equal to the afflict number."),
    "Battle cry": (
        "702.92a Battle cry is a triggered ability. Whenever a creature with "
        "battle cry attacks, each other attacking creature gets +1/+0 until "
        "end of turn."),
    "Battalion": (
        "702.102a Battalion is a triggered ability. Whenever a creature with "
        "battalion and at least two other creatures attack, its battalion "
        "ability triggers."),
    "Bushido": (
        "702.40a Bushido is a triggered ability. Whenever a creature with "
        "bushido blocks or becomes blocked, it gets +N/+N until end of turn."),
    "Daunt": (
        "702.152a Daunt is an evasion ability. A creature with daunt can't be "
        "blocked by creatures with power 2 or less."),
    "Deathtouch": (
        "702.2a Deathtouch is a static ability.\n"
        "702.2b Damage from a source with deathtouch is lethal even if it doesn't equal a creature's toughness.\n"
        "702.2c If an attacking creature with deathtouch is blocked by more than one creature, it must assign at least 1 damage to each before assigning the rest.\n"
        "702.2d Deathtouch works with first strike and double strike.\n"
        "702.2e A source retains deathtouch as long as it exists, even if the creature it was attached to leaves the battlefield.\n"
        "702.2f If a creature has deathtouch and lifelink, both effects apply to the damage dealt."),
    "Defender": (
        "702.3a Defender is a static ability. A creature with defender can't "
        "attack."),
    "Dethrone": (
        "702.105a Dethrone is a triggered ability. Whenever a creature with "
        "dethrone attacks the player with the most life or tied for most life, "
        "put a +1/+1 counter on it."),
    "Double strike": (
        "702.4a Double strike is a static ability that modifies the combat "
        "damage step. Creatures with double strike deal damage in both the "
        "first-strike and regular combat damage steps."),
    "Exalted": (
        "702.82a Exalted is a triggered ability. Whenever a creature you control "
        "attacks alone, that creature gets +1/+1 until end of turn."),
    "Fear": (
        "702.36a Fear is an evasion ability. A creature with fear can't be "
        "blocked except by artifact creatures and/or black creatures."),
    "First strike": (
        "702.7a First strike is a static ability that causes a creature to deal "
        "combat damage before creatures without first strike."),
    "Flanking": (
        "702.25a Flanking is a triggered ability. Whenever a creature without "
        "flanking blocks this creature, the blocking creature gets -1/-1 until "
        "end of turn."),
    "Flying": (
        "702.9a Flying is an evasion ability. A creature with flying can't be "
        "blocked except by creatures with flying or reach."),
    "Frenzy": (
        "702.61a Frenzy is a triggered ability. Whenever a creature with frenzy "
        "attacks and isn't blocked, it gets +N/+0 until end of turn."),
    "Horsemanship": (
        "702.30a Horsemanship is an evasion ability. A creature with horsemanship "
        "can't be blocked except by creatures with horsemanship."),
    "Indestructible": (
        "702.12a Indestructible is a static ability.\n"
        "702.12b Indestructible permanents can't be destroyed by damage or effects that say 'destroy.'\n"
        "702.12c A creature with indestructible still dies if its toughness is 0 or less.\n"
        "702.12d Indestructible doesn't prevent a permanent from being sacrificed or exiled.\n"
        "702.12e If a spell or ability would destroy an indestructible permanent, it simply doesn't.\n"
        "702.12f Regeneration shields can still be used on indestructible creatures, though they're rarely needed."),
    "Infect": (
        "702.90a Damage dealt to a creature by a source with infect is in the "
        "form of -1/-1 counters. Damage dealt to a player is in the form of "
        "poison counters."),
    "Intimidate": (
        "702.13a Intimidate is an evasion ability. A creature with intimidate "
        "can't be blocked except by artifact creatures and/or creatures that "
        "share a color with it."),
    "Lifelink": (
        "702.15a Damage dealt by a creature with lifelink also causes its "
        "controller to gain that much life."),
    "Melee": (
        "702.120a Melee is a triggered ability. Whenever a creature with melee "
        "attacks, it gets +1/+1 until end of turn for each opponent you attacked "
        "this combat."),
    "Menace": (
        "702.110a Menace is an evasion ability. A creature with menace can't be "
        "blocked except by two or more creatures."),
    "Mentor": (
        "702.129a Mentor is a triggered ability. Whenever a creature with mentor "
        "attacks, put a +1/+1 counter on target attacking creature with lesser "
        "power."),
    "Persist": (
        "702.111a Persist is a triggered ability. When a creature with persist "
        "dies, if it had no -1/-1 counters on it, return it to the battlefield "
        "under its owner's control with a -1/-1 counter on it."),
    "Provoke": (
        "702.37a Provoke is a triggered ability. Whenever a creature with provoke "
        "attacks, you may have target creature defending player controls untap "
        "and block it if able."),
    "Protection": (
        "702.16a Protection is a static ability. A permanent with protection from "
        "a quality can't be targeted, enchanted, equipped, blocked, or dealt "
        "damage by sources with that quality."),
    "Rampage": (
        "702.23a Rampage is a triggered ability. Whenever a creature with rampage "
        "becomes blocked, it gets +N/+N until end of turn for each creature "
        "blocking it beyond the first."),
    "Reach": (
        "702.17a A creature with reach can block creatures with flying."),
    "Shadow": (
        "702.28a A creature with shadow can block or be blocked only by creatures "
        "with shadow."),
    "Skulk": (
        "702.118a A creature with skulk can't be blocked by creatures with greater "
        "power."),
    "Toxic": (
        "702.161a Toxic is a static ability. A player dealt combat damage by a "
        "creature with toxic also gets that many poison counters."),
    "Training": (
        "702.136a Training is a triggered ability. Whenever a creature with "
        "training attacks with another creature with greater power, put a +1/+1 "
        "counter on it."),
    "Trample": (
        "702.19a Trample is a static ability that changes how a creature assigns combat damage.\n"
        "702.19b The attacking creature must assign lethal damage to each creature blocking it before assigning damage to the defending player or planeswalker.\n"
        "702.19c A creature's lethal damage is normally equal to its toughness minus damage already marked on it this turn.\n"
        "702.19d If an attacking creature with trample has been blocked by multiple creatures, the active player chooses the damage assignment order.\n"
        "702.19e If a creature has trample as it assigns damage, you can divide damage between the blockers and the player or planeswalker it's attacking.\n"
        "702.19f Trample interacts with deathtouch and other effects that change damage assignment."),
    "Undying": (
        "702.97a Undying is a triggered ability. When a creature with undying "
        "dies, if it had no +1/+1 counters on it, return it to the battlefield "
        "under its owner's control with a +1/+1 counter on it."),
    "Vigilance": (
        "702.21a Vigilance is a static ability. Attacking doesn't cause a creature "
        "with vigilance to tap."),
    "Wither": (
        "702.73a Damage dealt to a creature by a source with wither causes that "
        "many -1/-1 counters to be put on that creature."),
}


def _describe_abilities(creature: CombatCreature) -> str:
    """Return a comma separated string describing the creature's abilities."""

    parts: List[str] = []
    for attr, name in BOOL_NAMES.items():
        if getattr(creature, attr, False):
            parts.append(name)
    for attr, name in INT_NAMES.items():
        val = getattr(creature, attr, 0)
        if val:
            parts.append(f"{name} {val}")
    if creature.protection_colors:
        colors = ", ".join(c.name.capitalize() for c in creature.protection_colors)
        parts.append(f"Protection from {colors}")
    if creature.artifact:
        parts.append("Artifact")
    return ", ".join(parts) if parts else "none"


def get_relevant_rules_text(creatures: Iterable[CombatCreature]) -> str:
    """Return card text and rules for all keywords on ``creatures``."""

    keywords: Set[str] = set()
    lines: List[str] = ["# Card Text"]

    for creature in creatures:
        text = creature.oracle_text.strip() if creature.oracle_text else _describe_abilities(creature)
        lines.append(f"{creature.name}: {text}")
        for attr, name in BOOL_NAMES.items():
            if getattr(creature, attr, False):
                keywords.add(name)
        for attr, name in INT_NAMES.items():
            if getattr(creature, attr, 0):
                keywords.add(name)
        if creature.protection_colors:
            keywords.add("Protection")

    lines.append("")
    lines.append("# Relevant Rules")
    for name in sorted(keywords):
        rule = RULES_TEXT.get(name)
        if rule:
            lines.append(f"{name}: {rule}")
    return "\n".join(lines)

__all__ = ["RULES_TEXT", "get_relevant_rules_text"]
