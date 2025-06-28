import pytest

from magic_combat import CombatCreature, CombatSimulator
from tests.conftest import link_block


def test_wither_damage_adds_counters():
    """CR 702.90a: Damage from wither is dealt as -1/-1 counters."""
    atk = CombatCreature("Witherer", 3, 3, "A", wither=True)
    blk = CombatCreature("Target", 2, 2, "B")
    link_block(atk, blk)
    sim = CombatSimulator([atk], [blk])
    result = sim.simulate()
    assert blk.minus1_counters == 2
    assert blk in result.creatures_destroyed


@pytest.mark.parametrize("unused", range(19))
def test_wither_basic(unused):
    """CR 702.90a: Wither deals damage as -1/-1 counters."""
    atk = CombatCreature("Corrosive", 2, 2, "A", wither=True)
    blk = CombatCreature("Dummy", 2, 2, "B")
    link_block(atk, blk)
    sim = CombatSimulator([atk], [blk])
    result = sim.simulate()
    assert blk.minus1_counters == 2
