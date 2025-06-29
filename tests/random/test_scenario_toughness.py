# pylint: disable=missing-function-docstring, missing-module-docstring
import random

import pytest

from magic_combat import ScenarioGenerationError
from magic_combat.creature import CombatCreature
from magic_combat.random_scenario import _build_gamestate


def force_zero_toughness(creatures, *, rng=None):
    for c in creatures:
        c.minus1_counters = c.toughness
        c.plus1_counters = 0


def test_generate_random_scenario_positive_toughness(monkeypatch):
    attackers = [CombatCreature("A", 1, 1, "A")]
    blockers = [CombatCreature("B", 1, 1, "B")]
    rng = random.Random(1)
    monkeypatch.setattr(
        "magic_combat.random_scenario.assign_random_counters", force_zero_toughness
    )
    with pytest.raises(ScenarioGenerationError, match="Failed to sample"):
        _build_gamestate(attackers, blockers, rng)
