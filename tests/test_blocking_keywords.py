import pytest
from pathlib import Path
import sys

# Ensure the package is importable when running tests from any location
sys.path.append(str(Path(__file__).resolve().parents[1]))

from magic_combat import CombatCreature, CombatSimulator


def test_flying_requires_flying_or_reach():
    """CR 702.9b: A creature with flying can be blocked only by creatures with flying or reach."""
    attacker = CombatCreature("Hawk", 1, 1, "A", flying=True)
    blocker = CombatCreature("Bear", 2, 2, "B")
    attacker.blocked_by.append(blocker)
    blocker.blocking = attacker
    sim = CombatSimulator([attacker], [blocker])
    with pytest.raises(ValueError):
        sim.validate_blocking()


def test_reach_allows_blocking_flying():
    """CR 702.9c: Creatures with reach can block creatures with flying."""
    attacker = CombatCreature("Hawk", 1, 1, "A", flying=True)
    blocker = CombatCreature("Spider", 1, 2, "B", reach=True)
    attacker.blocked_by.append(blocker)
    blocker.blocking = attacker
    sim = CombatSimulator([attacker], [blocker])
    # Should not raise
    sim.validate_blocking()


def test_menace_requires_two_blockers():
    """CR 702.110b: A creature with menace can't be blocked except by two or more creatures."""
    attacker = CombatCreature("Ogre", 3, 3, "A", menace=True)
    blocker = CombatCreature("Goblin", 1, 1, "B")
    attacker.blocked_by.append(blocker)
    blocker.blocking = attacker
    sim = CombatSimulator([attacker], [blocker])
    with pytest.raises(ValueError):
        sim.validate_blocking()


def test_menace_with_two_blockers_allowed():
    """CR 702.110b allows blocking a menace creature with two blockers."""
    attacker = CombatCreature("Ogre", 3, 3, "A", menace=True)
    b1 = CombatCreature("Goblin1", 1, 1, "B")
    b2 = CombatCreature("Goblin2", 1, 1, "B")
    attacker.blocked_by.extend([b1, b2])
    b1.blocking = attacker
    b2.blocking = attacker
    sim = CombatSimulator([attacker], [b1, b2])
    sim.validate_blocking()


def test_fear_blocking():
    """CR 702.36b: Fear allows blocking only by artifact or black creatures."""
    attacker = CombatCreature("Nightmare", 2, 2, "A", fear=True)
    blocker = CombatCreature("Knight", 2, 2, "B", colors={"white"})
    attacker.blocked_by.append(blocker)
    blocker.blocking = attacker
    sim = CombatSimulator([attacker], [blocker])
    with pytest.raises(ValueError):
        sim.validate_blocking()

    black_blocker = CombatCreature("Shade", 1, 1, "B", colors={"black"})
    attacker.blocked_by = [black_blocker]
    black_blocker.blocking = attacker
    sim = CombatSimulator([attacker], [black_blocker])
    sim.validate_blocking()


def test_protection_prevents_blocking():
    """CR 702.16b: Protection from a color means it can't be blocked by creatures of that color."""
    attacker = CombatCreature("Paladin", 2, 2, "A", protection_colors={"red"})
    blocker = CombatCreature("Orc", 2, 2, "B", colors={"red"})
    attacker.blocked_by.append(blocker)
    blocker.blocking = attacker
    sim = CombatSimulator([attacker], [blocker])
    with pytest.raises(ValueError):
        sim.validate_blocking()
