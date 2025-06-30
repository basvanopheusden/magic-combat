"""Heuristics for choosing optimal blocks."""

from __future__ import annotations

from itertools import product
from typing import List
from typing import Optional
from typing import Sequence
from typing import Tuple

from .block_utils import evaluate_block_assignment
from .creature import CombatCreature
from .damage import damage_order_permutations
from .exceptions import IllegalBlockError
from .gamestate import GameState
from .limits import IterationCounter
from .simulator import CombatResult
from .simulator import CombatSimulator
from .utils import can_block


def _should_force_provoke(
    attacker: CombatCreature,
    blocker: CombatCreature,
    blockers: Sequence[CombatCreature],
) -> bool:
    """Return ``True`` if ``blocker`` must block ``attacker``."""

    if not can_block(attacker, blocker):
        return False
    if attacker.menace:
        eligible = [
            b
            for b in blockers
            if b is not blocker and not b.tapped and can_block(attacker, b)
        ]
        if not eligible:
            return False
    return True


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
    """Search simple blocks focusing on favorable trades.

    This routine maximizes creature value traded first, then creature count,
    and finally the total mana value destroyed.
    """

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
        if forced is not None and _should_force_provoke(forced, blk, blockers):
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
                attackers,
                blockers,
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
        if blk.tapped:
            options.append([None])
            continue
        forced = provoked.get(blk)
        if forced is not None and _should_force_provoke(forced, blk, blockers):
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
            c.value() for c in result.creatures_destroyed if c.controller == defender
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


def _minimax_blocks(
    attackers: Sequence[CombatCreature],
    blockers: Sequence[CombatCreature],
    options: Sequence[Sequence[int | None]],
    game_state: Optional[GameState],
    counter: IterationCounter,
    provoke_map: Optional[dict[CombatCreature, CombatCreature]],
) -> tuple[
    tuple[Optional[int], ...] | None, tuple[int, float, int, int, int, int] | None, int
]:
    best: tuple[Optional[int], ...] | None = None
    best_score: tuple[
        int, float, int, int, int, int, tuple[Optional[int], ...]
    ] | None = None
    optimal_count = 0

    for assignment in product(*options):
        worst_for_defender: tuple[
            int, float, int, int, int, int, tuple[Optional[int], ...]
        ] | None = None
        # Attacker chooses ordering to maximize the score
        block_map: dict[CombatCreature, list[CombatCreature]] = {
            atk: [] for atk in attackers
        }
        for blk_idx, choice in enumerate(assignment):
            if choice is not None:
                block_map[attackers[choice]].append(blockers[blk_idx])

        order_options = []
        atk_keys = []
        for atk, blks in block_map.items():
            if len(blks) > 1:
                atk_keys.append(atk)
                order_options.append(list(damage_order_permutations(atk, blks)))

        order_iter = product(*order_options) if order_options else [tuple()]
        for orders in order_iter:
            damage_order = {atk_keys[i]: orders[i] for i in range(len(orders))}
            score = evaluate_block_assignment(
                attackers,
                blockers,
                assignment,
                game_state,
                counter,
                provoke_map,
                damage_order,
            )
            numeric = score[:-1]
            if worst_for_defender is None or numeric > worst_for_defender[:-1]:
                worst_for_defender = score
            elif numeric == worst_for_defender[:-1] and score > worst_for_defender:
                worst_for_defender = score

        if worst_for_defender is None:
            continue

        numeric = worst_for_defender[:-1]
        if best_score is None or numeric < best_score[:-1]:
            best_score = worst_for_defender
            best = tuple(assignment)
            optimal_count = 1
        elif numeric == best_score[:-1]:
            optimal_count += 1
            if worst_for_defender < best_score:
                best_score = worst_for_defender
                best = tuple(assignment)

    return best, best_score[:-1] if best_score else None, optimal_count


def decide_optimal_blocks(
    attackers: List[CombatCreature],
    blockers: List[CombatCreature],
    game_state: Optional[GameState] = None,
    *,
    provoke_map: Optional[dict[CombatCreature, CombatCreature]] = None,
    max_iterations: int = int(1e4),
) -> Tuple[int, int]:
    """Assign blockers to attackers using a minimax search over block assignments."""

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
        if blk.tapped:
            options.append([None])
            continue
        forced = provoked.get(blk)
        if forced is not None and _should_force_provoke(forced, blk, blockers):
            options.append([attackers.index(forced)])
        else:
            options.append(list(range(len(attackers))) + [None])

    best, _best_score, optimal_count = _minimax_blocks(
        attackers,
        blockers,
        options,
        game_state,
        counter,
        provoke_map,
    )

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
