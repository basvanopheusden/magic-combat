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
