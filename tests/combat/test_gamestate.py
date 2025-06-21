import pytest
from magic_combat import (
    CombatCreature,
    CombatSimulator,
    GameState,
    PlayerState,
    DEFAULT_STARTING_LIFE,
    has_player_lost,
)
from tests.conftest import link_block


def test_player_loses_when_life_zero():
    """CR 104.3a: A player with 0 or less life loses the game."""
    atk = CombatCreature("Bear", 2, 2, "A")
    defender = CombatCreature("Dummy", 0, 1, "B")
    state = GameState(
        players={
            "A": PlayerState(life=DEFAULT_STARTING_LIFE, creatures=[atk]),
            "B": PlayerState(life=2, creatures=[defender]),
        }
    )
    sim = CombatSimulator([atk], [defender], game_state=state)
    sim.simulate()
    assert state.players["B"].life == 0
    assert has_player_lost(state, "B")
    assert "B" in sim.players_lost


def test_player_loses_from_poison():
    """CR 104.3c: A player with ten or more poison counters loses the game."""
    atk = CombatCreature("Infector", 2, 2, "A", infect=True)
    defender = CombatCreature("Dummy", 0, 1, "B")
    state = GameState(
        players={
            "A": PlayerState(life=DEFAULT_STARTING_LIFE, creatures=[atk]),
            "B": PlayerState(life=DEFAULT_STARTING_LIFE, creatures=[defender], poison=9),
        }
    )
    sim = CombatSimulator([atk], [defender], game_state=state)
    sim.simulate()
    assert state.players["B"].poison == 11
    assert has_player_lost(state, "B")
    assert "B" in sim.players_lost


def test_trample_infect_assigns_excess_poison():
    """CR 702.19b & 702.90b: Trample with infect deals excess damage as poison counters."""
    atk = CombatCreature("Toxic Beast", 4, 4, "A", trample=True, infect=True)
    blk = CombatCreature("Chump", 1, 1, "B")
    link_block(atk, blk)
    state = GameState(
        players={
            "A": PlayerState(life=DEFAULT_STARTING_LIFE, creatures=[atk]),
            "B": PlayerState(life=DEFAULT_STARTING_LIFE, creatures=[blk]),
        }
    )
    sim = CombatSimulator([atk], [blk], game_state=state)
    result = sim.simulate()
    assert blk.minus1_counters == 1
    assert state.players["B"].life == 20
    assert state.players["B"].poison == 3
    assert result.poison_counters["B"] == 3


def test_infect_with_lifelink_grants_life():
    """CR 702.90b & 702.15a: Infect damage gives poison counters but still triggers lifelink."""
    atk = CombatCreature("Toxic Healer", 2, 2, "A", infect=True, lifelink=True)
    defender = CombatCreature("Dummy", 0, 1, "B")
    state = GameState(
        players={
            "A": PlayerState(life=10, creatures=[atk]),
            "B": PlayerState(life=DEFAULT_STARTING_LIFE, creatures=[defender]),
        }
    )
    sim = CombatSimulator([atk], [defender], game_state=state)
    result = sim.simulate()
    assert result.poison_counters["B"] == 2
    assert result.damage_to_players.get("B", 0) == 0
    assert result.lifegain["A"] == 2
    assert state.players["A"].life == 12


def test_wither_and_lifelink_vs_creature():
    """CR 702.90a & 702.15a: Wither deals -1/-1 counters but counts as damage for lifelink."""
    atk = CombatCreature("Pain Giver", 3, 3, "A", wither=True, lifelink=True)
    blk = CombatCreature("Target", 2, 2, "B")
    link_block(atk, blk)
    state = GameState(
        players={
            "A": PlayerState(life=DEFAULT_STARTING_LIFE, creatures=[atk]),
            "B": PlayerState(life=DEFAULT_STARTING_LIFE, creatures=[blk]),
        }
    )
    sim = CombatSimulator([atk], [blk], game_state=state)
    result = sim.simulate()
    assert blk.minus1_counters == 2
    assert blk in result.creatures_destroyed
    assert result.lifegain["A"] == 2
    assert state.players["A"].life == 22


def test_deathtouch_trample_hits_player():
    """CR 702.19b & 702.2b: Only 1 damage must be assigned to the blocker before excess hits the player."""
    atk = CombatCreature("Crusher", 4, 4, "A", trample=True, deathtouch=True)
    blk = CombatCreature("Wall", 5, 5, "B")
    link_block(atk, blk)
    state = GameState(
        players={
            "A": PlayerState(life=DEFAULT_STARTING_LIFE, creatures=[atk]),
            "B": PlayerState(life=DEFAULT_STARTING_LIFE, creatures=[blk]),
        }
    )
    sim = CombatSimulator([atk], [blk], game_state=state)
    result = sim.simulate()
    assert result.damage_to_players["B"] == 3
    assert blk.damage_marked == 1
    assert blk in result.creatures_destroyed
    assert state.players["B"].life == 17


def test_double_strike_lifelink_twice():
    """CR 702.4b & 702.15a: Double strike causes lifelink damage in both steps."""
    atk = CombatCreature("Swift Healer", 2, 2, "A", double_strike=True, lifelink=True)
    defender = CombatCreature("Dummy", 0, 1, "B")
    state = GameState(
        players={
            "A": PlayerState(life=10, creatures=[atk]),
            "B": PlayerState(life=DEFAULT_STARTING_LIFE, creatures=[defender]),
        }
    )
    sim = CombatSimulator([atk], [defender], game_state=state)
    result = sim.simulate()
    assert result.damage_to_players["B"] == 4
    assert result.lifegain["A"] == 4
    assert state.players["A"].life == 14


def test_double_strike_infect_can_cause_loss():
    """CR 702.4b & 104.3c: Infect with double strike can give enough poison counters to lose."""
    atk = CombatCreature("Toxic Duelist", 1, 1, "A", infect=True, double_strike=True)
    defender = CombatCreature("Dummy", 0, 1, "B")
    state = GameState(
        players={
            "A": PlayerState(life=DEFAULT_STARTING_LIFE, creatures=[atk]),
            "B": PlayerState(life=DEFAULT_STARTING_LIFE, creatures=[defender], poison=8),
        }
    )
    sim = CombatSimulator([atk], [defender], game_state=state)
    result = sim.simulate()
    assert state.players["B"].poison == 10
    assert has_player_lost(state, "B")
    assert "B" in sim.players_lost
    assert result.poison_counters["B"] == 2
