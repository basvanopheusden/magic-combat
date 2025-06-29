from magic_combat import CombatCreature
from magic_combat import GameState
from magic_combat import PlayerState
from magic_combat import decide_optimal_blocks
from magic_combat import decide_simple_blocks


def test_simple_ai_skips_nonlethal_double_block():
    """CR 509.1a: Multiple blockers may be assigned to one attacker."""
    atk = CombatCreature("Giant", 6, 6, "A")
    b1 = CombatCreature("Guard1", 4, 4, "B")
    b2 = CombatCreature("Guard2", 4, 4, "B")
    state = GameState(
        players={
            "A": PlayerState(life=20, creatures=[atk]),
            "B": PlayerState(life=20, creatures=[b1, b2]),
        }
    )
    decide_simple_blocks([atk], [b1, b2], game_state=state)
    assert b1.blocking is None and b2.blocking is None

    atk_o = CombatCreature("Giant", 6, 6, "A")
    c1 = CombatCreature("Guard1", 4, 4, "B")
    c2 = CombatCreature("Guard2", 4, 4, "B")
    state_o = GameState(
        players={
            "A": PlayerState(life=20, creatures=[atk_o]),
            "B": PlayerState(life=20, creatures=[c1, c2]),
        }
    )
    decide_optimal_blocks([atk_o], [c1, c2], game_state=state_o)
    assert c1.blocking is atk_o and c2.blocking is atk_o


def test_simple_ai_chumps_instead_of_double_blocking_lethal():
    """CR 509.1a: Multiple blockers may be assigned to one attacker."""
    atk = CombatCreature("Giant", 6, 6, "A")
    b1 = CombatCreature("Guard1", 4, 4, "B")
    b2 = CombatCreature("Guard2", 4, 4, "B")
    state = GameState(
        players={
            "A": PlayerState(life=20, creatures=[atk]),
            "B": PlayerState(life=6, creatures=[b1, b2]),
        }
    )
    decide_simple_blocks([atk], [b1, b2], game_state=state)
    assert sum(blk.blocking is atk for blk in (b1, b2)) == 1

    atk_o = CombatCreature("Giant", 6, 6, "A")
    c1 = CombatCreature("Guard1", 4, 4, "B")
    c2 = CombatCreature("Guard2", 4, 4, "B")
    state_o = GameState(
        players={
            "A": PlayerState(life=20, creatures=[atk_o]),
            "B": PlayerState(life=6, creatures=[c1, c2]),
        }
    )
    decide_optimal_blocks([atk_o], [c1, c2], game_state=state_o)
    assert c1.blocking is atk_o and c2.blocking is atk_o
