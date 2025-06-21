import pytest
from magic_combat import (
    CombatCreature,
    CombatSimulator,
    GameState,
    PlayerState,
    has_player_lost,
)


def test_player_loses_when_life_zero():
    """CR 104.3a: A player with 0 or less life loses the game."""
    atk = CombatCreature("Bear", 2, 2, "A")
    defender = CombatCreature("Dummy", 0, 1, "B")
    state = GameState(
        players={
            "A": PlayerState(life=20, creatures=[atk]),
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
            "A": PlayerState(life=20, creatures=[atk]),
            "B": PlayerState(life=20, creatures=[defender], poison=9),
        }
    )
    sim = CombatSimulator([atk], [defender], game_state=state)
    sim.simulate()
    assert state.players["B"].poison == 11
    assert has_player_lost(state, "B")
    assert "B" in sim.players_lost


def test_wither_damage_to_player():
    """CR 702.78b: Wither affects only damage dealt to creatures."""
    atk = CombatCreature("Witherer", 2, 2, "A", wither=True)
    defender = CombatCreature("Dummy", 0, 1, "B")
    state = GameState(
        players={
            "A": PlayerState(life=20, creatures=[atk]),
            "B": PlayerState(life=20, creatures=[defender]),
        }
    )
    sim = CombatSimulator([atk], [defender], game_state=state)
    sim.simulate()
    assert state.players["B"].life == 18
    assert state.players["B"].poison == 0


def test_infect_lifelink_poison_and_lifegain():
    """CR 702.90b & 702.15a: Infect gives poison counters and lifelink gains life."""
    atk = CombatCreature("Infector", 2, 2, "A", infect=True, lifelink=True)
    defender = CombatCreature("Dummy", 0, 1, "B")
    state = GameState(
        players={
            "A": PlayerState(life=10, creatures=[atk]),
            "B": PlayerState(life=20, creatures=[defender]),
        }
    )
    sim = CombatSimulator([atk], [defender], game_state=state)
    result = sim.simulate()
    assert state.players["B"].life == 20
    assert state.players["B"].poison == 2
    assert state.players["A"].life == 12
    assert result.lifegain["A"] == 2


def test_trample_deathtouch_excess_damage():
    """CR 702.19b & 702.2b: Deathtouch reduces lethal damage before trampling to the player."""
    atk = CombatCreature("Beast", 2, 2, "A", trample=True, deathtouch=True)
    blk = CombatCreature("Guard", 2, 2, "B")
    atk.blocked_by.append(blk)
    blk.blocking = atk
    state = GameState(
        players={
            "A": PlayerState(life=20, creatures=[atk]),
            "B": PlayerState(life=20, creatures=[blk]),
        }
    )
    sim = CombatSimulator([atk], [blk], game_state=state)
    result = sim.simulate()
    assert state.players["B"].life == 19
    assert blk in result.creatures_destroyed


def test_unblocked_double_strike_player_loss():
    """CR 702.4b & 104.3a: First-strike damage can cause a player to lose before the normal step."""
    atk = CombatCreature("Striker", 1, 1, "A", double_strike=True)
    defender = CombatCreature("Dummy", 0, 1, "B")
    state = GameState(
        players={
            "A": PlayerState(life=20, creatures=[atk]),
            "B": PlayerState(life=1, creatures=[defender]),
        }
    )
    sim = CombatSimulator([atk], [defender], game_state=state)
    sim.simulate()
    assert state.players["B"].life <= 0
    assert "B" in sim.players_lost


def test_infect_double_strike_player_loss():
    """CR 702.4b & 702.90b & 104.3c: Infect double strike can defeat a poisoned player during first strike."""
    atk = CombatCreature("InfectDS", 1, 1, "A", infect=True, double_strike=True)
    defender = CombatCreature("Dummy", 0, 1, "B")
    state = GameState(
        players={
            "A": PlayerState(life=20, creatures=[atk]),
            "B": PlayerState(life=20, creatures=[defender], poison=9),
        }
    )
    sim = CombatSimulator([atk], [defender], game_state=state)
    sim.simulate()
    assert state.players["B"].poison == 11
    assert "B" in sim.players_lost


def test_lifelink_double_strike_gains_twice():
    """CR 702.4b & 702.15a: Double strike with lifelink gains life twice."""
    atk = CombatCreature("Duelist", 1, 1, "A", double_strike=True, lifelink=True)
    defender = CombatCreature("Dummy", 0, 1, "B")
    state = GameState(
        players={
            "A": PlayerState(life=10, creatures=[atk]),
            "B": PlayerState(life=20, creatures=[defender]),
        }
    )
    sim = CombatSimulator([atk], [defender], game_state=state)
    result = sim.simulate()
    assert state.players["A"].life == 12
    assert state.players["B"].life == 18
    assert result.lifegain["A"] == 2
