from __future__ import annotations

import json
from pathlib import Path

from magic_combat import build_value_map, generate_random_scenario, load_cards

DATA_PATH = Path(__file__).resolve().parents[1] / "data"
CARD_FILE = DATA_PATH / "example_test_cards.json"
SNAPSHOT_FILE = DATA_PATH / "blocking_snapshots.json"


def test_blocking_snapshots() -> None:
    """Ensure optimal blocks remain stable for known random seeds."""
    snapshots = json.loads(SNAPSHOT_FILE.read_text())
    cards = load_cards(str(CARD_FILE))
    values = build_value_map(cards)

    for snap in snapshots:
        seed = snap["seed"]
        (
            _state,
            _attackers,
            _blockers,
            _prov,
            _mentor,
            opt_map,
            simple_map,
            combat_value,
        ) = generate_random_scenario(cards, values, seed=seed)
        assert list(opt_map) == snap["optimal_assignment"]
        expected_simple = snap["simple_assignment"]
        assert (list(simple_map) if simple_map is not None else None) == expected_simple
        assert list(combat_value) == snap["combat_value"]
