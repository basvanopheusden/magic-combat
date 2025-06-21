from pathlib import Path
import sys
import pytest

# Ensure the package is importable when running tests from any location
sys.path.append(str(Path(__file__).resolve().parents[1]))

from magic_combat import CombatCreature, CombatSimulator




def test_skulk_bushido_combat():
    """CR 702.120 & 702.46a: Bushido bonuses apply after blockers are declared."""
    atk = CombatCreature("Sneaky Samurai", 2, 2, "A", skulk=True, bushido=1)
    blk = CombatCreature("Peasant", 1, 1, "B")
    atk.blocked_by.append(blk)
    blk.blocking = atk
    sim = CombatSimulator([atk], [blk])
    result = sim.simulate()
    assert blk in result.creatures_destroyed
    assert atk not in result.creatures_destroyed


def test_flying_and_horsemanship_blocking():
    """CR 702.9b & 702.30a: A creature with flying and horsemanship can be blocked only by one with horsemanship and flying or reach."""
    atk = CombatCreature("Pegasus Rider", 2, 2, "A", flying=True, horsemanship=True)

    fly_only = CombatCreature("Falcon", 1, 1, "B", flying=True)
    atk.blocked_by.append(fly_only)
    fly_only.blocking = atk
    sim = CombatSimulator([atk], [fly_only])
    with pytest.raises(ValueError):
        sim.validate_blocking()

    horse_only = CombatCreature("Horseman", 1, 1, "B", horsemanship=True)
    atk.blocked_by = [horse_only]
    horse_only.blocking = atk
    sim = CombatSimulator([atk], [horse_only])
    with pytest.raises(ValueError):
        sim.validate_blocking()

    both = CombatCreature("Sky Rider", 1, 1, "B", flying=True, horsemanship=True)
    atk.blocked_by = [both]
    both.blocking = atk
    sim = CombatSimulator([atk], [both])
    sim.validate_blocking()

    reach_both = CombatCreature("Archer", 1, 1, "B", reach=True, horsemanship=True)
    atk.blocked_by = [reach_both]
    reach_both.blocking = atk
    sim = CombatSimulator([atk], [reach_both])
    sim.validate_blocking()


def test_fear_and_protection_from_black():
    """CR 702.36b & 702.16b: Fear allows only artifact or black blockers, but protection from black stops black blockers."""
    atk = CombatCreature(
        "Nightblade", 2, 2, "A", fear=True, protection_colors={"black"}
    )
    blk = CombatCreature(
        "Black Artifact", 2, 2, "B", colors={"black"}, artifact=True
    )
    atk.blocked_by.append(blk)
    blk.blocking = atk
    sim = CombatSimulator([atk], [blk])
    with pytest.raises(ValueError):
        sim.validate_blocking()

    golem = CombatCreature("Golem", 2, 2, "B", artifact=True)
    atk.blocked_by = [golem]
    golem.blocking = atk
    sim = CombatSimulator([atk], [golem])
    sim.validate_blocking()


def test_menace_and_skulk_two_small_blockers():
    """CR 702.110b & 702.120: A menace creature with skulk can be blocked by two small creatures."""
    atk = CombatCreature("Tricky Brute", 2, 2, "A", menace=True, skulk=True)
    b1 = CombatCreature("Goblin1", 1, 1, "B")
    b2 = CombatCreature("Goblin2", 1, 1, "B")
    atk.blocked_by.extend([b1, b2])
    b1.blocking = atk
    b2.blocking = atk
    sim = CombatSimulator([atk], [b1, b2])
    sim.validate_blocking()


def test_melee_and_exalted_stack():
    """CR 702.111a & 702.90a: Melee and exalted each grant +1/+1 when a creature attacks alone."""
    attacker = CombatCreature("Champion", 2, 2, "A", melee=True, exalted_count=1)
    sim = CombatSimulator([attacker], [])
    result = sim.simulate()
    assert result.damage_to_players["defender"] == 4
    assert result.creatures_destroyed == []


def test_training_with_battle_cry():
    """CR 702.92a & 702.138a: Battle cry boosts allies and training adds a +1/+1 counter with a stronger attacker."""
    leader = CombatCreature("Leader", 4, 4, "A", battle_cry_count=1)
    trainee = CombatCreature("Trainee", 2, 2, "A", training=True)
    sim = CombatSimulator([leader, trainee], [])
    result = sim.simulate()
    assert trainee.plus1_counters == 1
    assert result.damage_to_players["defender"] == 8


def test_rampage_and_flanking_combined():
    """CR 702.23a & 702.25a: Rampage enlarges the attacker while flanking weakens each blocker."""
    attacker = CombatCreature("Warrior", 3, 3, "A", rampage=1, flanking=1)
    b1 = CombatCreature("Soldier1", 2, 2, "B")
    b2 = CombatCreature("Soldier2", 2, 2, "B")
    attacker.blocked_by.extend([b1, b2])
    b1.blocking = attacker
    b2.blocking = attacker
    sim = CombatSimulator([attacker], [b1, b2])
    result = sim.simulate()
    assert b1 in result.creatures_destroyed
    assert b2 in result.creatures_destroyed
    assert attacker not in result.creatures_destroyed
