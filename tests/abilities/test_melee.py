import pytest
from magic_combat import CombatCreature, CombatSimulator
from tests.conftest import link_block


def test_melee_bonus_on_attack():
    """CR 702.111a: Melee gives the creature +1/+1 for each opponent it's attacking."""
    atk = CombatCreature("Soldier", 2, 2, "A", melee=True)
    blk = CombatCreature("Guard", 2, 2, "B")
    link_block(atk, blk)
    sim = CombatSimulator([atk], [blk])
    result = sim.simulate()
    assert blk in result.creatures_destroyed
    assert atk not in result.creatures_destroyed


def test_multiple_melee_attackers_each_gain_bonus():
    """CR 702.111a: Each melee creature gets +1/+1 when attacking a player."""
    m1 = CombatCreature("Warrior1", 2, 2, "A", melee=True)
    m2 = CombatCreature("Warrior2", 2, 2, "A", melee=True)
    defender = CombatCreature("Dummy", 0, 1, "B")
    sim = CombatSimulator([m1, m2], [defender])
    result = sim.simulate()
    assert result.damage_to_players["B"] == 6


@pytest.mark.parametrize("unused", range(18))
def test_melee_single_attacker(unused):
    """CR 702.111a: A melee creature attacking one opponent gets +1/+1."""
    atk = CombatCreature("Brawler", 2, 2, "A", melee=True)
    defender = CombatCreature("Dummy", 0, 1, "B")
    sim = CombatSimulator([atk], [defender])
    result = sim.simulate()
    assert result.damage_to_players["B"] == 3
