#!/usr/bin/env python
"""Generate random combat scenarios and simulate outcomes."""

import argparse
import os
import random
import sys
from typing import Dict, List

# Allow running without installing the package
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from magic_combat import (
    cards_to_creatures,
    load_cards,
    save_cards,
    fetch_french_vanilla_cards,
    CombatSimulator,
    decide_optimal_blocks,
    GameState,
    PlayerState,
)
from magic_combat.damage import _blocker_value

DATA_FILE = "data/cards.json"


def ensure_card_data() -> List[Dict]:
    """Load card data from disk or download it if missing."""
    if os.path.exists(DATA_FILE):
        return load_cards(DATA_FILE)
    cards = fetch_french_vanilla_cards()
    os.makedirs(os.path.dirname(DATA_FILE) or ".", exist_ok=True)
    save_cards(cards, DATA_FILE)
    return cards


def geometric_sample(mean: float) -> int:
    """Sample from a geometric distribution with given mean."""
    p = 1.0 / mean
    count = 1
    while random.random() > p:
        count += 1
    return count


def choose_balanced(
    cards: List[Dict],
    values: Dict[str, float],
    n_atk: int,
    n_blk: int,
    tolerance: float = 1.0,
    attempts: int = 1000,
) -> tuple[List[Dict], List[Dict]]:
    """Sample two groups of cards with roughly equal total value."""
    if not cards:
        raise ValueError("No cards available")
    last = ([], [])
    for _ in range(attempts):
        atks = random.sample(cards, n_atk)
        blks = random.sample(cards, n_blk)
        last = (atks, blks)
        diff = abs(
            sum(values[c["name"]] for c in atks)
            - sum(values[c["name"]] for c in blks)
        )
        if diff <= tolerance:
            break
    return last


def main() -> None:
    parser = argparse.ArgumentParser(description="Simulate random combat")
    parser.add_argument(
        "iterations",
        nargs="?",
        type=int,
        default=10,
        help="Number of scenarios to run",
    )
    args = parser.parse_args()

    cards = ensure_card_data()
    # Compute heuristic value for each card name using controller "A"
    dummy_creatures = cards_to_creatures(cards, "A")
    value_by_name = {c.name: _blocker_value(c) for c in dummy_creatures}

    for i in range(args.iterations):
        n_atk = geometric_sample(2.5)
        n_blk = geometric_sample(2.5)
        atk_cards, blk_cards = choose_balanced(cards, value_by_name, n_atk, n_blk)

        attackers = cards_to_creatures(atk_cards, "A")
        blockers = cards_to_creatures(blk_cards, "B")
        all_creatures = attackers + blockers

        poison_relevant = any(c.infect or c.toxic for c in all_creatures)

        state = GameState(
            players={
                "A": PlayerState(
                    life=random.randint(1, 20),
                    creatures=attackers,
                    poison=random.randint(0, 9) if poison_relevant else 0,
                ),
                "B": PlayerState(
                    life=random.randint(1, 20),
                    creatures=blockers,
                    poison=random.randint(0, 9) if poison_relevant else 0,
                ),
            }
        )

        provoke_map = {}
        if blockers:
            for atk in attackers:
                if atk.provoke:
                    provoke_map[atk] = random.choice(blockers)

        decide_optimal_blocks(attackers, blockers, game_state=state)
        sim = CombatSimulator(
            attackers,
            blockers,
            game_state=state,
            provoke_map=provoke_map,
        )
        result = sim.simulate()

        print(f"Scenario {i + 1}:")
        print("  Attackers:")
        for c in attackers:
            blocks = ", ".join(b.name for b in c.blocked_by) or "None"
            print(f"    {c} -- blocked by: {blocks}")
        print("  Blockers:")
        for c in blockers:
            target = c.blocking.name if c.blocking else "None"
            print(f"    {c} -- blocking: {target}")
        print("  Result:", result)
        print()


if __name__ == "__main__":
    main()
