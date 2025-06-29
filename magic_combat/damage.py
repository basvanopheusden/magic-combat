"""Damage assignment ordering strategies."""

from typing import List

from .creature import CombatCreature
from .limits import IterationCounter


class DamageAssignmentStrategy:
    """Base strategy for ordering blockers when assigning combat damage."""

    def order_blockers(
        self, attacker: CombatCreature, blockers: List[CombatCreature]
    ) -> List[CombatCreature]:
        """Return blockers in the order the attacker will assign damage."""
        return list(blockers)


class OptimalDamageStrategy(DamageAssignmentStrategy):
    """Order blockers to maximize value destroyed similarly to optimal blocks."""

    def __init__(self, counter: IterationCounter | None = None) -> None:
        self.counter = counter

    def order_blockers(
        self, attacker: CombatCreature, blockers: List[CombatCreature]
    ) -> List[CombatCreature]:
        if len(blockers) <= 1:
            return list(blockers)

        from copy import deepcopy
        from itertools import permutations

        from .simulator import CombatSimulator

        index_map = {id(b): i for i, b in enumerate(blockers)}
        best_order = list(blockers)
        best_score = None

        for perm in permutations(blockers):
            atk = deepcopy(attacker)
            blks = [deepcopy(b) for b in blockers]
            clone_map = {id(orig): clone for orig, clone in zip(blockers, blks)}
            atk.blocked_by = [clone_map[id(b)] for b in perm]
            for b in perm:
                clone_map[id(b)].blocking = atk

            class _Fixed(DamageAssignmentStrategy):
                def __init__(self, order: List[CombatCreature]) -> None:
                    self._order = order

                def order_blockers(
                    self, attacker: CombatCreature, blockers: List[CombatCreature]
                ) -> List[CombatCreature]:
                    return self._order

            strat = _Fixed([clone_map[id(b)] for b in perm])
            sim = CombatSimulator([atk], blks, strategy=strat)
            if self.counter is not None:
                self.counter.increment()
            result = sim.simulate()

            attacker_player = attacker.controller
            defender = blockers[0].controller
            key = tuple(index_map[id(b)] for b in perm)
            score = result.score(attacker_player, defender) + (key,)
            if best_score is None or score > best_score:
                best_score = score
                best_order = list(perm)

        return best_order
