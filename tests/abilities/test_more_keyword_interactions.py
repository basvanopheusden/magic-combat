import pytest

from magic_combat import (
    CombatCreature,
    CombatSimulator,
    GameState,
    PlayerState,
    Color,
)
from tests.conftest import link_block


# 1

def test_rampage_single_blocker_no_bonus():
    """CR 702.23a: Rampage counts blockers beyond the first."""
    attacker = CombatCreature("Beast", 3, 3, "A", rampage=2)
    blocker = CombatCreature("Ogre", 3, 3, "B")
    link_block(attacker, blocker)
    sim = CombatSimulator([attacker], [blocker])
    result = sim.simulate()
    assert attacker in result.creatures_destroyed
    assert blocker in result.creatures_destroyed


# 4

def test_training_no_stronger_ally():
    """CR 702.138a: Training triggers only with a stronger attacker."""
    trainee = CombatCreature("Student", 2, 2, "A", training=True)
    weak = CombatCreature("Weak", 1, 1, "A")
    sim = CombatSimulator([trainee, weak], [])
    sim.simulate()
    assert trainee.plus1_counters == 0


# 5

def test_training_multiple_stronger_allies_single_counter():
    """CR 702.138a: Multiple stronger allies still give only one training counter."""
    trainee = CombatCreature("Student", 2, 2, "A", training=True)
    ally1 = CombatCreature("Ally1", 3, 3, "A")
    ally2 = CombatCreature("Ally2", 4, 4, "A")
    sim = CombatSimulator([trainee, ally1, ally2], [])
    sim.simulate()
    assert trainee.plus1_counters == 1


# 6

def test_dethrone_no_counter_if_not_highest():
    """CR 702.103a: Dethrone doesn't trigger if the defender isn't at the highest life total."""
    attacker = CombatCreature("Challenger", 2, 2, "A", dethrone=True)
    defender = CombatCreature("Dummy", 0, 1, "B")
    state = GameState(players={
        "A": PlayerState(life=20, creatures=[attacker]),
        "B": PlayerState(life=15, creatures=[defender]),
    })
    sim = CombatSimulator([attacker], [defender], game_state=state)
    sim.simulate()
    assert attacker.plus1_counters == 0


# 7

def test_dethrone_triggers_when_tied_for_highest():
    """CR 702.103a: Tied for the most life still satisfies dethrone."""
    attacker = CombatCreature("Challenger", 2, 2, "A", dethrone=True)
    defender = CombatCreature("Dummy", 0, 1, "B")
    state = GameState(players={
        "A": PlayerState(life=20, creatures=[attacker]),
        "B": PlayerState(life=20, creatures=[defender]),
    })
    sim = CombatSimulator([attacker], [defender], game_state=state)
    sim.simulate()
    assert attacker.plus1_counters == 1


# 8

def test_bushido_first_strike_bonus_considered():
    """CR 702.46a & 702.7b: Bushido applies before first-strike damage."""
    atk = CombatCreature("Samurai", 1, 1, "A", bushido=1, first_strike=True)
    blk = CombatCreature("Bear", 2, 2, "B")
    link_block(atk, blk)
    sim = CombatSimulator([atk], [blk])
    result = sim.simulate()
    assert blk in result.creatures_destroyed
    assert atk not in result.creatures_destroyed


# 9

def test_flanking_only_nonflanking_debuffed():
    """CR 702.25a: Flanking affects only blockers without flanking."""
    atk = CombatCreature("Knight", 2, 2, "A", flanking=1)
    b1 = CombatCreature("Soldier1", 2, 2, "B")
    b2 = CombatCreature("Soldier2", 2, 2, "B", flanking=1)
    link_block(atk, b1, b2)
    sim = CombatSimulator([atk], [b1, b2])
    result = sim.simulate()
    assert b2 in result.creatures_destroyed
    assert b1 not in result.creatures_destroyed
    assert atk in result.creatures_destroyed


# 10

def test_blocker_bushido_grants_bonus():
    """CR 702.46a: Bushido triggers for a creature when it blocks."""
    atk = CombatCreature("Warrior", 2, 2, "A")
    blk = CombatCreature("Guardian", 2, 2, "B", bushido=1)
    link_block(atk, blk)
    sim = CombatSimulator([atk], [blk])
    result = sim.simulate()
    assert atk in result.creatures_destroyed
    assert blk not in result.creatures_destroyed


# 11

def test_afflict_unblocked_no_life_loss():
    """CR 702.131a: Afflict only triggers when the creature becomes blocked."""
    atk = CombatCreature("Tormentor", 3, 3, "A", afflict=2)
    defender = CombatCreature("Dummy", 0, 1, "B")
    sim = CombatSimulator([atk], [defender])
    result = sim.simulate()
    assert result.damage_to_players["B"] == 3


