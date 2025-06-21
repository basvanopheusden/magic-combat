from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parents[1]))

from magic_combat import CombatCreature, CombatSimulator


def test_deathtouch_double_block():
    """CR 702.2b: Any amount of damage from a creature with deathtouch is lethal."""
    attacker = CombatCreature("Assassin", 2, 2, "A", deathtouch=True)
    b1 = CombatCreature("Guard1", 2, 2, "B")
    b2 = CombatCreature("Guard2", 2, 2, "B")
    attacker.blocked_by.extend([b1, b2])
    b1.blocking = attacker
    b2.blocking = attacker
    sim = CombatSimulator([attacker], [b1, b2])
    result = sim.simulate()
    assert b1 in result.creatures_destroyed
    assert b2 in result.creatures_destroyed
    assert attacker in result.creatures_destroyed


def test_deathtouch_prevented_by_first_strike():
    """CR 702.2b & 702.7b: If a deathtouch creature dies before dealing damage, it destroys nothing."""
    attacker = CombatCreature("Asp", 2, 2, "A", deathtouch=True)
    blocker = CombatCreature("Knight", 2, 2, "B", first_strike=True)
    attacker.blocked_by.append(blocker)
    blocker.blocking = attacker
    sim = CombatSimulator([attacker], [blocker])
    result = sim.simulate()
    assert attacker in result.creatures_destroyed
    assert blocker not in result.creatures_destroyed


def test_deathtouch_vs_indestructible():
    """CR 702.2b & 702.12b: Deathtouch doesn't destroy indestructible creatures."""
    attacker = CombatCreature("Snake", 1, 1, "A", deathtouch=True)
    blocker = CombatCreature("Golem", 0, 3, "B", indestructible=True)
    attacker.blocked_by.append(blocker)
    blocker.blocking = attacker
    sim = CombatSimulator([attacker], [blocker])
    result = sim.simulate()
    assert result.creatures_destroyed == []
