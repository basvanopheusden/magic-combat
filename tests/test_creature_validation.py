from pathlib import Path
import sys
import pytest

# Ensure the package is importable when running tests from any location
sys.path.append(str(Path(__file__).resolve().parents[1]))

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

