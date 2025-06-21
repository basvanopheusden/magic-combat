import pytest

from magic_combat import CombatCreature, CombatSimulator, GameState, PlayerState, Color
from tests.conftest import link_block


def test_rampage_unblocked_no_bonus():
    """CR 702.23a: Rampage only triggers when blocked by multiple creatures."""
    atk = CombatCreature("Beast", 3, 3, "A", rampage=2)
    defender = CombatCreature("Dummy", 0, 1, "B")
    sim = CombatSimulator([atk], [defender])
    result = sim.simulate()
    assert result.damage_to_players["B"] == 3


def test_bushido_first_strike_vs_deathtouch():
    """CR 702.7b, 702.46a & 702.2b: Bushido with first strike kills a deathtouch blocker before it deals damage."""
    atk = CombatCreature("Samurai", 1, 1, "A", bushido=1, first_strike=True)
    blk = CombatCreature("Assassin", 1, 1, "B", deathtouch=True)
    link_block(atk, blk)
    sim = CombatSimulator([atk], [blk])
    result = sim.simulate()
    assert blk in result.creatures_destroyed
    assert atk not in result.creatures_destroyed


def test_wither_lifelink_indestructible():
    """CR 702.90a, 702.15a & 702.12b: Wither counters can reduce an indestructible creature to 0 toughness while granting life."""
    atk = CombatCreature("Corrosive", 2, 2, "A", wither=True, lifelink=True)
    blk = CombatCreature("Guardian", 2, 2, "B", indestructible=True)
    link_block(atk, blk)
    state = GameState(players={"A": PlayerState(life=20, creatures=[atk]), "B": PlayerState(life=20, creatures=[blk])})
    sim = CombatSimulator([atk], [blk], game_state=state)
    result = sim.simulate()
    assert blk in result.creatures_destroyed
    assert result.lifegain["A"] == 2
    assert blk.minus1_counters == 2


def test_fear_menace_one_blocker_illegal():
    """CR 702.36b & 702.110b: A creature with fear and menace needs two black or artifact blockers."""
    atk = CombatCreature("Night Terror", 2, 2, "A", fear=True, menace=True)
    blk = CombatCreature("Shade", 2, 2, "B", colors={Color.BLACK})
    link_block(atk, blk)
    sim = CombatSimulator([atk], [blk])
    with pytest.raises(ValueError):
        sim.validate_blocking()


def test_fear_menace_two_artifact_blockers_ok():
    """CR 702.36b & 702.110b: Two artifact blockers satisfy fear and menace."""
    atk = CombatCreature("Night Terror", 2, 2, "A", fear=True, menace=True)
    b1 = CombatCreature("Golem1", 1, 1, "B", artifact=True)
    b2 = CombatCreature("Golem2", 1, 1, "B", artifact=True)
    link_block(atk, b1, b2)
    sim = CombatSimulator([atk], [b1, b2])
    sim.validate_blocking()


def test_training_no_stronger_ally_no_counter():
    """CR 702.138a: Training doesn't trigger without a stronger attacking creature."""
    trainee = CombatCreature("Student", 2, 2, "A", training=True)
    ally = CombatCreature("Peer", 2, 2, "A")
    sim = CombatSimulator([trainee, ally], [])
    sim.simulate()
    assert trainee.plus1_counters == 0


def test_battalion_requires_three_attackers():
    """CR 702.101a: Battalion triggers only if it and at least two others attack."""
    leader = CombatCreature("Sergeant", 2, 2, "A", battalion=True)
    ally = CombatCreature("Ally", 2, 2, "A")
    sim = CombatSimulator([leader, ally], [])
    sim.simulate()
    assert leader.temp_power == 0


def test_dethrone_no_counter_if_defender_not_highest():
    """CR 702.103a: Dethrone gives a counter only when attacking the player with the most life."""
    atk = CombatCreature("Challenger", 2, 2, "A", dethrone=True)
    defender = CombatCreature("Dummy", 0, 1, "B")
    state = GameState(players={"A": PlayerState(life=20, creatures=[atk]), "B": PlayerState(life=15, creatures=[defender])})
    sim = CombatSimulator([atk], [defender], game_state=state)
    sim.simulate()
    assert atk.plus1_counters == 0


def test_intimidate_menace_single_blocker_fails():
    """CR 702.13a & 702.110b: Intimidate with menace needs two appropriate blockers."""
    atk = CombatCreature("Ruffian", 2, 2, "A", intimidate=True, menace=True, colors={Color.RED})
    blk = CombatCreature("Guard", 2, 2, "B", artifact=True)
    link_block(atk, blk)
    sim = CombatSimulator([atk], [blk])
    with pytest.raises(ValueError):
        sim.validate_blocking()


def test_intimidate_menace_two_allowed():
    """CR 702.13a & 702.110b: Two legal blockers satisfy intimidate and menace."""
    atk = CombatCreature("Ruffian", 2, 2, "A", intimidate=True, menace=True, colors={Color.RED})
    b1 = CombatCreature("Artifact", 1, 1, "B", artifact=True)
    b2 = CombatCreature("Red Ally", 1, 1, "B", colors={Color.RED})
    link_block(atk, b1, b2)
    sim = CombatSimulator([atk], [b1, b2])
    sim.validate_blocking()


