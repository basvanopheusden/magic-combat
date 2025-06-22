#!/usr/bin/env python
"""Generate and resolve random combat scenarios."""

import argparse
import os
import random
from typing import Dict, List

import numpy as np

from magic_combat import (
    cards_to_creatures,
    card_to_creature,
    load_cards,
    save_cards,
    fetch_french_vanilla_cards,
    decide_optimal_blocks,
    CombatSimulator,
    GameState,
    PlayerState,
)
from magic_combat.damage import _blocker_value


def ensure_cards(path: str) -> List[dict]:
    """Load card data, downloading it if necessary."""
    if not os.path.exists(path):
        print(f"Downloading card data to {path}...")
        try:
            cards = fetch_french_vanilla_cards()
        except Exception as exc:
            raise SystemExit(f"Failed to download card data: {exc}")
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        save_cards(cards, path)
    return load_cards(path)


def build_value_map(cards: List[dict]) -> Dict[int, float]:
    """Return a mapping of card index to combat value.

    Cards with invalid stats (e.g. ``"*"`` toughness) are skipped.
    """
    values: Dict[int, float] = {}
    for idx, card in enumerate(cards):
        try:
            creature = card_to_creature(card, "A")
        except ValueError as exc:  # toughness/power may be invalid
            print(f"Skipping {card.get('name', '?')}: {exc}")
            continue
        values[idx] = _blocker_value(creature)
    if not values:
        raise ValueError("No usable creatures found in card data")
    return values


def sample_balanced(
    cards: List[dict], values: Dict[int, float], n_att: int, n_blk: int
) -> tuple[List[int], List[int]]:
    """Select creatures for each side with roughly equal total value."""
    idxs = list(values.keys())
    if n_att + n_blk > len(idxs):
        raise ValueError("Not enough cards to sample from")
    attempts = 0
    while attempts < 1000:
        attempts += 1
        att_idx = random.sample(idxs, n_att)
        remaining = [i for i in idxs if i not in att_idx]
        blk_idx = random.sample(remaining, n_blk)
        att_val = sum(values[i] for i in att_idx)
        blk_val = sum(values[i] for i in blk_idx)
        avg = (att_val + blk_val) / 2 or 1
        if abs(att_val - blk_val) / avg <= 0.25:
            return att_idx, blk_idx
    return att_idx, blk_idx


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Simulate random combat scenarios"
    )
    parser.add_argument(
        "-n",
        "--iterations",
        type=int,
        default=10,
        help="Number of scenarios to generate",
    )
    parser.add_argument(
        "--cards",
        default="data/cards.json",
        help="Path to card data JSON",
    )
    args = parser.parse_args()

    cards = ensure_cards(args.cards)
    values = build_value_map(cards)
    valid_len = len(values)

    for i in range(args.iterations):
        n_atk = int(np.random.geometric(1 / 2.5))
        n_blk = int(np.random.geometric(1 / 2.5))
        n_atk = max(1, min(n_atk, valid_len // 2))
        n_blk = max(1, min(n_blk, valid_len // 2))

        atk_idx, blk_idx = sample_balanced(cards, values, n_atk, n_blk)
        attackers = cards_to_creatures((cards[i] for i in atk_idx), "A")
        blockers = cards_to_creatures((cards[i] for i in blk_idx), "B")

        poison_relevant = any(c.infect or c.toxic for c in attackers + blockers)

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

        provoke_map = {
            atk: random.choice(blockers)
            for atk in attackers
            if atk.provoke
        }

        decide_optimal_blocks(attackers, blockers, game_state=state)
        sim = CombatSimulator(
            attackers,
            blockers,
            game_state=state,
            provoke_map=provoke_map,
        )
        result = sim.simulate()

        print(f"\n=== Scenario {i+1} ===")
        print("Attackers:")
        for atk in attackers:
            blocks = ", ".join(b.name for b in atk.blocked_by) or "unblocked"
            print(f"  {atk} -> {blocks}")
        print("Blockers:")
        for blk in blockers:
            target = blk.blocking.name if blk.blocking else "none"
            print(f"  {blk} -> {target}")
        if provoke_map:
            prov = {a.name: b.name for a, b in provoke_map.items()}
            print("Provoke targets:", prov)
        print("Outcome:", result)


if __name__ == "__main__":
    main()
