# pylint: disable=missing-function-docstring, missing-module-docstring
import random

from magic_combat import CombatCreature
from magic_combat.random_creature import assign_random_counters


def test_assign_random_counters_valid():
    rng = random.Random(123)
    creatures = [CombatCreature("A", 2, 2, "A"), CombatCreature("B", 3, 1, "B")]
    assign_random_counters(creatures, rng=rng)
    for c in creatures:
        assert not (c.plus1_counters and c.minus1_counters)
        assert c.toughness - c.minus1_counters >= 0
