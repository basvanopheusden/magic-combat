from magic_combat import CombatCreature
from magic_combat import GameState
from magic_combat import PlayerState
from magic_combat import decide_optimal_blocks
from magic_combat import decide_simple_blocks
from magic_combat.constants import DEFAULT_STARTING_LIFE


def test_simple_ai_single_blocks_when_double_block_survives():
    """CR 509.1a: The defending player chooses how creatures block."""
    big_atk = CombatCreature("Giant", 5, 5, "A")
    small_atk = CombatCreature("Scout", 3, 3, "A")
    big_blk = CombatCreature("Guard", 3, 3, "B")
    small_blk = CombatCreature("Assistant", 2, 2, "B")
    state_simple = GameState(
        players={
            "A": PlayerState(
                life=DEFAULT_STARTING_LIFE, creatures=[big_atk, small_atk]
            ),
            "B": PlayerState(life=5, creatures=[big_blk, small_blk]),
        }
    )
    decide_simple_blocks(
        [big_atk, small_atk], [big_blk, small_blk], game_state=state_simple
    )
    assert big_blk.blocking is small_atk
    assert small_blk.blocking is big_atk

    big_atk2 = CombatCreature("Giant", 5, 5, "A")
    small_atk2 = CombatCreature("Scout", 3, 3, "A")
    big_blk2 = CombatCreature("Guard", 3, 3, "B")
    small_blk2 = CombatCreature("Assistant", 2, 2, "B")
    state_opt = GameState(
        players={
            "A": PlayerState(
                life=DEFAULT_STARTING_LIFE, creatures=[big_atk2, small_atk2]
            ),
            "B": PlayerState(life=5, creatures=[big_blk2, small_blk2]),
        }
    )
    decide_optimal_blocks(
        [big_atk2, small_atk2], [big_blk2, small_blk2], game_state=state_opt
    )
    assert big_blk2.blocking is big_atk2 and small_blk2.blocking is big_atk2


def test_simple_ai_blocks_lifelink_instead_of_killing_bigger():
    """CR 702.15a: Lifelink causes its controller to gain that much life."""
    lifelink_atk = CombatCreature("Priest", 5, 5, "A", lifelink=True)
    big_atk = CombatCreature("Colossus", 7, 7, "A")
    blk1 = CombatCreature("Guard1", 5, 5, "B")
    blk2 = CombatCreature("Guard2", 5, 5, "B")
    state_simple = GameState(
        players={
            "A": PlayerState(
                life=DEFAULT_STARTING_LIFE, creatures=[lifelink_atk, big_atk]
            ),
            "B": PlayerState(life=10, creatures=[blk1, blk2]),
        }
    )
    decide_simple_blocks(
        [lifelink_atk, big_atk],
        [blk1, blk2],
        game_state=state_simple,
    )
    assert blk1.blocking is lifelink_atk and blk2.blocking is None

    lifelink_atk2 = CombatCreature("Priest", 5, 5, "A", lifelink=True)
    big_atk2 = CombatCreature("Colossus", 7, 7, "A")
    blk1o = CombatCreature("Guard1", 5, 5, "B")
    blk2o = CombatCreature("Guard2", 5, 5, "B")
    state_opt = GameState(
        players={
            "A": PlayerState(
                life=DEFAULT_STARTING_LIFE, creatures=[lifelink_atk2, big_atk2]
            ),
            "B": PlayerState(life=10, creatures=[blk1o, blk2o]),
        }
    )
    decide_optimal_blocks(
        [lifelink_atk2, big_atk2], [blk1o, blk2o], game_state=state_opt
    )
    assert blk1o.blocking is big_atk2 and blk2o.blocking is big_atk2
