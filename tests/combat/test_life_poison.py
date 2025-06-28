import pytest

from magic_combat import (DEFAULT_STARTING_LIFE, POISON_LOSS_THRESHOLD,
                          CombatCreature, CombatSimulator, GameState,
                          PlayerState, has_player_lost)
from tests.conftest import link_block


def test_infect_lifelink_poison_lethal():
    """CR 702.90b & 104.3c: Infect damage gives poison counters and a player with ten or more poison counters loses."""
    atk = CombatCreature("Infect Angel", 2, 2, "A", infect=True, lifelink=True)
    defender = CombatCreature("Dummy", 0, 1, "B")
    state = GameState(
        players={
            "A": PlayerState(life=DEFAULT_STARTING_LIFE, creatures=[atk]),
            "B": PlayerState(
                life=DEFAULT_STARTING_LIFE, creatures=[defender], poison=8
            ),
        }
    )
    sim = CombatSimulator([atk], [defender], game_state=state)
    result = sim.simulate()
    assert state.players["B"].life == 20
    assert state.players["B"].poison == POISON_LOSS_THRESHOLD
    assert result.lifegain["A"] == 2
    assert has_player_lost(state, "B")
    assert "B" in sim.players_lost


def test_double_strike_lifelink_player_lethal():
    """CR 702.4b & 702.15a & 104.3a: Double strike causes two instances of damage and lifelink gains that much life; a player with 0 or less life loses."""
    atk = CombatCreature("Champion", 2, 2, "A", double_strike=True, lifelink=True)
    defender = CombatCreature("Dummy", 0, 1, "B")
    state = GameState(
        players={
            "A": PlayerState(life=DEFAULT_STARTING_LIFE, creatures=[atk]),
            "B": PlayerState(life=3, creatures=[defender]),
        }
    )
    sim = CombatSimulator([atk], [defender], game_state=state)
    result = sim.simulate()
    assert state.players["B"].life == -1
    assert result.lifegain["A"] == 4
    assert has_player_lost(state, "B")
    assert "B" in sim.players_lost


def test_infect_double_strike_lifelink_poison_lethal():
    """CR 702.4b, 702.15a & 702.90b: Double strike with infect deals damage twice as poison counters and lifelink gains that much life."""
    atk = CombatCreature(
        "Toxic Duelist", 1, 1, "A", infect=True, lifelink=True, double_strike=True
    )
    defender = CombatCreature("Dummy", 0, 1, "B")
    state = GameState(
        players={
            "A": PlayerState(life=DEFAULT_STARTING_LIFE, creatures=[atk]),
            "B": PlayerState(
                life=DEFAULT_STARTING_LIFE, creatures=[defender], poison=9
            ),
        }
    )
    sim = CombatSimulator([atk], [defender], game_state=state)
    result = sim.simulate()
    assert state.players["B"].poison == 11
    assert result.lifegain["A"] == 2
    assert has_player_lost(state, "B")
    assert "B" in sim.players_lost


def test_lifelink_killed_before_dealing_damage():
    """CR 702.7b & 702.15a: A lifelink creature killed by first strike deals no damage and grants no life."""
    atk = CombatCreature("Cleric", 2, 2, "A", lifelink=True)
    blk = CombatCreature("First Striker", 2, 2, "B", first_strike=True)
    link_block(atk, blk)
    sim = CombatSimulator([atk], [blk])
    result = sim.simulate()
    assert result.lifegain.get("A", 0) == 0
    assert atk in result.creatures_destroyed
    assert blk not in result.creatures_destroyed


def test_trample_deathtouch_lifelink_lethal():
    """CR 702.2b, 702.19b & 702.15a: With trample and deathtouch only 1 damage must be assigned to the blocker; the rest hits the player and lifelink gains total damage."""
    atk = CombatCreature(
        "Charging Snake", 3, 3, "A", trample=True, deathtouch=True, lifelink=True
    )
    blk = CombatCreature("Bear", 2, 2, "B")
    link_block(atk, blk)
    state = GameState(
        players={
            "A": PlayerState(life=DEFAULT_STARTING_LIFE, creatures=[atk]),
            "B": PlayerState(life=2, creatures=[blk]),
        }
    )
    sim = CombatSimulator([atk], [blk], game_state=state)
    result = sim.simulate()
    assert state.players["B"].life == 0
    assert result.lifegain["A"] == 3
    assert has_player_lost(state, "B")
    assert "B" in sim.players_lost
