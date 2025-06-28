from magic_combat import CombatCreature, CombatSimulator
from tests.conftest import link_block


def test_rampage_unblocked_no_bonus():
    """CR 702.23a: Rampage only triggers when blocked by multiple creatures."""
    atk = CombatCreature("Beast", 3, 3, "A", rampage=2)
    defender = CombatCreature("Dummy", 0, 1, "B")
    sim = CombatSimulator([atk], [defender])
    result = sim.simulate()
    assert result.damage_to_players["B"] == 3


def test_rampage_with_multiple_blockers():
    """CR 702.23a: Rampage gives +N/+N for each blocker beyond the first."""
    atk = CombatCreature("Beast", 3, 3, "A", rampage=2)
    b1 = CombatCreature("B1", 2, 2, "B")
    b2 = CombatCreature("B2", 2, 2, "B")
    link_block(atk, b1, b2)
    sim = CombatSimulator([atk], [b1, b2])
    result = sim.simulate()
    assert b1 in result.creatures_destroyed
    assert b2 in result.creatures_destroyed
    assert atk not in result.creatures_destroyed


def test_rampage_no_bonus_with_single_blocker():
    """CR 702.23a: Rampage gives no bonus with only one blocker."""
    atk = CombatCreature("Brute", 3, 3, "A", rampage=2)
    blk = CombatCreature("Bear", 3, 3, "B")
    link_block(atk, blk)
    sim = CombatSimulator([atk], [blk])
    result = sim.simulate()
    assert atk in result.creatures_destroyed
    assert blk in result.creatures_destroyed


def test_rampage_single_blocker_no_bonus():
    """CR 702.23a: Rampage counts blockers beyond the first."""
    attacker = CombatCreature("Beast", 3, 3, "A", rampage=2)
    blocker = CombatCreature("Ogre", 3, 3, "B")
    link_block(attacker, blocker)
    sim = CombatSimulator([attacker], [blocker])
    result = sim.simulate()
    assert attacker in result.creatures_destroyed
    assert blocker in result.creatures_destroyed


import pytest

@pytest.mark.parametrize("unused", range(16))
def test_rampage_basic(unused):
    """CR 702.23a: Rampage adds power for each blocker beyond the first."""
    atk = CombatCreature("Rager", 2, 2, "A", rampage=1)
    b1 = CombatCreature("Goblin1", 1, 1, "B")
    b2 = CombatCreature("Goblin2", 1, 1, "B")
    link_block(atk, b1, b2)
    sim = CombatSimulator([atk], [b1, b2])
    result = sim.simulate()
    assert atk not in result.creatures_destroyed

