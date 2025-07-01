# pylint: disable=missing-function-docstring, missing-module-docstring
import random

from magic_combat import CombatCreature
from magic_combat.random_creature import assign_random_tapped


def test_assign_random_tapped_respects_vigilance():
    rng = random.Random(42)
    creatures = [
        CombatCreature("A", 2, 2, "B"),
        CombatCreature("B", 2, 2, "B", vigilance=True),
        CombatCreature("C", 2, 2, "B"),
    ]
    assign_random_tapped(creatures, rng=rng, tap_probability=1.0)
    assert creatures[0].tapped
    assert not creatures[1].tapped
    assert creatures[2].tapped
