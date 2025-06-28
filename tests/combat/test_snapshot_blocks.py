import json
import warnings
from pathlib import Path
from typing import List, Optional

from magic_combat import (
    SNAPSHOT_VERSION,
    build_value_map,
    generate_random_scenario,
    load_cards,
)
from magic_combat.blocking_ai import decide_optimal_blocks
from magic_combat.random_scenario import _score_optimal_result

DATA_PATH = Path(__file__).resolve().parents[1] / "data"
CARDS_PATH = DATA_PATH / "example_test_cards.json"
SNAP_PATH = DATA_PATH / "blocking_snapshots.json"


def _load_snapshots() -> List[dict]:
    with SNAP_PATH.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def test_optimal_blocks_snapshots() -> None:
    """CR 509.1a: The defending player chooses how creatures block."""
    cards = load_cards(str(CARDS_PATH))
    values = build_value_map(cards)
    snapshots = _load_snapshots()
    for snap in snapshots:
        seed = snap["seed"]
        (
            state,
            attackers,
            blockers,
            provoke_map,
            mentor_map,
            *_,
        ) = generate_random_scenario(cards, values, seed=seed)
        decide_optimal_blocks(
            attackers,
            blockers,
            game_state=state,
            provoke_map=provoke_map,
        )
        chosen: List[Optional[int]] = [
            attackers.index(b.blocking) if b.blocking is not None else None
            for b in blockers
        ]
        if snap.get("snapshot_version") != SNAPSHOT_VERSION:
            warnings.warn(
                "Outdated snapshot for seed %s (have %s, expected %s)"
                % (seed, snap.get("snapshot_version"), SNAPSHOT_VERSION)
            )
            continue
        assert chosen == snap["optimal_assignment"]
        value = list(
            _score_optimal_result(
                attackers,
                blockers,
                state,
                tuple(chosen),
                provoke_map,
                mentor_map,
            )
        )
        assert value == snap["combat_value"]
