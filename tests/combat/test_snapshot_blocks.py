import json
from pathlib import Path
from typing import List
from typing import Optional

from magic_combat import build_value_map
from magic_combat import generate_random_scenario
from magic_combat import load_cards
from magic_combat.blocking_ai import decide_optimal_blocks
from magic_combat.constants import SNAPSHOT_VERSION
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
        if snap.get("version") != SNAPSHOT_VERSION:
            print(
                "Warning: snapshot version",
                snap.get("version"),
                "!=",
                SNAPSHOT_VERSION,
            )
            continue
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
