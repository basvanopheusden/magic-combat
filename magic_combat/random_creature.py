"""Utilities for generating random creatures based on card statistics."""

from __future__ import annotations

import random
from collections import Counter
from collections import defaultdict
from typing import Any
from typing import Dict
from typing import Iterable
from typing import Tuple
from typing import cast

import numpy as np

from .abilities import BOOL_ATTRIBUTES as _BOOL_ABILITIES
from .abilities import INT_ATTRIBUTES as _INT_ABILITIES
from .creature import Color
from .creature import CombatCreature
from .scryfall_loader import cards_to_creatures

# Probability thresholds for assigning +1/+1 or -1/-1 counters
PLUS1_PROB = 0.1
MINUS1_PROB = 0.2

# Default probability used when randomly tapping creatures
DEFAULT_TAP_PROB = 0.3

__all__ = [
    "PLUS1_PROB",
    "MINUS1_PROB",
    "DEFAULT_TAP_PROB",
    "compute_card_statistics",
    "generate_random_creature",
    "assign_random_counters",
    "assign_random_tapped",
]


def compute_card_statistics(cards: Iterable[dict]) -> Dict[str, Any]:
    """Return first and second order statistics for ``cards``.

    The returned mapping contains the mean and standard deviation of power and
    toughness along with the observed probability of each ability and pairwise
    ability co-occurrences.
    """

    creatures = cards_to_creatures(cards, "A")
    powers: list[int] = []
    toughnesses: list[int] = []
    ability_counts: Counter[str] = Counter()
    pair_counts: Dict[str, Counter[str]] = defaultdict(Counter)

    for cr in creatures:
        powers.append(cr.power)
        toughnesses.append(cr.toughness)
        present = []
        for attr in _BOOL_ABILITIES:
            if getattr(cr, attr, False):
                present.append(attr)
        for attr in _INT_ABILITIES:
            if getattr(cr, attr, 0):
                present.append(attr)
        if cr.protection_colors:
            present.append("protection")
        ability_counts.update(present)
        for i, a in enumerate(present):
            for b in present[i + 1 :]:
                pair = tuple(sorted((a, b)))
                pair_counts[pair[0]][pair[1]] += 1
                pair_counts[pair[1]][pair[0]] += 1

    total = len(creatures) or 1
    ability_prob = {a: ability_counts[a] / total for a in ability_counts}
    pair_prob: Dict[Tuple[str, str], float] = {}
    for a, inner in pair_counts.items():
        for b, count in inner.items():
            pair_prob[(a, b)] = count / total

    stats = {
        "power_mean": float(np.mean(powers) if powers else 0.0),
        "power_std": float(np.std(powers) if powers else 1.0),
        "toughness_mean": float(np.mean(toughnesses) if toughnesses else 0.0),
        "toughness_std": float(np.std(toughnesses) if toughnesses else 1.0),
        "ability_prob": ability_prob,
        "pair_prob": pair_prob,
    }
    return stats


def _conditional_probability(a: str, b: str, stats: Dict[str, Any]) -> float:
    pair_prob = stats["pair_prob"].get((min(a, b), max(a, b)), 0.0)
    base = stats["ability_prob"].get(a, 0.0)
    if base <= 0:
        return 0.0
    return min(1.0, pair_prob / base)


def generate_random_creature(
    stats: Dict[str, Any], controller: str = "A", name: str | None = None
) -> CombatCreature:
    """Generate a random creature matching the provided statistics."""

    if name is None:
        name = f"Generated {random.randint(1, 9999)}"

    mean_p = stats.get("power_mean", 0.0)
    std_p = stats.get("power_std", 1.0)
    mean_t = stats.get("toughness_mean", 0.0)
    std_t = stats.get("toughness_std", 1.0)

    power = max(0, int(round(random.gauss(mean_p, std_p))))
    toughness = max(1, int(round(random.gauss(mean_t, std_t))))

    chosen: set[str] = set()
    abilities = list(stats.get("ability_prob", {}).keys())
    random.shuffle(abilities)
    for a in abilities:
        if random.random() < stats["ability_prob"].get(a, 0.0):
            chosen.add(a)
            for b in abilities:
                if b != a and b not in chosen:
                    cond = _conditional_probability(a, b, stats)
                    if cond and random.random() < cond:
                        chosen.add(b)

    kwargs: Dict[str, object] = {
        "name": name,
        "power": power,
        "toughness": toughness,
        "controller": controller,
    }
    for ability in chosen:
        if ability in _BOOL_ABILITIES:
            kwargs[ability] = True
        elif ability in _INT_ABILITIES:
            kwargs[ability] = 1
        elif ability == "protection":
            kwargs["protection_colors"] = {random.choice(list(Color))}
    return CombatCreature(**cast(Any, kwargs))


def assign_random_counters(
    creatures: Iterable[CombatCreature], *, rng: random.Random | None = None
) -> None:
    """Add random +1/+1 or -1/-1 counters to ``creatures``.

    A creature receives at most one kind of counter and never enough -1/-1
    counters to reduce its toughness below zero.
    """
    rng = rng if rng is not None else random.Random()
    for cr in creatures:
        roll = rng.random()
        if roll < PLUS1_PROB:
            cr.plus1_counters = rng.randint(1, 2)
        elif roll < MINUS1_PROB:
            max_minus = min(2, cr.toughness)
            if max_minus > 0:
                cr.minus1_counters = rng.randint(1, max_minus)


def assign_random_tapped(
    creatures: Iterable[CombatCreature],
    *,
    rng: random.Random | None = None,
    prob: float = DEFAULT_TAP_PROB,
) -> None:
    """Randomly tap creatures without vigilance.

    CR 302.2 states that tapped creatures can't attack or block. Vigilance
    (CR 702.21b) keeps a creature from tapping when it attacks, so vigilant
    defenders remain untapped here.
    """

    rng = rng if rng is not None else random.Random()
    for cr in creatures:
        if cr.vigilance:
            cr.tapped = False
        elif rng.random() < prob:
            cr.tapped = True
