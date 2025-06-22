"""Damage assignment ordering strategies."""

from typing import List, Tuple

from .limits import IterationCounter

from .creature import CombatCreature


# Keyword sets used for estimating combat value of a creature
_POSITIVE_KEYWORDS = [
    "flying",
    "reach",
    "menace",
    "fear",
    "shadow",
    "horsemanship",
    "skulk",
    "unblockable",
    "vigilance",
    "daunt",
    "first_strike",
    "double_strike",
    "deathtouch",
    "trample",
    "lifelink",
    "wither",
    "infect",
    "indestructible",
    "melee",
    "training",
    "battalion",
    "dethrone",
    "intimidate",
    "undying",
    "persist",
]

_STACKABLE_KEYWORDS = [
    "bushido",
    "flanking",
    "rampage",
    "exalted_count",
    "battle_cry_count",
    "frenzy",
    "afflict",
]


def _blocker_value(blocker: CombatCreature) -> float:
    """Heuristic combat value for tie-breaking."""

    positive = sum(1 for attr in _POSITIVE_KEYWORDS if getattr(blocker, attr, False))
    if blocker.double_strike:
        # Count double strike twice so it contributes 1 point instead of 0.5.
        positive += 1
    if blocker.lifelink:
        # Favor killing lifelinkers so opponents gain less life.
        positive += 1
    positive += sum(getattr(blocker, attr, 0) for attr in _STACKABLE_KEYWORDS)
    return blocker.power + blocker.toughness + positive / 2


def _select_kill_indices(power: int, costs: List[float], values: List[float]) -> List[int]:
    """Return indices of blockers that should be destroyed first."""

    dp: List[Tuple[int, float, List[int]]] = [(0, 0.0, []) for _ in range(power + 1)]
    for i, cost in enumerate(costs):
        if cost == float("inf") or cost > power:
            continue
        int_cost = int(cost)
        for w in range(power, int_cost - 1, -1):
            prev_cnt, prev_val, prev_set = dp[w - int_cost]
            cand_cnt = prev_cnt + 1
            cand_val = prev_val + values[i]
            curr_cnt, curr_val, _ = dp[w]
            if cand_cnt > curr_cnt or (cand_cnt == curr_cnt and cand_val > curr_val):
                dp[w] = (cand_cnt, cand_val, prev_set + [i])

    best = dp[0]
    for w in range(1, power + 1):
        cnt, val, _ = dp[w]
        if cnt > best[0] or (cnt == best[0] and val > best[1]):
            best = dp[w]

    return best[2]


class DamageAssignmentStrategy:
    """Base strategy for ordering blockers when assigning combat damage."""

    def order_blockers(
        self, attacker: CombatCreature, blockers: List[CombatCreature]
    ) -> List[CombatCreature]:
        """Return blockers in the order the attacker will assign damage."""
        return list(blockers)


class MostCreaturesKilledStrategy(DamageAssignmentStrategy):
    """Order blockers so the attacker tries to kill as many as possible."""

    def order_blockers(
        self, attacker: CombatCreature, blockers: List[CombatCreature]
    ) -> List[CombatCreature]:
        power = attacker.effective_power()

        def lethal_cost(blocker: CombatCreature) -> float:
            """Damage needed to remove ``blocker`` from combat."""
            if blocker.indestructible and not (attacker.infect or attacker.wither):
                return float("inf")
            if attacker.deathtouch and not blocker.indestructible:
                return 1
            return blocker.effective_toughness()

        costs = [lethal_cost(b) for b in blockers]
        values = [_blocker_value(b) for b in blockers]

        kill_indices = set(_select_kill_indices(power, costs, values))

        kill_first = [blockers[i] for i in kill_indices]
        kill_first.sort(key=_blocker_value, reverse=True)

        remaining = [b for idx, b in enumerate(blockers) if idx not in kill_indices]
        remaining.sort(key=_blocker_value, reverse=True)

        return kill_first + remaining

class OptimalDamageStrategy(DamageAssignmentStrategy):
    """Order blockers to maximize value destroyed similarly to optimal blocks."""

    def __init__(self, counter: "IterationCounter | None" = None) -> None:
        self.counter = counter

    def order_blockers(
        self, attacker: CombatCreature, blockers: List[CombatCreature]
    ) -> List[CombatCreature]:
        if len(blockers) <= 1:
            return list(blockers)

        from itertools import permutations
        from copy import deepcopy
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
                def __init__(self, order):
                    self._order = order
                def order_blockers(self, a, bs):
                    return self._order
            strat = _Fixed([clone_map[id(b)] for b in perm])
            sim = CombatSimulator([atk], blks, strategy=strat)
            if self.counter is not None:
                self.counter.increment()
            result = sim.simulate()

            attacker_player = attacker.controller
            defender = blockers[0].controller
            att_val = sum(
                _blocker_value(c)
                for c in result.creatures_destroyed
                if c.controller == attacker_player
            )
            def_val = sum(
                _blocker_value(c)
                for c in result.creatures_destroyed
                if c.controller == defender
            )
            val_diff = def_val - att_val

            att_cnt = sum(
                1 for c in result.creatures_destroyed if c.controller == attacker_player
            )
            def_cnt = sum(
                1 for c in result.creatures_destroyed if c.controller == defender
            )
            cnt_diff = def_cnt - att_cnt

            att_life = result.lifegain.get(attacker_player, 0)
            def_life = result.lifegain.get(defender, 0)
            life_diff = def_life - att_life

            mana_total = sum(c.mana_value for c in result.creatures_destroyed)
            key = tuple(index_map[id(b)] for b in perm)
            score = (-val_diff, -cnt_diff, life_diff, -mana_total, key)
            if best_score is None or score < best_score:
                best_score = score
                best_order = list(perm)

        return best_order

