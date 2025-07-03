"""Utilities for creating random combat scenarios."""

from __future__ import annotations

import copy
import logging
import os
import random
from typing import Any
from typing import Dict
from typing import Generator
from typing import Iterable
from typing import List
from typing import Optional
from typing import Tuple

import numpy as np

from .blocking_ai import decide_optimal_blocks
from .blocking_ai import decide_simple_blocks
from .creature import CombatCreature
from .exceptions import CardDataError
from .exceptions import IllegalBlockError
from .exceptions import InvalidBlockScenarioError
from .exceptions import MagicCombatError
from .exceptions import MissingStatisticsError
from .exceptions import ScenarioGenerationError
from .gamestate import GameState
from .gamestate import PlayerState
from .random_creature import assign_random_counters
from .random_creature import assign_random_tapped
from .random_creature import generate_random_creature
from .scryfall_loader import card_to_creature
from .scryfall_loader import cards_to_creatures
from .scryfall_loader import fetch_french_vanilla_cards
from .scryfall_loader import load_cards
from .scryfall_loader import save_cards

__all__ = [
    "ensure_cards",
    "build_value_map",
    "sample_balanced",
    "generate_balanced_creatures",
    "generate_random_scenario",
]


def ensure_cards(path: str) -> list[dict[str, Any]]:
    """Load card data, downloading it if necessary."""
    if not os.path.exists(path):
        try:
            cards = fetch_french_vanilla_cards()
        except Exception as exc:  # pragma: no cover - network failure
            raise CardDataError(f"Failed to download card data: {exc}") from exc
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        save_cards(cards, path)
    return load_cards(path)


def build_value_map(cards: Iterable[dict[str, Any]]) -> Dict[int, float]:
    """Return a mapping of card index to combat value."""
    values: Dict[int, float] = {}
    for idx, card in enumerate(cards):
        try:
            creature = card_to_creature(card, "A")
        except ValueError:
            continue
        values[idx] = creature.value()
    if not values:
        raise CardDataError("No usable creatures found in card data")
    return values


def sample_balanced(
    cards: list[dict[str, Any]],
    values: Dict[int, float],
    n_att: int,
    n_blk: int,
    *,
    rng: random.Random | None = None,
) -> Tuple[List[int], List[int]]:
    """Select attackers and blockers with roughly equal value."""
    rng = rng if rng is not None else random.Random()
    idxs = list(values.keys())
    if n_att + n_blk > len(idxs):
        raise CardDataError("Not enough cards to sample from")

    best: Tuple[List[int], List[int]] | None = None
    best_diff = float("inf")

    for _ in range(1000):
        att_idx = rng.sample(idxs, n_att)
        remaining = [i for i in idxs if i not in att_idx]
        blk_idx = rng.sample(remaining, n_blk)

        att_val = sum(values[i] for i in att_idx)
        blk_val = sum(values[i] for i in blk_idx)
        avg = (att_val + blk_val) / 2 or 1
        diff = abs(att_val - blk_val) / avg

        if diff < best_diff:
            best = (att_idx, blk_idx)
            best_diff = diff

        if diff <= 0.25:
            return att_idx, blk_idx

    if best is None:
        raise ScenarioGenerationError("Failed to sample creatures")
    raise ScenarioGenerationError("Unable to generate balanced creature sets")


def generate_balanced_creatures(
    stats: Dict[str, object], n_att: int, n_blk: int
) -> Tuple[list[CombatCreature], list[CombatCreature]]:
    """Generate two sets of creatures with roughly equal value."""
    best: Tuple[list[CombatCreature], list[CombatCreature]] | None = None
    best_diff = float("inf")

    for _ in range(1000):
        attackers = [
            generate_random_creature(stats, controller="A") for _ in range(n_att)
        ]
        blockers = [
            generate_random_creature(stats, controller="B") for _ in range(n_blk)
        ]

        att_val = sum(c.value() for c in attackers)
        blk_val = sum(c.value() for c in blockers)
        avg = (att_val + blk_val) / 2 or 1
        diff = abs(att_val - blk_val) / avg

        if diff < best_diff:
            best = (attackers, blockers)
            best_diff = diff

        if diff <= 0.25:
            return attackers, blockers

    if best is None:
        raise ScenarioGenerationError("Failed to generate creatures")
    raise ScenarioGenerationError("Unable to generate balanced creature sets")


