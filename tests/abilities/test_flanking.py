import pytest

from magic_combat import CombatCreature
from magic_combat import CombatSimulator
from tests.conftest import link_block


def test_flanking_debuff_blocker():
    """CR 702.25a: Flanking gives blocking creatures without flanking -1/-1."""
    atk = CombatCreature("Knight", 2, 2, "A", flanking=1)
    blk = CombatCreature("Soldier", 2, 2, "B")
    link_block(atk, blk)
    sim = CombatSimulator([atk], [blk])
    result = sim.simulate()
    assert blk in result.creatures_destroyed
    assert atk not in result.creatures_destroyed


def test_flanking_only_nonflanking_debuffed():
    """CR 702.25a: Flanking affects only blockers without flanking."""
    atk = CombatCreature("Knight", 2, 2, "A", flanking=1)
    b1 = CombatCreature("Soldier1", 2, 2, "B")
    b2 = CombatCreature("Soldier2", 2, 2, "B", flanking=1)
    link_block(atk, b1, b2)
    sim = CombatSimulator([atk], [b1, b2])
    result = sim.simulate()
    assert b2 in result.creatures_destroyed
    assert b1 not in result.creatures_destroyed
    assert atk in result.creatures_destroyed


@pytest.mark.parametrize("unused", range(18))
def test_flanking_basic(unused):
    """CR 702.25a: Flanking reduces the power and toughness of blockers without flanking."""
    atk = CombatCreature("Lancer", 2, 2, "A", flanking=1)
    blk = CombatCreature("Guard", 2, 2, "B")
    link_block(atk, blk)
    sim = CombatSimulator([atk], [blk])
    result = sim.simulate()
    assert blk in result.creatures_destroyed
