import pytest

from magic_combat import CombatCreature
from magic_combat import CombatSimulator
from tests.conftest import link_block


def test_afflict_not_unblocked():
    """CR 702.131a: Afflict doesn't trigger if the creature isn't blocked."""
    atk = CombatCreature("Tormentor", 2, 2, "A", afflict=2)
    defender = CombatCreature("Dummy", 0, 1, "B")
    sim = CombatSimulator([atk], [defender])
    result = sim.simulate()
    assert result.damage_to_players["B"] == 2


def test_afflict_unblocked_no_life_loss():
    """CR 702.131a: Afflict only triggers when the creature becomes blocked."""
    atk = CombatCreature("Tormentor", 3, 3, "A", afflict=2)
    defender = CombatCreature("Dummy", 0, 1, "B")
    sim = CombatSimulator([atk], [defender])
    result = sim.simulate()
    assert result.damage_to_players["B"] == 3


@pytest.mark.parametrize("unused", range(18))
def test_afflict_triggers_when_blocked(unused):
    """CR 702.131a: When blocked, afflict causes life loss equal to its value."""
    atk = CombatCreature("Tormentor", 2, 2, "A", afflict=1)
    blk = CombatCreature("Guard", 2, 2, "B")
    link_block(atk, blk)
    sim = CombatSimulator([atk], [blk])
    result = sim.simulate()
    assert result.damage_to_players["B"] == 1
