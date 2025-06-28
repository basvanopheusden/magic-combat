import pytest

from magic_combat import CombatCreature, CombatSimulator
from tests.conftest import link_block


def test_trample_multiple_blockers_ordering():
    """CR 702.19b: Lethal damage must be assigned to each blocker before any excess can hit the defending player."""
    attacker = CombatCreature("Giant", 5, 5, "A", trample=True)
    small = CombatCreature("Soldier", 2, 2, "B")
    big = CombatCreature("Golem", 5, 5, "B")
    link_block(attacker, small, big)
    sim = CombatSimulator([attacker], [small, big])
    result = sim.simulate()
    assert big in result.creatures_destroyed
    assert small not in result.creatures_destroyed
    assert result.damage_to_players.get("B", 0) == 0


def test_trample_first_strike_hits_player():
    """CR 702.19b & 702.7b: A first strike attacker assigns trample damage during the first-strike step."""
    attacker = CombatCreature(
        "Charging Knight", 3, 3, "A", trample=True, first_strike=True
    )
    blocker = CombatCreature("Bear", 2, 2, "B")
    link_block(attacker, blocker)
    sim = CombatSimulator([attacker], [blocker])
    result = sim.simulate()
    assert result.damage_to_players["B"] == 1
    assert blocker in result.creatures_destroyed


def test_trample_attacker_killed_by_first_strike():
    """CR 702.7b & 702.19b: If the blocker deals first-strike lethal damage, the trample creature deals none."""
    attacker = CombatCreature("Boar", 2, 2, "A", trample=True)
    blocker = CombatCreature("Elite Guard", 3, 3, "B", first_strike=True)
    link_block(attacker, blocker)
    sim = CombatSimulator([attacker], [blocker])
    result = sim.simulate()
    assert attacker in result.creatures_destroyed
    assert result.damage_to_players.get("B", 0) == 0


def test_double_strike_trample_deals_damage_twice():
    """CR 702.4b & 702.19b: Double strike with trample deals damage in both steps, assigning excess to the player each time."""
    attacker = CombatCreature(
        "Ferocious Duelist", 3, 3, "A", trample=True, double_strike=True
    )
    blocker = CombatCreature("Peasant", 1, 1, "B")
    link_block(attacker, blocker)
    sim = CombatSimulator([attacker], [blocker])
    result = sim.simulate()
    assert result.damage_to_players["B"] == 5
    assert blocker in result.creatures_destroyed


def test_trample_excess_damage_to_player():
    """CR 702.19b: Damage beyond lethal can be assigned to the defending player."""
    atk = CombatCreature("Rhino", 4, 4, "A", trample=True)
    blk = CombatCreature("Wall", 0, 3, "B")
    link_block(atk, blk)
    sim = CombatSimulator([atk], [blk])
    result = sim.simulate()
    assert blk in result.creatures_destroyed
    assert result.damage_to_players["B"] == 1


@pytest.mark.parametrize("unused", range(15))
def test_trample_simple(unused):
    """CR 702.19b: Trample lets excess damage hit the defending player."""
    atk = CombatCreature("Beast", 3, 3, "A", trample=True)
    blk = CombatCreature("Wall", 0, 2, "B")
    link_block(atk, blk)
    sim = CombatSimulator([atk], [blk])
    result = sim.simulate()
    assert result.damage_to_players["B"] == 1
