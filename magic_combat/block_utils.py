"""Utility helpers for evaluating blocking assignments."""

from __future__ import annotations

from copy import deepcopy
from typing import Dict
from typing import Optional
from typing import Sequence
from typing import Tuple

from .creature import CombatCreature
from .damage import optimal_damage_order
from .exceptions import IllegalBlockError
from .gamestate import GameState
from .limits import IterationCounter
from .simulator import CombatSimulator


def evaluate_block_assignment(
    attackers: Sequence[CombatCreature],
    blockers: Sequence[CombatCreature],
    assignment: Sequence[Optional[int]],
    state: Optional[GameState],
    counter: IterationCounter,
    provoke_map: Optional[Dict[CombatCreature, CombatCreature]] = None,
    damage_order: Optional[dict[CombatCreature, tuple[CombatCreature, ...]]] = None,
) -> Tuple[int, float, int, int, int, int, Tuple[Optional[int], ...]]:
    """Simulate combat for ``assignment`` and return a scoring tuple."""
    atks = deepcopy(list(attackers))
    blks = deepcopy(list(blockers))
    for idx, choice in enumerate(assignment):
        if choice is not None:
            blk = blks[idx]
            atk = atks[choice]
            blk.blocking = atk
            atk.blocked_by.append(blk)

    prov_copies: Dict[CombatCreature, CombatCreature] = {}
    if provoke_map:
        for atk, blk in provoke_map.items():
            if atk in attackers and blk in blockers:
                prov_copies[atks[attackers.index(atk)]] = blks[blockers.index(blk)]

    order_map: dict[CombatCreature, tuple[CombatCreature, ...]] | None = None
    if damage_order:
        atk_map = {orig: copy for orig, copy in zip(attackers, atks)}
        blk_map = {orig: copy for orig, copy in zip(blockers, blks)}
        order_map = {
            atk_map[a]: tuple(blk_map[b] for b in seq)
            for a, seq in damage_order.items()
            if a in atk_map
        }
    else:
        order_map = {}
        for atk in atks:
            if len(atk.blocked_by) > 1:
                order = optimal_damage_order(atk, atk.blocked_by, counter)
                order_map[atk] = tuple(order)
        if not order_map:
            order_map = None

    sim = CombatSimulator(
        atks,
        blks,
        game_state=deepcopy(state),
        damage_order_map=order_map,
        provoke_map=prov_copies or None,
    )
    try:
        counter.increment()
        result = sim.simulate()
    except IllegalBlockError:
        ass_key = tuple(
            len(attackers) if choice is None else choice for choice in assignment
        )
        return (
            1,
            float("inf"),
            -len(atks) - len(blks),
            -(10**9),
            10**9,
            10**9,
            ass_key,
        )

    defender = blks[0].controller if blks else "defender"
    attacker_player = atks[0].controller if atks else "attacker"
    ass_key = tuple(
        len(attackers) if choice is None else choice for choice in assignment
    )
    score = result.score(attacker_player, defender) + (ass_key,)
    return score