# 12

def test_intimidate_same_color_blocker_allowed():
    """CR 702.13a: A creature that shares a color may block an intimidate attacker."""
    atk = CombatCreature("Rogue", 2, 2, "A", intimidate=True, colors={Color.RED})
    blk = CombatCreature("Ally", 2, 2, "B", colors={Color.RED})
    link_block(atk, blk)
    sim = CombatSimulator([atk], [blk])
    sim.validate_blocking()


# 13

def test_defender_can_block():
    """CR 702.3b: Defender prevents attacking but not blocking."""
    atk = CombatCreature("Aggressor", 2, 2, "A")
    blk = CombatCreature("Wall", 3, 3, "B", defender=True)
    link_block(atk, blk)
    sim = CombatSimulator([atk], [blk])
    sim.validate_blocking()


# 14

def test_infect_wither_stack_counters_on_blocker():
    """CR 702.90a & 702.90b: Infect with wither still deals only one set of counters."""
    atk = CombatCreature("Blight", 2, 2, "A", infect=True, wither=True)
    blk = CombatCreature("Target", 2, 2, "B")
    link_block(atk, blk)
    sim = CombatSimulator([atk], [blk])
    result = sim.simulate()
    assert blk.minus1_counters == 2


# 15

def test_infect_wither_player_poison_only():
    """CR 702.90b & 702.90a: Wither doesn't affect players, so only poison counters are given."""
    atk = CombatCreature("Agent", 2, 2, "A", infect=True, wither=True)
    defender = CombatCreature("Dummy", 0, 1, "B")
    sim = CombatSimulator([atk], [defender])
    result = sim.simulate()
    assert result.poison_counters["B"] == 2
    assert result.damage_to_players.get("B", 0) == 0


# 16

def test_lifelink_vigilance_unblocked_gains_life():
    """CR 702.15a & 702.21b: Lifelink gains life while vigilance leaves the creature untapped."""
    atk = CombatCreature("Angel", 2, 2, "A", lifelink=True, vigilance=True)
    defender = CombatCreature("Dummy", 0, 1, "B")
    state = GameState(players={"A": PlayerState(life=20, creatures=[atk]), "B": PlayerState(life=20, creatures=[defender])})
    sim = CombatSimulator([atk], [defender], game_state=state)
    result = sim.simulate()
    assert not atk.tapped
    assert result.lifegain["A"] == 2
    assert state.players["A"].life == 22


# 17

def test_shadow_and_fear_requires_shadow():
    """CR 702.27b & 702.36b: A creature with shadow can be blocked only by creatures with shadow."""
    atk = CombatCreature("Shade Stalker", 2, 2, "A", shadow=True, fear=True)
    blk = CombatCreature("Nightmare", 2, 2, "B", fear=True)
    link_block(atk, blk)
    sim = CombatSimulator([atk], [blk])
    with pytest.raises(ValueError):
        sim.validate_blocking()


# 18

def test_unblockable_with_menace_still_unblockable():
    """CR 509.1b & 702.110b: Unblockable creatures can't be blocked even with menace."""
    atk = CombatCreature("Sneak", 2, 2, "A", unblockable=True, menace=True)
    b1 = CombatCreature("Guard1", 1, 1, "B")
    b2 = CombatCreature("Guard2", 1, 1, "B")
    link_block(atk, b1, b2)
    sim = CombatSimulator([atk], [b1, b2])
    with pytest.raises(ValueError):
        sim.validate_blocking()


# 19

def test_trample_vs_indestructible_blocker_excess_to_player():
    """CR 702.19b & 702.12b: Trample assigns lethal damage to an indestructible blocker before hitting the player."""
    atk = CombatCreature("Rhino", 4, 4, "A", trample=True)
    blk = CombatCreature("Wall", 0, 3, "B", indestructible=True)
    link_block(atk, blk)
    sim = CombatSimulator([atk], [blk])
    result = sim.simulate()
    assert blk not in result.creatures_destroyed
    assert result.damage_to_players["B"] == 1


# 20

def test_provoke_battalion_no_bonus_without_three_attackers():
    """CR 702.40a & 702.101a: Provoke doesn't grant battalion's bonus if only two creatures attack."""
    provoker = CombatCreature("Leader", 2, 2, "A", battalion=True)
    ally = CombatCreature("Ally", 2, 2, "A")
    blocker = CombatCreature("Guard", 2, 2, "B")
    provoker.provoke_target = blocker
    link_block(provoker, blocker)
    sim = CombatSimulator([provoker, ally], [blocker])
    result = sim.simulate()
    assert provoker in result.creatures_destroyed
    assert blocker in result.creatures_destroyed

