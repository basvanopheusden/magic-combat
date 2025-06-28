#!/usr/bin/env python
"""Generate and resolve random combat scenarios."""

import argparse
import copy
import random
from typing import List

import numpy as np

from magic_combat import CombatSimulator
from magic_combat import PlayerState
from magic_combat import build_value_map
from magic_combat import compute_card_statistics
from magic_combat import ensure_cards
from magic_combat import generate_random_scenario
from magic_combat.abilities import BOOL_NAMES as _BOOL_ABILITIES
from magic_combat.abilities import INT_NAMES as _INT_ABILITIES
from magic_combat.damage import blocker_value

# Ability name mappings for pretty printing come from ``magic_combat.abilities``


def describe_abilities(creature) -> str:
    """Return a comma-separated string of the creature's keyword abilities."""
    parts: List[str] = []
    for attr, name in _BOOL_ABILITIES.items():
        if getattr(creature, attr, False):
            parts.append(name)
    for attr, name in _INT_ABILITIES.items():
        val = getattr(creature, attr, 0)
        if val:
            parts.append(f"{name} {val}")
    if creature.protection_colors:
        colors = ", ".join(c.name.capitalize() for c in creature.protection_colors)
        parts.append(f"Protection from {colors}")
    if creature.artifact:
        parts.append("Artifact")
    return ", ".join(parts) if parts else "none"


def summarize_creature(creature) -> str:
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
    extras = f" [{' ,'.join(extra)}]" if extra else ""
    return f"{creature}{extras} -- {describe_abilities(creature)}"


def print_player_state(label: str, ps: PlayerState, destroyed: List) -> None:
    """Display life total and surviving creatures for a player."""
    print(f"{label}: {ps.life} life, {ps.poison} poison")
    survivors = [c for c in ps.creatures if c not in destroyed]
    if survivors:
        for cr in survivors:
            print(f"  {summarize_creature(cr)}")
    else:
        print("  no creatures")


def main() -> None:
    parser = argparse.ArgumentParser(description="Simulate random combat scenarios")
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
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed controlling sampling",
    )
    parser.add_argument(
        "--max-iterations",
        type=int,
        default=int(1e6),
        help="Maximum combat simulations per scenario",
    )
    parser.add_argument(
        "--generated-cards",
        action="store_true",
        help="Use randomly generated creatures instead of real cards",
    )
    parser.add_argument(
        "--unique-optimal",
        action="store_true",
        help="Skip scenarios without a single optimal blocking set",
    )
    args = parser.parse_args()

    random.seed(args.seed)
    np.random.seed(args.seed)

    cards = ensure_cards(args.cards)
    values = build_value_map(cards)
    stats = compute_card_statistics(cards) if args.generated_cards else None

    for i in range(args.iterations):
        (
            start_state,
            attackers,
            blockers,
            provoke_map,
            mentor_map,
            *_,
        ) = generate_random_scenario(
            cards,
            values,
            stats,
            generated_cards=args.generated_cards,
            max_iterations=args.max_iterations,
            unique_optimal=args.unique_optimal,
        )
        state = copy.deepcopy(start_state)
        result = CombatSimulator(
            attackers,
            blockers,
            game_state=state,
            provoke_map=provoke_map,
            mentor_map=mentor_map,
        ).simulate()

        print(f"\n=== Scenario {i+1} ===")
        print("Starting life totals:")
        for p in ["A", "B"]:
            ps = start_state.players[p]
            print(f"  Player {p}: {ps.life} life, {ps.poison} poison")

        print("Attackers:")
        for atk in start_state.players["A"].creatures:
            print(f"  {summarize_creature(atk)}, {blocker_value(atk)}")
        print("Blockers:")
        for blk in start_state.players["B"].creatures:
            print(f"  {summarize_creature(blk)}, {blocker_value(blk)}")

        prov_map_display = (
            {a.name: b.name for a, b in provoke_map.items()} if provoke_map else None
        )
        mentor_map_display = (
            {m.name: t.name for m, t in mentor_map.items()} if mentor_map else None
        )

        print("Block assignments:")
        for atk in start_state.players["A"].creatures:
            blocks = ", ".join(b.name for b in atk.blocked_by) or "unblocked"
            print(f"  {atk.name} -> {blocks}")
        for blk in start_state.players["B"].creatures:
            target = blk.blocking.name if blk.blocking else "none"
            print(f"  {blk.name} -> {target}")
        if prov_map_display:
            print("Provoke targets:", prov_map_display)
        if mentor_map_display:
            print("Mentor targets:", mentor_map_display)

        print("Outcome:")
        print(result)

        print("Final state:")
        for p in ["A", "B"]:
            print_player_state(
                f"Player {p}", state.players[p], result.creatures_destroyed
            )
        if result.players_lost:
            print("Players lost:", ", ".join(result.players_lost))
        print()


if __name__ == "__main__":
    main()
