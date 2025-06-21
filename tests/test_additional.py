from pathlib import Path
import sys
import pytest

# Ensure the package is importable when running tests from any location
sys.path.append(str(Path(__file__).resolve().parents[1]))

from magic_combat import CombatCreature, CombatSimulator, DamageAssignmentStrategy


def test_bad_power_init():
    """CR 107.1: game numbers can't be negative."""
    with pytest.raises(ValueError):
        CombatCreature(name="Zero", power=-1, toughness=1, controller="A")


def test_bad_toughness_init():
    """CR 107.1: game numbers can't be negative."""
    with pytest.raises(ValueError):
        CombatCreature(name="Zero", power=1, toughness=0, controller="A")


def test_bad_damage_marked_init():
    """CR 107.1: game numbers can't be negative."""
    with pytest.raises(ValueError):
        CombatCreature(name="Zero", power=1, toughness=1, controller="A", damage_marked=-1)


def test_effective_stats_with_counters():
    """CR 121.5: +1/+1 and -1/-1 counters cancel each other out."""
    c = CombatCreature(name="Mod", power=2, toughness=2, controller="A", _plus1_counters=3, _minus1_counters=2)
    assert c.effective_power() == 3
    assert c.effective_toughness() == 3


def test_string_representation():
    """CR 110.6: power and toughness are written as 'X/Y'."""
    c = CombatCreature(name="Bear", power=2, toughness=2, controller="A")
    assert str(c) == "Bear (2/2)"


def test_protection_check():
    """CR 702.16b: Protection prevents damage from sources of the stated quality."""
    c = CombatCreature(name="Knight", power=2, toughness=2, controller="A", protection_colors={"red"})
    assert c.has_protection_from("red")
    assert not c.has_protection_from("green")


def test_property_setters():
    """CR 107.1: counters can't be negative."""
    c = CombatCreature(name="Growth", power=1, toughness=1, controller="A")
    c.plus1_counters = 2
    c.minus1_counters = 1
    assert c.plus1_counters == 2
    assert c.minus1_counters == 1


def test_is_destroyed_by_damage():
    """CR 704.5g: a creature with lethal damage is destroyed."""
    c = CombatCreature(name="Weak", power=1, toughness=1, controller="A")
    c.damage_marked = 1
    assert c.is_destroyed_by_damage()


def test_base_strategy_returns_blockers():
    """CR 510.2: combat damage is dealt simultaneously to all blockers."""
    a = CombatCreature("Bear", 2, 2, "A")
    b1 = CombatCreature("B1", 1, 1, "B")
    strat = DamageAssignmentStrategy()
    ordered = strat.order_blockers(a, [b1])
    assert ordered == [b1]


def test_unblocked_attacker_no_defenders():
    """CR 510.1c: unblocked attackers damage the player they're attacking."""
    a = CombatCreature("Lone", 3, 3, "A")
    sim = CombatSimulator([a], [])
    result = sim.simulate()
    assert result.damage_to_players["defender"] == 3


def test_validate_blocking_unknown_attacker():
    """CR 509.1a: the defending player chooses which attackers blockers block."""
    a = CombatCreature("A", 2, 2, "A")
    b = CombatCreature("B", 1, 1, "B")
    other = CombatCreature("Other", 2, 2, "A")
    b.blocking = other
    sim = CombatSimulator([a], [b])
    with pytest.raises(ValueError):
        sim.validate_blocking()


def test_validate_blocking_inconsistent():
    """CR 509.1a: blockers must actually block the attacker they're assigned to."""
    a = CombatCreature("A", 2, 2, "A")
    b = CombatCreature("B", 1, 1, "B")
    a.blocked_by.append(b)
    sim = CombatSimulator([a], [b])
    with pytest.raises(ValueError):
        sim.validate_blocking()
