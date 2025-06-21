import pytest

from magic_combat import (
    CombatCreature,
    CombatSimulator,
    GameState,
    PlayerState,
    DEFAULT_STARTING_LIFE,
)
from tests.conftest import link_block


def test_zero_power_deathtouch_deals_no_damage():
    """CR 702.2b: Deathtouch only matters if damage is dealt; 0 damage isn't lethal."""
    atk = CombatCreature("Weak Snake", 0, 1, "A", deathtouch=True)
    blk = CombatCreature("Bear", 2, 2, "B")
    link_block(atk, blk)
    sim = CombatSimulator([atk], [blk])
    result = sim.simulate()
    assert blk not in result.creatures_destroyed
    assert atk in result.creatures_destroyed


def test_infect_deathtouch_lethal():
    """CR 702.90b & 702.2b: Infect damage from a deathtouch creature is lethal."""
    atk = CombatCreature("Toxic Snake", 1, 1, "A", infect=True, deathtouch=True)
    blk = CombatCreature("Soldier", 2, 2, "B")
    link_block(atk, blk)
    sim = CombatSimulator([atk], [blk])
    result = sim.simulate()
    assert blk in result.creatures_destroyed
    assert atk in result.creatures_destroyed
    assert blk.minus1_counters == 1


def test_wither_deathtouch_lethal():
    """CR 702.90a & 702.2b: Wither damage from deathtouch still destroys."""
    atk = CombatCreature("Corrosive", 1, 1, "A", wither=True, deathtouch=True)
    blk = CombatCreature("Giant", 4, 4, "B")
    link_block(atk, blk)
    sim = CombatSimulator([atk], [blk])
    result = sim.simulate()
    assert blk in result.creatures_destroyed
    assert atk in result.creatures_destroyed
    assert blk.minus1_counters == 1


def test_deathtouch_lifelink_gain_life():
    """CR 702.15a & 702.2b: Lifelink still gains life when deathtouch kills a creature."""
    atk = CombatCreature("Vampire", 1, 1, "A", deathtouch=True, lifelink=True)
    blk = CombatCreature("Bear", 2, 2, "B")
    link_block(atk, blk)
    state = GameState(players={"A": PlayerState(life=DEFAULT_STARTING_LIFE, creatures=[atk]), "B": PlayerState(life=DEFAULT_STARTING_LIFE, creatures=[blk])})
    sim = CombatSimulator([atk], [blk], game_state=state)
    result = sim.simulate()
    assert blk in result.creatures_destroyed
    assert result.lifegain["A"] == 1
    assert state.players["A"].life == 21


def test_infect_deathtouch_vs_indestructible():
    """CR 702.12b & 702.90b & 702.2b: Indestructible survives but still gets counters."""
    atk = CombatCreature("Toxic Blade", 1, 1, "A", infect=True, deathtouch=True)
    blk = CombatCreature("Guardian", 2, 2, "B", indestructible=True)
    link_block(atk, blk)
    sim = CombatSimulator([atk], [blk])
    result = sim.simulate()
    assert blk not in result.creatures_destroyed
    assert blk.minus1_counters == 1
    assert atk in result.creatures_destroyed


def test_double_strike_vs_deathtouch_blocker():
    """CR 702.4b & 702.2b: Double strike lets an attacker kill a deathtouch blocker before it strikes."""
    atk = CombatCreature("Champion", 2, 2, "A", double_strike=True)
    blk = CombatCreature("Assassin", 2, 2, "B", deathtouch=True)
    link_block(atk, blk)
    sim = CombatSimulator([atk], [blk])
    result = sim.simulate()
    assert blk in result.creatures_destroyed
    assert atk not in result.creatures_destroyed


def test_double_strike_deathtouch_no_player_damage():
    """CR 509.1h & 702.4b: A double strike deathtouch attacker remains blocked and deals no player damage."""
    atk = CombatCreature("Swift Blade", 3, 3, "A", deathtouch=True, double_strike=True)
    blk = CombatCreature("Wall", 1, 4, "B")
    link_block(atk, blk)
    sim = CombatSimulator([atk], [blk])
    result = sim.simulate()
    assert blk in result.creatures_destroyed
    assert result.damage_to_players.get("B", 0) == 0


def test_first_strike_deathtouch_blocker():
    """CR 702.7b & 702.2b: A blocker with first strike and deathtouch kills before normal damage."""
    atk = CombatCreature("Bear", 2, 2, "A")
    blk = CombatCreature("Slayer", 1, 1, "B", deathtouch=True, first_strike=True)
    link_block(atk, blk)
    sim = CombatSimulator([atk], [blk])
    result = sim.simulate()
    assert atk in result.creatures_destroyed
    assert blk not in result.creatures_destroyed


def test_deathtouch_vs_undying_creature_returns():
    """CR 702.92a & 702.2b: Undying brings back a creature destroyed by deathtouch."""
    atk = CombatCreature("Killer", 1, 1, "A", deathtouch=True)
    blk = CombatCreature("Phoenix", 1, 1, "B", undying=True)
    link_block(atk, blk)
    sim = CombatSimulator([atk], [blk])
    result = sim.simulate()
    assert blk not in result.creatures_destroyed
    assert blk.plus1_counters == 1


def test_first_strike_deathtouch_both_sides():
    """CR 702.7b & 702.2b: With first strike and deathtouch on both sides, both die in the first strike step."""
    atk = CombatCreature("Duelist A", 1, 1, "A", deathtouch=True, first_strike=True)
    blk = CombatCreature("Duelist B", 1, 1, "B", deathtouch=True, first_strike=True)
    link_block(atk, blk)
    sim = CombatSimulator([atk], [blk])
    result = sim.simulate()
    assert atk in result.creatures_destroyed
    assert blk in result.creatures_destroyed
