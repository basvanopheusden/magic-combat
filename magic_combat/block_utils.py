"""Utility helpers for evaluating blocking assignments."""

from __future__ import annotations

from copy import deepcopy
from typing import Dict
from typing import Optional
from typing import Sequence

from .creature import CombatCreature
from .damage import OptimalDamageStrategy
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
) -> tuple[
    tuple[int, float, int, int, int, int, tuple[Optional[int], ...]],
    Optional[GameState],
]:
    """Return score and final state for ``assignment``."""
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
                atk_copy = atks[attackers.index(atk)]
                blk_copy = blks[blockers.index(blk)]
                prov_copies[atk_copy] = blk_copy

    state_copy = deepcopy(state)
    if state_copy is not None:
        for orig, copy_creature in zip(attackers, atks):
            ps = state_copy.players.get(orig.controller)
            if ps and orig in ps.creatures:
                ps.creatures[ps.creatures.index(orig)] = copy_creature
        for orig, copy_creature in zip(blockers, blks):
            ps = state_copy.players.get(orig.controller)
            if ps and orig in ps.creatures:
                ps.creatures[ps.creatures.index(orig)] = copy_creature
    sim = CombatSimulator(
        atks,
        blks,
        game_state=state_copy,
        strategy=OptimalDamageStrategy(counter),
        provoke_map=prov_copies or None,
    )
    try:
        counter.increment()
        result = sim.simulate()
    except IllegalBlockError:
        ass_key = tuple(
            len(attackers) if choice is None else choice for choice in assignment
        )
        score = (
            1,
            float("inf"),
            -len(atks) - len(blks),
            -(10**9),
            10**9,
            10**9,
            ass_key,
        )
        return score, state_copy

    if state_copy is not None:
        for dead in result.creatures_destroyed:
            ps = state_copy.players.get(dead.controller)
            if ps and dead in ps.creatures:
                ps.creatures.remove(dead)

    defender = blks[0].controller if blks else "defender"
    attacker_player = atks[0].controller if atks else "attacker"
    ass_key = tuple(
        len(attackers) if choice is None else choice for choice in assignment
    )
    score = result.score(attacker_player, defender) + (ass_key,)
    return score, state_copy
