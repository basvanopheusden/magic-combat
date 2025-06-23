import pytest
from magic_combat import (
    CombatCreature,
    CombatSimulator,
    GameState,
    PlayerState,
    DEFAULT_STARTING_LIFE,
)
from tests.conftest import link_block


def test_infect_kills_creature_with_counters():
    """CR 702.90b: Infect damage to a creature is dealt as -1/-1 counters."""
    atk = CombatCreature("Toxic Bear", 3, 3, "A", infect=True)
    blk = CombatCreature("Wall", 2, 2, "B")
    link_block(atk, blk)
    sim = CombatSimulator([atk], [blk])
    result = sim.simulate()
    assert blk.minus1_counters == 2
    assert blk in result.creatures_destroyed


def test_infect_lifelink_vs_blocker():
    """CR 702.90b & 702.15a: Infect gives counters and lifelink gains that much life."""
    atk = CombatCreature("Toxic Cleric", 2, 2, "A", infect=True, lifelink=True)
    blk = CombatCreature("Bear", 2, 2, "B")
    link_block(atk, blk)
    state = GameState(players={"A": PlayerState(life=10, creatures=[atk]), "B": PlayerState(life=DEFAULT_STARTING_LIFE, creatures=[blk])})
    sim = CombatSimulator([atk], [blk], game_state=state)
    result = sim.simulate()
    assert blk.minus1_counters == 2
    assert result.lifegain["A"] == 2
    assert state.players["A"].life == 12


def test_infect_first_strike_kills_before_damage():
    """CR 702.7b & 702.90b: First strike infect kills the blocker before it can deal damage."""
    atk = CombatCreature("Toxic Fencer", 2, 2, "A", infect=True, first_strike=True)
    blk = CombatCreature("Bear", 2, 2, "B")
    link_block(atk, blk)
    sim = CombatSimulator([atk], [blk])
    result = sim.simulate()
    assert blk.minus1_counters == 2
    assert blk in result.creatures_destroyed
    assert atk not in result.creatures_destroyed


def test_double_strike_infect_poison_twice():
    """CR 702.4b & 702.90b: Double strike applies infect damage in both combat steps."""
    atk = CombatCreature("Toxic Duelist", 1, 1, "A", infect=True, double_strike=True)
    defender = CombatCreature("Dummy", 0, 1, "B")
    sim = CombatSimulator([atk], [defender])
    result = sim.simulate()
    assert result.poison_counters["B"] == 2
    assert result.damage_to_players.get("B", 0) == 0


def test_trample_infect_multiple_blockers():
    """CR 702.19b & 702.90b: Excess infect damage with trample becomes poison counters."""
    atk = CombatCreature("Toxic Beast", 3, 3, "A", trample=True, infect=True)
    b1 = CombatCreature("Goblin1", 1, 1, "B")
    b2 = CombatCreature("Goblin2", 1, 1, "B")
    link_block(atk, b1, b2)
    sim = CombatSimulator([atk], [b1, b2])
    result = sim.simulate()
    assert b1.minus1_counters == 1
    assert b2.minus1_counters == 1
    assert result.poison_counters["B"] == 1
    assert b1 in result.creatures_destroyed and b2 in result.creatures_destroyed


def test_infect_prevents_persist_return():
    """CR 702.90b & 702.77a: Infect counters stop a persist creature from returning."""
    atk = CombatCreature("Infecting Knight", 2, 2, "A", infect=True)
    blk = CombatCreature("Everlasting", 2, 2, "B", persist=True)
    link_block(atk, blk)
    sim = CombatSimulator([atk], [blk])
    result = sim.simulate()
    assert blk in result.creatures_destroyed
    assert blk.minus1_counters == 2


def test_infect_kills_undying_but_it_returns():
    """CR 702.92a & 702.90b: Undying brings back a creature even if infect dealt the damage."""
    atk = CombatCreature("Toxic Slayer", 2, 2, "A", infect=True)
    blk = CombatCreature("Spirit", 2, 2, "B", undying=True)
    link_block(atk, blk)
    sim = CombatSimulator([atk], [blk])
    result = sim.simulate()
    assert blk not in result.creatures_destroyed
    assert blk.plus1_counters == 1
    assert blk.minus1_counters == 0


def test_infect_and_toxic_stack_poison():
    """CR 702.90b & 702.180a: Infect and toxic both add poison counters."""
    atk = CombatCreature("Super Toxic", 1, 1, "A", infect=True, toxic=2)
    defender = CombatCreature("Dummy", 0, 1, "B")
    sim = CombatSimulator([atk], [defender])
    result = sim.simulate()
    assert result.poison_counters["B"] == 3


def test_lifelink_infect_vs_creature():
    """CR 702.15a & 702.90b: Lifelink gains life even when infect damages a creature."""
    atk = CombatCreature("Toxic Healer", 3, 3, "A", infect=True, lifelink=True)
    blk = CombatCreature("Bear", 3, 3, "B")
    link_block(atk, blk)
    state = GameState(players={"A": PlayerState(life=10, creatures=[atk]), "B": PlayerState(life=DEFAULT_STARTING_LIFE, creatures=[blk])})
    sim = CombatSimulator([atk], [blk], game_state=state)
    result = sim.simulate()
    assert result.lifegain["A"] == 3
    assert blk.minus1_counters == 3
    assert state.players["A"].life == 13


def test_infect_with_afflict_still_causes_life_loss():
    """CR 702.131a & 702.90b: Afflict causes life loss even when an infect creature is blocked."""
    atk = CombatCreature("Tormentor", 2, 2, "A", infect=True, afflict=1)
    blk = CombatCreature("Guard", 2, 2, "B")
    link_block(atk, blk)
    state = GameState(players={"A": PlayerState(life=DEFAULT_STARTING_LIFE, creatures=[atk]), "B": PlayerState(life=DEFAULT_STARTING_LIFE, creatures=[blk])})
    sim = CombatSimulator([atk], [blk], game_state=state)
    result = sim.simulate()
    assert state.players["B"].life == 19
    assert result.poison_counters.get("B", 0) == 0
    assert blk.minus1_counters == 2
