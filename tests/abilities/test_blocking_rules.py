import pytest

from magic_combat import Color
from magic_combat import CombatCreature
from magic_combat import CombatSimulator
from tests.conftest import link_block


def test_flying_requires_flying_or_reach():
    """CR 702.9b: A creature with flying can be blocked only by creatures with flying or reach."""
    attacker = CombatCreature("Hawk", 1, 1, "A", flying=True)
    blocker = CombatCreature("Bear", 2, 2, "B")
    link_block(attacker, blocker)
    sim = CombatSimulator([attacker], [blocker])
    with pytest.raises(ValueError):
        sim.validate_blocking()


def test_reach_allows_blocking_flying():
    """CR 702.9c: Creatures with reach can block creatures with flying."""
    attacker = CombatCreature("Hawk", 1, 1, "A", flying=True)
    blocker = CombatCreature("Spider", 1, 2, "B", reach=True)
    link_block(attacker, blocker)
    sim = CombatSimulator([attacker], [blocker])
    # Should not raise
    sim.validate_blocking()


def test_menace_requires_two_blockers():
    """CR 702.110b: A creature with menace can't be blocked except by two or more creatures."""
    attacker = CombatCreature("Ogre", 3, 3, "A", menace=True)
    blocker = CombatCreature("Goblin", 1, 1, "B")
    link_block(attacker, blocker)
    sim = CombatSimulator([attacker], [blocker])
    with pytest.raises(ValueError):
        sim.validate_blocking()


def test_menace_with_two_blockers_allowed():
    """CR 702.110b allows blocking a menace creature with two blockers."""
    attacker = CombatCreature("Ogre", 3, 3, "A", menace=True)
    b1 = CombatCreature("Goblin1", 1, 1, "B")
    b2 = CombatCreature("Goblin2", 1, 1, "B")
    link_block(attacker, b1, b2)
    sim = CombatSimulator([attacker], [b1, b2])
    sim.validate_blocking()


def test_fear_blocking():
    """CR 702.36b: Fear allows blocking only by artifact or black creatures."""
    attacker = CombatCreature("Nightmare", 2, 2, "A", fear=True)
    blocker = CombatCreature("Knight", 2, 2, "B", colors={Color.WHITE})
    link_block(attacker, blocker)
    sim = CombatSimulator([attacker], [blocker])
    with pytest.raises(ValueError):
        sim.validate_blocking()

    black_blocker = CombatCreature("Shade", 1, 1, "B", colors={Color.BLACK})
    attacker.blocked_by = [black_blocker]
    black_blocker.blocking = attacker
    sim = CombatSimulator([attacker], [black_blocker])
    sim.validate_blocking()


def test_protection_prevents_blocking():
    """CR 702.16b: Protection from a color means it can't be blocked by creatures of that color."""
    attacker = CombatCreature("Paladin", 2, 2, "A", protection_colors={Color.RED})
    blocker = CombatCreature("Orc", 2, 2, "B", colors={Color.RED})
    link_block(attacker, blocker)
    sim = CombatSimulator([attacker], [blocker])
    with pytest.raises(ValueError):
        sim.validate_blocking()


def test_shadow_requires_shadow_blocker():
    """CR 702.27b: A creature with shadow can be blocked only by creatures with shadow."""
    attacker = CombatCreature("Shade", 1, 1, "A", shadow=True)
    blocker = CombatCreature("Bear", 2, 2, "B")
    link_block(attacker, blocker)
    sim = CombatSimulator([attacker], [blocker])
    with pytest.raises(ValueError):
        sim.validate_blocking()


def test_unblockable_cannot_be_blocked():
    """CR 509.1b: An unblockable creature can't be legally blocked."""
    attacker = CombatCreature("Sneak", 2, 2, "A", unblockable=True)
    blocker = CombatCreature("Guard", 2, 2, "B")
    link_block(attacker, blocker)
    sim = CombatSimulator([attacker], [blocker])
    with pytest.raises(ValueError):
        sim.validate_blocking()


def test_blocker_listed_multiple_times():
    """CR 509.1c: A creature can't block the same attacker more than once."""
    attacker = CombatCreature("Ogre", 3, 3, "A")
    blocker = CombatCreature("Soldier", 2, 2, "B")
    attacker.blocked_by.extend([blocker, blocker])
    blocker.blocking = attacker
    sim = CombatSimulator([attacker], [blocker])
    with pytest.raises(ValueError):
        sim.validate_blocking()


def test_flying_menace_requires_two_flying_blockers():
    """CR 702.9b & 702.110b: A creature with flying and menace can't be blocked unless two creatures with flying or reach do so."""
    attacker = CombatCreature("Horror", 3, 3, "A", flying=True, menace=True)
    flyer1 = CombatCreature("Bird1", 1, 1, "B", flying=True)
    link_block(attacker, flyer1)
    sim = CombatSimulator([attacker], [flyer1])
    with pytest.raises(ValueError):
        sim.validate_blocking()
    flyer2 = CombatCreature("Bird2", 1, 1, "B", flying=True)
    link_block(attacker, flyer2)
    sim = CombatSimulator([attacker], [flyer1, flyer2])
    sim.validate_blocking()
