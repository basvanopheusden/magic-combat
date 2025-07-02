#!/usr/bin/env python
"""Generate snapshot scenarios for optimal blocking tests."""

import argparse
import json
import random
from pathlib import Path
from typing import List

import numpy as np

from magic_combat import build_value_map
from magic_combat import creature_to_dict
from magic_combat import encode_map
from magic_combat import generate_random_scenario
from magic_combat import load_cards
from magic_combat import state_to_dict
from magic_combat.constants import SNAPSHOT_VERSION


def _dump_snapshot(data: List[dict[str, object]], path: Path) -> None:
    """Write snapshot data to ``path`` in JSON format."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2)


def main() -> None:
    parser = argparse.ArgumentParser(description="Create optimal block snapshots")
    parser.add_argument("-n", "--num", type=int, default=5, help="Number of scenarios")
    parser.add_argument(
        "--cards",
        default="tests/data/example_test_cards.json",
        help="Path to card data JSON",
    )
    parser.add_argument(
        "--seed", type=int, default=0, help="Base random seed controlling sampling"
    )
    parser.add_argument(
        "--output",
        default="tests/data/blocking_snapshots.json",
        help="Output JSON file",
    )
    args = parser.parse_args()

    random.seed(args.seed)
    np.random.seed(args.seed)

    cards = load_cards(args.cards)
    values = build_value_map(cards)

    snapshots: List[dict[str, object]] = []
    for i in range(args.num):
        seed = args.seed + i
        (
            state,
            provoke_map,
            mentor_map,
            opt_map,
            simple_map,
            combat_value,
        ) = generate_random_scenario(cards, values, seed=seed)
        attackers = list(state.players["A"].creatures)
        blockers = list(state.players["B"].creatures)

        snapshot: dict[str, object] = {
            "version": SNAPSHOT_VERSION,
            "seed": seed,
            "attackers": [creature_to_dict(c) for c in attackers],
            "blockers": [creature_to_dict(c) for c in blockers],
            "state": state_to_dict(state),
            "provoke_map": encode_map(provoke_map, attackers, blockers),
            "mentor_map": encode_map(mentor_map, attackers, attackers),
            "optimal_assignment": list(opt_map),
            "simple_assignment": list(simple_map) if simple_map is not None else None,
            "combat_value": list(combat_value),
        }
        snapshots.append(snapshot)
        print(snapshot)

    _dump_snapshot(snapshots, Path(args.output))


if __name__ == "__main__":
    main()
