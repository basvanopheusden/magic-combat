import pytest

from magic_combat import CombatCreature, CombatSimulator
from tests.conftest import link_block


@pytest.mark.parametrize("i", range(20))
def test_menace_requires_two_blockers(i):
    """CR 702.110b: A creature with menace can't be blocked except by two or more creatures."""
    atk = CombatCreature(f"Brute{i}", 2, 2, "A", menace=True)
    b1 = CombatCreature("Guard1", 1, 1, "B")
    b2 = CombatCreature("Guard2", 1, 1, "B")
    link_block(atk, b1, b2)
    sim = CombatSimulator([atk], [b1, b2])
    sim.validate_blocking()
