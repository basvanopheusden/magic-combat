import pytest
from magic_combat import CombatCreature, CombatSimulator
from tests.conftest import link_block


def test_undying_with_counter_does_not_return():
    """CR 702.92a: Undying doesn't return a creature that already had a +1/+1 counter."""
    atk = CombatCreature("Slayer", 3, 3, "A")
    blk = CombatCreature("Phoenix", 2, 2, "B", undying=True)
    blk.plus1_counters = 1
    link_block(atk, blk)
    sim = CombatSimulator([atk], [blk])
    result = sim.simulate()
    assert blk in result.creatures_destroyed


def test_persist_with_minus1_counter_does_not_return():
    """CR 702.77a: Persist only returns if the creature had no -1/-1 counters."""
    atk = CombatCreature("Ogre", 2, 2, "A")
    blk = CombatCreature("Spirit", 2, 2, "B", persist=True)
    blk.minus1_counters = 1
    link_block(atk, blk)
    sim = CombatSimulator([atk], [blk])
    result = sim.simulate()
    assert blk in result.creatures_destroyed


def test_persist_creature_returns_with_counter():
    """CR 702.77a: Persist returns a creature that died without -1/-1 counters."""
    attacker = CombatCreature("Giant", 3, 3, "A")
    blocker = CombatCreature("Undying Wall", 2, 2, "B", persist=True)
    link_block(attacker, blocker)
    sim = CombatSimulator([attacker], [blocker])
    result = sim.simulate()
    assert blocker not in result.creatures_destroyed
    assert blocker.minus1_counters == 1


def test_undying_with_plus1_counter_no_return():
    """CR 702.92a: Undying doesn't return a creature that already has a +1/+1 counter."""
    atk = CombatCreature("Slayer", 3, 3, "A")
    blk = CombatCreature("Spirit", 2, 2, "B", undying=True)
    blk.plus1_counters = 1
    link_block(atk, blk)
    sim = CombatSimulator([atk], [blk])
    result = sim.simulate()
    assert blk in result.creatures_destroyed


@pytest.mark.parametrize("unused", range(16))
def test_undying_returns_once(unused):
    """CR 702.92a: Undying returns the creature with a +1/+1 counter."""
    atk = CombatCreature("Slayer", 3, 3, "A")
    blk = CombatCreature("Spirit", 2, 2, "B", undying=True)
    link_block(atk, blk)
    sim = CombatSimulator([atk], [blk])
    result = sim.simulate()
    assert blk not in result.creatures_destroyed
    assert blk.plus1_counters == 1
