# pylint: disable=missing-function-docstring, missing-module-docstring
import pytest

from magic_combat import DEFAULT_STARTING_LIFE, PlayerState


def test_negative_life_init():
    with pytest.raises(ValueError):
        PlayerState(life=-1, creatures=[])


def test_negative_poison_init():
    with pytest.raises(ValueError):
        PlayerState(life=DEFAULT_STARTING_LIFE, creatures=[], poison=-1)
