from magic_combat import CombatCreature
from magic_combat import GameState
from magic_combat import PlayerState
from magic_combat import decide_optimal_blocks
from magic_combat import decide_simple_blocks


def test_simple_ai_single_blocks_when_double_is_better():
    """CR 509.1a: The defending player chooses how creatures block."""
    big_atk = CombatCreature("Giant", 8, 8, "A")
    small_atk = CombatCreature("Scout", 1, 1, "A")
    blk1 = CombatCreature("Guard1", 5, 5, "B")
    blk2 = CombatCreature("Guard2", 5, 5, "B")
    state = GameState(
        players={
            "A": PlayerState(life=20, creatures=[big_atk, small_atk]),
            "B": PlayerState(life=20, creatures=[blk1, blk2]),
        }
    )
    decide_simple_blocks([big_atk, small_atk], [blk1, blk2], game_state=state)
    assert blk1.blocking is small_atk and blk2.blocking is None

    for atk in (big_atk, small_atk):
        atk.blocked_by.clear()
    blk1.blocking = None
    blk2.blocking = None

    decide_optimal_blocks([big_atk, small_atk], [blk1, blk2], game_state=state)
    assert blk1.blocking is big_atk and blk2.blocking is big_atk


def test_simple_ai_leaves_both_attackers_unblocked():
    """CR 509.1a: The defending player chooses how creatures block."""
    atk1 = CombatCreature("Crusher", 6, 6, "A")
    atk2 = CombatCreature("Juggernaut", 6, 6, "A")
    blk1 = CombatCreature("Wall1", 4, 4, "B")
    blk2 = CombatCreature("Wall2", 4, 4, "B")
    state = GameState(
        players={
            "A": PlayerState(life=20, creatures=[atk1, atk2]),
            "B": PlayerState(life=20, creatures=[blk1, blk2]),
        }
    )
    decide_simple_blocks([atk1, atk2], [blk1, blk2], game_state=state)
    assert blk1.blocking is None and blk2.blocking is None

    for atk in (atk1, atk2):
        atk.blocked_by.clear()
    blk1.blocking = None
    blk2.blocking = None

    decide_optimal_blocks([atk1, atk2], [blk1, blk2], game_state=state)
    assert blk1.blocking is atk1 and blk2.blocking is atk1
