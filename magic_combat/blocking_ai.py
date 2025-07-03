"""Heuristics for choosing optimal blocks."""

from __future__ import annotations

import heapq
from itertools import permutations
from itertools import product
from typing import Iterable
from typing import Optional
from typing import Sequence
from typing import Tuple
from typing import TypeAlias

from .block_utils import evaluate_block_assignment
from .block_utils import should_force_provoke
from .creature import CombatCreature
from .gamestate import GameState
from .limits import IterationCounter
from .utils import check_non_negative

ScoreVector: TypeAlias = tuple[int, float, int, int, int, int, tuple[int, ...]]


def _get_all_assignments(
    options: Sequence[Sequence[int | None]],
) -> list[tuple[Optional[int], ...]]:
    """Return every combination of blocker assignments."""

    return list(product(*options))


def _get_block_options(
    game_state: GameState,
    provoke_map: Optional[dict[CombatCreature, CombatCreature]] = None,
    *,
    indices: Optional[Sequence[int]] = None,
) -> list[list[int | None]]:
    """Return possible block choices for each selected blocker."""

    attackers = list(game_state.players["A"].creatures)
    blockers = list(game_state.players["B"].creatures)
    selected = list(range(len(blockers))) if indices is None else list(indices)

    provoked: dict[CombatCreature, CombatCreature] = {}
    if provoke_map:
        for atk, blk in provoke_map.items():
            if atk in attackers and blk in blockers:
                blk_idx = blockers.index(blk)
                if blk_idx in selected:
                    provoked[blk] = atk

    options: list[list[int | None]] = []
    for idx in selected:
        blk = blockers[idx]
        if blk.tapped:
            options.append([None])
            continue
        forced = provoked.get(blk)
        if forced is not None and should_force_provoke(forced, blk, game_state):
            options.append([attackers.index(forced)])
        else:
            options.append(list(range(len(attackers))) + [None])

    return options


def _valid_minimal(
    assignment: Sequence[Optional[int]],
    attackers: Sequence[CombatCreature],
) -> bool:
    """Return ``True`` if ``assignment`` uses the minimal number of blockers."""

    counts: dict[int, int] = {}
    for choice in assignment:
        if choice is not None:
            counts[choice] = counts.get(choice, 0) + 1

    for idx, atk in enumerate(attackers):
        cnt = counts.get(idx, 0)
        if atk.menace:
            if cnt not in (0, 2):
                return False
        elif cnt not in (0, 1):
            return False

    return True


def _valid_superset(
    reference: Sequence[Optional[int]],
    candidate: Sequence[Optional[int]],
) -> bool:
    """Return ``True`` if ``candidate`` extends ``reference`` without changes."""

    return all(r is None or r == c for r, c in zip(reference, candidate))


def damage_order_permutations(
    attacker: CombatCreature, blockers: Sequence[CombatCreature]
) -> Iterable[tuple[CombatCreature, ...]]:
    """Yield all possible damage orders for ``attacker``."""
    if len(blockers) <= 1:
        yield tuple(blockers)
    else:
        yield from permutations(blockers)


def get_all_damage_orderings(
    block_dict: dict[CombatCreature, CombatCreature],
) -> list[dict[CombatCreature, tuple[CombatCreature, ...]]]:
    """Return all possible damage orderings for ``assignment``."""

    block_map: dict[CombatCreature, list[CombatCreature]] = {}
    for blk, atk in block_dict.items():
        block_map.setdefault(atk, []).append(blk)

    order_options: list[list[tuple[CombatCreature, ...]]] = []
    atk_keys: list[CombatCreature] = []
    for atk, blks in block_map.items():
        if len(blks) > 1:
            atk_keys.append(atk)
            order_options.append(list(damage_order_permutations(atk, blks)))

    if not order_options:
        return [{}]

    orders_iter: Iterable[tuple[tuple[CombatCreature, ...], ...]] = product(
        *order_options
    )
    return [
        {atk_keys[i]: orders[i] for i in range(len(orders))} for orders in orders_iter
    ]


