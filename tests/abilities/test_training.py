import pytest
from magic_combat import CombatCreature, CombatSimulator
from tests.conftest import link_block


def test_training_adds_counter():
    """CR 702.138a: Training puts a +1/+1 counter on the creature if it attacks with a stronger ally."""
    trainee = CombatCreature("Trainee", 2, 2, "A", training=True)
    mentor = CombatCreature("Mentor", 3, 3, "A")
    sim = CombatSimulator([trainee, mentor], [])
    sim.simulate()
    assert trainee.plus1_counters == 1


def test_training_no_counter_without_stronger_ally():
    """CR 702.138a: Training checks for another attacking creature with greater power."""
    trainee = CombatCreature("Trainee", 2, 2, "A", training=True)
    ally = CombatCreature("Helper", 2, 2, "A")
    sim = CombatSimulator([trainee, ally], [])
    sim.simulate()
    assert trainee.plus1_counters == 0


def test_training_no_stronger_ally():
    """CR 702.138a: Training triggers only with a stronger attacker."""
    trainee = CombatCreature("Student", 2, 2, "A", training=True)
    weak = CombatCreature("Weak", 1, 1, "A")
    sim = CombatSimulator([trainee, weak], [])
    sim.simulate()
    assert trainee.plus1_counters == 0


def test_training_multiple_stronger_allies_single_counter():
    """CR 702.138a: Multiple stronger allies still give only one training counter."""
    trainee = CombatCreature("Student", 2, 2, "A", training=True)
    ally1 = CombatCreature("Ally1", 3, 3, "A")
    ally2 = CombatCreature("Ally2", 4, 4, "A")
    sim = CombatSimulator([trainee, ally1, ally2], [])
    sim.simulate()
    assert trainee.plus1_counters == 1


def test_training_no_stronger_ally_no_counter():
    """CR 702.138a: Training doesn't trigger without a stronger attacking creature."""
    trainee = CombatCreature("Student", 2, 2, "A", training=True)
    ally = CombatCreature("Peer", 2, 2, "A")
    sim = CombatSimulator([trainee, ally], [])
    sim.simulate()
    assert trainee.plus1_counters == 0


@pytest.mark.parametrize("unused", range(15))
def test_training_basics(unused):
    """CR 702.138a: Training requires a stronger attacking creature."""
    trainee = CombatCreature("Apprentice", 2, 2, "A", training=True)
    mentor = CombatCreature("Mentor", 3, 3, "A")
    sim = CombatSimulator([trainee, mentor], [])
    sim.simulate()
    assert trainee.plus1_counters == 1
