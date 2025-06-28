import pytest

from magic_combat import (CombatCreature, CombatSimulator, GameState,
                          PlayerState)
from tests.conftest import link_block


def test_exalted_single_attacker_multiple_instances():
    """CR 702.90a: Each instance of exalted grants +1/+1 if a creature attacks alone."""
    atk = CombatCreature("Lone", 2, 2, "A", exalted_count=2)
    blk = CombatCreature("Grizzly", 2, 2, "B")
    link_block(atk, blk)
    sim = CombatSimulator([atk], [blk])
    result = sim.simulate()
    assert blk in result.creatures_destroyed
    assert atk not in result.creatures_destroyed


def test_exalted_not_triggered_with_multiple_attackers():
    """CR 702.90a: Exalted triggers only if a creature attacks alone."""
    exalter = CombatCreature("Exalter", 2, 2, "A", exalted_count=1)
    ally = CombatCreature("Ally", 2, 2, "A")
    defender = CombatCreature("Dummy", 0, 1, "B")
    sim = CombatSimulator([exalter, ally], [defender])
    result = sim.simulate()
    assert result.damage_to_players["B"] == 4


def test_exalted_double_strike_kills_first():
    """CR 702.90a & 702.4b: Exalted boosts power so double strike can kill before regular damage."""
    atk = CombatCreature("Duelist", 2, 2, "A", exalted_count=1, double_strike=True)
    blk = CombatCreature("Guard", 3, 3, "B")
    link_block(atk, blk)
    sim = CombatSimulator([atk], [blk])
    result = sim.simulate()
    assert blk in result.creatures_destroyed
    assert atk not in result.creatures_destroyed


def test_exalted_lifelink_unblocked():
    """CR 702.90a & 702.15a: Exalted increases lifelink damage dealt when attacking alone."""
    atk = CombatCreature("Healer", 2, 2, "A", exalted_count=1, lifelink=True)
    defender = CombatCreature("Dummy", 0, 1, "B")
    sim = CombatSimulator([atk], [defender])
    result = sim.simulate()
    assert result.damage_to_players["B"] == 3
    assert result.lifegain["A"] == 3


def test_exalted_trample_over_blocker():
    """CR 702.90a & 702.19b: Exalted adds to trample so excess damage hits the player."""
    atk = CombatCreature("Rhino", 2, 2, "A", exalted_count=1, trample=True)
    blk = CombatCreature("Bear", 2, 2, "B")
    link_block(atk, blk)
    sim = CombatSimulator([atk], [blk])
    result = sim.simulate()
    assert result.damage_to_players["B"] == 1
    assert blk in result.creatures_destroyed


def test_exalted_training_alone_no_counter():
    """CR 702.90a & 702.138a: A lone attacker with training and exalted gets only the exalted bonus."""
    trainee = CombatCreature("Student", 2, 2, "A", exalted_count=1, training=True)
    defender = CombatCreature("Dummy", 0, 1, "B")
    sim = CombatSimulator([trainee], [defender])
    result = sim.simulate()
    assert trainee.plus1_counters == 0
    assert result.damage_to_players["B"] == 3


def test_exalted_training_with_stronger_ally():
    """CR 702.90a & 702.138a: Training triggers with a stronger ally while exalted does not."""
    trainee = CombatCreature("Student", 2, 2, "A", exalted_count=1, training=True)
    mentor = CombatCreature("Mentor", 3, 3, "A")
    sim = CombatSimulator([trainee, mentor], [])
    result = sim.simulate()
    assert trainee.plus1_counters == 1
    assert result.damage_to_players["defender"] == 6


def test_exalted_each_controller_gets_bonus():
    """CR 702.90a: Exalted checks attackers per controller so each lone attacker gets +1/+1."""
    atk_a = CombatCreature("KnightA", 2, 2, "A", exalted_count=1)
    atk_c = CombatCreature("KnightC", 2, 2, "C", exalted_count=1)
    blk_a = CombatCreature("BlockA", 2, 2, "B")
    blk_c = CombatCreature("BlockC", 2, 2, "B")
    link_block(atk_a, blk_a)
    link_block(atk_c, blk_c)
    sim = CombatSimulator([atk_a, atk_c], [blk_a, blk_c])
    result = sim.simulate()
    assert blk_a in result.creatures_destroyed
    assert blk_c in result.creatures_destroyed
    assert atk_a not in result.creatures_destroyed
    assert atk_c not in result.creatures_destroyed


def test_exalted_single_controller_multiple_attackers():
    """CR 702.90a: Exalted doesn't trigger when a controller attacks with more than one creature."""
    atk1 = CombatCreature("Leader", 2, 2, "A", exalted_count=1)
    atk2 = CombatCreature("Ally", 1, 1, "A")
    blk = CombatCreature("Wall", 3, 3, "B")
    link_block(atk1, blk)
    sim = CombatSimulator([atk1, atk2], [blk])
    result = sim.simulate()
    assert atk1 in result.creatures_destroyed
    assert blk not in result.creatures_destroyed


def test_exalted_with_dethrone():
    """CR 702.90a & 702.103a: Exalted boosts damage and dethrone adds a +1/+1 counter."""
    atk = CombatCreature("Upstart", 2, 2, "A", exalted_count=1, dethrone=True)
    defender = CombatCreature("Dummy", 0, 1, "B")
    state = GameState(
        players={
            "A": PlayerState(life=20, creatures=[atk]),
            "B": PlayerState(life=25, creatures=[defender]),
        }
    )
    sim = CombatSimulator([atk], [defender], game_state=state)
    result = sim.simulate()
    assert atk.plus1_counters == 1
    assert result.damage_to_players["B"] == 4


def test_exalted_vigilance_stays_untapped():
    """CR 702.90a & 702.21b: Exalted pumps a vigilant attacker that remains untapped."""
    atk = CombatCreature("Watcher", 2, 2, "A", exalted_count=1, vigilance=True)
    defender = CombatCreature("Dummy", 0, 1, "B")
    sim = CombatSimulator([atk], [defender])
    result = sim.simulate()
    assert not atk.tapped
    assert result.damage_to_players["B"] == 3


def test_exalted_battalion_without_bonus():
    """CR 702.90a & 702.101a: Battalion can trigger even though exalted does not with multiple attackers."""
    leader = CombatCreature("Sergeant", 2, 2, "A", exalted_count=1, battalion=True)
    ally1 = CombatCreature("Ally1", 1, 1, "A")
    ally2 = CombatCreature("Ally2", 1, 1, "A")
    sim = CombatSimulator([leader, ally1, ally2], [])
    result = sim.simulate()
    assert leader.temp_power == 1
    assert result.damage_to_players["defender"] == 5
