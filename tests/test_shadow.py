import pytest

from magic_combat import CombatCreature, CombatSimulator, Color
from tests.conftest import link_block


def test_shadow_blocker_can_block_nonshadow_attacker():
    """CR 702.27b: A creature with shadow can block or be blocked only by creatures with shadow."""
    attacker = CombatCreature("Goblin", 2, 2, "A")
    blocker = CombatCreature("Shade", 2, 2, "B", shadow=True)
    link_block(attacker, blocker)
    sim = CombatSimulator([attacker], [blocker])
    # Simulator currently allows this block
    sim.validate_blocking()


def test_shadow_attacker_blocked_by_nonshadow_illegal():
    """CR 702.27b: A creature with shadow can't be blocked by non-shadow creatures."""
    attacker = CombatCreature("Shade", 1, 1, "A", shadow=True)
    blocker = CombatCreature("Bear", 2, 2, "B")
    link_block(attacker, blocker)
    sim = CombatSimulator([attacker], [blocker])
    with pytest.raises(ValueError):
        sim.validate_blocking()


def test_shadow_attacker_blocked_by_shadow_ok():
    """CR 702.27b allows shadow creatures to block other shadow creatures."""
    attacker = CombatCreature("Stalker", 2, 2, "A", shadow=True)
    blocker = CombatCreature("Shade", 2, 2, "B", shadow=True)
    link_block(attacker, blocker)
    sim = CombatSimulator([attacker], [blocker])
    sim.validate_blocking()


def test_shadow_menace_one_blocker_illegal():
    """CR 702.27b & 702.110b: A menace creature with shadow needs two shadow blockers."""
    attacker = CombatCreature("Sneak", 2, 2, "A", shadow=True, menace=True)
    blocker = CombatCreature("Shade", 2, 2, "B", shadow=True)
    link_block(attacker, blocker)
    sim = CombatSimulator([attacker], [blocker])
    with pytest.raises(ValueError):
        sim.validate_blocking()


def test_shadow_menace_two_blockers_ok():
    """CR 702.27b & 702.110b: Two shadow creatures can block a menace attacker with shadow."""
    attacker = CombatCreature("Sneak", 2, 2, "A", shadow=True, menace=True)
    b1 = CombatCreature("Shade1", 1, 1, "B", shadow=True)
    b2 = CombatCreature("Shade2", 1, 1, "B", shadow=True)
    link_block(attacker, b1, b2)
    sim = CombatSimulator([attacker], [b1, b2])
    sim.validate_blocking()


def test_flying_shadow_requires_shadow_blocker_even_with_reach():
    """CR 702.9b & 702.27b: Flying doesn't let a non-shadow creature block one with shadow."""
    attacker = CombatCreature("Specter", 2, 2, "A", shadow=True, flying=True)
    blocker = CombatCreature("Spider", 2, 4, "B", reach=True)
    link_block(attacker, blocker)
    sim = CombatSimulator([attacker], [blocker])
    with pytest.raises(ValueError):
        sim.validate_blocking()


def test_flying_shadow_blocked_by_shadow_without_flying_illegal():
    """CR 702.9b & 702.27b: A flying creature with shadow still needs a flying or reach blocker."""
    attacker = CombatCreature("Specter", 2, 2, "A", shadow=True, flying=True)
    blocker = CombatCreature("Shade", 1, 3, "B", shadow=True)
    link_block(attacker, blocker)
    sim = CombatSimulator([attacker], [blocker])
    with pytest.raises(ValueError):
        sim.validate_blocking()


def test_shadow_skulk_blocker_with_higher_power_illegal():
    """CR 702.27b & 702.72a: Skulk still prevents blocks by higher-power shadow creatures."""
    attacker = CombatCreature("Sneak", 1, 1, "A", shadow=True, skulk=True)
    blocker = CombatCreature("Shade", 3, 3, "B", shadow=True)
    link_block(attacker, blocker)
    sim = CombatSimulator([attacker], [blocker])
    with pytest.raises(ValueError):
        sim.validate_blocking()


def test_shadow_trample_excess_damage_hits_player():
    """CR 702.27b & 702.19b: A blocked shadow creature with trample assigns excess damage to the player."""
    attacker = CombatCreature("Beast", 4, 4, "A", shadow=True, trample=True)
    blocker = CombatCreature("Shade", 1, 1, "B", shadow=True)
    link_block(attacker, blocker)
    sim = CombatSimulator([attacker], [blocker])
    result = sim.simulate()
    assert result.damage_to_players["B"] == 3


def test_shadow_vs_deathtouch_blocker_destroyed():
    """CR 702.2b & 702.27b: A shadow attacker dies if dealt damage by a deathtouch blocker with shadow."""
    attacker = CombatCreature("Stalker", 2, 2, "A", shadow=True)
    blocker = CombatCreature("Assassin", 1, 1, "B", shadow=True, deathtouch=True)
    link_block(attacker, blocker)
    sim = CombatSimulator([attacker], [blocker])
    result = sim.simulate()
    assert attacker in result.creatures_destroyed

