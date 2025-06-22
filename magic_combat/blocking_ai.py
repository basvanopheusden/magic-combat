"""Heuristics for choosing optimal blocks."""

from __future__ import annotations

from copy import deepcopy
from itertools import product
from typing import List, Optional, Sequence, Tuple

from .creature import CombatCreature
from .damage import _blocker_value, OptimalDamageStrategy
from .gamestate import GameState
from .simulator import CombatSimulator
from .limits import IterationCounter


def _creature_value(creature: CombatCreature) -> float:
    """Return a heuristic value for the creature."""
    return _blocker_value(creature)


def _evaluate_assignment(
    attackers: Sequence[CombatCreature],
    blockers: Sequence[CombatCreature],
    assignment: Sequence[Optional[int]],
    state: Optional[GameState],
    counter: "IterationCounter",
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

    sim = CombatSimulator(
        atks,
        blks,
        game_state=deepcopy(state),
        strategy=OptimalDamageStrategy(counter),
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

    lost = 1 if defender in result.players_lost else 0

    att_val = sum(
        _creature_value(c) for c in result.creatures_destroyed if c.controller == attacker_player
    )
    def_val = sum(
        _creature_value(c) for c in result.creatures_destroyed if c.controller == defender
    )
    val_diff = att_val - def_val

    att_cnt = sum(1 for c in result.creatures_destroyed if c.controller == attacker_player)
    def_cnt = sum(1 for c in result.creatures_destroyed if c.controller == defender)
    cnt_diff = att_cnt - def_cnt

    mana_total = sum(c.mana_value for c in result.creatures_destroyed)

    life_lost = result.damage_to_players.get(defender, 0)
    poison = result.poison_counters.get(defender, 0)

    # Lower tuple values are preferred. Convert ``assignment`` to a tuple of
    # integers so Python can compare scores deterministically even when ``None``
    # is present.
    ass_key = tuple(
        len(attackers) if choice is None else choice for choice in assignment
    )
    return (
        lost,
        -val_diff,
        -cnt_diff,
        -mana_total,
        life_lost,
        poison,
        ass_key,
    )


def decide_optimal_blocks(
    attackers: List[CombatCreature],
    blockers: List[CombatCreature],
    game_state: Optional[GameState] = None,
    *,
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
    """

    if not blockers:
        return 0

    counter = IterationCounter(max_iterations)

    options = [list(range(len(attackers))) + [None] for _ in blockers]

    best: Optional[Tuple[Optional[int], ...]] = None
    best_score: Optional[Tuple] = None

    for assignment in product(*options):
        score = _evaluate_assignment(
            attackers,
            blockers,
            assignment,
            game_state,
            counter,
        )
        if best_score is None or score < best_score:
            best_score = score
            best = tuple(assignment)

    # Apply the chosen assignment to the real objects
    for atk in attackers:
        atk.blocked_by.clear()
    for blk in blockers:
        blk.blocking = None
    if best is not None:
        for blk_idx, choice in enumerate(best):
            if choice is not None:
                blk = blockers[blk_idx]
                atk = attackers[choice]
                blk.blocking = atk
                atk.blocked_by.append(blk)

    return counter.count
