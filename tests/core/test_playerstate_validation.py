# pylint: disable=missing-function-docstring, missing-module-docstring
import pytest

from magic_combat import PlayerState
from magic_combat.constants import DEFAULT_STARTING_LIFE


def test_negative_life_init():
    with pytest.raises(ValueError):
        PlayerState(life=-1, creatures=[])


def test_negative_poison_init():
    with pytest.raises(ValueError):
        PlayerState(life=DEFAULT_STARTING_LIFE, creatures=[], poison=-1)
