import pytest

from magic_combat import CombatCreature, CombatSimulator
from tests.conftest import link_block


def test_skulk_blocked_by_greater_power_illegal():
    """CR 702.72a: Skulk prevents blocks by creatures with greater power."""
    attacker = CombatCreature("Sneak", 2, 2, "A", skulk=True)
    blocker = CombatCreature("Ogre", 3, 3, "B")
    link_block(attacker, blocker)
    sim = CombatSimulator([attacker], [blocker])
    with pytest.raises(ValueError):
        sim.validate_blocking()


def test_skulk_block_equal_power_allowed():
    """CR 702.72a: A blocker with equal power may block a skulk creature."""
    attacker = CombatCreature("Rogue", 2, 2, "A", skulk=True)
    blocker = CombatCreature("Guard", 2, 2, "B")
    link_block(attacker, blocker)
    sim = CombatSimulator([attacker], [blocker])
    result = sim.simulate()
    assert attacker in result.creatures_destroyed
    assert blocker in result.creatures_destroyed


def test_skulk_block_smaller_creature_allowed():
    """CR 702.72a: Creatures with lesser power can block a skulk attacker."""
    attacker = CombatCreature("Shadow", 3, 3, "A", skulk=True)
    blocker = CombatCreature("Goblin", 1, 1, "B")
    link_block(attacker, blocker)
    sim = CombatSimulator([attacker], [blocker])
    result = sim.simulate()
    assert blocker in result.creatures_destroyed
    assert attacker not in result.creatures_destroyed


def test_skulk_blocker_with_counters_illegal():
    """CR 702.72a: Skulk checks effective power including +1/+1 counters."""
    attacker = CombatCreature("Sneak", 2, 2, "A", skulk=True)
    blocker = CombatCreature("Fodder", 1, 1, "B")
    blocker.plus1_counters = 2
    link_block(attacker, blocker)
    sim = CombatSimulator([attacker], [blocker])
    with pytest.raises(ValueError):
        sim.validate_blocking()


def test_skulk_blocker_bushido_bonus_after_blocking():
    """CR 702.72a & 702.46a: Bushido bonuses don't affect skulk's legality."""
    attacker = CombatCreature("Ninja", 2, 2, "A", skulk=True)
    blocker = CombatCreature("Samurai", 2, 2, "B", bushido=2)
    link_block(attacker, blocker)
    sim = CombatSimulator([attacker], [blocker])
    result = sim.simulate()
    assert attacker in result.creatures_destroyed
    assert blocker not in result.creatures_destroyed


def test_skulk_double_block_one_big_illegal():
    """CR 702.72a: Each blocking creature must have power <= the skulk attacker."""
    attacker = CombatCreature("Sneak", 2, 2, "A", skulk=True)
    big = CombatCreature("Giant", 4, 4, "B")
    small = CombatCreature("Helper", 1, 1, "B")
    link_block(attacker, big, small)
    sim = CombatSimulator([attacker], [big, small])
    with pytest.raises(ValueError):
        sim.validate_blocking()


def test_skulk_menace_big_and_small_blockers():
    """CR 702.72a & 702.110b: Menace requires two blockers, each with low enough power."""
    attacker = CombatCreature("Brute", 2, 2, "A", skulk=True, menace=True)
    big = CombatCreature("Ogre", 3, 3, "B")
    small = CombatCreature("Goblin", 1, 1, "B")
    link_block(attacker, big, small)
    sim = CombatSimulator([attacker], [big, small])
    with pytest.raises(ValueError):
        sim.validate_blocking()


def test_skulk_flying_big_flyer_illegal():
    """CR 702.72a & 702.9b: A larger flying creature can't block skulk."""
    attacker = CombatCreature("Spy", 2, 2, "A", skulk=True, flying=True)
    blocker = CombatCreature("Dragon", 4, 4, "B", flying=True)
    link_block(attacker, blocker)
    sim = CombatSimulator([attacker], [blocker])
    with pytest.raises(ValueError):
        sim.validate_blocking()


def test_skulk_flying_reach_small_allowed():
    """CR 702.72a & 702.9c: A small creature with reach can block a skulk flyer."""
    attacker = CombatCreature("Spy", 2, 2, "A", skulk=True, flying=True)
    blocker = CombatCreature("Archer", 1, 3, "B", reach=True)
    link_block(attacker, blocker)
    sim = CombatSimulator([attacker], [blocker])
    result = sim.simulate()
    assert result.creatures_destroyed == []


def test_skulk_intimidate_artifact_big_illegal():
    """CR 702.72a & 702.68a: Intimidate doesn't bypass skulk's power restriction."""
    attacker = CombatCreature("Ghost", 2, 2, "A", skulk=True, intimidate=True)
    blocker = CombatCreature("Construct", 3, 3, "B", artifact=True)
    link_block(attacker, blocker)
    sim = CombatSimulator([attacker], [blocker])
    with pytest.raises(ValueError):
        sim.validate_blocking()
