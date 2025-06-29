from magic_combat import CombatCreature
from magic_combat import CombatResult


def test_score_optional_components():
    atk = CombatCreature("Goblin", 2, 2, "A")
    res = CombatResult(
        damage_to_players={"B": 2},
        creatures_destroyed=[atk],
        lifegain={},
        poison_counters={"B": 1},
    )
    full = res.score("A", "B")
    partial = res.score("A", "B", include_life=False, include_poison=False)
    assert full[4] == 2
    assert full[5] == 1
    assert partial[4] == 0
    assert partial[5] == 0
