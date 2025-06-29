import time

import pytest

from magic_combat import CombatCreature
from magic_combat import CombatSimulator
from magic_combat import GameState
from magic_combat import PlayerState
from magic_combat import decide_simple_blocks


def test_simple_ai_respects_provoke():
    """CR 702.40a: Provoke requires the chosen creature to block if able."""
    atk = CombatCreature("Taunter", 2, 2, "A", provoke=True)
    blk = CombatCreature("Guard", 2, 2, "B")
    state = GameState(
        players={
            "A": PlayerState(life=20, creatures=[atk]),
            "B": PlayerState(life=20, creatures=[blk]),
        }
    )
    decide_simple_blocks([atk], [blk], game_state=state, provoke_map={atk: blk})
    sim = CombatSimulator([atk], [blk], game_state=state, provoke_map={atk: blk})
    sim.validate_blocking()
    assert blk.blocking is atk
    assert atk.blocked_by == [blk]


def test_simple_ai_blocks_best_trade():
    """CR 509.1a: The defending player chooses how creatures block."""
    a1 = CombatCreature("Giant", 4, 4, "A")
    a2 = CombatCreature("Goblin", 2, 2, "A")
    b1 = CombatCreature("Knight", 3, 3, "B")
    b2 = CombatCreature("Soldier", 2, 2, "B")
    state = GameState(
        players={
            "A": PlayerState(life=20, creatures=[a1, a2]),
            "B": PlayerState(life=20, creatures=[b1, b2]),
        }
    )
    decide_simple_blocks([a1, a2], [b1, b2], game_state=state)
    assert b1.blocking is a2
    assert b2.blocking is None


def test_simple_ai_uses_deathtouch_block():
    """CR 702.2b: Any nonzero damage from a creature with deathtouch is lethal."""
    giant = CombatCreature("Giant", 4, 4, "A")
    deathtouch_blk = CombatCreature("Viper", 3, 3, "B", deathtouch=True)
    vanilla_blk = CombatCreature("Bear", 2, 2, "B")
    state = GameState(
        players={
            "A": PlayerState(life=20, creatures=[giant]),
            "B": PlayerState(life=20, creatures=[deathtouch_blk, vanilla_blk]),
        }
    )
    decide_simple_blocks([giant], [deathtouch_blk, vanilla_blk], game_state=state)
    assert deathtouch_blk.blocking is giant
    assert vanilla_blk.blocking is None


def test_simple_ai_blocks_first_striker_with_first_strike():
    """CR 702.7b: Creatures with first strike deal combat damage before creatures without it."""
    fs_atk = CombatCreature("Duelist", 3, 3, "A", first_strike=True)
    vanilla_atk = CombatCreature("Ogre", 4, 4, "A")
    fs_blk = CombatCreature("Knight", 3, 3, "B", first_strike=True)
    other_blk = CombatCreature("Soldier", 3, 3, "B")
    state = GameState(
        players={
            "A": PlayerState(life=20, creatures=[fs_atk, vanilla_atk]),
            "B": PlayerState(life=20, creatures=[fs_blk, other_blk]),
        }
    )
    decide_simple_blocks([fs_atk, vanilla_atk], [fs_blk, other_blk], game_state=state)
    assert fs_blk.blocking is fs_atk


def test_simple_ai_blocks_lifelink_attacker():
    """CR 702.15a: Damage from a creature with lifelink also causes its controller to gain that much life."""
    lifelink_atk = CombatCreature("Priest", 4, 4, "A", lifelink=True)
    vanilla_atk = CombatCreature("Brute", 4, 4, "A")
    blk = CombatCreature("Guardian", 4, 4, "B")
    state = GameState(
        players={
            "A": PlayerState(life=20, creatures=[lifelink_atk, vanilla_atk]),
            "B": PlayerState(life=20, creatures=[blk]),
        }
    )
    decide_simple_blocks([lifelink_atk, vanilla_atk], [blk], game_state=state)
    assert blk.blocking is lifelink_atk


def test_simple_ai_skips_indestructible_bad_trade():
    """CR 702.12b: Indestructible objects can't be destroyed."""
    indestructible_atk = CombatCreature("Titan", 3, 3, "A", indestructible=True)
    blk = CombatCreature("Guard", 3, 3, "B")
    state = GameState(
        players={
            "A": PlayerState(life=20, creatures=[indestructible_atk]),
            "B": PlayerState(life=20, creatures=[blk]),
        }
    )
    decide_simple_blocks([indestructible_atk], [blk], game_state=state)
    assert blk.blocking is None


