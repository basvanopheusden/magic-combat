"""Heuristics for choosing optimal blocks."""

from __future__ import annotations

from copy import deepcopy
from itertools import product
from typing import List, Optional, Sequence, Tuple

from .creature import CombatCreature
from .damage import _blocker_value, OptimalDamageStrategy, score_combat_result
from .gamestate import GameState
from .simulator import CombatSimulator
from .limits import IterationCounter
from . import DEFAULT_STARTING_LIFE
from .utils import _can_block


def _creature_value(creature: CombatCreature) -> float:
    """Return a heuristic value for the creature."""
    return _blocker_value(creature)


def _reset_block_assignments(
    attackers: Sequence[CombatCreature],
    blockers: Sequence[CombatCreature],
) -> None:
    """Clear ``blocked_by`` and ``blocking`` fields on all combatants."""

    for atk in attackers:
        atk.blocked_by.clear()
    for blk in blockers:
        blk.blocking = None


def _evaluate_assignment(
    attackers: Sequence[CombatCreature],
    blockers: Sequence[CombatCreature],
    assignment: Sequence[Optional[int]],
    state: Optional[GameState],
    counter: "IterationCounter",
    provoke_map: Optional[dict[CombatCreature, CombatCreature]] = None,
) -> Tuple[int, float, int, int, int, Tuple[Optional[int], ...]]:
    """Simulate combat for a blocking assignment and score it."""
    atks = deepcopy(list(attackers))
    blks = deepcopy(list(blockers))
    for idx, choice in enumerate(assignment):
        if choice is not None:
            blk = blks[idx]
            atk = atks[choice]
            blk.blocking = atk
            atk.blocked_by.append(blk)

    prov_copies: dict[CombatCreature, CombatCreature] = {}
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
        # Illegal block configuration. Convert ``assignment`` to numbers to avoid
        # ``TypeError`` during tuple comparisons.
        ass_key = tuple(
            len(attackers) if choice is None else choice for choice in assignment
        )
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

    # Lower tuple values are preferred. Convert ``assignment`` to a tuple of
    # integers so Python can compare scores deterministically even when ``None``
    # is present.
    ass_key = tuple(len(attackers) if choice is None else choice for choice in assignment)
    score = score_combat_result(result, attacker_player, defender) + (ass_key,)
    return score


def decide_optimal_blocks(
    attackers: List[CombatCreature],
    blockers: List[CombatCreature],
    game_state: Optional[GameState] = None,
    *,
    provoke_map: Optional[dict[CombatCreature, CombatCreature]] = None,
    max_iterations: int = int(1e6),
) -> int:
    """Assign blockers to attackers using a heuristic evaluation.

    This function enumerates all legal block configurations and chooses the one
    with the best outcome according to the following priorities:

    1. Avoid losing the game.
    2. Maximize the difference in total creature value destroyed (attacker minus
       defender).
    3. Maximize the difference in number of creatures destroyed.
    4. Maximize the total mana value of creatures lost.
    5. Minimize life lost.
    6. Minimize poison counters gained.
    7. Use a deterministic ordering to break any remaining ties.

    The function returns a tuple ``(iterations, optimal_count)``. ``optimal_count``
    counts how many blocking assignments are tied on criteria 1–6,
    before applying the deterministic ordering in step 7.
    """

    if not blockers:
        return 0, 1

    counter = IterationCounter(max_iterations)

    provoked: dict[CombatCreature, CombatCreature] = {}
    if provoke_map:
        for atk, blk in provoke_map.items():
            if atk in attackers and blk in blockers:
                provoked[blk] = atk

    options = []
    for blk in blockers:
        forced = provoked.get(blk)
        if forced is not None and _can_block(forced, blk):
            options.append([attackers.index(forced)])
        else:
            options.append(list(range(len(attackers))) + [None])

    best: Optional[Tuple[Optional[int], ...]] = None
    best_score: Optional[Tuple] = None
    optimal_count = 0

    for assignment in product(*options):
        score = _evaluate_assignment(
            attackers,
            blockers,
            assignment,
            game_state,
            counter,
            provoke_map,
        )
        if best_score is None or score < best_score:
            # Update the chosen assignment whenever we find a strictly better
            # score. Only reset ``optimal_count`` if the numeric portion of the
            # score actually improved; otherwise we simply update the stored
            # best score so the deterministic tiebreaker picks this assignment.
            if best_score is None or score[:-1] < best_score[:-1]:
                optimal_count = 1
            best_score = score
            best = tuple(assignment)
        else:
            # ``optimal_count`` should include all assignments that are tied on
            # the numeric criteria. Ignore the deterministic tiebreaker when
            # counting optimal results.
            if best_score is not None and score[:-1] == best_score[:-1]:
                optimal_count += 1

    # Apply the chosen assignment to the real objects
    _reset_block_assignments(attackers, blockers)
    if best is not None:
        for blk_idx, choice in enumerate(best):
            if choice is not None:
                blk = blockers[blk_idx]
                atk = attackers[choice]
                blk.blocking = atk
                atk.blocked_by.append(blk)

    return counter.count, optimal_count




def decide_simple_blocks(
    attackers: List[CombatCreature],
    blockers: List[CombatCreature],
    game_state: Optional[GameState] = None,
    provoke_map: Optional[dict[CombatCreature, CombatCreature]] = None,
) -> None:
    """Assign blocks using a simple non-searching heuristic."""

    _reset_block_assignments(attackers, blockers)

    if not blockers:
        return

    defender = blockers[0].controller
    life = (
        game_state.players[defender].life
        if game_state
        else DEFAULT_STARTING_LIFE
    )
    poison = game_state.players[defender].poison if game_state else 0

    available = list(blockers)
    if provoke_map:
        for attacker, target in provoke_map.items():
            if attacker in attackers and target in available and _can_block(attacker, target):
                target.blocking = attacker
                attacker.blocked_by.append(target)
                available.remove(target)
    attackers_sorted = sorted(attackers, key=_creature_value, reverse=True)

    # First pass: take favorable 1:1 trades
    for atk in attackers_sorted:
        choices = [b for b in available if _can_block(atk, b)]
        choices.sort(key=_creature_value)
        for blk in choices:
            if (
                blk.effective_power() >= atk.effective_toughness()
                and atk.effective_power() >= blk.effective_toughness()
                and _creature_value(blk) <= _creature_value(atk)
            ):
                blk.blocking = atk
                atk.blocked_by.append(blk)
                available.remove(blk)
                break

    # Second pass: chump block if lethal damage would occur
    def remaining_threat() -> tuple[int, int]:
        dmg = 0
        psn = 0
        for a in attackers:
            if not a.blocked_by:
                dmg += a.effective_power()
                psn += (a.effective_power() if a.infect else 0) + a.toxic
        return dmg, psn

    for atk in sorted([a for a in attackers if not a.blocked_by], key=lambda a: a.effective_power(), reverse=True):
        if not available:
            break
        dmg, psn = remaining_threat()
        if life <= dmg or poison + psn >= 10:
            choices = [b for b in available if _can_block(atk, b)]
            if not choices:
                continue
            blk = min(choices, key=_creature_value)
            blk.blocking = atk
            atk.blocked_by.append(blk)
            available.remove(blk)

