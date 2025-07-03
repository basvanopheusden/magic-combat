import json
from pathlib import Path
from typing import List
from typing import Optional

from magic_combat.blocking_ai import decide_optimal_blocks
from magic_combat.blocking_ai import decide_simple_blocks
from magic_combat.constants import SNAPSHOT_VERSION
from magic_combat.snapshot import creature_from_dict
from magic_combat.snapshot import decode_mentor
from magic_combat.snapshot import decode_provoke
from magic_combat.snapshot import state_from_dict

DATA_PATH = Path(__file__).resolve().parents[1] / "data"
SNAP_PATH = DATA_PATH / "blocking_snapshots.json"


def _load_snapshots() -> List[dict]:
    with SNAP_PATH.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def test_optimal_blocks_snapshots() -> None:
    """CR 509.1a: The defending player chooses how creatures block."""
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
        attackers = [creature_from_dict(d) for d in snap["attackers"]]
        blockers = [creature_from_dict(d) for d in snap["blockers"]]
        state = state_from_dict(snap["state"], attackers, blockers)
        provoke_map = decode_provoke(snap["provoke_map"], attackers, blockers)
        mentor_map = decode_mentor(snap["mentor_map"], attackers)
        decide_optimal_blocks(
            game_state=state,
            provoke_map=provoke_map,
            mentor_map=mentor_map,
        )
        chosen: List[Optional[int]] = [
            attackers.index(b.blocking) if b.blocking is not None else None
            for b in blockers
        ]
        assert chosen == snap["optimal_assignment"]


def test_simple_blocks_snapshots() -> None:
    """CR 509.1a: The defending player chooses how creatures block."""
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
        if snap.get("simple_assignment") is None:
            continue
        attackers = [creature_from_dict(d) for d in snap["attackers"]]
        blockers = [creature_from_dict(d) for d in snap["blockers"]]
        state = state_from_dict(snap["state"], attackers, blockers)
        provoke_map = decode_provoke(snap["provoke_map"], attackers, blockers)
        mentor_map = decode_mentor(snap["mentor_map"], attackers)
        decide_simple_blocks(
            game_state=state,
            provoke_map=provoke_map,
            mentor_map=mentor_map,
        )
        chosen: List[Optional[int]] = [
            attackers.index(b.blocking) if b.blocking is not None else None
            for b in blockers
        ]
        assert chosen == snap["simple_assignment"]
