import pytest

from magic_combat import PlayerState, STARTING_LIFE_TOTAL


def test_negative_life_init():
    """CR 107.1: Numbers like life totals can't be negative."""
    with pytest.raises(ValueError):
        PlayerState(life=-1, creatures=[])


def test_negative_poison_init():
    """CR 107.1: Numbers like poison counters can't be negative."""
    with pytest.raises(ValueError):
        PlayerState(life=STARTING_LIFE_TOTAL, creatures=[], poison=-1)
