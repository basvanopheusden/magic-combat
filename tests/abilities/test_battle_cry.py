import pytest

from magic_combat import CombatCreature, CombatSimulator
from tests.conftest import link_block


def test_battle_cry_multiple_instances_single_creature():
    """CR 702.92a: Each instance of battle cry adds +1/+0 to other attackers."""
    leader = CombatCreature("Warcaller", 2, 2, "A", battle_cry_count=2)
    ally = CombatCreature("Ally", 2, 2, "A")
    sim = CombatSimulator([leader, ally], [])
    result = sim.simulate()
    assert result.damage_to_players["defender"] == 6


def test_double_strike_battle_cry_damage():
    """CR 702.4b & 702.92a: Double strike with battle cry still pumps allies once."""
    leader = CombatCreature(
        "Champion", 2, 2, "A", double_strike=True, battle_cry_count=1
    )
    ally = CombatCreature("Ally", 2, 2, "A")
    sim = CombatSimulator([leader, ally], [])
    result = sim.simulate()
    assert result.damage_to_players["defender"] == 7


def test_battle_cry_pump_lingers_after_source_death():
    """CR 702.92a & 702.7b: The pump remains even if the battle cry creature dies first."""
    leader = CombatCreature("Cryer", 2, 2, "A", battle_cry_count=1)
    ally = CombatCreature("Ally", 2, 2, "A")
    blocker = CombatCreature("Strike", 2, 2, "B", first_strike=True)
    link_block(leader, blocker)
    sim = CombatSimulator([leader, ally], [blocker])
    result = sim.simulate()
    assert leader in result.creatures_destroyed
    assert result.damage_to_players["B"] == 3


def test_battle_cry_only_affects_controllers_creatures():
    """CR 702.92a: Battle cry affects only creatures controlled by the same player."""
    leader = CombatCreature("Leader", 2, 2, "A", battle_cry_count=1)
    ally_a = CombatCreature("AllyA", 2, 2, "A")
    other = CombatCreature("Other", 2, 2, "C")
    sim = CombatSimulator([leader, ally_a, other], [])
    result = sim.simulate()
    assert result.damage_to_players["defender"] == 7


def test_battle_cry_multiple_players_no_cross_pump():
    """CR 702.92a: Each battle cry only boosts creatures its controller attacks with."""
    leader_a = CombatCreature("LeaderA", 2, 2, "A", battle_cry_count=1)
    ally_a = CombatCreature("AllyA", 2, 2, "A")
    leader_c = CombatCreature("LeaderC", 2, 2, "C", battle_cry_count=1)
    ally_c = CombatCreature("AllyC", 2, 2, "C")
    sim = CombatSimulator([leader_a, ally_a, leader_c, ally_c], [])
    result = sim.simulate()
    assert result.damage_to_players["defender"] == 10


def test_battle_cry_and_melee_same_creature():
    """CR 702.92a & 702.111a: A creature with battle cry and melee boosts allies and itself."""
    champion = CombatCreature("Champion", 2, 2, "A", battle_cry_count=1, melee=True)
    ally = CombatCreature("Ally", 2, 2, "A")
    sim = CombatSimulator([champion, ally], [])
    result = sim.simulate()
    assert result.damage_to_players["defender"] == 6


def test_battle_cry_and_rampage_same_creature():
    """CR 702.23a & 702.92a: Rampage bonuses apply but battle cry doesn't pump itself."""
    attacker = CombatCreature("Rampager", 3, 3, "A", rampage=2, battle_cry_count=1)
    ally = CombatCreature("Ally", 2, 2, "A")
    b1 = CombatCreature("B1", 2, 2, "B")
    b2 = CombatCreature("B2", 2, 2, "B")
    link_block(attacker, b1, b2)
    sim = CombatSimulator([attacker, ally], [b1, b2])
    result = sim.simulate()
    assert b1 in result.creatures_destroyed and b2 in result.creatures_destroyed
    assert attacker not in result.creatures_destroyed
    assert result.damage_to_players["B"] == 3


def test_battle_cry_pumps_trample_damage():
    """CR 702.92a & 702.19b: Battle cry increases trample damage assigned to the player."""
    leader = CombatCreature("Leader", 2, 2, "A", battle_cry_count=1)
    trampler = CombatCreature("Rhino", 2, 2, "A", trample=True)
    blocker = CombatCreature("Wall", 1, 1, "B")
    link_block(trampler, blocker)
    sim = CombatSimulator([leader, trampler], [blocker])
    result = sim.simulate()
    assert result.damage_to_players["B"] == 4


def test_battle_cry_pumps_infect_poison():
    """CR 702.92a & 702.87a: Pumped infect damage gives extra poison counters."""
    leader = CombatCreature("Warcaller", 2, 2, "A", battle_cry_count=1)
    infector = CombatCreature("Infect", 1, 1, "A", infect=True)
    sim = CombatSimulator([leader, infector], [])
    result = sim.simulate()
    assert result.poison_counters["defender"] == 2


def test_battle_cry_counts_stack_across_creatures():
    """CR 702.92a: Battle cry bonuses from multiple sources add together."""
    c1 = CombatCreature("C1", 2, 2, "A", battle_cry_count=2)
    c2 = CombatCreature("C2", 2, 2, "A", battle_cry_count=1)
    ally = CombatCreature("Ally", 2, 2, "A")
    sim = CombatSimulator([c1, c2, ally], [])
    result = sim.simulate()
    assert result.damage_to_players["defender"] == 12


def test_battle_cry_boosts_allies():
    """CR 702.92a: Battle cry gives each other attacking creature +1/+0."""
    leader = CombatCreature("Leader", 2, 2, "A", battle_cry_count=1)
    ally = CombatCreature("Ally", 2, 2, "A")
    sim = CombatSimulator([leader, ally], [])
    result = sim.simulate()
    assert result.damage_to_players["defender"] == 5


def test_battle_cry_from_multiple_sources():
    """CR 702.92a: Each battle cry ability boosts other attackers."""
    leader1 = CombatCreature("Leader1", 2, 2, "A", battle_cry_count=1)
    leader2 = CombatCreature("Leader2", 2, 2, "A", battle_cry_count=1)
    ally = CombatCreature("Ally", 2, 2, "A")
    defender = CombatCreature("Dummy", 0, 1, "B")
    sim = CombatSimulator([leader1, leader2, ally], [defender])
    result = sim.simulate()
    assert result.damage_to_players["B"] == 10
