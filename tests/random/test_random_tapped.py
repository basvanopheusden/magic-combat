import random
from magic_combat import CombatCreature
from magic_combat.random_creature import assign_random_tapped


def test_assign_random_tapped_respects_vigilance():
    """CR 302.2 & 702.21b: Tapped creatures can't block and vigilance keeps them untapped."""
    rng = random.Random(42)
    creatures = [
        CombatCreature("A", 2, 2, "B"),
        CombatCreature("B", 2, 2, "B", vigilance=True),
        CombatCreature("C", 2, 2, "B"),
    ]
    assign_random_tapped(creatures, rng=rng, prob=1.0)
    assert creatures[0].tapped
    assert not creatures[1].tapped
    assert creatures[2].tapped
