"""Heuristics for choosing optimal blocks."""

from __future__ import annotations

from itertools import product
from typing import List
from typing import Optional
from typing import Sequence
from typing import Tuple

from .block_utils import evaluate_block_assignment
from .creature import CombatCreature
from .damage import blocker_value
from .damage import score_combat_result
from .exceptions import IllegalBlockError
from .gamestate import GameState
from .limits import IterationCounter
from .simulator import CombatResult
from .simulator import CombatSimulator
from .utils import can_block


def _creature_value(creature: CombatCreature) -> float:
    """Return a heuristic value for the creature."""
    return blocker_value(creature)


def _reset_block_assignments(
    attackers: Sequence[CombatCreature],
    blockers: Sequence[CombatCreature],
) -> None:
    """Clear ``blocked_by`` and ``blocking`` fields on all combatants."""

    for atk in attackers:
        atk.blocked_by.clear()
    for blk in blockers:
        blk.blocking = None


def _best_value_trade_assignment(
    attackers: Sequence[CombatCreature],
    blockers: Sequence[CombatCreature],
    game_state: Optional[GameState],
    provoke_map: Optional[dict[CombatCreature, CombatCreature]] = None,
    counter: IterationCounter | None = None,
) -> tuple[Tuple[Optional[int], ...], tuple[int, float, int, int, int, int]]:
    """Search simple blocks focusing on favorable trades."""

    provoked: dict[CombatCreature, CombatCreature] = {}
    if provoke_map:
        for atk, blk in provoke_map.items():
            if atk in attackers and blk in blockers:
                provoked[blk] = atk

    options: list[list[int | None]] = []
    for blk in blockers:
        forced = provoked.get(blk)
        if forced is not None and can_block(forced, blk):
            options.append([attackers.index(forced)])
        else:
            options.append(list(range(len(attackers))) + [None])

    best_assignment: Tuple[Optional[int], ...] = tuple(None for _ in blockers)
    best_score = (float("-inf"), float("-inf"))
    best_numeric: tuple[int, float, int, int, int, int] = (0, 0.0, 0, 0, 0, 0)

    for assignment in product(*options):
        counts: dict[int, int] = {}
        for choice in assignment:
            if choice is not None:
                counts[choice] = counts.get(choice, 0) + 1
        valid = True
        for idx, atk in enumerate(attackers):
            cnt = counts.get(idx, 0)
            if atk.menace:
                if cnt not in (0, 2):
                    valid = False
                    break
            elif cnt > 1:
                valid = False
                break
        if not valid:
            continue

        try:
            _, dead_atk, dead_blk, score = _simulate_assignment(
                attackers,
                blockers,
                assignment,
                game_state,
                provoke_map,
                counter,
            )
        except IllegalBlockError:
            continue

        # Reject any blocks that fail to at least trade.
        for blk_idx, choice in enumerate(assignment):
            if choice is None:
                continue
            died_blk = blk_idx in dead_blk
            died_atk = choice in dead_atk
            if not died_atk:
                valid = False
                break
            if died_blk and _creature_value(blockers[blk_idx]) > _creature_value(
                attackers[choice]
            ):
                valid = False
                break
        if not valid:
            continue

        val_diff = -score[1]
        cnt_diff = -score[2]
        if (val_diff, cnt_diff) > best_score:
            best_score = (val_diff, cnt_diff)
            best_assignment = tuple(assignment)
            best_numeric = score

    return best_assignment, best_numeric


def _best_survival_assignment(
    attackers: Sequence[CombatCreature],
    blockers: Sequence[CombatCreature],
    base_assignment: Sequence[Optional[int]],
    game_state: Optional[GameState],
    provoke_map: Optional[dict[CombatCreature, CombatCreature]] = None,
    counter: IterationCounter | None = None,
) -> Tuple[Optional[Tuple[Optional[int], ...]], tuple[int, float, int, int, int, int]]:
    """Try to prevent lethal damage with chump blocks."""

    remain_indices = [i for i, a in enumerate(base_assignment) if a is None]
    if not remain_indices:
        return None, (0, 0.0, 0, 0, 0, 0)

    provoked: dict[CombatCreature, CombatCreature] = {}
    if provoke_map:
        for atk, blk in provoke_map.items():
            if (
                atk in attackers
                and blk in blockers
                and blk in [blockers[i] for i in remain_indices]
            ):
                provoked[blk] = atk

    options: list[list[int | None]] = []
    for idx in remain_indices:
        blk = blockers[idx]
        forced = provoked.get(blk)
        if forced is not None and can_block(forced, blk):
            options.append([attackers.index(forced)])
        else:
            options.append(list(range(len(attackers))) + [None])

    best_assignment: Optional[Tuple[Optional[int], ...]] = None
    best_score = (float("inf"), float("inf"))
    best_numeric: tuple[int, float, int, int, int, int] = (0, 0.0, 0, 0, 0, 0)

    base_list = list(base_assignment)

    for combo in product(*options):
        ass = base_list[:]
        for idx, choice in zip(remain_indices, combo):
            ass[idx] = choice

        counts: dict[int, int] = {}
        for choice in ass:
            if choice is not None:
                counts[choice] = counts.get(choice, 0) + 1
        valid = True
        for atk_idx, atk in enumerate(attackers):
            cnt = counts.get(atk_idx, 0)
            if atk.menace:
                if cnt not in (0, 2):
                    valid = False
                    break
            elif cnt > 1:
                valid = False
                break
        if not valid:
            continue

        try:
            result, _dead_atk, _dead_blk, score = _simulate_assignment(
                attackers,
                blockers,
                ass,
                game_state,
                provoke_map,
                counter,
            )
        except IllegalBlockError:
            continue

        if score[0] != 0:
            continue

        defender = blockers[0].controller if blockers else "B"
        def_val = sum(
            blocker_value(c)
            for c in result.creatures_destroyed
            if c.controller == defender
        )
        def_cnt = sum(1 for c in result.creatures_destroyed if c.controller == defender)

        if (def_val, def_cnt) < best_score:
            best_score = (def_val, def_cnt)
            best_assignment = tuple(ass)
            best_numeric = score

    return best_assignment, best_numeric


