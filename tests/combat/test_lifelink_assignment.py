import pytest
from magic_combat import CombatCreature, CombatSimulator
from tests.conftest import link_block


def test_first_strike_prefers_killing_lifelink():
    """CR 702.7b & 702.15a: First strike can kill a lifelink creature before it deals damage, preventing life gain."""
    atk = CombatCreature("Fencer", 2, 2, "A", first_strike=True)
    link = CombatCreature("Healer", 2, 2, "B", lifelink=True)
    other = CombatCreature("Watcher", 2, 2, "B", vigilance=True)
    # Put lifelink second to ensure ordering matters
    atk.blocked_by.extend([other, link])
    other.blocking = atk
    link.blocking = atk
    sim = CombatSimulator([atk], [other, link])
    result = sim.simulate()
    dead = {c.name for c in result.creatures_destroyed}
    assert dead == {"Fencer", "Healer"}
    assert result.lifegain.get("B", 0) == 0


def test_first_strike_kills_lifelink_even_when_first():
    """CR 702.7b & 702.15a: Ordering shouldn't matter when choosing to kill the lifelink blocker."""
    atk = CombatCreature("Duelist", 2, 2, "A", first_strike=True)
    link = CombatCreature("Cleric", 2, 2, "B", lifelink=True)
    other = CombatCreature("Guard", 2, 2, "B", vigilance=True)
    link_block(atk, link, other)
    sim = CombatSimulator([atk], [link, other])
    result = sim.simulate()
    dead = {c.name for c in result.creatures_destroyed}
    assert dead == {"Duelist", "Cleric"}
    assert result.lifegain.get("B", 0) == 0


def test_double_strike_also_prefers_lifelink():
    """CR 702.4b & 702.15a: Double strike assigns first damage to the lifelink blocker to prevent life gain."""
    atk = CombatCreature("Blademaster", 3, 3, "A", double_strike=True)
    link = CombatCreature("Priest", 2, 2, "B", lifelink=True)
    other = CombatCreature("Soldier", 2, 2, "B")
    atk.blocked_by.extend([other, link])
    other.blocking = atk
    link.blocking = atk
    sim = CombatSimulator([atk], [other, link])
    result = sim.simulate()
    dead = {c.name for c in result.creatures_destroyed}
    assert "Priest" in dead
    assert result.lifegain.get("B", 0) == 0


def test_first_strike_cannot_kill_big_lifelink():
    """CR 702.7b & 702.15a: If lethal damage can't be assigned to the lifelink creature, it survives to gain life."""
    atk = CombatCreature("Fencer", 2, 2, "A", first_strike=True)
    link = CombatCreature("Angel", 3, 3, "B", lifelink=True)
    other = CombatCreature("Guard", 2, 2, "B")
    atk.blocked_by.extend([other, link])
    other.blocking = atk
    link.blocking = atk
    sim = CombatSimulator([atk], [other, link])
    result = sim.simulate()
    assert result.lifegain.get("B", 0) == 3
    dead = {c.name for c in result.creatures_destroyed}
    assert dead == {"Fencer", "Guard"}


def test_lifelink_with_first_strike_still_gains_life():
    """CR 702.7b & 702.15a: A lifelink creature with first strike deals damage in the first-strike step and gains life."""
    atk = CombatCreature("Swordsman", 2, 2, "A", first_strike=True)
    link = CombatCreature("Paladin", 2, 2, "B", first_strike=True, lifelink=True)
    link_block(atk, link)
    sim = CombatSimulator([atk], [link])
    result = sim.simulate()
    assert result.lifegain["B"] == 2
    dead = {c.name for c in result.creatures_destroyed}
    assert dead == {"Swordsman", "Paladin"}


def test_normal_combat_lifelink_gains_life():
    """CR 702.15a: Without first strike, both creatures deal damage simultaneously and lifelink grants life."""
    atk = CombatCreature("Bear", 2, 2, "A")
    link = CombatCreature("Priest", 2, 2, "B", lifelink=True)
    link_block(atk, link)
    sim = CombatSimulator([atk], [link])
    result = sim.simulate()
    assert result.lifegain["B"] == 2
    dead = {c.name for c in result.creatures_destroyed}
    assert dead == {"Bear", "Priest"}
