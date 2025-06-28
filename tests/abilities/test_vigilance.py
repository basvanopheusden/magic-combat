import pytest

from magic_combat import CombatCreature, CombatSimulator


def test_vigilance_attacker_stays_untapped():
    """CR 702.21b: Attacking doesn't cause a creature with vigilance to tap."""
    atk = CombatCreature("Watcher", 2, 2, "A", vigilance=True)
    defender = CombatCreature("Dummy", 0, 1, "B")
    sim = CombatSimulator([atk], [defender])
    result = sim.simulate()
    assert not atk.tapped
    assert result.damage_to_players.get("B", 0) == 2


@pytest.mark.parametrize("unused", range(19))
def test_vigilance_basic(unused):
    """CR 702.21b: Vigilance creatures remain untapped when attacking."""
    atk = CombatCreature("Guard", 2, 2, "A", vigilance=True)
    defender = CombatCreature("Dummy", 0, 1, "B")
    sim = CombatSimulator([atk], [defender])
    result = sim.simulate()
    assert not atk.tapped
    assert result.damage_to_players["B"] == 2
