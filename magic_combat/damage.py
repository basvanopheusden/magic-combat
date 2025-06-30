"""Damage assignment helpers."""

from copy import deepcopy
from itertools import permutations
from typing import Iterable
from typing import List
from typing import Sequence

from .creature import CombatCreature
from .limits import IterationCounter


def optimal_damage_order(
    attacker: CombatCreature,
    blockers: Sequence[CombatCreature],
    counter: IterationCounter | None = None,
) -> List[CombatCreature]:
    """Return the blocker order that maximizes destruction."""
    from .simulator import CombatSimulator

    if len(blockers) <= 1:
        return list(blockers)

    index_map = {id(b): i for i, b in enumerate(blockers)}
    best_order: List[CombatCreature] = list(blockers)
    best_score: tuple[int, float, int, int, int, int, tuple[int, ...]] | None = None

    for perm in permutations(blockers):
        atk = deepcopy(attacker)
        blks = [deepcopy(b) for b in blockers]
        clone_map = {id(orig): clone for orig, clone in zip(blockers, blks)}
        atk.blocked_by = [clone_map[id(b)] for b in perm]
        for b in perm:
            clone_map[id(b)].blocking = atk
        damage_map = {atk: tuple(clone_map[id(b)] for b in perm)}
        sim = CombatSimulator([atk], blks, damage_order_map=damage_map)
        if counter is not None:
            counter.increment()
        result = sim.simulate()
        attacker_player = attacker.controller
        defender = blockers[0].controller
        key = tuple(index_map[id(b)] for b in perm)
        score = result.score(attacker_player, defender) + (key,)
        if best_score is None or score > best_score:
            best_score = score
            best_order = list(perm)

    return best_order


def damage_order_permutations(
    attacker: CombatCreature, blockers: Sequence[CombatCreature]
) -> Iterable[tuple[CombatCreature, ...]]:
    """Yield all possible damage orders for ``attacker``."""
    if len(blockers) <= 1:
        yield tuple(blockers)
    else:
        yield from permutations(blockers)