def _simulate_assignment(
    attackers: Sequence[CombatCreature],
    blockers: Sequence[CombatCreature],
    assignment: Sequence[Optional[int]],
    game_state: Optional[GameState],
    provoke_map: Optional[dict[CombatCreature, CombatCreature]] = None,
    counter: IterationCounter | None = None,
) -> tuple[CombatResult, set[int], set[int], tuple[int, float, int, int, int, int]]:
    """Return simulation result and sets of dead attacker/blocker indices."""

    from copy import deepcopy

    atk_copy = deepcopy(list(attackers))
    blk_copy = deepcopy(list(blockers))
    atk_map = {id(c): i for i, c in enumerate(atk_copy)}
    blk_map = {id(c): i for i, c in enumerate(blk_copy)}

    for blk_idx, choice in enumerate(assignment):
        if choice is not None:
            blk_copy[blk_idx].blocking = atk_copy[choice]
            atk_copy[choice].blocked_by.append(blk_copy[blk_idx])

    prov_copies: dict[CombatCreature, CombatCreature] = {}
    if provoke_map:
        for atk, blk in provoke_map.items():
            if atk in attackers and blk in blockers:
                a_copy = atk_copy[attackers.index(atk)]
                b_copy = blk_copy[blockers.index(blk)]
                prov_copies[a_copy] = b_copy

    sim = CombatSimulator(
        atk_copy,
        blk_copy,
        game_state=deepcopy(game_state) if game_state else None,
        provoke_map=prov_copies or None,
    )
    if counter is not None:
        counter.increment()
    result = sim.simulate()
    attacker_player = atk_copy[0].controller if atk_copy else "attacker"
    defender = blk_copy[0].controller if blk_copy else "defender"
    score = score_combat_result(result, attacker_player, defender)

    dead_atk = {atk_map[id(c)] for c in result.creatures_destroyed if id(c) in atk_map}
    dead_blk = {blk_map[id(c)] for c in result.creatures_destroyed if id(c) in blk_map}

    return result, dead_atk, dead_blk, score


def decide_optimal_blocks(
    attackers: List[CombatCreature],
    blockers: List[CombatCreature],
    game_state: Optional[GameState] = None,
    *,
    provoke_map: Optional[dict[CombatCreature, CombatCreature]] = None,
    max_iterations: int = int(1e4),
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
        if forced is not None and can_block(forced, blk):
            options.append([attackers.index(forced)])
        else:
            options.append(list(range(len(attackers))) + [None])

    best: Optional[Tuple[Optional[int], ...]] = None
    best_score: Optional[
        Tuple[int, float, int, int, int, int, Tuple[Optional[int], ...]]
    ] = None
    best_score_numeric: Optional[Tuple[int, float, int, int, int, int]] = None
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
        elif best_score_numeric is not None:
            if numeric == best_score_numeric:
                # ``optimal_count`` should include all assignments that are
                # tied on the numeric criteria. Ignore the deterministic
                # tiebreaker when counting optimal results.
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
    max_iterations: int = int(1e4),
) -> None:
    """Assign blocks using a two-stage heuristic search."""

    counter = IterationCounter(max_iterations)

    _reset_block_assignments(attackers, blockers)

    if not blockers:
        return

    best_ass, best_score = _best_value_trade_assignment(
        attackers,
        blockers,
        game_state,
        provoke_map,
        counter,
    )

    _, *_ = _simulate_assignment(
        attackers,
        blockers,
        best_ass,
        game_state,
        provoke_map,
        counter,
    )

    if best_score[0] != 0:
        second_ass, _ = _best_survival_assignment(
            attackers,
            blockers,
            best_ass,
            game_state,
            provoke_map,
            counter,
        )
        if second_ass is not None:
            best_ass = second_ass

    _reset_block_assignments(attackers, blockers)
    for blk_idx, choice in enumerate(best_ass):
        if choice is not None:
            blk = blockers[blk_idx]
            atk = attackers[choice]
            blk.blocking = atk
            atk.blocked_by.append(blk)
