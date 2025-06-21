import pytest

from magic_combat import CombatCreature, CombatResult


def test_combat_result_repr_readable():
    """CR 104.3a: A player with 0 or less life loses the game."""
    creature = CombatCreature("Goblin", 2, 2, "A")
    result = CombatResult(
        damage_to_players={"B": 3},
        creatures_destroyed=[creature],
        lifegain={"A": 2},
        poison_counters={"B": 1},
        players_lost=["B"],
    )
    expected = (
        "CombatResult(damage_to_players={'B': 3}, "
        "creatures_destroyed=['Goblin'], lifegain={'A': 2}, "
        "poison_counters={'B': 1}, players_lost=['B'])"
    )
    assert repr(result) == expected
