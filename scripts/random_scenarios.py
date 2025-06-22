#!/usr/bin/env python
"""Generate random combat scenarios using Scryfall data."""

from __future__ import annotations

import argparse
import os
import random
import sys
from typing import Dict, Iterable, List, Tuple

# Allow running without installing the package
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from magic_combat import (
    load_cards,
    save_cards,
    fetch_french_vanilla_cards,
    cards_to_creatures,
    card_to_creature,
    GameState,
    PlayerState,
    CombatSimulator,
    decide_optimal_blocks,
)
from magic_combat.blocking_ai import _creature_value


def ensure_cards(path: str) -> List[dict]:
    """Load card data from ``path`` or download it if missing."""
    if not os.path.exists(path):
        print(f"Downloading card data to {path}...")
        cards = fetch_french_vanilla_cards()
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        save_cards(cards, path)
    return load_cards(path)


def geometric(mean: float) -> int:
    """Draw from a geometric distribution with given mean."""
    p = 1.0 / mean
    n = 1
    while random.random() >= p:
        n += 1
    return n


def build_value_by_creature(cards: Iterable[dict]) -> Dict[str, float]:
    """Return mapping of card names to heuristic combat values."""
    values: Dict[str, float] = {}
    for card in cards:
        creature = card_to_creature(card, "A")
        values[creature.name] = _creature_value(creature)
    return values


def sample_balanced(
    cards: List[dict],
    values: Dict[str, float],
    n_atk: int,
    n_blk: int,
    tolerance: float = 0.15,
    attempts: int = 1000,
) -> Tuple[List[dict], List[dict]]:
    """Sample attackers and blockers with roughly equal total value."""
    last_a: List[dict] = []
    last_b: List[dict] = []
    for _ in range(attempts):
        atk = random.sample(cards, n_atk)
        blk = random.sample(cards, n_blk)
        val_a = sum(values.get(card_to_creature(c, "A").name, 0.0) for c in atk)
        val_b = sum(values.get(card_to_creature(c, "A").name, 0.0) for c in blk)
        last_a, last_b = atk, blk
        if abs(val_a - val_b) <= tolerance * ((val_a + val_b) / 2.0):
            break
    return last_a, last_b


def describe(creature) -> str:
    """Return a simple description for printing."""
    return f"{creature.name} ({creature.power}/{creature.toughness})"


def main() -> None:
    parser = argparse.ArgumentParser(description="Run random combat scenarios")
    parser.add_argument(
        "iterations",
        nargs="?",
        type=int,
        default=10,
        help="Number of scenarios to generate",
    )
    parser.add_argument(
        "--cards",
        default="data/cards.json",
        help="Path to Scryfall card data",
    )
    args = parser.parse_args()

    cards = ensure_cards(args.cards)
    value_by_creature = build_value_by_creature(cards)

    for i in range(args.iterations):
        n_atk = geometric(2.5)
        n_blk = geometric(2.5)
        atk_cards, blk_cards = sample_balanced(cards, value_by_creature, n_atk, n_blk)

        attackers = cards_to_creatures(atk_cards, "A")
        blockers = cards_to_creatures(blk_cards, "B")

        life_a = random.randint(1, 20)
        life_b = random.randint(1, 20)
        poison_relevant = any(c.infect or c.toxic for c in attackers + blockers)
        if poison_relevant:
            poison_a = random.randint(0, 9)
            poison_b = random.randint(0, 9)
        else:
            poison_a = poison_b = 0

        game_state = GameState(
            players={
                "A": PlayerState(life=life_a, creatures=list(attackers), poison=poison_a),
                "B": PlayerState(life=life_b, creatures=list(blockers), poison=poison_b),
            }
        )

        provoke_map = {}
        provokers = [c for c in attackers if c.provoke]
        if provokers and blockers:
            for p in provokers:
                provoke_map[p] = random.choice(blockers)

        decide_optimal_blocks(attackers, blockers, game_state=game_state)

        for atk, target in provoke_map.items():
            if target.blocking is not atk:
                if target.blocking is not None:
                    target.blocking.blocked_by.remove(target)
                target.blocking = atk
                if target not in atk.blocked_by:
                    atk.blocked_by.append(target)

        sim = CombatSimulator(attackers, blockers, game_state=game_state, provoke_map=provoke_map)
        result = sim.simulate()

        print(f"--- Scenario {i+1} ---")
        print(f"A life: {life_a}  poison: {poison_a}")
        print(f"B life: {life_b}  poison: {poison_b}")
        print("Attackers:")
        for c in attackers:
            print("  ", describe(c))
        print("Blockers:")
        for c in blockers:
            blk = f" -> {c.blocking.name}" if c.blocking else ""
            print("  ", describe(c) + blk)
        print("Result:")
        print("  Damage:", result.damage_to_players)
        print("  Destroyed:", [c.name for c in result.creatures_destroyed])
        print("  Poison:", result.poison_counters)
        print("  Players lost:", result.players_lost)
        print()


if __name__ == "__main__":
    main()
