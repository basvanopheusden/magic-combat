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


def test_score_difference_metrics():
    """CR 702.15a: Lifelink life gain impacts scoring."""
    atk = CombatCreature("Vampire", 3, 3, "A", mana_cost="{1}{B}{B}", lifelink=True)
    blk = CombatCreature("Bear", 3, 3, "B", mana_cost="{2}")
    res = CombatResult(
        damage_to_players={"B": 3, "A": 2},
        creatures_destroyed=[atk, blk],
        lifegain={"A": 3},
        poison_counters={"B": 2, "A": 1},
    )
    score = res.score("A", "B")
    assert score[3] == -1  # mana value difference 2 - 3
    assert score[4] == 4  # life difference (3 - 2) + (3 - 0)
    assert score[5] == 1  # poison counters difference 2 - 1
