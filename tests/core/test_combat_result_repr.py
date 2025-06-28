# pylint: disable=missing-function-docstring, missing-module-docstring
from magic_combat import CombatCreature, CombatResult


def test_combat_result_repr_readable():
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
