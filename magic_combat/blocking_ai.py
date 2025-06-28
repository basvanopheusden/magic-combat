"""Heuristics for choosing optimal blocks."""

from __future__ import annotations

from itertools import product
from typing import List
from typing import Optional
from typing import Sequence
from typing import Tuple

from magic_combat.constants import DEFAULT_STARTING_LIFE
from magic_combat.constants import POISON_LOSS_THRESHOLD

from .block_utils import evaluate_block_assignment
from .creature import CombatCreature
from .damage import _blocker_value
from .damage import score_combat_result
from .gamestate import GameState
from .limits import IterationCounter
from .simulator import CombatSimulator
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


def _apply_provoke_assignments(
    attackers: Sequence[CombatCreature],
    available: List[CombatCreature],
    provoke_map: Optional[dict[CombatCreature, CombatCreature]],
) -> None:
    """Assign blocks dictated by provoke."""

    if not provoke_map:
        return

    for attacker, target in provoke_map.items():
        if (
            attacker in attackers
            and target in available
            and _can_block(attacker, target)
        ):
            target.blocking = attacker
            attacker.blocked_by.append(target)
            available.remove(target)


def _pair_value_diff(attacker: CombatCreature, blocker: CombatCreature) -> float:
    """Return attacker value minus blocker value for the combat pair."""

    from copy import deepcopy

    atk = deepcopy(attacker)
    blk = deepcopy(blocker)
    blk.blocking = atk
    atk.blocked_by.append(blk)
    sim = CombatSimulator([atk], [blk])
    result = sim.simulate()
    score = score_combat_result(result, attacker.controller, blocker.controller)
    # ``score[1]`` is defender value minus attacker value; invert for our metric
    return -score[1]


def _assign_favorable_trades(
    attackers_sorted: Sequence[CombatCreature],
    available: List[CombatCreature],
) -> None:
    """Block with favorable 1:1 trades when possible."""

    chosen: set[CombatCreature] = set()
    for blk in sorted(list(available), key=_creature_value, reverse=True):
        best_atk: Optional[CombatCreature] = None
        best_diff = float("-inf")
        for atk in attackers_sorted:
            if atk in chosen or not _can_block(atk, blk):
                continue
            diff = _pair_value_diff(atk, blk)
            if diff > best_diff:
                best_diff = diff
                best_atk = atk
        if best_atk is not None and best_diff >= 0:
            blk.blocking = best_atk
            best_atk.blocked_by.append(blk)
            chosen.add(best_atk)
            available.remove(blk)


def _perform_chump_blocks(
    attackers: Sequence[CombatCreature],
    available: List[CombatCreature],
    life: int,
    poison: int,
) -> None:
    """Chump block attackers if lethal damage would be dealt."""

    def remaining_threat() -> tuple[int, int]:
        dmg = 0
        psn = 0
        for a in attackers:
            if not a.blocked_by:
                dmg += a.effective_power()
                psn += (a.effective_power() if a.infect else 0) + a.toxic
        return dmg, psn

    for atk in sorted(
        [a for a in attackers if not a.blocked_by],
        key=lambda a: a.effective_power(),
        reverse=True,
    ):
        if not available:
            break
        dmg, psn = remaining_threat()
        if life <= dmg or poison + psn >= POISON_LOSS_THRESHOLD:
            choices = [b for b in available if _can_block(atk, b)]
            if not choices:
                continue
            blk = min(choices, key=_creature_value)
            blk.blocking = atk
            atk.blocked_by.append(blk)
            available.remove(blk)


def decide_optimal_blocks(
    attackers: List[CombatCreature],
    blockers: List[CombatCreature],
    game_state: Optional[GameState] = None,
    *,
    provoke_map: Optional[dict[CombatCreature, CombatCreature]] = None,
    max_iterations: int = int(1e6),
) -> Tuple[int, int]:
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

    options: List[List[int | None]] = []
    for blk in blockers:
        forced = provoked.get(blk)
        if forced is not None and _can_block(forced, blk):
            options.append([attackers.index(forced)])
        else:
            options.append(list(range(len(attackers))) + [None])

    best: Optional[Tuple[Optional[int], ...]] = None
    best_score: Optional[tuple] = None
    best_score_numeric: Optional[tuple] = None
    optimal_count = 0

    for assignment in product(*options):
        score = evaluate_block_assignment(
            attackers,
            blockers,
            assignment,
            game_state,
            counter,
            provoke_map,
        )
        numeric = score[:-1]
        if best_score is None or score < best_score:
            # Update the chosen assignment whenever we find a strictly better
            # score. Only reset ``optimal_count`` if the numeric portion of the
            # score actually improved; otherwise we simply update the stored
            # best score so the deterministic tiebreaker picks this assignment.
            if best_score is None:
                optimal_count = 1
            elif best_score_numeric is not None and numeric < best_score_numeric:
                optimal_count = 1
            best_score = score
            best_score_numeric = numeric
            best = tuple(assignment)
        elif (
            best_score is not None
            and best_score_numeric is not None
            and numeric == best_score_numeric
        ):
            # ``optimal_count`` should include all assignments that are tied on
            # the numeric criteria. Ignore the deterministic tiebreaker when
            # counting optimal results.
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
    life = game_state.players[defender].life if game_state else DEFAULT_STARTING_LIFE
    poison = game_state.players[defender].poison if game_state else 0

    available = list(blockers)
    _apply_provoke_assignments(attackers, available, provoke_map)

    attackers_sorted = sorted(attackers, key=_creature_value, reverse=True)
    _assign_favorable_trades(attackers_sorted, available)

    _perform_chump_blocks(attackers, available, life, poison)
