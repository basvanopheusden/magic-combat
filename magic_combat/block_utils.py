from __future__ import annotations

from copy import deepcopy
from typing import Dict
from typing import Optional
from typing import Sequence
from typing import Tuple

from .creature import CombatCreature
from .damage import OptimalDamageStrategy
from .exceptions import IllegalBlockError
from .gamestate import GameState
from .limits import IterationCounter
from .simulator import CombatSimulator

"""Utility helpers for evaluating blocking assignments."""


def evaluate_block_assignment(
    attackers: Sequence[CombatCreature],
    blockers: Sequence[CombatCreature],
    assignment: Sequence[Optional[int]],
    state: Optional[GameState],
    counter: IterationCounter,
    provoke_map: Optional[Dict[CombatCreature, CombatCreature]] = None,
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
