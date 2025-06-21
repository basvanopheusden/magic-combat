import pytest


from magic_combat import CombatCreature, CombatSimulator, Color
from tests.conftest import link_block


def test_fear_and_protection_from_black():
    """CR 702.36b & 702.16b: Fear allows only artifact or black blockers, but protection from black stops black blockers."""
    atk = CombatCreature(
        "Nightblade", 2, 2, "A", fear=True, protection_colors={Color.BLACK}
    )
    blk = CombatCreature(
        "Black Artifact", 2, 2, "B", colors={Color.BLACK}, artifact=True
    )
    link_block(atk, blk)
    sim = CombatSimulator([atk], [blk])
    with pytest.raises(ValueError):
        sim.validate_blocking()

    golem = CombatCreature("Golem", 2, 2, "B", artifact=True)
    atk.blocked_by = [golem]
    golem.blocking = atk
    sim = CombatSimulator([atk], [golem])
    sim.validate_blocking()


def test_menace_and_skulk_two_small_blockers():
    """CR 702.110b & 702.120: A menace creature with skulk can be blocked by two small creatures."""
    atk = CombatCreature("Tricky Brute", 2, 2, "A", menace=True, skulk=True)
    b1 = CombatCreature("Goblin1", 1, 1, "B")
    b2 = CombatCreature("Goblin2", 1, 1, "B")
    link_block(atk, b1, b2)
    sim = CombatSimulator([atk], [b1, b2])
    sim.validate_blocking()


def test_melee_and_exalted_stack():
    """CR 702.111a & 702.90a: Melee and exalted each grant +1/+1 when a creature attacks alone."""
    attacker = CombatCreature("Champion", 2, 2, "A", melee=True, exalted_count=1)
    sim = CombatSimulator([attacker], [])
    result = sim.simulate()
    assert result.damage_to_players["defender"] == 4
    assert result.creatures_destroyed == []


def test_training_with_battle_cry():
    """CR 702.92a & 702.138a: Battle cry boosts allies and training adds a +1/+1 counter with a stronger attacker."""
    leader = CombatCreature("Leader", 4, 4, "A", battle_cry_count=1)
    trainee = CombatCreature("Trainee", 2, 2, "A", training=True)
    sim = CombatSimulator([leader, trainee], [])
    result = sim.simulate()
    assert trainee.plus1_counters == 1
    assert result.damage_to_players["defender"] == 8


