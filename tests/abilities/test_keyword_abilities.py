from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parents[1]))

from magic_combat import CombatCreature, CombatSimulator


def test_bushido_bonus():
    """CR 702.46a: Bushido gives the creature +N/+N when it blocks or becomes blocked."""
    atk = CombatCreature("Samurai", 2, 2, "A", bushido=1)
    blk = CombatCreature("Bear", 2, 2, "B")
    atk.blocked_by.append(blk)
    blk.blocking = atk
    sim = CombatSimulator([atk], [blk])
    result = sim.simulate()
    assert blk in result.creatures_destroyed
    assert atk not in result.creatures_destroyed


def test_flanking_debuff_blocker():
    """CR 702.25a: Flanking gives blocking creatures without flanking -1/-1."""
    atk = CombatCreature("Knight", 2, 2, "A", flanking=1)
    blk = CombatCreature("Soldier", 2, 2, "B")
    atk.blocked_by.append(blk)
    blk.blocking = atk
    sim = CombatSimulator([atk], [blk])
    result = sim.simulate()
    assert blk in result.creatures_destroyed
    assert atk not in result.creatures_destroyed


def test_exalted_single_attacker_multiple_instances():
    """CR 702.90a: Each instance of exalted grants +1/+1 if a creature attacks alone."""
    atk = CombatCreature("Lone", 2, 2, "A", exalted_count=2)
    blk = CombatCreature("Grizzly", 2, 2, "B")
    atk.blocked_by.append(blk)
    blk.blocking = atk
    sim = CombatSimulator([atk], [blk])
    result = sim.simulate()
    assert blk in result.creatures_destroyed
    assert atk not in result.creatures_destroyed


def test_rampage_with_multiple_blockers():
    """CR 702.23a: Rampage gives +N/+N for each blocker beyond the first."""
    atk = CombatCreature("Beast", 3, 3, "A", rampage=2)
    b1 = CombatCreature("B1", 2, 2, "B")
    b2 = CombatCreature("B2", 2, 2, "B")
    atk.blocked_by.extend([b1, b2])
    b1.blocking = atk
    b2.blocking = atk
    sim = CombatSimulator([atk], [b1, b2])
    result = sim.simulate()
    assert b1 in result.creatures_destroyed
    assert b2 in result.creatures_destroyed
    assert atk not in result.creatures_destroyed


def test_battle_cry_boosts_allies():
    """CR 702.92a: Battle cry gives each other attacking creature +1/+0."""
    leader = CombatCreature("Leader", 2, 2, "A", battle_cry_count=1)
    ally = CombatCreature("Ally", 2, 2, "A")
    sim = CombatSimulator([leader, ally], [])
    result = sim.simulate()
    assert result.damage_to_players["defender"] == 5


def test_melee_bonus_on_attack():
    """CR 702.111a: Melee gives the creature +1/+1 for each opponent it's attacking."""
    atk = CombatCreature("Soldier", 2, 2, "A", melee=True)
    blk = CombatCreature("Guard", 2, 2, "B")
    atk.blocked_by.append(blk)
    blk.blocking = atk
    sim = CombatSimulator([atk], [blk])
    result = sim.simulate()
    assert blk in result.creatures_destroyed
    assert atk not in result.creatures_destroyed


def test_training_adds_counter():
    """CR 702.138a: Training puts a +1/+1 counter on the creature if it attacks with a stronger ally."""
    trainee = CombatCreature("Trainee", 2, 2, "A", training=True)
    mentor = CombatCreature("Mentor", 3, 3, "A")
    sim = CombatSimulator([trainee, mentor], [])
    sim.simulate()
    assert trainee.plus1_counters == 1


def test_skulk_and_bushido_combo():
    """CR 702.65a & 702.46a: Skulk restricts blocks to weaker creatures and bushido gives +N/+N when blocked."""
    attacker = CombatCreature("Ninja", 2, 2, "A", skulk=True, bushido=1)
    blocker = CombatCreature("Guard", 1, 1, "B")
    attacker.blocked_by.append(blocker)
    blocker.blocking = attacker
    sim = CombatSimulator([attacker], [blocker])
    result = sim.simulate()
    assert blocker in result.creatures_destroyed
    assert attacker not in result.creatures_destroyed

def test_exalted_not_triggered_with_multiple_attackers():
    """CR 702.90a: Exalted triggers only if a creature attacks alone."""
    exalter = CombatCreature("Exalter", 2, 2, "A", exalted_count=1)
    ally = CombatCreature("Ally", 2, 2, "A")
    defender = CombatCreature("Dummy", 0, 1, "B")
    sim = CombatSimulator([exalter, ally], [defender])
    result = sim.simulate()
    assert result.damage_to_players["B"] == 4


def test_deathtouch_basic_lethal():
    """CR 702.2b: Any nonzero damage from a creature with deathtouch is lethal."""
    atk = CombatCreature("Assassin", 1, 1, "A", deathtouch=True)
    blk = CombatCreature("Bear", 2, 2, "B")
    atk.blocked_by.append(blk)
    blk.blocking = atk
    sim = CombatSimulator([atk], [blk])
    result = sim.simulate()
    assert atk in result.creatures_destroyed
    assert blk in result.creatures_destroyed


def test_deathtouch_multiple_blockers():
    """CR 510.1a: Deathtouch lets an attacker assign only 1 damage per blocker."""
    atk = CombatCreature("Venomous", 3, 3, "A", deathtouch=True)
    b1 = CombatCreature("Guard1", 3, 3, "B")
    b2 = CombatCreature("Guard2", 3, 3, "B")
    atk.blocked_by.extend([b1, b2])
    b1.blocking = atk
    b2.blocking = atk
    sim = CombatSimulator([atk], [b1, b2])
    result = sim.simulate()
    assert atk in result.creatures_destroyed
    assert b1 in result.creatures_destroyed
    assert b2 in result.creatures_destroyed


def test_deathtouch_vs_indestructible():
    """CR 702.12b: Indestructible permanents aren't destroyed by deathtouch."""
    atk = CombatCreature("Snake", 1, 1, "A", deathtouch=True)
    blk = CombatCreature("Guardian", 2, 2, "B", indestructible=True)
    atk.blocked_by.append(blk)
    blk.blocking = atk
    sim = CombatSimulator([atk], [blk])
    result = sim.simulate()
    assert atk in result.creatures_destroyed
    assert blk not in result.creatures_destroyed


def test_deathtouch_killed_before_dealing_damage():
    """CR 702.7b: First strike damage can kill a deathtouch creature before it deals damage."""
    atk = CombatCreature("Biter", 2, 2, "A", deathtouch=True)
    blk = CombatCreature("Duelist", 2, 2, "B", first_strike=True)
    atk.blocked_by.append(blk)
    blk.blocking = atk
    sim = CombatSimulator([atk], [blk])
    result = sim.simulate()
    assert atk in result.creatures_destroyed
    assert blk not in result.creatures_destroyed
