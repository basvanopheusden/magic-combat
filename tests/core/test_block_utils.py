from magic_combat import CombatCreature
from magic_combat.block_utils import evaluate_block_assignment
from magic_combat.gamestate import GameState
from magic_combat.gamestate import PlayerState
from magic_combat.limits import IterationCounter


def test_evaluate_block_assignment_simple():
    atk = CombatCreature("A", 2, 2, "A")
    blk = CombatCreature("B", 2, 2, "B")
    state = GameState(
        players={
            "A": PlayerState(life=20, creatures=[atk]),
            "B": PlayerState(life=20, creatures=[blk]),
        }
    )
    score = evaluate_block_assignment([atk], [blk], [0], state, IterationCounter(10))
    numeric = score[:-2]
    new_state = score[-1]
    assert numeric == (0, 0.0, 0, 0, 0, 0)
    assert score[-2] == (0,)
    assert isinstance(new_state, GameState)
