import pytest

from magic_combat import Color, CombatCreature, CombatSimulator
from tests.conftest import link_block


def test_intimidate_artifact_blocker_allowed():
    """CR 702.13a: An artifact creature can block an intimidate attacker regardless of color."""
    atk = CombatCreature("Rogue", 2, 2, "A", intimidate=True, colors={Color.BLACK})
    blk = CombatCreature("Golem", 2, 2, "B", artifact=True)
    link_block(atk, blk)
    sim = CombatSimulator([atk], [blk])
    sim.validate_blocking()


def test_intimidate_same_color_blocker_allowed():
    """CR 702.13a: Intimidate allows blocking by a creature that shares a color."""
    atk = CombatCreature("Rogue", 2, 2, "A", intimidate=True, colors={Color.RED})
    blk = CombatCreature("Guard", 2, 2, "B", colors={Color.RED})
    link_block(atk, blk)
    sim = CombatSimulator([atk], [blk])
    sim.validate_blocking()


@pytest.mark.parametrize("unused", range(18))
def test_intimidate_blocking(unused):
    """CR 702.13a: Only artifacts or creatures that share a color may block."""
    atk = CombatCreature("Bandit", 2, 2, "A", intimidate=True, colors={Color.GREEN})
    blk = CombatCreature("Golem", 2, 2, "B", artifact=True)
    link_block(atk, blk)
    sim = CombatSimulator([atk], [blk])
    sim.validate_blocking()
