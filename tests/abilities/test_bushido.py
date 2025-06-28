import pytest

from magic_combat import CombatCreature, CombatSimulator
from tests.conftest import link_block


def test_bushido_bonus():
    """CR 702.46a: Bushido gives the creature +N/+N when it blocks or becomes blocked."""
    atk = CombatCreature("Samurai", 2, 2, "A", bushido=1)
    blk = CombatCreature("Bear", 2, 2, "B")
    link_block(atk, blk)
    sim = CombatSimulator([atk], [blk])
    result = sim.simulate()
    assert blk in result.creatures_destroyed
    assert atk not in result.creatures_destroyed


def test_bushido_multiple_instances_stack():
    """CR 702.46a: Multiple instances of bushido each give +1/+1."""
    atk = CombatCreature("Master Samurai", 2, 2, "A", bushido=2)
    blk = CombatCreature("Guard", 2, 2, "B")
    link_block(atk, blk)
    sim = CombatSimulator([atk], [blk])
    result = sim.simulate()
    assert blk in result.creatures_destroyed
    assert atk not in result.creatures_destroyed


def test_blocker_bushido_grants_bonus():
    """CR 702.46a: Bushido triggers for a creature when it blocks."""
    atk = CombatCreature("Warrior", 2, 2, "A")
    blk = CombatCreature("Guardian", 2, 2, "B", bushido=1)
    link_block(atk, blk)
    sim = CombatSimulator([atk], [blk])
    result = sim.simulate()
    assert atk in result.creatures_destroyed
    assert blk not in result.creatures_destroyed


@pytest.mark.parametrize("boost", range(1, 18))
def test_bushido_various(boost):
    """CR 702.46a: Bushido gives the creature +N/+N when blocked."""
    atk = CombatCreature("Samurai", 1, 1, "A", bushido=boost)
    blk = CombatCreature("Pawn", 1, 1, "B")
    link_block(atk, blk)
    sim = CombatSimulator([atk], [blk])
    result = sim.simulate()
    assert blk in result.creatures_destroyed
