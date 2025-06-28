#!/usr/bin/env python
"""Generate snapshot data for optimal blocking scenarios."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from magic_combat import build_value_map, generate_random_scenario, load_cards

DEFAULT_CARDS = Path("tests/data/example_test_cards.json")
DEFAULT_OUTPUT = Path("tests/data/blocking_snapshots.json")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Create snapshot data for optimal blocking tests"
    )
    parser.add_argument(
        "--cards", type=Path, default=DEFAULT_CARDS, help="Path to card data JSON"
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help="Where to write snapshot JSON",
    )
    parser.add_argument(
        "-n", "--count", type=int, default=5, help="Number of scenarios to generate"
    )
    parser.add_argument(
        "--seed", type=int, default=0, help="Base random seed controlling sampling"
    )
    args = parser.parse_args()

    cards = load_cards(str(args.cards))
    values = build_value_map(cards)

    data = []
    for i in range(args.count):
        seed = args.seed + i
        (
            _state,
            _attackers,
            _blockers,
            _prov_map,
            _mentor_map,
            opt_map,
            simple_map,
            combat_value,
        ) = generate_random_scenario(cards, values, seed=seed)
        data.append(
            {
                "seed": seed,
                "optimal_assignment": list(opt_map),
                "simple_assignment": (
                    list(simple_map) if simple_map is not None else None
                ),
                "combat_value": list(combat_value),
            }
        )

    args.output.write_text(json.dumps(data, indent=2))


if __name__ == "__main__":  # pragma: no cover - manual tool
    main()
