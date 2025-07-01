import pytest

from magic_combat import CombatCreature
from magic_combat import GameState
from magic_combat import PlayerState
from magic_combat import decide_optimal_blocks

# Scenario helpers


def _simple_state() -> GameState:
    a1 = CombatCreature("A1", 2, 2, "A")
    a2 = CombatCreature("A2", 3, 3, "A")
    b1 = CombatCreature("B1", 2, 2, "B")
    return GameState(
        players={
            "A": PlayerState(life=20, creatures=[a1, a2]),
            "B": PlayerState(life=20, creatures=[b1]),
        }
    )


def _tie_state() -> GameState:
    a1 = CombatCreature("A1", 2, 2, "A")
    a2 = CombatCreature("A2", 2, 2, "A")
    b1 = CombatCreature("B1", 2, 2, "B")
    b2 = CombatCreature("B2", 2, 2, "B")
    return GameState(
        players={
            "A": PlayerState(life=20, creatures=[a1, a2]),
            "B": PlayerState(life=20, creatures=[b1, b2]),
        }
    )


def test_negative_k_raises_error():
    """CR 509.1a: The defending player chooses how creatures block."""
    state = _simple_state()
    with pytest.raises(ValueError):
        decide_optimal_blocks(game_state=state, k=-1)


def test_result_length_not_exceed_k():
    """CR 509.1a: The defending player chooses how creatures block."""
    state = _simple_state()
    assns, _ = decide_optimal_blocks(game_state=state, k=2)
    assert len(assns) <= 2


def test_assignments_sorted_by_score():
    """CR 509.1a: The defending player chooses how creatures block."""
    state = _simple_state()
    assns, _ = decide_optimal_blocks(game_state=state, k=3)
    scores = [score for score, _ in assns]
    assert scores == sorted(scores)


def test_large_k_returns_all_assignments():
    """CR 509.1a: The defending player chooses how creatures block."""
    state = _simple_state()
    assns, _ = decide_optimal_blocks(game_state=state, k=10)
    assert len(assns) == 3


def test_best_assignment_applied_with_large_k():
    """CR 509.1a: The defending player chooses how creatures block."""
    state = _simple_state()
    assns, _ = decide_optimal_blocks(game_state=state, k=3)
    ((_, best),) = assns[:1]
    attackers = list(state.players["A"].creatures)
    blockers = list(state.players["B"].creatures)
    if best[0] is None:
        assert blockers[0].blocking is None
    else:
        assert blockers[0].blocking is attackers[best[0]]


def test_same_best_assignment_for_k1_and_k3():
    """CR 509.1a: The defending player chooses how creatures block."""
    state1 = _simple_state()
    assn1, _ = decide_optimal_blocks(game_state=state1, k=1)
    best1 = assn1[0][1]

    state2 = _simple_state()
    assn3, _ = decide_optimal_blocks(game_state=state2, k=3)
    best3 = assn3[0][1]

    assert best1 == best3


def test_optimal_count_independent_of_k():
    """CR 509.1a: The defending player chooses how creatures block."""
    state = _tie_state()
    _, count1 = decide_optimal_blocks(game_state=state, k=1)
    _, count2 = decide_optimal_blocks(game_state=_tie_state(), k=2)
    assert count1 == 2
    assert count1 == count2


def test_tie_results_sorted():
    """CR 509.1a: The defending player chooses how creatures block."""
    state = _tie_state()
    assns, _ = decide_optimal_blocks(game_state=state, k=2)
    scores = [score for score, _ in assns]
    assert scores == sorted(scores)


def test_large_k_tie_no_error():
    """CR 509.1a: The defending player chooses how creatures block."""
    state = _tie_state()
    assns, _ = decide_optimal_blocks(game_state=state, k=20)
    assert len(assns) == 9


def test_zero_k_returns_empty():
    """CR 509.1a: The defending player chooses how creatures block."""
    state = _simple_state()
    assns, _ = decide_optimal_blocks(game_state=state, k=0)
    assert assns == []
