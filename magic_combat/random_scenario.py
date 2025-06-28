"""Utilities for creating random combat scenarios."""

from __future__ import annotations

import copy
import os
import random
from typing import Dict, Iterable, List, Optional, Tuple

import numpy as np

from .blocking_ai import decide_optimal_blocks, decide_simple_blocks
from .creature import CombatCreature
from .damage import _blocker_value, score_combat_result
from .gamestate import GameState, PlayerState
from .random_creature import (assign_random_counters, assign_random_tapped,
                              generate_random_creature)
from .scryfall_loader import (card_to_creature, cards_to_creatures,
                              fetch_french_vanilla_cards, load_cards,
                              save_cards)
from .simulator import CombatSimulator

__all__ = [
    "ensure_cards",
    "build_value_map",
    "sample_balanced",
    "generate_balanced_creatures",
    "generate_random_scenario",
]


def ensure_cards(path: str) -> List[dict]:
    """Load card data, downloading it if necessary."""
    if not os.path.exists(path):
        try:
            cards = fetch_french_vanilla_cards()
        except Exception as exc:  # pragma: no cover - network failure
            raise SystemExit(f"Failed to download card data: {exc}")
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        save_cards(cards, path)
    return load_cards(path)


def build_value_map(cards: Iterable[dict]) -> Dict[int, float]:
    """Return a mapping of card index to combat value."""
    values: Dict[int, float] = {}
    for idx, card in enumerate(cards):
        try:
            creature = card_to_creature(card, "A")
        except ValueError:
            continue
        values[idx] = _blocker_value(creature)
    if not values:
        raise ValueError("No usable creatures found in card data")
    return values


