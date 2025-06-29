"""Helpers for encoding combat scenarios into JSON-friendly snapshots."""

from __future__ import annotations

from dataclasses import asdict
from typing import Any
from typing import Dict
from typing import List

from .creature import Color
from .creature import CombatCreature
from .gamestate import GameState
from .gamestate import PlayerState

_DEFENDER = "B"
_ATTACKER = "A"


def creature_to_dict(creature: CombatCreature) -> Dict[str, Any]:
    """Return a JSON-serializable representation of ``creature``."""
    data = asdict(creature)
    data["colors"] = [c.name for c in creature.colors]
    data["protection_colors"] = [c.name for c in creature.protection_colors]
    return data


def creature_from_dict(data: Dict[str, Any]) -> CombatCreature:
    """Reconstruct a :class:`CombatCreature` from ``data``."""
    conv = data.copy()
    conv["colors"] = {Color[c] for c in data.get("colors", [])}
    conv["protection_colors"] = {Color[c] for c in data.get("protection_colors", [])}
    return CombatCreature(**conv)


def state_to_dict(state: GameState) -> Dict[str, Any]:
    """Return life totals and poison counters for ``state``."""
    life = {p: ps.life for p, ps in state.players.items()}
    poison = {p: ps.poison for p, ps in state.players.items()}
    return {"life": life, "poison": poison}


def state_from_dict(
    data: Dict[str, Any],
    attackers: List[CombatCreature],
    blockers: List[CombatCreature],
) -> GameState:
    """Create a :class:`GameState` from ``data`` and creature lists."""
    return GameState(
        players={
            _ATTACKER: PlayerState(
                life=int(data["life"][_ATTACKER]),
                poison=int(data["poison"][_ATTACKER]),
                creatures=attackers,
            ),
            _DEFENDER: PlayerState(
                life=int(data["life"][_DEFENDER]),
                poison=int(data["poison"][_DEFENDER]),
                creatures=blockers,
            ),
        }
    )


def encode_map(
    mapping: Dict[CombatCreature, CombatCreature],
    atk: List[CombatCreature],
    blk: List[CombatCreature],
) -> Dict[str, int]:
    """Encode a creature mapping by using list indices."""
    return {str(atk.index(a)): blk.index(b) for a, b in mapping.items()}


def decode_provoke(
    data: Dict[str, int],
    atk: List[CombatCreature],
    blk: List[CombatCreature],
) -> Dict[CombatCreature, CombatCreature]:
    """Decode an encoded provoke mapping."""
    return {atk[int(k)]: blk[v] for k, v in data.items()}


def decode_mentor(
    data: Dict[str, int],
    atk: List[CombatCreature],
) -> Dict[CombatCreature, CombatCreature]:
    """Decode an encoded mentor mapping."""
    return {atk[int(k)]: atk[v] for k, v in data.items()}
