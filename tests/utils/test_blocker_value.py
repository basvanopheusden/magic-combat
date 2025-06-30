import pytest

from magic_combat import CombatCreature


def test_blocker_value_undying_with_plus_one_counter():
    creature = CombatCreature("Wolf", 2, 2, "A", undying=True)
    creature.plus1_counters = 1
    assert creature.creature_value() == pytest.approx(4.0)


def test_blocker_value_persist_with_minus_one_counter():
    creature = CombatCreature("Spirit", 2, 2, "A", persist=True)
    creature.minus1_counters = 1
    assert creature.creature_value() == pytest.approx(2.0)