def test_vigilance_melee_untapped_and_bonus():
    """CR 702.21b & 702.111a: Vigilance keeps the creature untapped while melee boosts power."""
    atk = CombatCreature("Knight", 2, 2, "A", vigilance=True, melee=True)
    defender = CombatCreature("Dummy", 0, 1, "B")
    sim = CombatSimulator([atk], [defender])
    result = sim.simulate()
    assert not atk.tapped
    assert result.damage_to_players["B"] == 3


def test_afflict_wither_blocked():
    """CR 702.131a & 702.90a: Afflict causes life loss while wither gives -1/-1 counters."""
    atk = CombatCreature("Tormentor", 2, 2, "A", afflict=2, wither=True)
    blk = CombatCreature("Soldier", 2, 2, "B")
    link_block(atk, blk)
    state = GameState(players={"A": PlayerState(life=20, creatures=[atk]), "B": PlayerState(life=20, creatures=[blk])})
    sim = CombatSimulator([atk], [blk], game_state=state)
    result = sim.simulate()
    assert blk.minus1_counters == 2
    assert state.players["B"].life == 18


def test_first_strike_wither_slays_before_damage():
    """CR 702.7b & 702.90a: First strike wither kills before the blocker can hit back."""
    atk = CombatCreature("Bladesinger", 1, 1, "A", first_strike=True, wither=True)
    blk = CombatCreature("Bear", 1, 1, "B")
    link_block(atk, blk)
    sim = CombatSimulator([atk], [blk])
    result = sim.simulate()
    assert blk in result.creatures_destroyed
    assert atk not in result.creatures_destroyed


def test_intimidate_artifact_blocker_allowed():
    """CR 702.13a: An artifact creature can block an intimidate attacker regardless of color."""
    atk = CombatCreature("Rogue", 2, 2, "A", intimidate=True, colors={Color.BLACK})
    blk = CombatCreature("Golem", 2, 2, "B", artifact=True)
    link_block(atk, blk)
    sim = CombatSimulator([atk], [blk])
    sim.validate_blocking()


def test_trample_wither_excess_damage_to_player():
    """CR 702.19b & 702.90a: Wither with trample assigns lethal counters then hits the player."""
    atk = CombatCreature("Crusher", 2, 2, "A", trample=True, wither=True)
    blk = CombatCreature("Wall", 1, 1, "B")
    link_block(atk, blk)
    sim = CombatSimulator([atk], [blk])
    result = sim.simulate()
    assert blk.minus1_counters == 1
    assert result.damage_to_players["B"] == 1


def test_trample_deathtouch_indestructible_min_damage():
    """CR 702.19b, 702.2b & 702.12b: Only one damage must be assigned to an indestructible blocker when the attacker has deathtouch and trample."""
    atk = CombatCreature("Crusher", 3, 3, "A", trample=True, deathtouch=True)
    blk = CombatCreature("Guardian", 5, 5, "B", indestructible=True)
    link_block(atk, blk)
    sim = CombatSimulator([atk], [blk])
    result = sim.simulate()
    assert result.damage_to_players["B"] == 2
    assert blk not in result.creatures_destroyed


def test_exalted_training_with_stronger_ally_counter_only():
    """CR 702.90a & 702.138a: Training triggers with a stronger ally while exalted doesn't with multiple attackers."""
    trainee = CombatCreature("Apprentice", 1, 1, "A", training=True)
    stronger = CombatCreature("Mentor", 3, 3, "A")
    exalted = CombatCreature("Squire", 2, 2, "A", exalted_count=1)
    sim = CombatSimulator([trainee, stronger, exalted], [])
    result = sim.simulate()
    assert trainee.plus1_counters == 1
    assert result.damage_to_players["defender"] == 7


def test_melee_battle_cry_both_bonuses():
    """CR 702.111a & 702.92a: Melee and battle cry from different creatures both increase damage."""
    leader = CombatCreature("Warleader", 2, 2, "A", battle_cry_count=1)
    melee = CombatCreature("Brawler", 2, 2, "A", melee=True)
    sim = CombatSimulator([leader, melee], [])
    result = sim.simulate()
    assert result.damage_to_players["defender"] == 6


def test_double_strike_infect_split_between_blockers():
    """CR 702.4b & 702.90a: Infect double strike assigns counters in both steps across blockers."""
    atk = CombatCreature("Toxic Duelist", 2, 2, "A", infect=True, double_strike=True)
    b1 = CombatCreature("B1", 2, 2, "B")
    b2 = CombatCreature("B2", 2, 2, "B")
    link_block(atk, b1, b2)
    sim = CombatSimulator([atk], [b1, b2])
    result = sim.simulate()
    assert b1.minus1_counters + b2.minus1_counters == 4


def test_infect_wither_combined_counters():
    """CR 702.90a & 702.90b: A creature with infect and wither deals damage as multiple -1/-1 counters."""
    atk = CombatCreature("Plague Bearer", 3, 3, "A", infect=True, wither=True)
    blk = CombatCreature("Target", 3, 3, "B")
    link_block(atk, blk)
    sim = CombatSimulator([atk], [blk])
    result = sim.simulate()
    assert blk.minus1_counters == 3
    assert blk in result.creatures_destroyed