def sample_balanced(
    cards: List[dict],
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
        raise ValueError("Not enough cards to sample from")

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
        raise ValueError("Failed to sample creatures")
    raise ValueError("Unable to generate balanced creature sets")


def generate_balanced_creatures(
    stats: Dict[str, object], n_att: int, n_blk: int
) -> Tuple[List, List]:
    """Generate two sets of creatures with roughly equal value."""
    best: Tuple[List, List] | None = None
    best_diff = float("inf")

    for _ in range(1000):
        attackers = [
            generate_random_creature(stats, controller="A") for _ in range(n_att)
        ]
        blockers = [
            generate_random_creature(stats, controller="B") for _ in range(n_blk)
        ]

        att_val = sum(_blocker_value(c) for c in attackers)
        blk_val = sum(_blocker_value(c) for c in blockers)
        avg = (att_val + blk_val) / 2 or 1
        diff = abs(att_val - blk_val) / avg

        if diff < best_diff:
            best = (attackers, blockers)
            best_diff = diff

        if diff <= 0.25:
            return attackers, blockers

    if best is None:
        raise ValueError("Failed to generate creatures")
    raise ValueError("Unable to generate balanced creature sets")


def generate_random_scenario(
    cards: List[dict],
    values: Dict[int, float],
    stats: Dict[str, object] | None = None,
    *,
    generated_cards: bool = False,
    max_iterations: int = int(1e6),
    unique_optimal: bool = False,
    seed: int | None = None,
) -> Tuple[
    GameState,
    List,
    List,
    dict,
    dict,
    Tuple[Optional[int], ...],
    Tuple[Optional[int], ...] | None,
    Tuple[int, int, int, float],
]:
    """Return a non-trivial random combat scenario.

    The returned ``GameState`` reflects the optimal blocks used to validate the
    scenario. ``attackers`` and ``blockers`` are cleared of any assignments so
    they can be reused. ``provoke_map`` and ``mentor_map`` describe any special
    attacker interactions and should be supplied when simulating combat. The
    optimal and simple block assignments are returned as tuples of attacker
    indices, along with a summary tuple of life lost, poison counters, number of
    creatures destroyed and value difference for the optimal blocks.
    """

    rng = random.Random(seed) if seed is not None else random.Random()
    np_rng = (
        np.random.default_rng(seed) if seed is not None else np.random.default_rng()
    )

    valid_len = len(values)
    attempts = 0
    while True:
        attempts += 1
        if attempts > 100:
            raise RuntimeError("Unable to generate valid scenario")

        n_atk = int(np_rng.geometric(1 / 2.5))
        n_blk = int(np_rng.geometric(1 / 2.5))
        n_atk = max(1, min(n_atk, valid_len // 2))
        n_blk = max(1, min(n_blk, valid_len // 2))

        try:
            if generated_cards:
                if stats is None:
                    raise ValueError(
                        "stats must be provided when generated_cards is True"
                    )
                attackers, blockers = generate_balanced_creatures(stats, n_atk, n_blk)
            else:
                atk_idx, blk_idx_list = sample_balanced(
                    cards, values, n_atk, n_blk, rng=rng
                )
                attackers = cards_to_creatures((cards[j] for j in atk_idx), "A")
                blockers = cards_to_creatures((cards[j] for j in blk_idx_list), "B")
        except ValueError:
            continue

        assign_random_counters(attackers + blockers, rng=rng)
        assign_random_tapped(blockers, rng=rng)

        poison_relevant = any(c.infect or c.toxic for c in attackers + blockers)

        state = GameState(
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

        provoke_map = {atk: rng.choice(blockers) for atk in attackers if atk.provoke}
        for blk in provoke_map.values():
            blk.tapped = False

        mentor_map = {}
        for mentor in attackers:
            if mentor.mentor:
                targets = [
                    c
                    for c in attackers
                    if c is not mentor
                    and c.effective_power() < mentor.effective_power()
                ]
                if targets:
                    mentor_map[mentor] = rng.choice(targets)

        simple_atk = copy.deepcopy(attackers)
        simple_blk = copy.deepcopy(blockers)
        simple_state = copy.deepcopy(state)
        try:
            decide_simple_blocks(
                simple_atk,
                simple_blk,
                game_state=simple_state,
                provoke_map=provoke_map,
            )
            sim_check = CombatSimulator(simple_atk, simple_blk, game_state=simple_state)
            sim_check.validate_blocking()
            atk_map = {id(a): i for i, a in enumerate(simple_atk)}
            simple_assignment = tuple(
                atk_map.get(id(b.blocking), None) for b in simple_blk
            )
        except ValueError:
            simple_assignment = None

        try:
            _, opt_count = decide_optimal_blocks(
                attackers,
                blockers,
                game_state=state,
                provoke_map=provoke_map,
                max_iterations=max_iterations,
            )
            if unique_optimal and opt_count != 1:
                continue
        except (ValueError, RuntimeError):
            continue

        opt_map = {id(a): i for i, a in enumerate(attackers)}
        optimal_assignment: Tuple[Optional[int], ...] = tuple(
            opt_map.get(id(b.blocking), None) for b in blockers
        )

        if simple_assignment is not None and simple_assignment == optimal_assignment:
            continue

        atk_copy = copy.deepcopy(attackers)
        blk_copy = copy.deepcopy(blockers)
        state_copy = copy.deepcopy(state)
        prov_copies: dict[CombatCreature, CombatCreature] = {}
        if provoke_map:
            atk_map_idx = {id(a): i for i, a in enumerate(attackers)}
            blk_map_idx = {id(b): i for i, b in enumerate(blockers)}
            for atk, blk in provoke_map.items():
                if atk in attackers and blk in blockers:
                    a_copy = atk_copy[atk_map_idx[id(atk)]]
                    b_copy = blk_copy[blk_map_idx[id(blk)]]
                    prov_copies[a_copy] = b_copy
        mentor_copies: dict[CombatCreature, CombatCreature] = {}
        if mentor_map:
            atk_map_idx = {id(a): i for i, a in enumerate(attackers)}
            for mentor, target in mentor_map.items():
                if mentor in attackers and target in attackers:
                    mentor_copies[atk_copy[atk_map_idx[id(mentor)]]] = atk_copy[
                        atk_map_idx[id(target)]
                    ]
        for blk_idx, choice in enumerate(optimal_assignment):
            if choice is not None:
                idx = int(choice)
                blk_copy[blk_idx].blocking = atk_copy[idx]
                atk_copy[idx].blocked_by.append(blk_copy[blk_idx])
        sim = CombatSimulator(
            atk_copy,
            blk_copy,
            game_state=state_copy,
            provoke_map=prov_copies or None,
            mentor_map=mentor_copies or None,
        )
        result = sim.simulate()
        score = score_combat_result(result, "A", "B")
        combat_value = (score[4], score[5], score[2], score[1])

        start_state = copy.deepcopy(state)
        for atk in attackers:
            atk.blocked_by.clear()
        for blk in blockers:
            blk.blocking = None
        return (
            start_state,
            attackers,
            blockers,
            provoke_map,
            mentor_map,
            optimal_assignment,
            simple_assignment,
            combat_value,
        )
