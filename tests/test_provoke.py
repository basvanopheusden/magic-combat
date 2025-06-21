import pytest

from magic_combat import CombatCreature, CombatSimulator, Color


def test_provoke_target_blocks_successfully():
    """CR 702.40a: Provoke forces the chosen creature to block if able."""
    atk = CombatCreature("Taunter", 2, 2, "A")
    blk = CombatCreature("Guard", 2, 2, "B")
    atk.provoke_target = blk
    atk.blocked_by.append(blk)
    blk.blocking = atk
    sim = CombatSimulator([atk], [blk])
    sim.validate_blocking()
    result = sim.simulate()
    assert atk in result.creatures_destroyed
    assert blk in result.creatures_destroyed


def test_provoke_target_must_block():
    """CR 702.40a: Provoke requires the chosen creature to block if able."""
    atk = CombatCreature("Taunter", 2, 2, "A")
    blk = CombatCreature("Guard", 2, 2, "B")
    atk.provoke_target = blk
    sim = CombatSimulator([atk], [blk])
    with pytest.raises(ValueError):
        sim.validate_blocking()


def test_provoke_target_not_defender():
    """CR 702.40a: Provoke targets a creature the defending player controls."""
    atk = CombatCreature("Taunter", 2, 2, "A")
    defender = CombatCreature("Blocker", 2, 2, "B")
    other = CombatCreature("Bystander", 2, 2, "C")
    atk.provoke_target = other
    sim = CombatSimulator([atk], [defender])
    with pytest.raises(ValueError):
        sim.validate_blocking()


def test_provoke_menace_single_blocker_fails():
    """CR 702.40a & 702.110b: Provoke doesn't override menace's two-blocker requirement."""
    atk = CombatCreature("Menacing", 2, 2, "A", menace=True)
    blk = CombatCreature("Goblin", 2, 2, "B")
    atk.provoke_target = blk
    atk.blocked_by.append(blk)
    blk.blocking = atk
    sim = CombatSimulator([atk], [blk])
    with pytest.raises(ValueError):
        sim.validate_blocking()


def test_provoke_menace_two_blockers_ok():
    """CR 702.40a & 702.110b: Provoke with menace is legal when two creatures including the target block."""
    atk = CombatCreature("Menacing", 2, 2, "A", menace=True)
    blk1 = CombatCreature("Goblin1", 2, 2, "B")
    blk2 = CombatCreature("Goblin2", 2, 2, "B")
    atk.provoke_target = blk1
    atk.blocked_by.extend([blk1, blk2])
    blk1.blocking = atk
    blk2.blocking = atk
    sim = CombatSimulator([atk], [blk1, blk2])
    sim.validate_blocking()
    result = sim.simulate()
    assert atk in result.creatures_destroyed


def test_provoke_unblockable_attacker():
    """CR 702.40a & 509.1b: Provoke can't force a block on an unblockable creature."""
    atk = CombatCreature("Sneak", 2, 2, "A", unblockable=True)
    blk = CombatCreature("Guard", 2, 2, "B")
    atk.provoke_target = blk
    atk.blocked_by.append(blk)
    blk.blocking = atk
    sim = CombatSimulator([atk], [blk])
    with pytest.raises(ValueError):
        sim.validate_blocking()


def test_provoke_flying_needs_reach():
    """CR 702.40a & 702.9b: A provoked creature without flying or reach can't block a flyer."""
    atk = CombatCreature("Dragon", 3, 3, "A", flying=True)
    blk = CombatCreature("Bear", 2, 2, "B")
    atk.provoke_target = blk
    atk.blocked_by.append(blk)
    blk.blocking = atk
    sim = CombatSimulator([atk], [blk])
    with pytest.raises(ValueError):
        sim.validate_blocking()


def test_provoke_flying_with_reach_success():
    """CR 702.40a & 702.9c: Reach lets a provoked creature block a flyer."""
    atk = CombatCreature("Dragon", 3, 3, "A", flying=True)
    blk = CombatCreature("Spider", 1, 4, "B", reach=True)
    atk.provoke_target = blk
    atk.blocked_by.append(blk)
    blk.blocking = atk
    sim = CombatSimulator([atk], [blk])
    sim.validate_blocking()
    result = sim.simulate()
    assert atk not in result.creatures_destroyed
    assert blk not in result.creatures_destroyed


def test_provoke_skulk_high_power_blocker():
    """CR 702.40a & 702.72a: Skulk prevents blocks by higher-power creatures even if provoked."""
    atk = CombatCreature("Sneak", 1, 1, "A", skulk=True)
    blk = CombatCreature("Ogre", 3, 3, "B")
    atk.provoke_target = blk
    atk.blocked_by.append(blk)
    blk.blocking = atk
    sim = CombatSimulator([atk], [blk])
    with pytest.raises(ValueError):
        sim.validate_blocking()


def test_provoke_protection_from_color():
    """CR 702.40a & 702.16b: Protection prevents the provoked creature from blocking."""
    atk = CombatCreature("Paladin", 2, 2, "A", protection_colors={Color.RED})
    blk = CombatCreature("Orc", 2, 2, "B", colors={Color.RED})
    atk.provoke_target = blk
    atk.blocked_by.append(blk)
    blk.blocking = atk
    sim = CombatSimulator([atk], [blk])
    with pytest.raises(ValueError):
        sim.validate_blocking()


def test_provoke_afflict_damage_triggers():
    """CR 702.40a & 702.131a: A provoked attacker with afflict still causes life loss when blocked."""
    atk = CombatCreature("Tormentor", 2, 2, "A", afflict=2)
    blk = CombatCreature("Guard", 2, 2, "B")
    atk.provoke_target = blk
    atk.blocked_by.append(blk)
    blk.blocking = atk
    sim = CombatSimulator([atk], [blk])
    result = sim.simulate()
    assert result.damage_to_players["B"] == 2
    assert atk in result.creatures_destroyed
    assert blk in result.creatures_destroyed
