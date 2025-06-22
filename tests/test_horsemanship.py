import pytest

from magic_combat import CombatCreature, CombatSimulator
from tests.conftest import link_block


def test_horsemanship_unblockable_by_normal_creature():
    """CR 702.108a: A creature with horsemanship can't be blocked except by creatures with horsemanship."""
    attacker = CombatCreature("Horseman", 2, 2, "A", horsemanship=True)
    blocker = CombatCreature("Foot Soldier", 2, 2, "B")
    link_block(attacker, blocker)
    sim = CombatSimulator([attacker], [blocker])
    with pytest.raises(ValueError):
        sim.validate_blocking()


def test_horsemanship_blocker_can_block():
    """CR 702.108a: A creature with horsemanship may block another with horsemanship."""
    attacker = CombatCreature("Horseman", 2, 2, "A", horsemanship=True)
    blocker = CombatCreature("Cavalry", 2, 2, "B", horsemanship=True)
    link_block(attacker, blocker)
    sim = CombatSimulator([attacker], [blocker])
    sim.validate_blocking()
    result = sim.simulate()
    assert attacker in result.creatures_destroyed
    assert blocker in result.creatures_destroyed


def test_horsemanship_menace_single_blocker_fails():
    """CR 702.110b & 702.108a: A menace creature with horsemanship needs two horseman blockers."""
    atk = CombatCreature("Raider", 2, 2, "A", menace=True, horsemanship=True)
    blk = CombatCreature("Cavalry", 2, 2, "B", horsemanship=True)
    link_block(atk, blk)
    sim = CombatSimulator([atk], [blk])
    with pytest.raises(ValueError):
        sim.validate_blocking()


def test_horsemanship_menace_two_blockers_ok():
    """CR 702.110b & 702.108a: Two horsemanship blockers satisfy menace."""
    atk = CombatCreature("Raider", 2, 2, "A", menace=True, horsemanship=True)
    b1 = CombatCreature("Cavalry1", 2, 2, "B", horsemanship=True)
    b2 = CombatCreature("Cavalry2", 2, 2, "B", horsemanship=True)
    link_block(atk, b1, b2)
    sim = CombatSimulator([atk], [b1, b2])
    sim.validate_blocking()


def test_provoke_non_horse_cant_block():
    """CR 702.40a & 702.108a: Provoke can't force a creature without horsemanship to block."""
    atk = CombatCreature("Taunter", 2, 2, "A", horsemanship=True)
    blk = CombatCreature("Guard", 2, 2, "B")
    link_block(atk, blk)
    sim = CombatSimulator([atk], [blk], provoke_map={atk: blk})
    with pytest.raises(ValueError):
        sim.validate_blocking()


def test_provoke_horse_target_blocks():
    """CR 702.40a & 702.108a: Provoke works when the target has horsemanship."""
    atk = CombatCreature("Taunter", 2, 2, "A", horsemanship=True)
    blk = CombatCreature("Cavalry", 2, 2, "B", horsemanship=True)
    link_block(atk, blk)
    sim = CombatSimulator([atk], [blk], provoke_map={atk: blk})
    sim.validate_blocking()
    result = sim.simulate()
    assert atk in result.creatures_destroyed
    assert blk in result.creatures_destroyed


def test_shadow_horsemanship_needs_both_shadow_only_fails():
    """CR 702.8b & 702.108a: Shadow alone can't block a creature with shadow and horsemanship."""
    atk = CombatCreature("Phantom Rider", 1, 1, "A", shadow=True, horsemanship=True)
    blk = CombatCreature("Wraith", 1, 1, "B", shadow=True)
    link_block(atk, blk)
    sim = CombatSimulator([atk], [blk])
    with pytest.raises(ValueError):
        sim.validate_blocking()


def test_shadow_horsemanship_needs_both_horse_only_fails():
    """CR 702.8b & 702.108a: Horsemanship alone can't block a creature with shadow and horsemanship."""
    atk = CombatCreature("Phantom Rider", 1, 1, "A", shadow=True, horsemanship=True)
    blk = CombatCreature("Cavalry", 1, 1, "B", horsemanship=True)
    link_block(atk, blk)
    sim = CombatSimulator([atk], [blk])
    with pytest.raises(ValueError):
        sim.validate_blocking()


def test_shadow_horsemanship_with_both_ok():
    """CR 702.8b & 702.108a: A creature with both shadow and horsemanship can block another with both."""
    atk = CombatCreature("Phantom Rider", 1, 1, "A", shadow=True, horsemanship=True)
    blk = CombatCreature("Specter Cavalry", 1, 1, "B", shadow=True, horsemanship=True)
    link_block(atk, blk)
    sim = CombatSimulator([atk], [blk])
    sim.validate_blocking()


def test_horsemanship_blocking_normal_attacker():
    """CR 702.108a: Horsemanship doesn't restrict blocking creatures without it."""
    attacker = CombatCreature("Bear", 2, 2, "A")
    blocker = CombatCreature("Cavalry", 2, 2, "B", horsemanship=True)
    link_block(attacker, blocker)
    sim = CombatSimulator([attacker], [blocker])
    sim.validate_blocking()
    result = sim.simulate()
    assert attacker in result.creatures_destroyed
    assert blocker in result.creatures_destroyed
