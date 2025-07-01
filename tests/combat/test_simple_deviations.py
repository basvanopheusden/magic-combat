from magic_combat import CombatCreature
from magic_combat import GameState
from magic_combat import PlayerState
from magic_combat import decide_optimal_blocks
from magic_combat import decide_simple_blocks
from magic_combat.constants import DEFAULT_STARTING_LIFE


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
    decide_simple_blocks(game_state=state)
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
    decide_optimal_blocks(game_state=state_o)
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
    decide_simple_blocks(game_state=state)
    assert all(blk.blocking is atk for blk in (b1, b2))

    atk_o = CombatCreature("Giant", 6, 6, "A")
    c1 = CombatCreature("Guard1", 4, 4, "B")
    c2 = CombatCreature("Guard2", 4, 4, "B")
    state_o = GameState(
        players={
            "A": PlayerState(life=20, creatures=[atk_o]),
            "B": PlayerState(life=6, creatures=[c1, c2]),
        }
    )
    decide_optimal_blocks(game_state=state_o)
    assert c1.blocking is atk_o and c2.blocking is atk_o


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
    decide_simple_blocks(game_state=state_simple)
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
    decide_optimal_blocks(game_state=state_opt)
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
    decide_simple_blocks(game_state=state_simple)
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
    decide_optimal_blocks(game_state=state_opt)
    assert blk1o.blocking is big_atk2 and blk2o.blocking is big_atk2


def test_simple_vs_optimal_chump_block() -> None:
    """CR 509.1a: The defending player chooses how creatures block."""
    big = CombatCreature("Brute", 5, 5, "A")
    small = CombatCreature("Scout", 2, 2, "A")
    g1 = CombatCreature("Guard1", 2, 2, "B")
    g2 = CombatCreature("Guard2", 2, 2, "B")
    state = GameState(
        players={
            "A": PlayerState(life=20, creatures=[big, small]),
            "B": PlayerState(life=20, creatures=[g1, g2]),
        }
    )
    decide_simple_blocks(game_state=state)
    simple = [blk.blocking for blk in (g1, g2)]

    atk2 = [CombatCreature("Brute", 5, 5, "A"), CombatCreature("Scout", 2, 2, "A")]
    blk2 = [CombatCreature("Guard1", 2, 2, "B"), CombatCreature("Guard2", 2, 2, "B")]
    state2 = GameState(
        players={
            "A": PlayerState(life=20, creatures=atk2),
            "B": PlayerState(life=20, creatures=blk2),
        }
    )
    decide_optimal_blocks(game_state=state2)
    optimal = [blk.blocking for blk in blk2]

    assert [b.name if b else None for b in simple] == ["Scout", None]
    assert [b.name if b else None for b in optimal] == ["Scout", "Scout"]


def test_simple_vs_optimal_poison() -> None:
    """CR 104.3c: A player with ten or more poison counters loses the game."""
    infect = CombatCreature("Carrier", 1, 1, "A", infect=True)
    big = CombatCreature("Brute", 4, 4, "A")
    b1 = CombatCreature("B1", 2, 2, "B")
    b2 = CombatCreature("B2", 2, 2, "B")
    state = GameState(
        players={
            "A": PlayerState(life=20, creatures=[infect, big]),
            "B": PlayerState(life=20, creatures=[b1, b2], poison=8),
        }
    )
    decide_simple_blocks(game_state=state)
    simple = [blk.blocking for blk in (b1, b2)]

    atk2 = [
        CombatCreature("Carrier", 1, 1, "A", infect=True),
        CombatCreature("Brute", 4, 4, "A"),
    ]
    blk2 = [CombatCreature("B1", 2, 2, "B"), CombatCreature("B2", 2, 2, "B")]
    state2 = GameState(
        players={
            "A": PlayerState(life=20, creatures=atk2),
            "B": PlayerState(life=20, creatures=blk2, poison=8),
        }
    )
    decide_optimal_blocks(game_state=state2)
    optimal = [blk.blocking for blk in blk2]

    assert [b.name if b else None for b in simple] == ["Carrier", None]
    assert [b.name if b else None for b in optimal] == ["Carrier", "Carrier"]


def test_simple_vs_optimal_indestructible() -> None:
    """CR 702.12b: Indestructible objects can't be destroyed."""
    titan = CombatCreature("Titan", 8, 8, "A", indestructible=True)
    small = CombatCreature("Warrior", 4, 4, "A")
    g1 = CombatCreature("G1", 4, 4, "B")
    g2 = CombatCreature("G2", 4, 4, "B")
    state = GameState(
        players={
            "A": PlayerState(life=20, creatures=[titan, small]),
            "B": PlayerState(life=20, creatures=[g1, g2]),
        }
    )
    decide_simple_blocks(game_state=state)
    simple = [blk.blocking for blk in (g1, g2)]

    atk2 = [
        CombatCreature("Titan", 8, 8, "A", indestructible=True),
        CombatCreature("Warrior", 4, 4, "A"),
    ]
    blk2 = [CombatCreature("G1", 4, 4, "B"), CombatCreature("G2", 4, 4, "B")]
    state2 = GameState(
        players={
            "A": PlayerState(life=20, creatures=atk2),
            "B": PlayerState(life=20, creatures=blk2),
        }
    )
    decide_optimal_blocks(game_state=state2)
    optimal = [blk.blocking for blk in blk2]

    assert [b.name if b else None for b in simple] == ["Warrior", None]
    assert [b.name if b else None for b in optimal] == ["Warrior", "Warrior"]


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
    decide_simple_blocks(game_state=state)
    assert blk1.blocking is small_atk and blk2.blocking is None

    for atk in (big_atk, small_atk):
        atk.blocked_by.clear()
    blk1.blocking = None
    blk2.blocking = None

    decide_optimal_blocks(game_state=state)
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
    decide_simple_blocks(game_state=state)
    assert blk1.blocking is None and blk2.blocking is None

    for atk in (atk1, atk2):
        atk.blocked_by.clear()
    blk1.blocking = None
    blk2.blocking = None

    decide_optimal_blocks(game_state=state)
    assert blk1.blocking is atk1 and blk2.blocking is atk1