def test_simple_ai_blocks_flyer_with_reach():
    """CR 702.9b: A creature with reach can block creatures with flying."""
    flyer = CombatCreature("Hawk", 1, 1, "A", flying=True)
    ground = CombatCreature("Squire", 3, 3, "A")
    reacher = CombatCreature("Archer", 2, 2, "B", reach=True)
    other_blk = CombatCreature("Bear", 3, 3, "B")
    state = GameState(
        players={
            "A": PlayerState(life=20, creatures=[flyer, ground]),
            "B": PlayerState(life=20, creatures=[reacher, other_blk]),
        }
    )
    decide_simple_blocks([flyer, ground], [reacher, other_blk], game_state=state)
    assert reacher.blocking is flyer


def test_simple_ai_blocks_double_strike_first():
    """CR 702.4b: Double strike deals damage in both first-strike and regular combat damage steps."""
    ds_atk = CombatCreature("Champion", 4, 4, "A", double_strike=True)
    vanilla_atk = CombatCreature("Ogre", 4, 4, "A")
    blk = CombatCreature("Guardian", 4, 4, "B")
    state = GameState(
        players={
            "A": PlayerState(life=20, creatures=[ds_atk, vanilla_atk]),
            "B": PlayerState(life=20, creatures=[blk]),
        }
    )
    decide_simple_blocks([ds_atk, vanilla_atk], [blk], game_state=state)
    assert blk.blocking is vanilla_atk


def test_simple_ai_trade_instead_of_chump_when_safe():
    """CR 104.3a: A player with 0 or less life loses the game."""
    big_atk = CombatCreature("Giant", 5, 5, "A")
    small_atk = CombatCreature("Scout", 1, 1, "A")
    big_blk = CombatCreature("Ogre", 5, 5, "B")
    chump = CombatCreature("Peasant", 1, 1, "B")
    state = GameState(
        players={
            "A": PlayerState(life=20, creatures=[big_atk, small_atk]),
            "B": PlayerState(life=20, creatures=[big_blk, chump]),
        }
    )
    decide_simple_blocks([big_atk, small_atk], [big_blk, chump], game_state=state)
    assert big_blk.blocking is small_atk
    assert chump.blocking is None


def test_simple_ai_chump_to_prevent_lethal():
    """CR 104.3a: A player with 0 or less life loses the game."""
    big_atk = CombatCreature("Brute", 5, 5, "A")
    small_atk = CombatCreature("Sneak", 2, 2, "A")
    big_blk = CombatCreature("Guardian", 5, 5, "B")
    chump = CombatCreature("Squire", 1, 1, "B")
    state = GameState(
        players={
            "A": PlayerState(life=20, creatures=[big_atk, small_atk]),
            "B": PlayerState(life=2, creatures=[big_blk, chump]),
        }
    )
    decide_simple_blocks([big_atk, small_atk], [big_blk, chump], game_state=state)
    assert big_blk.blocking is small_atk
    assert chump.blocking is big_atk


def test_simple_ai_lets_infect_kill_when_value_trade():
    """CR 104.3c: A player with ten or more poison counters loses the game."""
    infect = CombatCreature("Carrier", 1, 1, "A", infect=True)
    big = CombatCreature("Brute", 3, 3, "A")
    b1 = CombatCreature("Soldier", 2, 2, "B")
    b2 = CombatCreature("Peasant", 1, 1, "B")
    state = GameState(
        players={
            "A": PlayerState(life=20, creatures=[infect, big]),
            "B": PlayerState(life=20, creatures=[b1, b2], poison=9),
        }
    )
    decide_simple_blocks([infect, big], [b1, b2], game_state=state)
    sim = CombatSimulator([infect, big], [b1, b2], game_state=state)
    result = sim.simulate()
    assert b1.blocking is infect
    assert b2.blocking is None
    assert result.players_lost == []


def test_simple_ai_trade_and_die_from_second_attacker():
    """CR 104.3a: A player with 0 or less life loses the game."""
    a1 = CombatCreature("Colossus", 6, 6, "A")
    a2 = CombatCreature("Crusher", 6, 6, "A")
    blk = CombatCreature("Defender", 6, 6, "B")
    state = GameState(
        players={
            "A": PlayerState(life=20, creatures=[a1, a2]),
            "B": PlayerState(life=6, creatures=[blk]),
        }
    )
    decide_simple_blocks([a1, a2], [blk], game_state=state)
    sim = CombatSimulator([a1, a2], [blk], game_state=state)
    result = sim.simulate()
    assert blk.blocking in (a1, a2)
    assert "B" in result.players_lost


def test_simple_ai_block_lifelink_then_chump_other_attacker():
    """CR 702.15a: Lifelink causes its controller to gain that much life."""
    lifelink_atk = CombatCreature("Priest", 4, 4, "A", lifelink=True)
    other_atk = CombatCreature("Brute", 4, 4, "A")
    big_blk = CombatCreature("Guardian", 4, 4, "B")
    chump = CombatCreature("Peasant", 1, 1, "B")
    state = GameState(
        players={
            "A": PlayerState(life=20, creatures=[lifelink_atk, other_atk]),
            "B": PlayerState(life=4, creatures=[big_blk, chump]),
        }
    )
    decide_simple_blocks([lifelink_atk, other_atk], [big_blk, chump], game_state=state)
    assert big_blk.blocking is lifelink_atk
    assert chump.blocking is other_atk


