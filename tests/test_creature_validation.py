import pytest

from magic_combat import CombatCreature

def test_negative_counters_init():
    """CR 107.1: counters can't be negative."""
    with pytest.raises(ValueError):
        CombatCreature(name="Bad", power=1, toughness=1, controller="A", _plus1_counters=-1)

def test_negative_counters_assignment():
    creature = CombatCreature(name="Good", power=1, toughness=1, controller="A")
    with pytest.raises(ValueError):
        creature.plus1_counters = -3

def test_negative_minus1_counters_assignment():
    creature = CombatCreature(name="Good", power=1, toughness=1, controller="A")
    with pytest.raises(ValueError):
        creature.minus1_counters = -2

def test_invalid_power_or_toughness():
    """CR 107.1: Numbers like power and toughness can't be negative."""
    with pytest.raises(ValueError):
        CombatCreature(name="Oops", power=-1, toughness=1, controller="A")
    with pytest.raises(ValueError):
        CombatCreature(name="Oops", power=1, toughness=0, controller="A")


def test_negative_damage_marked():
    """CR 107.1: Damage values can't be negative."""
    with pytest.raises(ValueError):
        CombatCreature(name="Oops", power=1, toughness=1, controller="A", damage_marked=-1)
