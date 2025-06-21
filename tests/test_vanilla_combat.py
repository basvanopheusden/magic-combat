from pathlib import Path
import sys
import pytest

# Ensure the package is importable when running tests from any location
sys.path.append(str(Path(__file__).resolve().parents[1]))

from magic_combat import CombatCreature, CombatSimulator


def setup_vanilla():
    attacker = CombatCreature("Bear", 2, 2, "A")
    blocker = CombatCreature("Piker", 3, 1, "B")
    attacker.blocked_by.append(blocker)
    blocker.blocking = attacker
    return attacker, blocker


def test_simple_trade():
    """CR 510.2: combat damage is dealt simultaneously."""
    a, b = setup_vanilla()
    sim = CombatSimulator([a], [b])
    result = sim.simulate()
    assert a in result.creatures_destroyed
    assert b in result.creatures_destroyed


def test_double_block_not_supported():
    """CR 509.1h: each creature can block a single attacker."""
    a = CombatCreature("Bear", 2, 2, "A")
    b1 = CombatCreature("Goblin", 1, 1, "B")
    b2 = CombatCreature("Goblin2", 1, 1, "B")
    a.blocked_by.extend([b1, b2])
    b1.blocking = a
    b2.blocking = a
    sim = CombatSimulator([a], [b1, b2])
    with pytest.raises(ValueError):
        sim.simulate()

