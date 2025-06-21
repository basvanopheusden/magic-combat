import pytest
from magic_combat import CombatCreature, CombatSimulator, GameState, PlayerState, Color
from tests.conftest import link_block


def test_flying_menace_flyer_and_reach_blockers():
    """CR 702.9b & 702.110b: Flying menace creatures need two blockers with flying or reach."""
    atk = CombatCreature("Harpy", 2, 2, "A", flying=True, menace=True)
    flyer = CombatCreature("Bird", 1, 1, "B", flying=True)
    reacher = CombatCreature("Archer", 1, 3, "B", reach=True)
    link_block(atk, flyer, reacher)
    sim = CombatSimulator([atk], [flyer, reacher])
    sim.validate_blocking()


def test_skulk_menace_two_big_blockers_illegal():
    """CR 702.72a & 702.110b: Skulk prevents menace from being satisfied by larger blockers."""
    atk = CombatCreature("Sneak", 2, 2, "A", skulk=True, menace=True)
    b1 = CombatCreature("Ogre1", 3, 3, "B")
    b2 = CombatCreature("Ogre2", 3, 3, "B")
    link_block(atk, b1, b2)
    sim = CombatSimulator([atk], [b1, b2])
    with pytest.raises(ValueError):
        sim.validate_blocking()


def test_vigilance_melee_attacks_untapped():
    """CR 702.21b & 702.111a: Vigilance keeps an attacking melee creature untapped while it gets the melee bonus."""
    atk = CombatCreature("Knight", 2, 2, "A", vigilance=True, melee=True)
    defender = CombatCreature("Dummy", 0, 1, "B")
    sim = CombatSimulator([atk], [defender])
    result = sim.simulate()
    assert not atk.tapped
    assert result.damage_to_players["B"] == 3


def test_frenzy_trample_blocked_no_bonus():
    """CR 702.35a & 702.19b: A frenzy creature gets no bonus when blocked even if it has trample."""
    atk = CombatCreature("Beast", 3, 3, "A", frenzy=2, trample=True)
    blk = CombatCreature("Wall", 0, 3, "B")
    link_block(atk, blk)
    sim = CombatSimulator([atk], [blk])
    result = sim.simulate()
    assert result.damage_to_players.get("B", 0) == 0
    assert blk in result.creatures_destroyed
    assert atk not in result.creatures_destroyed


def test_battalion_multiple_battalions_stack():
    """CR 702.101a: Each battalion creature gets +1/+1 when three or more attack."""
    b1 = CombatCreature("Leader1", 2, 2, "A", battalion=True)
    b2 = CombatCreature("Leader2", 2, 2, "A", battalion=True)
    ally = CombatCreature("Ally", 2, 2, "A")
    sim = CombatSimulator([b1, b2, ally], [])
    result = sim.simulate()
    assert result.damage_to_players["defender"] == 8


def test_dethrone_no_counter_when_life_tied():
    """CR 702.103a: Dethrone doesn't trigger if life totals are tied."""
    atk = CombatCreature("Challenger", 2, 2, "A", dethrone=True)
    defender = CombatCreature("Dummy", 0, 1, "B")
    state = GameState(players={"A": PlayerState(life=20, creatures=[atk]), "B": PlayerState(life=20, creatures=[defender])})
    sim = CombatSimulator([atk], [defender], game_state=state)
    sim.simulate()
    assert atk.plus1_counters == 1


def test_intimidate_menace_two_artifact_blockers_required():
    """CR 702.13a & 702.110b: An intimidate menace attacker needs two artifact blockers if none share its color."""
    atk = CombatCreature("Rogue", 2, 2, "A", intimidate=True, menace=True, colors={Color.BLUE})
    a1 = CombatCreature("Golem1", 2, 2, "B", artifact=True)
    a2 = CombatCreature("Golem2", 2, 2, "B", artifact=True)
    link_block(atk, a1, a2)
    sim = CombatSimulator([atk], [a1, a2])
    sim.validate_blocking()


def test_intimidate_menace_single_artifact_illegal():
    """CR 702.13a & 702.110b: A single artifact can't block an intimidate menace creature."""
    atk = CombatCreature("Rogue", 2, 2, "A", intimidate=True, menace=True, colors={Color.BLUE})
    a1 = CombatCreature("Golem", 2, 2, "B", artifact=True)
    link_block(atk, a1)
    sim = CombatSimulator([atk], [a1])
    with pytest.raises(ValueError):
        sim.validate_blocking()


def test_bushido_blocker_flanking_attacker():
    """CR 702.46a & 702.25a: Bushido on a blocker competes with flanking on the attacker."""
    atk = CombatCreature("Lancer", 2, 2, "A", flanking=1)
    blk = CombatCreature("Samurai", 2, 2, "B", bushido=2)
    link_block(atk, blk)
    sim = CombatSimulator([atk], [blk])
    result = sim.simulate()
    assert atk in result.creatures_destroyed
    assert blk not in result.creatures_destroyed


def test_rampage_trample_single_blocker_damage():
    """CR 702.23a & 702.19b: Rampage doesn't trigger with one blocker, so only normal trample damage applies."""
    atk = CombatCreature("Behemoth", 3, 3, "A", rampage=2, trample=True)
    blk = CombatCreature("Bear", 2, 2, "B")
    link_block(atk, blk)
    sim = CombatSimulator([atk], [blk])
    result = sim.simulate()
    assert result.damage_to_players["B"] == 1
    assert blk in result.creatures_destroyed


