import pytest
from pathlib import Path
import sys

# Ensure the package is importable when running tests from any location
sys.path.append(str(Path(__file__).resolve().parents[1]))

from magic_combat import (
    CombatCreature,
    DamageAssignmentStrategy,
    MostCreaturesKilledStrategy,
    CombatSimulator,
    Color,
)


def test_string_representation():
    """CR 109.2: A creature's power and toughness are written as `X/Y`."""
    creature = CombatCreature(name="Bear", power=2, toughness=2, controller="A")
    assert str(creature) == "Bear (2/2)"


def test_effective_stats_with_counters():
    """CR 122.1a: +1/+1 counters modify a creature's power and toughness."""
    creature = CombatCreature(
        name="Scute", power=1, toughness=1, controller="A", _plus1_counters=2, _minus1_counters=1
    )
    assert creature.effective_power() == 2
    assert creature.effective_toughness() == 2


def test_has_protection_from():
    """CR 702.16b: Protection prevents effects from objects of that color."""
    creature = CombatCreature(
        name="Paladin", power=2, toughness=2, controller="A", protection_colors={Color.BLACK}
    )
    assert creature.has_protection_from(Color.BLACK)
    assert not creature.has_protection_from(Color.RED)


def test_destroyed_by_damage():
    """CR 704.5g: A creature with lethal damage is destroyed."""
    creature = CombatCreature(name="Goblin", power=2, toughness=2, controller="A")
    creature.damage_marked = 3
    assert creature.is_destroyed_by_damage()


def test_damage_assignment_strategy_identity():
    """CR 510.2: Damage assignment order matters only if multiple blockers are present."""
    strat = DamageAssignmentStrategy()
    a = CombatCreature("A", 2, 2, "A")
    b1 = CombatCreature("B1", 1, 1, "B")
    b2 = CombatCreature("B2", 1, 1, "B")
    ordered = strat.order_blockers(a, [b1, b2])
    assert ordered == [b1, b2]


def test_most_creatures_killed_strategy_sorts():
    """CR 510.2: Attackers may order blockers to maximize kills."""
    strat = MostCreaturesKilledStrategy()
    a = CombatCreature("A", 3, 3, "A")
    b1 = CombatCreature("Wall", 0, 4, "B")
    b2 = CombatCreature("Goblin", 1, 1, "B")
    ordered = strat.order_blockers(a, [b1, b2])
    assert ordered == [b2, b1]


def test_plus1_minus1_counter_setters():
    """CR 122.1a: Counters can increase or decrease stats."""
    creature = CombatCreature(name="Bug", power=1, toughness=1, controller="A")
    creature.plus1_counters = 1
    creature.minus1_counters = 1
    assert creature.plus1_counters == 1
    assert creature.minus1_counters == 1
    assert creature.effective_power() == 1
    assert creature.effective_toughness() == 1


def test_validate_blocking_unknown_attacker():
    """CR 509.1a: A creature can block only a creature that's attacking it."""
    attacker = CombatCreature("Attacker", 2, 2, "A")
    blocker = CombatCreature("Blocker", 2, 2, "B")
    blocker.blocking = attacker  # attacker not included in simulator attackers
    sim = CombatSimulator([], [blocker])
    with pytest.raises(ValueError):
        sim.validate_blocking()


def test_validate_blocking_inconsistent():
    """CR 509.1b: Each blocker must be declared blocking a specific attacker."""
    attacker = CombatCreature("Attacker", 2, 2, "A")
    blocker = CombatCreature("Blocker", 2, 2, "B")
    attacker.blocked_by.append(blocker)
    # blocker.blocking not set -> inconsistent
    sim = CombatSimulator([attacker], [blocker])
    with pytest.raises(ValueError):
        sim.validate_blocking()


def test_repr_includes_characteristics():
    """CR 109.3: An object's characteristics include its name, power, toughness, and controller."""
    creature = CombatCreature(name="Elf", power=1, toughness=1, controller="A")
    assert (
        repr(creature)
        == "CombatCreature(name='Elf', power=1, toughness=1, controller='A')"
    )
