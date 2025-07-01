"""Heuristics for choosing optimal blocks."""

from __future__ import annotations

import heapq
from itertools import product
from typing import Iterable
from typing import List
from typing import Optional
from typing import Sequence
from typing import Tuple
from typing import TypeAlias

from .block_utils import evaluate_block_assignment
from .block_utils import reset_block_assignments
from .block_utils import should_force_provoke
from .creature import CombatCreature
from .damage import damage_order_permutations
from .exceptions import IllegalBlockError
from .gamestate import GameState
from .limits import IterationCounter
from .simulator import CombatResult
from .simulator import CombatSimulator
from .utils import check_non_negative

ScoreVector: TypeAlias = tuple[int, float, int, int, int, int, tuple[int, ...]]


def _best_value_trade_assignment(
    game_state: GameState,
    provoke_map: Optional[dict[CombatCreature, CombatCreature]] = None,
    counter: IterationCounter | None = None,
) -> tuple[Tuple[Optional[int], ...], tuple[int, float, int, int, int, int]]:
    """Search simple blocks focusing on favorable trades.

    This routine maximizes creature value traded first, then creature count,
    and finally the total mana value destroyed.
    """

    attackers = list(game_state.players["A"].creatures)
    blockers = list(game_state.players["B"].creatures)
    provoked: dict[CombatCreature, CombatCreature] = {}
    if provoke_map:
        for atk, blk in provoke_map.items():
            if atk in attackers and blk in blockers:
                provoked[blk] = atk

    options: list[list[int | None]] = []
    for blk in blockers:
        if blk.tapped:
            options.append([None])
            continue
        forced = provoked.get(blk)
        if forced is not None and should_force_provoke(forced, blk, game_state):
            options.append([attackers.index(forced)])
        else:
            options.append(list(range(len(attackers))) + [None])

    best_assignment: Tuple[Optional[int], ...] = tuple(None for _ in blockers)
    best_score = (float("-inf"), float("-inf"), float("-inf"))
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
                assignment,
                game_state,
                provoke_map,
                counter,
                include_life=False,
                include_poison=False,
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
            if died_blk and blockers[blk_idx].value() > attackers[choice].value():
                valid = False
                break
        if not valid:
            continue

        val_diff = -score[1]
        cnt_diff = -score[2]
        mana_diff = -score[3]
        if (val_diff, cnt_diff, mana_diff) > best_score:
            best_score = (val_diff, cnt_diff, mana_diff)
            best_assignment = tuple(assignment)
            best_numeric = score

    return best_assignment, best_numeric


def _best_survival_assignment(
    base_assignment: Sequence[Optional[int]],
    game_state: GameState,
    provoke_map: Optional[dict[CombatCreature, CombatCreature]] = None,
    counter: IterationCounter | None = None,
) -> Tuple[Optional[Tuple[Optional[int], ...]], tuple[int, float, int, int, int, int]]:
    """Try to prevent lethal damage with chump blocks."""

    attackers = list(game_state.players["A"].creatures)
    blockers = list(game_state.players["B"].creatures)
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
        if blk.tapped:
            options.append([None])
            continue
        forced = provoked.get(blk)
        if forced is not None and should_force_provoke(forced, blk, game_state):
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
            c.value() for c in result.creatures_destroyed if c.controller == defender
        )
        def_cnt = sum(1 for c in result.creatures_destroyed if c.controller == defender)

        if (def_val, def_cnt) < best_score:
            best_score = (def_val, def_cnt)
            best_assignment = tuple(ass)
            best_numeric = score

    return best_assignment, best_numeric