def _minimax_assignments(
    assignments: Iterable[Sequence[Optional[int]]],
    game_state: GameState,
    counter: IterationCounter,
    provoke_map: Optional[dict[CombatCreature, CombatCreature]],
    mentor_map: Optional[dict[CombatCreature, CombatCreature]],
    *,
    include_loss: bool,
    k: int,
) -> Tuple[list[tuple[ScoreVector, tuple[Optional[int], ...]]], int]:
    """Evaluate a collection of predetermined blocking assignments.

    ``provoke_map`` and ``mentor_map`` ensure special interactions are
    enforced when simulating each assignment.
    """

    attackers = list(game_state.players["A"].creatures)
    blockers = list(game_state.players["B"].creatures)

    results: list[tuple[ScoreVector, tuple[Optional[int], ...]]] = []

    for assignment in assignments:
        key = tuple(len(attackers) if c is None else c for c in assignment)
        scores_for_attacker: list[ScoreVector] = []
        block_dict = {
            blockers[blk_idx]: attackers[choice]
            for blk_idx, choice in enumerate(assignment)
            if choice is not None
        }
        for damage_order in get_all_damage_orderings(block_dict):
            result, _ = evaluate_block_assignment(
                block_dict,
                game_state,
                counter,
                provoke_map=provoke_map,
                mentor_map=mentor_map,
                damage_order=damage_order,
            )
            if result is not None:
                score = result.score("A", "B", include_loss=include_loss) + (key,)
                scores_for_attacker.append(score)

        if not scores_for_attacker:
            continue

        worst_for_defender = max(scores_for_attacker)
        results.append((worst_for_defender, tuple(assignment)))

    if not results:
        return [], 0

    best_numeric = min(score[:-1] for score, _ in results)
    optimal_count = sum(1 for score, _ in results if score[:-1] == best_numeric)

    top = heapq.nsmallest(k, results)
    return top, optimal_count


def decide_optimal_blocks(
    game_state: GameState,
    *,
    provoke_map: Optional[dict[CombatCreature, CombatCreature]] = None,
    mentor_map: Optional[dict[CombatCreature, CombatCreature]] = None,
    max_iterations: int = int(1e4),
    k: int = 1,
) -> Tuple[list[tuple[ScoreVector, tuple[Optional[int], ...]]], int,]:
    """Assign blockers to attackers using a minimax search.

    ``provoke_map`` and ``mentor_map`` describe forced blocks and mentor
    targets that must be respected when evaluating assignments.
    """

    check_non_negative(k, "k")

    attackers = list(game_state.players["A"].creatures)
    blockers = list(game_state.players["B"].creatures)
    if not blockers:
        return [], 1

    counter = IterationCounter(max_iterations)

    options = _get_block_options(
        game_state,
        provoke_map,
    )

    assignments = _get_all_assignments(options)
    top, optimal_count = _minimax_assignments(
        assignments,
        game_state,
        counter,
        provoke_map,
        mentor_map,
        include_loss=True,
        k=k,
    )

    # Apply the chosen assignment to the real objects
    game_state.reset_block_assignments()
    if len(top) == 0:
        return [], optimal_count

    _, best_assignment = top[0]
    for blk_idx, choice in enumerate(best_assignment):
        if choice is not None:
            blk = blockers[blk_idx]
            atk = attackers[choice]
            blk.blocking = atk
            atk.blocked_by.append(blk)

    return top, optimal_count


def decide_simple_blocks(
    game_state: GameState,
    provoke_map: Optional[dict[CombatCreature, CombatCreature]] = None,
    mentor_map: Optional[dict[CombatCreature, CombatCreature]] = None,
    max_iterations: int = int(1e4),
) -> tuple[ScoreVector, tuple[Optional[int], ...]]:
    """Assign blocks using a small two-stage minimax search.

    ``provoke_map`` and ``mentor_map`` function the same as in
    :func:`decide_optimal_blocks`.
    """

    attackers = list(game_state.players["A"].creatures)
    blockers = list(game_state.players["B"].creatures)
    counter = IterationCounter(max_iterations)

    game_state.reset_block_assignments()

    block_options = _get_block_options(
        game_state,
        provoke_map,
    )

    all_assignments = _get_all_assignments(block_options)

    minimal_assignments = [a for a in all_assignments if _valid_minimal(a, attackers)]

    top, _ = _minimax_assignments(
        minimal_assignments,
        game_state,
        counter,
        provoke_map,
        mentor_map,
        include_loss=False,
        k=5,
    )
    print(top)

    _, best_assignment = top[0]

    superset_assignments = [
        a for a in all_assignments if _valid_superset(best_assignment, a)
    ]
    top, _ = _minimax_assignments(
        superset_assignments,
        game_state,
        counter,
        provoke_map,
        mentor_map,
        include_loss=True,
        k=1,
    )

    final_score, final_assignment = top[0]

    game_state.reset_block_assignments()
    for blk_idx, choice in enumerate(final_assignment):
        if choice is not None:
            blk = blockers[blk_idx]
            atk = attackers[choice]
            blk.blocking = atk
            atk.blocked_by.append(blk)

    return final_score, final_assignment