def test_simple_ai_chumps_trample_big_attack():
    """CR 702.19b: Trample damage exceeding lethal damage to blockers is dealt to the player."""
    trampler = CombatCreature("Beast", 6, 6, "A", trample=True)
    other_atk = CombatCreature("Goblin", 2, 2, "A")
    b1 = CombatCreature("Warrior", 2, 2, "B")
    b2 = CombatCreature("Squire", 1, 1, "B")
    state = GameState(
        players={
            "A": PlayerState(life=20, creatures=[trampler, other_atk]),
            "B": PlayerState(life=5, creatures=[b1, b2]),
        }
    )
    decide_simple_blocks([trampler, other_atk], [b1, b2], game_state=state)
    assert b1.blocking is other_atk
    assert b2.blocking is None


def test_simple_ai_first_strike_blocks_deathtouch():
    """CR 702.7b & 702.2b: First strike combat damage is dealt before deathtouch can kill the blocker."""
    dt_atk = CombatCreature("Viper", 2, 2, "A", deathtouch=True)
    fs_blk = CombatCreature("Knight", 2, 2, "B", first_strike=True)
    vanilla_blk = CombatCreature("Soldier", 2, 2, "B")
    state = GameState(
        players={
            "A": PlayerState(life=20, creatures=[dt_atk]),
            "B": PlayerState(life=20, creatures=[fs_blk, vanilla_blk]),
        }
    )
    decide_simple_blocks([dt_atk], [fs_blk, vanilla_blk], game_state=state)
    assert fs_blk.blocking is dt_atk
    assert vanilla_blk.blocking is None


def test_simple_ai_blocks_provoke_target_favorably():
    """CR 702.40a: Provoke forces a creature to block if able."""
    atk1 = CombatCreature("Taunter", 2, 2, "A", provoke=True)
    atk2 = CombatCreature("Brute", 4, 4, "A")
    blk1 = CombatCreature("Guard1", 2, 2, "B")
    blk2 = CombatCreature("Guard2", 4, 4, "B")
    state = GameState(
        players={
            "A": PlayerState(life=20, creatures=[atk1, atk2]),
            "B": PlayerState(life=20, creatures=[blk1, blk2]),
        }
    )
    decide_simple_blocks(
        [atk1, atk2], [blk1, blk2], game_state=state, provoke_map={atk1: blk1}
    )
    assert blk1.blocking is atk1
    assert blk2.blocking is atk2


def test_simple_ai_reacher_blocks_flyer_only():
    """CR 702.9b: Reach allows blocking a creature with flying."""
    flyer = CombatCreature("Angel", 3, 3, "A", flying=True)
    ground = CombatCreature("Footman", 1, 1, "A")
    reacher = CombatCreature("Spider", 2, 4, "B", reach=True)
    state = GameState(
        players={
            "A": PlayerState(life=20, creatures=[flyer, ground]),
            "B": PlayerState(life=20, creatures=[reacher]),
        }
    )
    decide_simple_blocks([flyer, ground], [reacher], game_state=state)
    assert reacher.blocking is ground


def test_simple_ai_iteration_limit_triggers():
    """CR 509.1a: The defending player chooses how creatures block."""
    atk = CombatCreature("Big", 5, 5, "A")
    b1 = CombatCreature("B1", 2, 2, "B")
    b2 = CombatCreature("B2", 2, 2, "B")
    state = GameState(
        players={
            "A": PlayerState(life=20, creatures=[atk]),
            "B": PlayerState(life=20, creatures=[b1, b2]),
        }
    )
    from magic_combat import IterationLimitError

    with pytest.raises(IterationLimitError):
        decide_simple_blocks([atk], [b1, b2], game_state=state, max_iterations=1)


def test_simple_ai_iteration_limit_allows_fast_run():
    """CR 509.1a: The defending player chooses how creatures block."""
    a1 = CombatCreature("A1", 3, 3, "A")
    a2 = CombatCreature("A2", 3, 3, "A")
    b1 = CombatCreature("B1", 3, 3, "B")
    b2 = CombatCreature("B2", 3, 3, "B")
    state = GameState(
        players={
            "A": PlayerState(life=20, creatures=[a1, a2]),
            "B": PlayerState(life=20, creatures=[b1, b2]),
        }
    )
    start = time.perf_counter()
    decide_simple_blocks(
        [a1, a2],
        [b1, b2],
        game_state=state,
        max_iterations=1000,
    )
    duration = time.perf_counter() - start
    assert duration < 2
