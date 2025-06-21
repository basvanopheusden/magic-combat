import pytest

from magic_combat import PlayerState, DEFAULT_STARTING_LIFE


def test_negative_life_init():
    """CR 107.1: Numbers like life totals can't be negative."""
    with pytest.raises(ValueError):
        PlayerState(life=-1, creatures=[])


def test_negative_poison_init():
    """CR 107.1: Numbers like poison counters can't be negative."""
    with pytest.raises(ValueError):
        PlayerState(life=DEFAULT_STARTING_LIFE, creatures=[], poison=-1)
