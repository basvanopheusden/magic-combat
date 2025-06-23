from __future__ import annotations

"""Utility helpers for evaluating blocking assignments."""

from copy import deepcopy
from typing import Sequence, Optional, Tuple, Dict

from .creature import CombatCreature
from .gamestate import GameState
from .limits import IterationCounter
from .damage import OptimalDamageStrategy, score_combat_result
from .simulator import CombatSimulator


def evaluate_block_assignment(
    attackers: Sequence[CombatCreature],
    blockers: Sequence[CombatCreature],
    assignment: Sequence[Optional[int]],
    state: Optional[GameState],
    counter: IterationCounter,
    provoke_map: Optional[Dict[CombatCreature, CombatCreature]] = None,
) -> Tuple[int, float, int, int, int, Tuple[Optional[int], ...]]:
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

    sim = CombatSimulator(
        atks,
        blks,
        game_state=deepcopy(state),
        strategy=OptimalDamageStrategy(counter),
        provoke_map=prov_copies or None,
    )
    try:
        counter.increment()
        result = sim.simulate()
    except ValueError:
        ass_key = tuple(len(attackers) if choice is None else choice for choice in assignment)
        return (
            1,
            float("inf"),
            -len(atks) - len(blks),
            -float("inf"),
            float("inf"),
            float("inf"),
            ass_key,
        )

    defender = blks[0].controller if blks else "defender"
    attacker_player = atks[0].controller if atks else "attacker"
    ass_key = tuple(len(attackers) if choice is None else choice for choice in assignment)
    score = score_combat_result(result, attacker_player, defender) + (ass_key,)
    return score