def _sample_creatures(
    cards: list[dict[str, Any]],
    values: Dict[int, float],
    stats: Dict[str, object] | None,
    *,
    generated_cards: bool,
    rng: random.Random,
    np_rng: np.random.Generator,
) -> Tuple[list[CombatCreature], list[CombatCreature]]:
    """Select or generate attackers and blockers with similar value."""

    n_atk = int(np_rng.geometric(1 / 2.5))
    n_blk = int(np_rng.geometric(1 / 2.5))
    n_atk = max(1, min(n_atk, len(values) // 2))
    n_blk = max(1, min(n_blk, len(values) // 2))

    if generated_cards:
        if stats is None:
            raise MissingStatisticsError(
                "stats must be provided when generated_cards is True"
            )
        return generate_balanced_creatures(stats, n_atk, n_blk)

    try:
        atk_idx, blk_idx_list = sample_balanced(cards, values, n_atk, n_blk, rng=rng)
    except ValueError as exc:  # pragma: no cover - rare
        raise InvalidBlockScenarioError(str(exc)) from exc
    attackers = cards_to_creatures((cards[j] for j in atk_idx), "A")
    blockers = cards_to_creatures((cards[j] for j in blk_idx_list), "B")
    return attackers, blockers


def _build_gamestate(
    attackers: list[CombatCreature],
    blockers: list[CombatCreature],
    rng: random.Random,
) -> GameState:
    """Return a randomized ``GameState`` for the provided creatures."""

    assign_random_counters(attackers + blockers, rng=rng)
    if not all(c.effective_toughness() > 0 for c in attackers + blockers):
        raise ScenarioGenerationError("Failed to sample creatures")
    assign_random_tapped(blockers, rng=rng)

    poison_relevant = any(c.infect or c.toxic for c in attackers + blockers)

    return GameState(
        players={
            "A": PlayerState(
                life=rng.randint(1, 20),
                creatures=attackers,
                poison=rng.randint(0, 9) if poison_relevant else 0,
            ),
            "B": PlayerState(
                life=rng.randint(1, 20),
                creatures=blockers,
                poison=rng.randint(0, 9) if poison_relevant else 0,
            ),
        }
    )


def _generate_interactions(
    attackers: list[CombatCreature],
    blockers: list[CombatCreature],
    rng: random.Random,
) -> Tuple[dict[CombatCreature, CombatCreature], dict[CombatCreature, CombatCreature],]:
    """Create provoke and mentor interaction mappings."""

    provoke_map: dict[CombatCreature, CombatCreature] = {
        atk: rng.choice(blockers) for atk in attackers if atk.provoke
    }
    for blk in provoke_map.values():
        blk.tapped = False

    mentor_map: dict[CombatCreature, CombatCreature] = {}
    for mentor in attackers:
        if mentor.mentor:
            targets = [
                c
                for c in attackers
                if c is not mentor and c.effective_power() < mentor.effective_power()
            ]
            if targets:
                mentor_map[mentor] = rng.choice(targets)

    return provoke_map, mentor_map


def _attempt_random_scenario(
    cards: list[dict[str, Any]],
    values: Dict[int, float],
    stats: Dict[str, object] | None,
    generated_cards: bool,
    rng: random.Random,
    np_rng: np.random.Generator,
    max_iterations: int,
    unique_optimal: bool,
) -> Tuple[
    GameState,
    dict[CombatCreature, CombatCreature],
    dict[CombatCreature, CombatCreature],
    Tuple[Optional[int], ...],
    Tuple[Optional[int], ...] | None,
]:
    """Attempt to create a single random combat scenario."""

    attackers, blockers = _sample_creatures(
        cards,
        values,
        stats,
        generated_cards=generated_cards,
        rng=rng,
        np_rng=np_rng,
    )

    original_state = _build_gamestate(attackers, blockers, rng)
    provoke_map, mentor_map = _generate_interactions(attackers, blockers, rng)

    optimal_state = copy.deepcopy(original_state)
    simple_state = copy.deepcopy(original_state)
    top, opt_count = decide_optimal_blocks(
        game_state=optimal_state,
        provoke_map=provoke_map,
        mentor_map=mentor_map,
        max_iterations=max_iterations,
        k=1,
    )
    if unique_optimal and opt_count != 1:
        logging.warning("Invalid block scenario: multiple optimal blocks found")
        raise InvalidBlockScenarioError("non unique optimal blocks")

    _, optimal_assignment = top[0]
    _, simple_assignment = decide_simple_blocks(
        game_state=simple_state,
        provoke_map=provoke_map,
        mentor_map=mentor_map,
        max_iterations=max_iterations,
    )

    if simple_assignment == optimal_assignment:
        logging.warning("Invalid block scenario: simple blocks equal optimal")
        raise InvalidBlockScenarioError("simple blocks equal optimal")
    return (
        original_state,
        provoke_map,
        mentor_map,
        optimal_assignment,
        simple_assignment,
    )


def generate_random_scenario(
    cards: list[dict[str, Any]],
    values: Dict[int, float],
    stats: Dict[str, object] | None = None,
    *,
    generated_cards: bool = False,
    max_iterations: int = int(1e4),
    unique_optimal: bool = False,
    seed: int | None = None,
) -> Generator[
    Tuple[
        GameState,
        dict[CombatCreature, CombatCreature],
        dict[CombatCreature, CombatCreature],
        Tuple[Optional[int], ...],
        Tuple[Optional[int], ...] | None,
    ],
    None,
    None,
]:
    """Yield non-trivial random combat scenarios indefinitely.

    Each yielded scenario passes the uniqueness and simple/optimal block checks.
    The ``GameState`` reflects the optimal blocks used to validate the scenario.
    ``attackers`` and ``blockers`` are cleared of any assignments so they can be
    reused. ``provoke_map`` and ``mentor_map`` describe any special attacker
    interactions and should be supplied when simulating combat. The optimal and
    simple block assignments are returned as tuples of attacker indices, along
    with a summary tuple of life lost, poison counters, number of creatures
    destroyed, value difference and mana value difference for the optimal blocks.
    """

    if not cards or not values:
        raise ScenarioGenerationError("Unable to generate valid scenario")

    rng = random.Random(seed) if seed is not None else random.Random()
    np_rng = (
        np.random.default_rng(seed) if seed is not None else np.random.default_rng()
    )

    while True:
        try:
            yield _attempt_random_scenario(
                cards,
                values,
                stats,
                generated_cards,
                rng,
                np_rng,
                max_iterations,
                unique_optimal,
            )
        except MissingStatisticsError:
            raise
        except (
            ScenarioGenerationError,
            IllegalBlockError,
            InvalidBlockScenarioError,
            MagicCombatError,
        ):
            continue
