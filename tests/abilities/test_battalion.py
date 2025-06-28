from magic_combat import CombatCreature, CombatSimulator
from tests.conftest import link_block


def test_battalion_needs_three_attackers_no_bonus():
    """CR 702.101a: Battalion triggers only if the creature and at least two others attack."""
    leader = CombatCreature("Sergeant", 2, 2, "A", battalion=True)
    ally = CombatCreature("Ally", 2, 2, "A")
    sim = CombatSimulator([leader, ally], [])
    sim.simulate()
    assert leader.temp_power == 0


def test_battalion_triggers_with_three_attackers():
    """CR 702.101a: Battalion gives +1/+1 when three attackers are declared."""
    leader = CombatCreature("Leader", 2, 2, "A", battalion=True)
    ally1 = CombatCreature("Ally1", 2, 2, "A")
    ally2 = CombatCreature("Ally2", 2, 2, "A")
    sim = CombatSimulator([leader, ally1, ally2], [])
    result = sim.simulate()
    assert result.damage_to_players["defender"] == 7


def test_battalion_fewer_than_three_no_bonus():
    """CR 702.101a: Battalion doesn't trigger with fewer than three attackers."""
    leader = CombatCreature("Leader", 2, 2, "A", battalion=True)
    ally = CombatCreature("Ally", 2, 2, "A")
    sim = CombatSimulator([leader, ally], [])
    result = sim.simulate()
    assert result.damage_to_players["defender"] == 4


def test_battalion_bonus_when_three_attack():
    """CR 702.101a: Battalion triggers when it and at least two other creatures attack."""
    leader = CombatCreature("Leader", 2, 2, "A", battalion=True)
    ally1 = CombatCreature("Ally1", 2, 2, "A")
    ally2 = CombatCreature("Ally2", 2, 2, "A")
    blocker = CombatCreature("Guard", 0, 1, "B")
    sim = CombatSimulator([leader, ally1, ally2], [blocker])
    result = sim.simulate()
    assert result.damage_to_players["B"] == 7


def test_exalted_battalion_without_bonus():
    """CR 702.90a & 702.101a: Battalion can trigger even though exalted does not when multiple attackers attack."""
    leader = CombatCreature("Sergeant", 2, 2, "A", exalted_count=1, battalion=True)
    ally1 = CombatCreature("Ally1", 1, 1, "A")
    ally2 = CombatCreature("Ally2", 1, 1, "A")
    sim = CombatSimulator([leader, ally1, ally2], [])
    result = sim.simulate()
    assert leader.temp_power == 1
    assert result.damage_to_players["defender"] == 5


def test_provoke_battalion_no_bonus_without_three_attackers():
    """CR 702.40a & 702.101a: Provoke doesn't grant battalion's bonus if only two creatures attack."""
    provoker = CombatCreature("Leader", 2, 2, "A", battalion=True)
    ally = CombatCreature("Ally", 2, 2, "A")
    blocker = CombatCreature("Guard", 2, 2, "B")
    link_block(provoker, blocker)
    sim = CombatSimulator([provoker, ally], [blocker], provoke_map={provoker: blocker})
    result = sim.simulate()
    assert provoker in result.creatures_destroyed
    assert blocker in result.creatures_destroyed


def test_battalion_multiple_battalions_stack():
    """CR 702.101a: Each battalion creature gets +1/+1 when three or more attack."""
    b1 = CombatCreature("Leader1", 2, 2, "A", battalion=True)
    b2 = CombatCreature("Leader2", 2, 2, "A", battalion=True)
    ally = CombatCreature("Ally", 2, 2, "A")
    sim = CombatSimulator([b1, b2, ally], [])
    result = sim.simulate()
    assert result.damage_to_players["defender"] == 8


def test_battalion_bonus_kills_larger_blocker():
    """CR 702.101a: The battalion bonus applies even if the creature is blocked."""
    leader = CombatCreature("Captain", 2, 2, "A", battalion=True)
    ally1 = CombatCreature("Ally1", 2, 2, "A")
    ally2 = CombatCreature("Ally2", 2, 2, "A")
    blocker = CombatCreature("Wall", 0, 3, "B")
    link_block(leader, blocker)
    sim = CombatSimulator([leader, ally1, ally2], [blocker])
    result = sim.simulate()
    assert blocker in result.creatures_destroyed
    assert leader not in result.creatures_destroyed


def test_battalion_bonus_with_four_attackers():
    """CR 702.101a: Battalion still triggers with more than three attackers."""
    leader = CombatCreature("Captain", 2, 2, "A", battalion=True)
    ally1 = CombatCreature("Ally1", 2, 2, "A")
    ally2 = CombatCreature("Ally2", 2, 2, "A")
    ally3 = CombatCreature("Ally3", 2, 2, "A")
    sim = CombatSimulator([leader, ally1, ally2, ally3], [])
    result = sim.simulate()
    assert result.damage_to_players["defender"] == 9


def test_battalion_creature_at_home_no_trigger():
    """CR 702.101a: Battalion doesn't trigger if the battalion creature itself doesn't attack."""
    leader = CombatCreature("Captain", 2, 2, "A", battalion=True)
    ally1 = CombatCreature("Ally1", 2, 2, "A")
    ally2 = CombatCreature("Ally2", 2, 2, "A")
    # leader stays home
    sim = CombatSimulator([ally1, ally2], [])
    sim.simulate()
    assert leader.temp_power == 0
