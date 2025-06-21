import pytest
from magic_combat import CombatCreature, CombatSimulator, GameState, PlayerState



def test_wither_lifelink_blocker_gains_life():
    """CR 702.90a & 702.15a: Wither damage is -1/-1 counters but still causes life gain from lifelink."""
    atk = CombatCreature("Aggressor", 2, 2, "A")
    blk = CombatCreature("Corrosive Guard", 1, 1, "B", wither=True, lifelink=True)
    atk.blocked_by.append(blk)
    blk.blocking = atk
    sim = CombatSimulator([atk], [blk])
    result = sim.simulate()
    assert atk.minus1_counters == 1
    assert blk in result.creatures_destroyed
    assert result.lifegain["B"] == 1


def test_afflict_lifelink_no_extra_life():
    """CR 702.131a & 702.15a: Afflict causes life loss that isn't damage, so lifelink only counts combat damage."""
    atk = CombatCreature("Tormentor", 3, 3, "A", afflict=2, lifelink=True)
    blk = CombatCreature("Soldier", 2, 2, "B")
    atk.blocked_by.append(blk)
    blk.blocking = atk
    sim = CombatSimulator([atk], [blk])
    result = sim.simulate()
    assert result.damage_to_players["B"] == 2
    assert result.lifegain["A"] == 2


def test_double_strike_trample_lifelink():
    """CR 702.4b, 702.19b & 702.15a: Double strike with trample deals damage twice and lifelink gains that much life."""
    atk = CombatCreature("Champion", 2, 2, "A", double_strike=True, trample=True, lifelink=True)
    blk = CombatCreature("Chump", 1, 1, "B")
    atk.blocked_by.append(blk)
    blk.blocking = atk
    sim = CombatSimulator([atk], [blk])
    result = sim.simulate()
    assert result.damage_to_players["B"] == 3
    assert result.lifegain["A"] == 4


def test_first_strike_lifelink_vs_deathtouch():
    """CR 702.7b, 702.2b & 702.15a: First strike lifelink kills a deathtouch blocker before it can deal damage."""
    atk = CombatCreature("Paladin", 2, 2, "A", first_strike=True, lifelink=True)
    blk = CombatCreature("Assassin", 2, 2, "B", deathtouch=True)
    atk.blocked_by.append(blk)
    blk.blocking = atk
    sim = CombatSimulator([atk], [blk])
    result = sim.simulate()
    assert blk in result.creatures_destroyed
    assert atk not in result.creatures_destroyed
    assert result.lifegain["A"] == 2


def test_lifelink_blocker_gains_life():
    """CR 702.15a: A creature with lifelink gains life when dealing combat damage as a blocker."""
    atk = CombatCreature("Brute", 2, 2, "A")
    blk = CombatCreature("Healer", 2, 2, "B", lifelink=True)
    atk.blocked_by.append(blk)
    blk.blocking = atk
    sim = CombatSimulator([atk], [blk])
    result = sim.simulate()
    assert result.lifegain["B"] == 2


def test_multiple_lifelink_attackers_stack():
    """CR 702.15a: Each lifelink creature grants life separately when dealing damage."""
    a1 = CombatCreature("Vampire", 2, 2, "A", lifelink=True)
    a2 = CombatCreature("Cleric", 1, 1, "A", lifelink=True)
    defender = CombatCreature("Dummy", 0, 1, "B")
    sim = CombatSimulator([a1, a2], [defender])
    result = sim.simulate()
    assert result.damage_to_players["B"] == 3
    assert result.lifegain["A"] == 3


def test_infect_lifelink_blocker():
    """CR 702.90b & 702.15a: Infect damage from a lifelink blocker still grants life."""
    atk = CombatCreature("Attacker", 3, 3, "A")
    blk = CombatCreature("Toxic Guard", 1, 1, "B", infect=True, lifelink=True)
    atk.blocked_by.append(blk)
    blk.blocking = atk
    sim = CombatSimulator([atk], [blk])
    result = sim.simulate()
    assert atk.minus1_counters == 1
    assert result.lifegain["B"] == 1


def test_deathtouch_lifelink_blocker():
    """CR 702.2b & 702.15a: Deathtouch from a lifelink blocker destroys and also grants life."""
    atk = CombatCreature("Charger", 2, 2, "A")
    blk = CombatCreature("Venomous", 1, 1, "B", deathtouch=True, lifelink=True)
    atk.blocked_by.append(blk)
    blk.blocking = atk
    sim = CombatSimulator([atk], [blk])
    result = sim.simulate()
    assert atk in result.creatures_destroyed
    assert blk in result.creatures_destroyed
    assert result.lifegain["B"] == 1


def test_toxic_lifelink_unblocked():
    """CR 702.15a & 702.??: Toxic adds poison counters while lifelink gains life from the damage."""
    atk = CombatCreature("Viper", 1, 1, "A", toxic=2, lifelink=True)
    defender = CombatCreature("Dummy", 0, 1, "B")
    sim = CombatSimulator([atk], [defender])
    result = sim.simulate()
    assert result.damage_to_players["B"] == 1
    assert result.poison_counters["B"] == 2
    assert result.lifegain["A"] == 1


def test_lifelink_on_both_sides():
    """CR 702.15a: When both creatures have lifelink, each controller gains life for the damage their creature deals."""
    atk = CombatCreature("Angel", 2, 2, "A", lifelink=True)
    blk = CombatCreature("Cleric", 2, 2, "B", lifelink=True)
    atk.blocked_by.append(blk)
    blk.blocking = atk
    sim = CombatSimulator([atk], [blk])
    result = sim.simulate()
    assert result.lifegain["A"] == 2
    assert result.lifegain["B"] == 2

