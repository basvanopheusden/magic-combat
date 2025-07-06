#!/usr/bin/env python
"""Explore a random combat scenario using built-in AI players."""

from __future__ import annotations

import argparse
import copy
import random
from typing import Optional

import numpy as np

from magic_combat import CombatSimulator
from magic_combat import build_value_map
from magic_combat import compute_card_statistics
from magic_combat import decide_optimal_blocks
from magic_combat import decide_simple_blocks
from magic_combat import ensure_cards
from magic_combat import generate_random_scenario
from magic_combat.creature import CombatCreature
from magic_combat.exceptions import CardDataError


def _print_assignment(
    assignment: tuple[Optional[int], ...],
    attackers: list[CombatCreature],
    blockers: list[CombatCreature],
) -> None:
    """Show which blockers are assigned to which attackers."""
    for blk_idx, choice in enumerate(assignment):
        if choice is None:
            continue
        blk = blockers[blk_idx]
        atk = attackers[choice]
        print(f"  {blk.name} -> {atk.name}")


def investigate_scenario(
    cards: str, *, seed: int = 0, generated_cards: bool = False
) -> None:
    """Print a random scenario and the results of the simple and optimal AIs."""
    random.seed(seed)
    np.random.seed(seed)

    try:
        card_data = ensure_cards(cards)
    except CardDataError as exc:  # pragma: no cover - invalid path
        raise SystemExit(str(exc)) from exc

    values = build_value_map(card_data)
    stats = compute_card_statistics(card_data) if generated_cards else None

    state, provoke_map, mentor_map, *_ = next(
        generate_random_scenario(
            card_data,
            values,
            stats,
            generated_cards=generated_cards,
            seed=seed,
            unique_optimal=True,
        )
    )

    print("Initial game state:")
    print(state)

    attackers = list(state.players["A"].creatures)
    blockers = list(state.players["B"].creatures)

    simple_state = copy.deepcopy(state)
    _, simple_assignment = decide_simple_blocks(
        simple_state,
        provoke_map=provoke_map,
        mentor_map=mentor_map,
    )
    simple_result = CombatSimulator(
        attackers,
        blockers,
        game_state=simple_state,
        provoke_map=provoke_map,
        mentor_map=mentor_map,
    ).simulate()

    optimal_state = copy.deepcopy(state)
    top, _ = decide_optimal_blocks(
        optimal_state,
        provoke_map=provoke_map,
        mentor_map=mentor_map,
    )
    _, optimal_assignment = top[0]
    optimal_result = CombatSimulator(
        attackers,
        blockers,
        game_state=optimal_state,
        provoke_map=provoke_map,
        mentor_map=mentor_map,
    ).simulate()

    print("\nSimple AI blocks:")
    _print_assignment(simple_assignment, attackers, blockers)
    print(simple_result)
    print(simple_result.score("A", "B"))

    print("\nOptimal AI blocks:")
    _print_assignment(optimal_assignment, attackers, blockers)
    print(optimal_result)
    print(optimal_result.score("A", "B"))


def main() -> None:
    parser = argparse.ArgumentParser(description="Investigate a random scenario")
    parser.add_argument(
        "--cards",
        default="tests/data/example_test_cards.json",
        help="Path to card data JSON",
    )
    parser.add_argument("--seed", type=int, default=0, help="Random seed")
    parser.add_argument(
        "--generated-cards",
        action="store_true",
        help="Use randomly generated creatures",
    )
    args = parser.parse_args()

    investigate_scenario(
        args.cards, seed=args.seed, generated_cards=args.generated_cards
    )


if __name__ == "__main__":  # pragma: no cover - manual invocation
    main()
