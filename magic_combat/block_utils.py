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
from .simulator import CombatResult
from .simulator import CombatSimulator


def evaluate_block_assignment(
    assignment: Sequence[Optional[int]],
    state: GameState,
    counter: IterationCounter,
    provoke_map: Optional[Dict[CombatCreature, CombatCreature]] = None,
    damage_order: Optional[dict[CombatCreature, tuple[CombatCreature, ...]]] = None,
) -> Tuple[Optional[CombatResult], Optional[GameState]]:
    """Simulate combat for ``assignment`` and return the result and new state."""
    orig_atks = list(state.players["A"].creatures)
    orig_blks = list(state.players["B"].creatures)
    state_copy = deepcopy(state)
    atks = list(state_copy.players["A"].creatures)
    blks = list(state_copy.players["B"].creatures)
    atk_map = {orig: copy for orig, copy in zip(orig_atks, atks)}
    blk_map = {orig: copy for orig, copy in zip(orig_blks, blks)}
    for idx, choice in enumerate(assignment):
        if choice is not None:
            blk = blks[idx]
            atk = atks[choice]
            blk.blocking = atk
            atk.blocked_by.append(blk)

    prov_copies: Dict[CombatCreature, CombatCreature] = {}
    if provoke_map:
        for atk, blk in provoke_map.items():
            if atk in atk_map and blk in blk_map:
                prov_copies[atk_map[atk]] = blk_map[blk]

    order_map: dict[CombatCreature, tuple[CombatCreature, ...]] | None = None
    if damage_order:
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
        game_state=state_copy,
        damage_order_map=order_map,
        provoke_map=prov_copies or None,
    )
    try:
        counter.increment()
        result = sim.simulate()
    except IllegalBlockError:
        return None, None

    return result, sim.game_state
