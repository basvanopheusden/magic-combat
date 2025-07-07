from magic_combat import CombatCreature
from magic_combat import GameState
from magic_combat import PlayerState
from magic_combat import decide_optimal_blocks
from magic_combat.block_utils import evaluate_block_assignment
from magic_combat.blocking_ai import _get_all_assignments
from magic_combat.blocking_ai import _get_block_options
from magic_combat.limits import IterationCounter
from magic_combat.scoring import AGGREGATE_WEIGHTS
from magic_combat.scoring import compute_aggregate_score


def test_compute_aggregate_score_vector():
    best = (0, 0.0, 0, 0, 0, 0)
    vec = (0, 5.0, 1, 2, 10, 3)
    expected = -sum(
        w * abs(float(s) - float(b)) for w, s, b in zip(AGGREGATE_WEIGHTS, vec, best)
    )
    assert compute_aggregate_score(vec, best) == expected


def test_optimal_assignment_zero_aggregate():
    """CR 509.1a: The defending player chooses how creatures block."""
    atk1 = CombatCreature("A1", 3, 3, "A")
    atk2 = CombatCreature("A2", 2, 2, "A")
    blk = CombatCreature("B", 3, 3, "B")
    state = GameState(
        players={
            "A": PlayerState(life=20, creatures=[atk1, atk2]),
            "B": PlayerState(life=20, creatures=[blk]),
        }
    )

    attackers = list(state.players["A"].creatures)
    blockers = list(state.players["B"].creatures)
    options = _get_block_options(state, None)
    assignments = _get_all_assignments(options)

    score_map = {}
    best_vec = None
    for ass in assignments:
        blk_map = {
            blockers[i]: attackers[a] for i, a in enumerate(ass) if a is not None
        }
        result, _ = evaluate_block_assignment(blk_map, state, IterationCounter(10))
        if result is None:
            continue
        vec = result.score("A", "B")
        score_map[ass] = vec
        if best_vec is None or vec < best_vec:
            best_vec = vec

    assert best_vec is not None

    # compute aggregates
    aggregates = {
        ass: compute_aggregate_score(vec, best_vec) for ass, vec in score_map.items()
    }

    # Optimal AI assignment should have zero aggregate
    top, _ = decide_optimal_blocks(game_state=state)
    ai_assignment = top[0][1]
    assert aggregates[ai_assignment] == 0
    # All other assignments must be negative
    for ass, agg in aggregates.items():
        if ass != ai_assignment:
            assert agg < 0
