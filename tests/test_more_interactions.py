import pytest
from pathlib import Path
import sys

# Ensure the package is importable when running tests from any location
sys.path.append(str(Path(__file__).resolve().parents[1]))

from magic_combat import CombatCreature, CombatSimulator


def test_fear_and_skulk_interaction():
    """CR 702.36b & 702.121a: Fear limits blockers to artifact or black creatures, and skulk disallows those with greater power."""
    attacker = CombatCreature("Sneaky Horror", 2, 2, "A", fear=True, skulk=True)
    big_artifact = CombatCreature("Golem", 3, 3, "B", artifact=True)
    attacker.blocked_by.append(big_artifact)
    big_artifact.blocking = attacker
    sim = CombatSimulator([attacker], [big_artifact])
    with pytest.raises(ValueError):
        sim.validate_blocking()

    attacker.blocked_by.clear()
    small_artifact = CombatCreature("Servo", 1, 1, "B", artifact=True)
    attacker.blocked_by.append(small_artifact)
    small_artifact.blocking = attacker
    sim = CombatSimulator([attacker], [small_artifact])
    sim.validate_blocking()


def test_flanking_vs_flanking_blocker():
    """CR 702.25a: Flanking gives -1/-1 only to blocking creatures without flanking."""
    attacker = CombatCreature("Veteran", 2, 2, "A", flanking=1)
    blocker = CombatCreature("Opposing Knight", 2, 2, "B", flanking=1)
    attacker.blocked_by.append(blocker)
    blocker.blocking = attacker
    sim = CombatSimulator([attacker], [blocker])
    result = sim.simulate()
    assert attacker in result.creatures_destroyed
    assert blocker in result.creatures_destroyed