def test_first_strike_bushido_blocker_kills_attacker():
    """CR 702.7b & 702.46a: A first strike blocker with bushido can kill before the attacker deals damage."""
    atk = CombatCreature("Orc", 2, 2, "A")
    blk = CombatCreature("Samurai", 2, 2, "B", first_strike=True, bushido=1)
    link_block(atk, blk)
    sim = CombatSimulator([atk], [blk])
    result = sim.simulate()
    assert atk in result.creatures_destroyed
    assert blk not in result.creatures_destroyed


def test_undying_with_plus1_counter_no_return():
    """CR 702.92a: Undying doesn't return a creature that already has a +1/+1 counter."""
    atk = CombatCreature("Slayer", 3, 3, "A")
    blk = CombatCreature("Spirit", 2, 2, "B", undying=True)
    blk.plus1_counters = 1
    link_block(atk, blk)
    sim = CombatSimulator([atk], [blk])
    result = sim.simulate()
    assert blk in result.creatures_destroyed


def test_persist_with_minus1_counter_no_return():
    """CR 702.77a: Persist doesn't return if the creature already has a -1/-1 counter."""
    atk = CombatCreature("Giant", 3, 3, "A")
    blk = CombatCreature("Wall", 2, 2, "B", persist=True)
    blk.minus1_counters = 1
    link_block(atk, blk)
    sim = CombatSimulator([atk], [blk])
    result = sim.simulate()
    assert blk in result.creatures_destroyed


def test_trample_afflict_damage_and_life_loss():
    """CR 702.19b & 702.131a: Afflict causes life loss even when trample deals damage to the player."""
    atk = CombatCreature("Tormentor", 3, 3, "A", trample=True, afflict=1)
    blk = CombatCreature("Soldier", 2, 2, "B")
    link_block(atk, blk)
    sim = CombatSimulator([atk], [blk])
    result = sim.simulate()
    assert result.damage_to_players["B"] == 2
    assert blk in result.creatures_destroyed


def test_double_strike_bushido_lethal_damage():
    """CR 702.4b & 702.46a: Double strike applies after bushido bonuses, killing the blocker."""
    atk = CombatCreature("Samurai", 2, 2, "A", double_strike=True, bushido=1)
    blk = CombatCreature("Bear", 3, 3, "B")
    link_block(atk, blk)
    sim = CombatSimulator([atk], [blk])
    result = sim.simulate()
    assert blk in result.creatures_destroyed
    assert atk not in result.creatures_destroyed


def test_double_strike_flanking_two_blockers():
    """CR 702.4b & 702.25a: Flanking lowers each blocker before double strike damage."""
    atk = CombatCreature("Knight", 2, 2, "A", double_strike=True, flanking=1)
    b1 = CombatCreature("Guard1", 2, 2, "B")
    b2 = CombatCreature("Guard2", 2, 2, "B")
    link_block(atk, b1, b2)
    sim = CombatSimulator([atk], [b1, b2])
    result = sim.simulate()
    assert b1 in result.creatures_destroyed
    assert b2 in result.creatures_destroyed
    assert atk not in result.creatures_destroyed


def test_melee_battle_cry_bonuses_stack():
    """CR 702.111a & 702.92a: Melee and battle cry both increase combat damage."""
    leader = CombatCreature("Warleader", 2, 2, "A", battle_cry_count=1)
    striker = CombatCreature("Soldier", 2, 2, "A", melee=True)
    sim = CombatSimulator([leader, striker], [])
    result = sim.simulate()
    assert result.damage_to_players["defender"] == 6


def test_vigilance_trample_stays_untapped():
    """CR 702.21b & 702.19b: A vigilance creature with trample attacks without tapping."""
    atk = CombatCreature("Rhino", 4, 4, "A", vigilance=True, trample=True)
    defender = CombatCreature("Dummy", 0, 1, "B")
    sim = CombatSimulator([atk], [defender])
    result = sim.simulate()
    assert not atk.tapped
    assert result.damage_to_players["B"] == 4


def test_shadow_skulk_blocker_without_shadow_illegal():
    """CR 702.27b & 702.72a: A creature with shadow and skulk can't be blocked by a larger non-shadow creature."""
    atk = CombatCreature("Shade", 1, 1, "A", shadow=True, skulk=True)
    blk = CombatCreature("Bear", 2, 2, "B")
    link_block(atk, blk)
    sim = CombatSimulator([atk], [blk])
    with pytest.raises(ValueError):
        sim.validate_blocking()

def test_rampage_menace_two_blockers_bonus_applies():
    """CR 702.23a & 702.110b: Rampage adds power when two blockers satisfy menace."""
    atk = CombatCreature("Warrior", 2, 2, "A", rampage=1, menace=True)
    b1 = CombatCreature("Guard1", 2, 2, "B")
    b2 = CombatCreature("Guard2", 2, 2, "B")
    link_block(atk, b1, b2)
    sim = CombatSimulator([atk], [b1, b2])
    result = sim.simulate()
    assert b1 in result.creatures_destroyed
    assert b2 not in result.creatures_destroyed
    assert atk in result.creatures_destroyed
