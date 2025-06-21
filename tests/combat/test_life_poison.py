import pytest

from magic_combat import (
    CombatCreature,
    CombatSimulator,
    GameState,
    PlayerState,
    has_player_lost,
)


def test_trample_lifelink_hits_player_and_gains_life():
    """CR 702.19b & 702.15a: Trample lets excess damage hit the player and lifelink causes its controller to gain that much life."""
    atk = CombatCreature("Rhino", 4, 4, "A", trample=True, lifelink=True)
    blk = CombatCreature("Wall", 0, 3, "B")
    atk.blocked_by.append(blk)
    blk.blocking = atk
    state = GameState(players={"A": PlayerState(20, [atk]), "B": PlayerState(20, [blk])})
    sim = CombatSimulator([atk], [blk], game_state=state)
    result = sim.simulate()
    assert result.damage_to_players["B"] == 1
    assert result.lifegain["A"] == 4
    assert blk in result.creatures_destroyed
    assert state.players["B"].life == 19


def test_infect_lifelink_causes_poison_and_life_gain():
    """CR 702.90b & 702.15a: Damage from infect gives poison counters but lifelink still grants life."""
    atk = CombatCreature("Plague", 2, 2, "A", infect=True, lifelink=True)
    defender = CombatCreature("Dummy", 0, 1, "B")
    state = GameState(players={"A": PlayerState(20, [atk]), "B": PlayerState(20, [defender], poison=9)})
    sim = CombatSimulator([atk], [defender], game_state=state)
    result = sim.simulate()
    assert result.poison_counters["B"] == 2
    assert result.lifegain["A"] == 2
    assert result.damage_to_players.get("B", 0) == 0
    assert state.players["B"].poison == 11
    assert has_player_lost(state, "B")
    assert "B" in sim.players_lost


def test_double_strike_lifelink_player_loses_after_damage():
    """CR 702.4b & 702.15a: A double strike creature with lifelink deals damage twice and gains that much life."""
    atk = CombatCreature("Champion", 2, 2, "A", double_strike=True, lifelink=True)
    defender = CombatCreature("Dummy", 0, 1, "B")
    state = GameState(players={"A": PlayerState(20, [atk]), "B": PlayerState(3, [defender])})
    sim = CombatSimulator([atk], [defender], game_state=state)
    result = sim.simulate()
    assert result.damage_to_players["B"] == 4
    assert result.lifegain["A"] == 4
    assert state.players["B"].life == -1
    assert has_player_lost(state, "B")
    assert "B" in sim.players_lost


def test_trample_deathtouch_lifelink_assignment():
    """CR 702.19b, 702.2b & 702.15a: Deathtouch makes 1 damage lethal per blocker, excess with trample hits the player and lifelink gains that much."""
    atk = CombatCreature("Beast", 3, 3, "A", trample=True, deathtouch=True, lifelink=True)
    b1 = CombatCreature("B1", 2, 2, "B")
    b2 = CombatCreature("B2", 2, 2, "B")
    atk.blocked_by.extend([b1, b2])
    b1.blocking = atk
    b2.blocking = atk
    state = GameState(players={"A": PlayerState(20, [atk]), "B": PlayerState(20, [b1, b2])})
    sim = CombatSimulator([atk], [b1, b2], game_state=state)
    result = sim.simulate()
    assert result.damage_to_players["B"] == 1
    assert result.lifegain["A"] == 3
    assert b1 in result.creatures_destroyed
    assert b2 in result.creatures_destroyed
    assert state.players["B"].life == 19


def test_wither_lifelink_damage_to_player():
    """CR 702.90a & 702.15a: Wither affects only creatures, so damage to a player still causes normal life loss and lifelink."""
    atk = CombatCreature("Blight", 2, 2, "A", wither=True, lifelink=True)
    defender = CombatCreature("Dummy", 0, 1, "B")
    state = GameState(players={"A": PlayerState(20, [atk]), "B": PlayerState(20, [defender])})
    sim = CombatSimulator([atk], [defender], game_state=state)
    result = sim.simulate()
    assert result.damage_to_players["B"] == 2
    assert result.lifegain["A"] == 2
    assert state.players["B"].life == 18