def _simulate_assignment(
    assignment: Sequence[Optional[int]],
    game_state: GameState,
    provoke_map: Optional[dict[CombatCreature, CombatCreature]] = None,
    counter: IterationCounter | None = None,
    *,
    include_life: bool = True,
    include_poison: bool = True,
    include_mana: bool = True,
    include_value: bool = True,
    include_count: bool = True,
    include_loss: bool = True,
) -> tuple[CombatResult, set[int], set[int], tuple[int, float, int, int, int, int]]:
    """Return simulation result and sets of dead attacker/blocker indices."""

    from copy import deepcopy

    attackers = list(game_state.players["A"].creatures)
    blockers = list(game_state.players["B"].creatures)
    atk_copy = deepcopy(attackers)
    blk_copy = deepcopy(blockers)
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
        game_state=deepcopy(game_state),
        provoke_map=prov_copies or None,
    )
    if counter is not None:
        counter.increment()
    result = sim.simulate()
    attacker_player = atk_copy[0].controller if atk_copy else "attacker"
    defender = blk_copy[0].controller if blk_copy else "defender"
    score = result.score(
        attacker_player,
        defender,
        include_life=include_life,
        include_poison=include_poison,
        include_mana=include_mana,
        include_value=include_value,
        include_count=include_count,
        include_loss=include_loss,
    )

    dead_atk = {atk_map[id(c)] for c in result.creatures_destroyed if id(c) in atk_map}
    dead_blk = {blk_map[id(c)] for c in result.creatures_destroyed if id(c) in blk_map}

    return result, dead_atk, dead_blk, score


def get_all_blocking_assignments(
    options: Sequence[Sequence[int | None]],
) -> list[tuple[Optional[int], ...]]:
    """Return every combination of blocker assignments."""

    return list(product(*options))


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


def _minimax_blocks(
    options: Sequence[Sequence[int | None]],
    game_state: GameState,
    counter: IterationCounter,
    provoke_map: Optional[dict[CombatCreature, CombatCreature]],
    *,
    k: int,
) -> Tuple[list[tuple[ScoreVector, tuple[Optional[int], ...]]], int]:
    attackers = list(game_state.players["A"].creatures)
    blockers = list(game_state.players["B"].creatures)
    results: list[tuple[ScoreVector, tuple[Optional[int], ...]]] = []

    for assignment in get_all_blocking_assignments(options):
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
                provoke_map,
                damage_order,
            )
            if result is not None:
                score = result.score("A", "B") + (key,)
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
    max_iterations: int = int(1e4),
    k: int = 1,
) -> Tuple[list[tuple[ScoreVector, tuple[Optional[int], ...]]], int,]:
    """Assign blockers to attackers using a minimax search over block assignments."""

    check_non_negative(k, "k")

    attackers = list(game_state.players["A"].creatures)
    blockers = list(game_state.players["B"].creatures)
    if not blockers:
        return [], 1

    counter = IterationCounter(max_iterations)

    provoked: dict[CombatCreature, CombatCreature] = {}
    if provoke_map:
        for atk, blk in provoke_map.items():
            if atk in attackers and blk in blockers:
                provoked[blk] = atk

    options: List[List[int | None]] = []
    for blk in blockers:
        if blk.tapped:
            options.append([None])
            continue
        forced = provoked.get(blk)
        if forced is not None and should_force_provoke(forced, blk, game_state):
            options.append([attackers.index(forced)])
        else:
            options.append(list(range(len(attackers))) + [None])

    top, optimal_count = _minimax_blocks(
        options,
        game_state,
        counter,
        provoke_map,
        k=k,
    )

    # Apply the chosen assignment to the real objects
    reset_block_assignments(game_state)
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
    max_iterations: int = int(1e4),
) -> None:
    """Assign blocks using a two-stage heuristic search."""

    attackers = list(game_state.players["A"].creatures)
    blockers = list(game_state.players["B"].creatures)
    counter = IterationCounter(max_iterations)

    reset_block_assignments(game_state)

    if not blockers:
        return

    best_ass, best_score = _best_value_trade_assignment(
        game_state,
        provoke_map,
        counter,
    )

    _, *_ = _simulate_assignment(
        best_ass,
        game_state,
        provoke_map,
        counter,
    )

    if best_score[0] != 0:
        second_ass, _ = _best_survival_assignment(
            best_ass,
            game_state,
            provoke_map,
            counter,
        )
        if second_ass is not None:
            best_ass = second_ass

    reset_block_assignments(game_state)
    for blk_idx, choice in enumerate(best_ass):
        if choice is not None:
            blk = blockers[blk_idx]
            atk = attackers[choice]
            blk.blocking = atk
            atk.blocked_by.append(blk)
