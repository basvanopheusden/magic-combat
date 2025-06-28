import pytest

from magic_combat import CombatCreature, CombatSimulator
from tests.conftest import link_block


def test_skulk_bushido_block_illegal():
    """CR 702.72a & 702.46a: Skulk checks power before bushido triggers."""
    attacker = CombatCreature("Sneaky Samurai", 2, 2, "A", skulk=True, bushido=2)
    blocker = CombatCreature("Giant", 3, 3, "B")
    link_block(attacker, blocker)
    sim = CombatSimulator([attacker], [blocker])
    with pytest.raises(ValueError):
        sim.validate_blocking()


def test_skulk_bushido_equal_power_allowed():
    """CR 702.72a: A blocker with equal power may block despite later bushido."""
    attacker = CombatCreature("Sneaky Samurai", 2, 2, "A", skulk=True, bushido=2)
    blocker = CombatCreature("Guard", 2, 2, "B")
    link_block(attacker, blocker)
    sim = CombatSimulator([attacker], [blocker])
    sim.validate_blocking()  # should be allowed


def test_flying_horsemanship_needs_both_flying_only():
    """CR 702.9b & 702.108a: Flying alone can't block flying+horsemanship."""
    attacker = CombatCreature(
        "Pegasus Rider", 2, 2, "A", flying=True, horsemanship=True
    )
    blocker = CombatCreature("Bird", 1, 1, "B", flying=True)
    link_block(attacker, blocker)
    sim = CombatSimulator([attacker], [blocker])
    with pytest.raises(ValueError):
        sim.validate_blocking()


def test_flying_horsemanship_needs_both_horse_only():
    """CR 702.9b & 702.108a: Horsemanship alone can't block flying+horsemanship."""
    attacker = CombatCreature(
        "Pegasus Rider", 2, 2, "A", flying=True, horsemanship=True
    )
    blocker = CombatCreature("Cavalry", 2, 2, "B", horsemanship=True)
    link_block(attacker, blocker)
    sim = CombatSimulator([attacker], [blocker])
    with pytest.raises(ValueError):
        sim.validate_blocking()


def test_flying_horsemanship_block_with_both_ok():
    """CR 702.9b & 702.108a: A creature with both abilities can block."""
    attacker = CombatCreature(
        "Pegasus Rider", 2, 2, "A", flying=True, horsemanship=True
    )
    blocker = CombatCreature("Winged Knight", 2, 2, "B", flying=True, horsemanship=True)
    link_block(attacker, blocker)
    sim = CombatSimulator([attacker], [blocker])
    sim.validate_blocking()  # should not raise


def test_flying_horsemanship_with_reach_and_horse_ok():
    """CR 702.9c & 702.108a: Reach plus horsemanship can block."""
    attacker = CombatCreature("Sky Cavalry", 2, 2, "A", flying=True, horsemanship=True)
    blocker = CombatCreature("Archer", 2, 3, "B", reach=True, horsemanship=True)
    link_block(attacker, blocker)
    sim = CombatSimulator([attacker], [blocker])
    sim.validate_blocking()  # should not raise


def test_flanking_and_bushido_combined():
    """CR 702.25a & 702.46a: Flanking debuffs blockers while bushido buffs the attacker."""
    attacker = CombatCreature("Samurai Knight", 2, 2, "A", flanking=1, bushido=1)
    blocker = CombatCreature("Hill Giant", 3, 3, "B")
    link_block(attacker, blocker)
    sim = CombatSimulator([attacker], [blocker])
    result = sim.simulate()
    assert blocker in result.creatures_destroyed
    assert attacker not in result.creatures_destroyed


def test_rampage_and_bushido_multi_block():
    """CR 702.23a & 702.46a: Rampage and bushido bonuses stack with multiple blockers."""
    attacker = CombatCreature("Warlord", 3, 3, "A", rampage=1, bushido=1)
    b1 = CombatCreature("B1", 2, 2, "B")
    b2 = CombatCreature("B2", 2, 2, "B")
    link_block(attacker, b1, b2)
    sim = CombatSimulator([attacker], [b1, b2])
    result = sim.simulate()
    assert b1 in result.creatures_destroyed
    assert b2 in result.creatures_destroyed
    assert attacker not in result.creatures_destroyed


def test_exalted_and_bushido_stack():
    """CR 702.90a & 702.46a: Exalted and bushido each grant +1/+1."""
    attacker = CombatCreature("Disciplined", 2, 2, "A", exalted_count=1, bushido=1)
    blocker = CombatCreature("Grunt", 2, 2, "B")
    link_block(attacker, blocker)
    sim = CombatSimulator([attacker], [blocker])
    result = sim.simulate()
    assert blocker in result.creatures_destroyed
    assert attacker not in result.creatures_destroyed


def test_training_after_battle_cry_equal_power():
    """CR 702.92a & 702.138a: Battle cry may prevent training if powers tie."""
    trainee = CombatCreature("Trainee", 2, 2, "A", training=True)
    leader = CombatCreature("Leader", 3, 3, "A", battle_cry_count=1)
    sim = CombatSimulator([trainee, leader], [])
    sim.simulate()
    assert trainee.plus1_counters == 0


def test_rampage_and_flanking_multi_block():
    """CR 702.23a & 702.25a: Rampage boosts attackers while flanking weakens blockers."""
    attacker = CombatCreature("Warrior", 3, 3, "A", rampage=2, flanking=1)
    b1 = CombatCreature("B1", 2, 2, "B")
    b2 = CombatCreature("B2", 2, 2, "B")
    link_block(attacker, b1, b2)
    sim = CombatSimulator([attacker], [b1, b2])
    result = sim.simulate()
    assert b1 in result.creatures_destroyed
    assert b2 in result.creatures_destroyed
    assert attacker not in result.creatures_destroyed


def test_blocked_creature_no_trample_hits_no_player():
    """CR 509.1h: A creature remains blocked even if its blocker dies."""
    attacker = CombatCreature("Fencer", 2, 2, "A", first_strike=True)
    blocker = CombatCreature("Guard", 2, 2, "B")
    link_block(attacker, blocker)
    sim = CombatSimulator([attacker], [blocker])
    result = sim.simulate()
    assert result.damage_to_players.get("B", 0) == 0


def test_normal_attacker_taps_on_attack():
    """CR 508.1g: Declaring an attacker causes it to become tapped."""
    atk = CombatCreature("Orc", 2, 2, "A")
    defender = CombatCreature("Dummy", 0, 1, "B")
    sim = CombatSimulator([atk], [defender])
    sim.simulate()
    assert atk.tapped
