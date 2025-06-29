"""Damage assignment ordering strategies."""

from typing import TYPE_CHECKING
from typing import List
from typing import Tuple

from .creature import CombatCreature
from .limits import IterationCounter

if TYPE_CHECKING:  # pragma: no cover - used for type checking only
    from .simulator import CombatResult

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


def blocker_value(blocker: CombatCreature) -> float:
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


def score_combat_result(
    result: "CombatResult",
    attacker_player: str,
    defender: str,
) -> Tuple[int, float, int, int, int, int]:
    """Return a scoring tuple evaluating combat from the defender's perspective."""

    lost = 1 if defender in getattr(result, "players_lost", []) else 0

    att_val = sum(
        blocker_value(c)
        for c in result.creatures_destroyed
        if c.controller == attacker_player
    )
    def_val = sum(
        blocker_value(c) for c in result.creatures_destroyed if c.controller == defender
    )
    val_diff = def_val - att_val

    att_cnt = sum(
        1 for c in result.creatures_destroyed if c.controller == attacker_player
    )
    def_cnt = sum(1 for c in result.creatures_destroyed if c.controller == defender)
    cnt_diff = def_cnt - att_cnt

    mana_total = sum(c.mana_value for c in result.creatures_destroyed)
    life_lost = result.damage_to_players.get(defender, 0)
    poison = result.poison_counters.get(defender, 0)

    return (lost, val_diff, cnt_diff, -mana_total, life_lost, poison)


class DamageAssignmentStrategy:
    """Base strategy for ordering blockers when assigning combat damage."""

    def order_blockers(
        self, attacker: CombatCreature, blockers: List[CombatCreature]
    ) -> List[CombatCreature]:
        """Return blockers in the order the attacker will assign damage."""
        return list(blockers)


class OptimalDamageStrategy(DamageAssignmentStrategy):
    """Order blockers to maximize value destroyed similarly to optimal blocks."""

    def __init__(self, counter: "IterationCounter | None" = None) -> None:
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
            score = score_combat_result(result, attacker_player, defender) + (key,)
            if best_score is None or score > best_score:
                best_score = score
                best_order = list(perm)

        return best_order
