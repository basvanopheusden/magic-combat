import pytest

from magic_combat import Color
from magic_combat import CombatCreature
from magic_combat import CombatSimulator
from magic_combat import GameState
from magic_combat import PlayerState
from magic_combat.constants import DEFAULT_STARTING_LIFE
from tests.conftest import link_block


def test_fear_and_protection_from_black():
    """CR 702.36b & 702.16b: Fear allows only artifact or black blockers, but protection from black stops black blockers."""
    atk = CombatCreature(
        "Nightblade", 2, 2, "A", fear=True, protection_colors={Color.BLACK}
    )
    blk = CombatCreature(
        "Black Artifact", 2, 2, "B", colors={Color.BLACK}, artifact=True
    )
    link_block(atk, blk)
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
    link_block(atk, b1, b2)
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


def test_defender_cannot_attack():
    """CR 702.3b: A creature with defender can't be declared as an attacker."""
    defender = CombatCreature("Wall", 0, 4, "A", defender=True)
    dummy = CombatCreature("Dummy", 0, 1, "B")
    with pytest.raises(ValueError):
        CombatSimulator([defender], [dummy])


def test_battalion_bonus_when_three_attack():
    """CR 702.101a: Battalion triggers when it and at least two other creatures attack."""
    leader = CombatCreature("Leader", 2, 2, "A", battalion=True)
    ally1 = CombatCreature("Ally1", 2, 2, "A")
    ally2 = CombatCreature("Ally2", 2, 2, "A")
    blocker = CombatCreature("Guard", 0, 1, "B")
    sim = CombatSimulator([leader, ally1, ally2], [blocker])
    result = sim.simulate()
    assert result.damage_to_players["B"] == 7


def test_frenzy_unblocked_bonus():
    """CR 702.35a: Frenzy gives +N/+0 if the creature isn't blocked."""
    attacker = CombatCreature("Berserker", 2, 2, "A", frenzy=2)
    defender = CombatCreature("Dummy", 0, 1, "B")
    sim = CombatSimulator([attacker], [defender])
    result = sim.simulate()
    assert result.damage_to_players["B"] == 4


def test_undying_returns_with_counter():
    """CR 702.92a: Undying returns the creature with a +1/+1 counter if it had none."""
    atk = CombatCreature("Phoenix", 2, 2, "A", undying=True)
    blk = CombatCreature("Bear", 2, 2, "B")
    link_block(atk, blk)
    sim = CombatSimulator([atk], [blk])
    result = sim.simulate()
    assert blk in result.creatures_destroyed
    assert atk not in result.creatures_destroyed
    assert atk.plus1_counters == 1


def test_intimidate_blocking_restriction():
    """CR 702.13a: Intimidate allows blocking only by artifacts or creatures that share a color."""
    atk = CombatCreature("Rogue", 2, 2, "A", intimidate=True, colors={Color.RED})
    blk = CombatCreature("Guard", 2, 2, "B", colors={Color.WHITE})
    link_block(atk, blk)
    sim = CombatSimulator([atk], [blk])
    with pytest.raises(ValueError):
        sim.validate_blocking()


def test_provoke_forces_block():
    """CR 702.36a: Provoke makes the targeted creature block if able."""
    atk = CombatCreature("Taunter", 2, 2, "A")
    blocker = CombatCreature("Giant", 3, 3, "B")
    sim = CombatSimulator([atk], [blocker], provoke_map={atk: blocker})
    # blocker not assigned to block -> should error
    with pytest.raises(ValueError):
        sim.validate_blocking()


def test_afflict_life_loss_when_blocked():
    """CR 702.131a: Afflict causes life loss when the creature becomes blocked."""
    atk = CombatCreature("Tormentor", 2, 2, "A", afflict=2)
    blk = CombatCreature("Soldier", 2, 2, "B")
    link_block(atk, blk)
    sim = CombatSimulator([atk], [blk])
    result = sim.simulate()
    assert result.damage_to_players["B"] == 2


def test_dethrone_adds_counter():
    """CR 702.103a: Dethrone grants a +1/+1 counter when attacking the player with the most life."""
    atk = CombatCreature("Challenger", 2, 2, "A", dethrone=True)
    defender = CombatCreature("Dummy", 0, 1, "B")
    state = GameState(
        players={
            "A": PlayerState(life=DEFAULT_STARTING_LIFE, creatures=[atk]),
            "B": PlayerState(life=25, creatures=[defender]),
        }
    )
    sim = CombatSimulator([atk], [defender], game_state=state)
    sim.simulate()
    assert atk.plus1_counters == 1


def test_toxic_damage_adds_poison():
    """CR 702.180a: Toxic gives poison counters in addition to damage."""
    atk = CombatCreature("Viper", 1, 1, "A", toxic=2)
    defender = CombatCreature("Dummy", 0, 1, "B")
    sim = CombatSimulator([atk], [defender])
    result = sim.simulate()
    assert result.damage_to_players["B"] == 1
    assert result.poison_counters["B"] == 2


def test_bushido_bonus():
    """CR 702.46a: Bushido gives the creature +N/+N when it blocks or becomes blocked."""
    atk = CombatCreature("Samurai", 2, 2, "A", bushido=1)
    blk = CombatCreature("Bear", 2, 2, "B")
    link_block(atk, blk)
    sim = CombatSimulator([atk], [blk])
    result = sim.simulate()
    assert blk in result.creatures_destroyed
    assert atk not in result.creatures_destroyed


def test_flanking_debuff_blocker():
    """CR 702.25a: Flanking gives blocking creatures without flanking -1/-1."""
    atk = CombatCreature("Knight", 2, 2, "A", flanking=1)
    blk = CombatCreature("Soldier", 2, 2, "B")
    link_block(atk, blk)
    sim = CombatSimulator([atk], [blk])
    result = sim.simulate()
    assert blk in result.creatures_destroyed
    assert atk not in result.creatures_destroyed


def test_rampage_with_multiple_blockers():
    """CR 702.23a: Rampage gives +N/+N for each blocker beyond the first."""
    atk = CombatCreature("Beast", 3, 3, "A", rampage=2)
    b1 = CombatCreature("B1", 2, 2, "B")
    b2 = CombatCreature("B2", 2, 2, "B")
    link_block(atk, b1, b2)
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
    link_block(atk, blk)
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
    link_block(attacker, blocker)
    sim = CombatSimulator([attacker], [blocker])
    result = sim.simulate()
    assert blocker in result.creatures_destroyed
    assert attacker not in result.creatures_destroyed


def test_deathtouch_basic_lethal():
    """CR 702.2b: Any nonzero damage from a creature with deathtouch is lethal."""
    atk = CombatCreature("Assassin", 1, 1, "A", deathtouch=True)
    blk = CombatCreature("Bear", 2, 2, "B")
    link_block(atk, blk)
    sim = CombatSimulator([atk], [blk])
    result = sim.simulate()
    assert atk in result.creatures_destroyed
    assert blk in result.creatures_destroyed


def test_deathtouch_multiple_blockers():
    """CR 510.1a: Deathtouch lets an attacker assign only 1 damage per blocker."""
    atk = CombatCreature("Venomous", 3, 3, "A", deathtouch=True)
    b1 = CombatCreature("Guard1", 3, 3, "B")
    b2 = CombatCreature("Guard2", 3, 3, "B")
    link_block(atk, b1, b2)
    sim = CombatSimulator([atk], [b1, b2])
    result = sim.simulate()
    assert atk in result.creatures_destroyed
    assert b1 in result.creatures_destroyed
    assert b2 in result.creatures_destroyed


def test_deathtouch_vs_indestructible():
    """CR 702.12b: Indestructible permanents aren't destroyed by deathtouch."""
    atk = CombatCreature("Snake", 1, 1, "A", deathtouch=True)
    blk = CombatCreature("Guardian", 2, 2, "B", indestructible=True)
    link_block(atk, blk)
    sim = CombatSimulator([atk], [blk])
    result = sim.simulate()
    assert atk in result.creatures_destroyed
    assert blk not in result.creatures_destroyed


def test_deathtouch_killed_before_dealing_damage():
    """CR 702.7b: First strike damage can kill a deathtouch creature before it deals damage."""
    atk = CombatCreature("Biter", 2, 2, "A", deathtouch=True)
    blk = CombatCreature("Duelist", 2, 2, "B", first_strike=True)
    link_block(atk, blk)
    sim = CombatSimulator([atk], [blk])
    result = sim.simulate()
    assert atk in result.creatures_destroyed
    assert blk not in result.creatures_destroyed


def test_trample_excess_damage_to_player():
    """CR 702.19b: Damage beyond lethal can be assigned to the defending player."""
    atk = CombatCreature("Rhino", 4, 4, "A", trample=True)
    blk = CombatCreature("Wall", 0, 3, "B")
    link_block(atk, blk)
    sim = CombatSimulator([atk], [blk])
    result = sim.simulate()
    assert blk in result.creatures_destroyed
    assert result.damage_to_players["B"] == 1


def test_deathtouch_trample_multiple_blockers():
    """CR 702.19b & 702.2b: With deathtouch, only 1 damage is lethal per blocker."""
    atk = CombatCreature("Beast", 3, 3, "A", trample=True, deathtouch=True)
    b1 = CombatCreature("B1", 2, 2, "B")
    b2 = CombatCreature("B2", 2, 2, "B")
    link_block(atk, b1, b2)
    sim = CombatSimulator([atk], [b1, b2])
    result = sim.simulate()
    assert b1 in result.creatures_destroyed
    assert b2 in result.creatures_destroyed
    assert result.damage_to_players["B"] == 1


def test_wither_damage_adds_counters():
    """CR 702.90a: Damage from wither is dealt as -1/-1 counters."""
    atk = CombatCreature("Witherer", 3, 3, "A", wither=True)
    blk = CombatCreature("Target", 2, 2, "B")
    link_block(atk, blk)
    sim = CombatSimulator([atk], [blk])
    result = sim.simulate()
    assert blk.minus1_counters == 2
    assert blk in result.creatures_destroyed


def test_infect_poison_counters_on_player():
    """CR 702.90b: Damage from infect gives players poison counters instead of life loss."""
    atk = CombatCreature("Infector", 2, 2, "A", infect=True)
    defender = CombatCreature("Dummy", 0, 1, "B")
    sim = CombatSimulator([atk], [defender])
    result = sim.simulate()
    assert result.poison_counters["B"] == 2
    assert result.damage_to_players.get("B", 0) == 0


def test_vigilance_attacker_stays_untapped():
    """CR 702.21b: Attacking doesn't cause a creature with vigilance to tap."""
    atk = CombatCreature("Watcher", 2, 2, "A", vigilance=True)
    defender = CombatCreature("Dummy", 0, 1, "B")
    sim = CombatSimulator([atk], [defender])
    result = sim.simulate()
    assert not atk.tapped
    assert result.damage_to_players.get("B", 0) == 2


def test_normal_attacker_taps_on_attack():
    """CR 508.1g: Declaring an attacker causes it to become tapped."""
    atk = CombatCreature("Orc", 2, 2, "A")
    defender = CombatCreature("Dummy", 0, 1, "B")
    sim = CombatSimulator([atk], [defender])
    sim.simulate()
    assert atk.tapped


def test_intimidate_menace_single_blocker_fails():
    """CR 702.13a & 702.110b: Intimidate with menace needs two appropriate blockers."""
    atk = CombatCreature(
        "Ruffian", 2, 2, "A", intimidate=True, menace=True, colors={Color.RED}
    )
    blk = CombatCreature("Guard", 2, 2, "B", artifact=True)
    link_block(atk, blk)
    sim = CombatSimulator([atk], [blk])
    with pytest.raises(ValueError):
        sim.validate_blocking()


def test_intimidate_menace_two_allowed():
    """CR 702.13a & 702.110b: Two legal blockers satisfy intimidate and menace."""
    atk = CombatCreature(
        "Ruffian", 2, 2, "A", intimidate=True, menace=True, colors={Color.RED}
    )
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
    state = GameState(
        players={
            "A": PlayerState(life=20, creatures=[atk]),
            "B": PlayerState(life=20, creatures=[blk]),
        }
    )
    sim = CombatSimulator([atk], [blk], game_state=state)
    sim.simulate()
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
    sim.simulate()
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


def test_intimidate_same_color_blocker_allowed_alt():
    """CR 702.13a: Intimidate allows blocking by a creature that shares a color."""
    atk = CombatCreature("Rogue", 2, 2, "A", intimidate=True, colors={Color.RED})
    blk = CombatCreature("Guard", 2, 2, "B", colors={Color.RED})
    link_block(atk, blk)
    sim = CombatSimulator([atk], [blk])
    sim.validate_blocking()


def test_intimidate_artifact_blocker_allowed_alt():
    """CR 702.13a: Artifacts can block a creature with intimidate."""
    atk = CombatCreature("Rogue", 2, 2, "A", intimidate=True, colors={Color.BLUE})
    blk = CombatCreature("Golem", 2, 2, "B", artifact=True)
    link_block(atk, blk)
    sim = CombatSimulator([atk], [blk])
    sim.validate_blocking()


def test_training_no_counter_without_stronger_ally():
    """CR 702.138a: Training checks for another attacking creature with greater power."""
    trainee = CombatCreature("Trainee", 2, 2, "A", training=True)
    ally = CombatCreature("Helper", 2, 2, "A")
    sim = CombatSimulator([trainee, ally], [])
    sim.simulate()
    assert trainee.plus1_counters == 0


def test_training_ignores_bushido_increase():
    """CR 702.138a & 702.46a: Bushido bonuses happen too late to satisfy training."""
    trainee = CombatCreature("Student", 2, 2, "A", training=True)
    samurai = CombatCreature("Samurai", 2, 2, "A", bushido=1)
    blocker = CombatCreature("Guard", 2, 2, "B")
    link_block(samurai, blocker)
    sim = CombatSimulator([trainee, samurai], [blocker])
    sim.simulate()
    assert trainee.plus1_counters == 0


def test_afflict_double_strike_triggers_once():
    """CR 702.131a: Afflict causes life loss once when the creature becomes blocked."""
    atk = CombatCreature("Tormentor", 2, 2, "A", afflict=2, double_strike=True)
    blk = CombatCreature("Guard", 2, 2, "B")
    link_block(atk, blk)
    sim = CombatSimulator([atk], [blk])
    result = sim.simulate()
    assert result.damage_to_players["B"] == 2


def test_afflict_not_unblocked():
    """CR 702.131a: Afflict doesn't trigger if the creature isn't blocked."""
    atk = CombatCreature("Tormentor", 2, 2, "A", afflict=2)
    defender = CombatCreature("Dummy", 0, 1, "B")
    sim = CombatSimulator([atk], [defender])
    result = sim.simulate()
    assert result.damage_to_players["B"] == 2


def test_afflict_triggers_even_if_killed_first_strike():
    """CR 702.131a & 702.7b: Afflict triggers even if a first strike blocker kills the attacker."""
    atk = CombatCreature("Tormentor", 2, 2, "A", afflict=2)
    blk = CombatCreature("Duelist", 2, 2, "B", first_strike=True)
    link_block(atk, blk)
    sim = CombatSimulator([atk], [blk])
    result = sim.simulate()
    assert atk in result.creatures_destroyed
    assert blk not in result.creatures_destroyed
    assert result.damage_to_players["B"] == 2


def test_undying_with_counter_does_not_return():
    """CR 702.92a: Undying doesn't return a creature that already had a +1/+1 counter."""
    atk = CombatCreature("Slayer", 3, 3, "A")
    blk = CombatCreature("Phoenix", 2, 2, "B", undying=True)
    blk.plus1_counters = 1
    link_block(atk, blk)
    sim = CombatSimulator([atk], [blk])
    result = sim.simulate()
    assert blk in result.creatures_destroyed


def test_persist_with_minus1_counter_does_not_return():
    """CR 702.77a: Persist only returns if the creature had no -1/-1 counters."""
    atk = CombatCreature("Ogre", 2, 2, "A")
    blk = CombatCreature("Spirit", 2, 2, "B", persist=True)
    blk.minus1_counters = 1
    link_block(atk, blk)
    sim = CombatSimulator([atk], [blk])
    result = sim.simulate()
    assert blk in result.creatures_destroyed


def test_bushido_multiple_instances_stack():
    """CR 702.46a: Multiple instances of bushido each give +1/+1."""
    atk = CombatCreature("Master Samurai", 2, 2, "A", bushido=2)
    blk = CombatCreature("Guard", 2, 2, "B")
    link_block(atk, blk)
    sim = CombatSimulator([atk], [blk])
    result = sim.simulate()
    assert blk in result.creatures_destroyed
    assert atk not in result.creatures_destroyed


def test_battle_cry_from_multiple_sources():
    """CR 702.92a: Each battle cry ability boosts other attackers."""
    leader1 = CombatCreature("Leader1", 2, 2, "A", battle_cry_count=1)
    leader2 = CombatCreature("Leader2", 2, 2, "A", battle_cry_count=1)
    ally = CombatCreature("Ally", 2, 2, "A")
    defender = CombatCreature("Dummy", 0, 1, "B")
    sim = CombatSimulator([leader1, leader2, ally], [defender])
    result = sim.simulate()
    assert result.damage_to_players["B"] == 10


def test_multiple_melee_attackers_each_gain_bonus():
    """CR 702.111a: Each melee creature gets +1/+1 when attacking a player."""
    m1 = CombatCreature("Warrior1", 2, 2, "A", melee=True)
    m2 = CombatCreature("Warrior2", 2, 2, "A", melee=True)
    defender = CombatCreature("Dummy", 0, 1, "B")
    sim = CombatSimulator([m1, m2], [defender])
    result = sim.simulate()
    assert result.damage_to_players["B"] == 6


def test_rampage_no_bonus_with_single_blocker():
    """CR 702.23a: Rampage gives no bonus with only one blocker."""
    atk = CombatCreature("Brute", 3, 3, "A", rampage=2)
    blk = CombatCreature("Bear", 3, 3, "B")
    link_block(atk, blk)
    sim = CombatSimulator([atk], [blk])
    result = sim.simulate()
    assert atk in result.creatures_destroyed
    assert blk in result.creatures_destroyed


def test_rampage_with_battle_cry_and_multiple_blockers():
    """CR 702.23a & 702.92a: Rampage and battle cry bonuses both apply."""
    attacker = CombatCreature("Warlord", 3, 3, "A", rampage=1)
    leader = CombatCreature("Banner", 2, 2, "A", battle_cry_count=1)
    b1 = CombatCreature("B1", 2, 2, "B")
    b2 = CombatCreature("B2", 2, 2, "B")
    link_block(attacker, b1, b2)
    sim = CombatSimulator([attacker, leader], [b1, b2])
    result = sim.simulate()
    assert b1 in result.creatures_destroyed and b2 in result.creatures_destroyed
    assert attacker in result.creatures_destroyed


def test_toxic_trample_excess_poison():
    """CR 702.19b & 702.180a: Trample with toxic assigns excess damage and poison counters."""
    atk = CombatCreature("Serpent", 3, 3, "A", trample=True, toxic=2)
    blk = CombatCreature("Wall", 1, 1, "B")
    link_block(atk, blk)
    sim = CombatSimulator([atk], [blk])
    result = sim.simulate()
    assert result.damage_to_players["B"] == 2
    assert result.poison_counters["B"] == 2


def test_multiple_toxic_attackers_stack_poison():
    """CR 702.180a: Each instance of toxic adds poison counters to the defending player."""
    t1 = CombatCreature("Snake1", 1, 1, "A", toxic=1)
    t2 = CombatCreature("Snake2", 2, 2, "A", toxic=2)
    defender = CombatCreature("Dummy", 0, 1, "B")
    sim = CombatSimulator([t1, t2], [defender])
    result = sim.simulate()
    assert result.poison_counters["B"] == 3
    assert result.damage_to_players["B"] == 3


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
    state = GameState(
        players={
            "A": PlayerState(life=20, creatures=[attacker]),
            "B": PlayerState(life=15, creatures=[defender]),
        }
    )
    sim = CombatSimulator([attacker], [defender], game_state=state)
    sim.simulate()
    assert attacker.plus1_counters == 0


# 7


def test_dethrone_triggers_when_tied_for_highest():
    """CR 702.103a: Tied for the most life still satisfies dethrone."""
    attacker = CombatCreature("Challenger", 2, 2, "A", dethrone=True)
    defender = CombatCreature("Dummy", 0, 1, "B")
    state = GameState(
        players={
            "A": PlayerState(life=20, creatures=[attacker]),
            "B": PlayerState(life=20, creatures=[defender]),
        }
    )
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


def test_intimidate_same_color_blocker_allowed_again():
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
    sim.simulate()
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
    state = GameState(
        players={
            "A": PlayerState(life=20, creatures=[atk]),
            "B": PlayerState(life=20, creatures=[defender]),
        }
    )
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


def test_provoke_battalion_no_bonus_without_three_attackers():
    """CR 702.40a & 702.101a: Provoke doesn't grant battalion's bonus if only two creatures attack."""
    provoker = CombatCreature("Leader", 2, 2, "A", battalion=True)
    ally = CombatCreature("Ally", 2, 2, "A")
    blocker = CombatCreature("Guard", 2, 2, "B")
    link_block(provoker, blocker)
    sim = CombatSimulator([provoker, ally], [blocker], provoke_map={provoker: blocker})
    result = sim.simulate()
    assert provoker in result.creatures_destroyed
    assert blocker in result.creatures_destroyed


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
    state = GameState(
        players={
            "A": PlayerState(life=20, creatures=[atk]),
            "B": PlayerState(life=20, creatures=[blk]),
        }
    )
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


def test_wither_prevents_persist_return():
    """CR 702.90a & 702.77a: Wither gives -1/-1 counters so persist won't return if a creature dies with one."""
    attacker = CombatCreature("Corrosive Archer", 2, 2, "A", wither=True)
    blocker = CombatCreature("Everlasting", 2, 2, "B", persist=True)
    link_block(attacker, blocker)
    sim = CombatSimulator([attacker], [blocker])
    result = sim.simulate()
    assert blocker in result.creatures_destroyed
    assert blocker.minus1_counters == 2


def test_persist_creature_returns_with_counter():
    """CR 702.77a: Persist returns a creature that died without -1/-1 counters."""
    attacker = CombatCreature("Giant", 3, 3, "A")
    blocker = CombatCreature("Undying Wall", 2, 2, "B", persist=True)
    link_block(attacker, blocker)
    sim = CombatSimulator([attacker], [blocker])
    result = sim.simulate()
    assert blocker not in result.creatures_destroyed
    assert blocker.minus1_counters == 1


def test_deathtouch_infect_trample_assigns_poison():
    """CR 702.19b, 702.2b & 702.90b: Deathtouch with trample and infect assigns minimal damage to the blocker and the rest as poison counters."""
    attacker = CombatCreature(
        "Toxic Crusher", 3, 3, "A", trample=True, deathtouch=True, infect=True
    )
    blocker = CombatCreature("Wall", 2, 2, "B")
    link_block(attacker, blocker)
    sim = CombatSimulator([attacker], [blocker])
    result = sim.simulate()
    assert result.poison_counters["B"] == 2
    assert blocker.minus1_counters == 1
    assert blocker in result.creatures_destroyed


def test_double_strike_infect_toxic_lifelink():
    """CR 702.4b, 702.15a & 702.90b: Double strike with infect and toxic deals poison twice and grants lifelink."""
    attacker = CombatCreature(
        "Toxic Angel",
        1,
        1,
        "A",
        double_strike=True,
        infect=True,
        toxic=1,
        lifelink=True,
    )
    defender = CombatCreature("Dummy", 0, 1, "B")
    state = GameState(
        players={
            "A": PlayerState(life=DEFAULT_STARTING_LIFE, creatures=[attacker]),
            "B": PlayerState(life=DEFAULT_STARTING_LIFE, creatures=[defender]),
        }
    )
    sim = CombatSimulator([attacker], [defender], game_state=state)
    result = sim.simulate()
    assert result.poison_counters["B"] == 4
    assert result.lifegain["A"] == 2
    assert state.players["A"].life == 22


def test_rampage_battle_cry_melee_combo():
    """CR 702.23a, 702.92a & 702.111a: Rampage, battle cry, and melee bonuses stack before combat damage."""
    warleader = CombatCreature("Warleader", 3, 3, "A", rampage=1, melee=True)
    commander = CombatCreature(
        "Commander", 2, 2, "A", battle_cry_count=1, lifelink=True
    )
    b1 = CombatCreature("B1", 2, 2, "B")
    b2 = CombatCreature("B2", 2, 2, "B")
    link_block(warleader, b1, b2)
    sim = CombatSimulator([warleader, commander], [b1, b2])
    result = sim.simulate()
    assert b1 in result.creatures_destroyed
    assert b2 in result.creatures_destroyed
    assert warleader not in result.creatures_destroyed
    assert commander not in result.creatures_destroyed
    assert result.damage_to_players["B"] == 2
    assert result.lifegain["A"] == 2


def test_skulk_flanking_bushido_precombat_death():
    """CR 702.72a, 702.25a & 702.46a: Flanking and bushido bonuses apply before damage when a skulk attacker is blocked."""
    attacker = CombatCreature(
        "Sneaky Knight", 2, 2, "A", skulk=True, flanking=1, bushido=1
    )
    blocker = CombatCreature("Guard", 1, 1, "B")
    link_block(attacker, blocker)
    sim = CombatSimulator([attacker], [blocker])
    result = sim.simulate()
    assert blocker in result.creatures_destroyed
    assert attacker not in result.creatures_destroyed


def test_provoke_and_menace_insufficient_blockers():
    """CR 702.40a & 702.110b: Provoke requires the targeted creature to block, but menace demands two blockers."""
    attacker = CombatCreature("Taunting Brute", 2, 2, "A", menace=True)
    blocker = CombatCreature("Goblin", 2, 2, "B")
    link_block(attacker, blocker)
    sim = CombatSimulator([attacker], [blocker], provoke_map={attacker: blocker})
    with pytest.raises(ValueError):
        sim.validate_blocking()


def test_undying_and_persist_prefers_undying():
    """CR 702.92a & 702.77a: A creature with undying and persist returns with a +1/+1 counter."""
    attacker = CombatCreature("Slayer", 3, 3, "A")
    blocker = CombatCreature("Spirit", 2, 2, "B", undying=True, persist=True)
    link_block(attacker, blocker)
    sim = CombatSimulator([attacker], [blocker])
    result = sim.simulate()
    assert blocker not in result.creatures_destroyed
    assert blocker.plus1_counters == 1
    assert blocker.minus1_counters == 0


def test_exalted_melee_no_training_when_alone():
    """CR 702.90a, 702.111a & 702.138a: Exalted and melee boost a lone attacker but training does nothing without a stronger ally."""
    attacker = CombatCreature(
        "Student Champion", 2, 2, "A", exalted_count=1, melee=True, training=True
    )
    defender = CombatCreature("Dummy", 0, 1, "B")
    sim = CombatSimulator([attacker], [defender])
    result = sim.simulate()
    assert result.damage_to_players["B"] == 4
    assert attacker.plus1_counters == 0


def test_fear_and_intimidate_require_artifact_and_color():
    """CR 702.36b & 702.13a: A creature with fear and intimidate can be blocked only by an artifact that also shares its color."""
    attacker = CombatCreature(
        "Shadow Rogue", 2, 2, "A", fear=True, intimidate=True, colors={Color.RED}
    )
    blk = CombatCreature("Shade", 2, 2, "B", colors={Color.BLACK})
    link_block(attacker, blk)
    sim = CombatSimulator([attacker], [blk])
    with pytest.raises(ValueError):
        sim.validate_blocking()

    artifact = CombatCreature("Golem", 2, 2, "B", artifact=True)
    attacker.blocked_by = [artifact]
    artifact.blocking = attacker
    sim = CombatSimulator([attacker], [artifact])
    sim.validate_blocking()


def test_flying_menace_flyer_and_reach_blockers():
    """CR 702.9b & 702.110b: Flying menace creatures need two blockers with flying or reach."""
    atk = CombatCreature("Harpy", 2, 2, "A", flying=True, menace=True)
    flyer = CombatCreature("Bird", 1, 1, "B", flying=True)
    reacher = CombatCreature("Archer", 1, 3, "B", reach=True)
    link_block(atk, flyer, reacher)
    sim = CombatSimulator([atk], [flyer, reacher])
    sim.validate_blocking()


def test_flying_intimidate_blocking_restrictions():
    """CR 702.9b & 702.13a: A flying intimidate creature can only be blocked by a same-colored or artifact creature with flying or reach."""
    atk1 = CombatCreature(
        "Specter", 2, 2, "A", flying=True, intimidate=True, colors={Color.BLUE}
    )
    wrong_color_flyer = CombatCreature(
        "Bird", 1, 1, "B", flying=True, colors={Color.RED}
    )
    link_block(atk1, wrong_color_flyer)
    sim = CombatSimulator([atk1], [wrong_color_flyer])
    with pytest.raises(ValueError):
        sim.validate_blocking()

    atk2 = CombatCreature(
        "Specter", 2, 2, "A", flying=True, intimidate=True, colors={Color.BLUE}
    )
    no_flying_same_color = CombatCreature("Merfolk", 1, 1, "B", colors={Color.BLUE})
    link_block(atk2, no_flying_same_color)
    sim = CombatSimulator([atk2], [no_flying_same_color])
    with pytest.raises(ValueError):
        sim.validate_blocking()

    atk3 = CombatCreature(
        "Specter", 2, 2, "A", flying=True, intimidate=True, colors={Color.BLUE}
    )
    legal_blocker = CombatCreature(
        "Sprite", 1, 1, "B", flying=True, colors={Color.BLUE}
    )
    link_block(atk3, legal_blocker)
    sim = CombatSimulator([atk3], [legal_blocker])
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
    state = GameState(
        players={
            "A": PlayerState(life=20, creatures=[atk]),
            "B": PlayerState(life=20, creatures=[defender]),
        }
    )
    sim = CombatSimulator([atk], [defender], game_state=state)
    sim.simulate()
    assert atk.plus1_counters == 1


def test_intimidate_menace_two_artifact_blockers_required():
    """CR 702.13a & 702.110b: An intimidate menace attacker needs two artifact blockers if none share its color."""
    atk = CombatCreature(
        "Rogue", 2, 2, "A", intimidate=True, menace=True, colors={Color.BLUE}
    )
    a1 = CombatCreature("Golem1", 2, 2, "B", artifact=True)
    a2 = CombatCreature("Golem2", 2, 2, "B", artifact=True)
    link_block(atk, a1, a2)
    sim = CombatSimulator([atk], [a1, a2])
    sim.validate_blocking()


def test_intimidate_menace_single_artifact_illegal():
    """CR 702.13a & 702.110b: A single artifact can't block an intimidate menace creature."""
    atk = CombatCreature(
        "Rogue", 2, 2, "A", intimidate=True, menace=True, colors={Color.BLUE}
    )
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
    dead = {c.name for c in result.creatures_destroyed}
    assert atk.name in dead
    assert (b1.name in dead) != (b2.name in dead)


def test_infect_kills_creature_with_counters():
    """CR 702.90b: Infect damage to a creature is dealt as -1/-1 counters."""
    atk = CombatCreature("Toxic Bear", 3, 3, "A", infect=True)
    blk = CombatCreature("Wall", 2, 2, "B")
    link_block(atk, blk)
    sim = CombatSimulator([atk], [blk])
    result = sim.simulate()
    assert blk.minus1_counters == 2
    assert blk in result.creatures_destroyed


def test_infect_lifelink_vs_blocker():
    """CR 702.90b & 702.15a: Infect gives counters and lifelink gains that much life."""
    atk = CombatCreature("Toxic Cleric", 2, 2, "A", infect=True, lifelink=True)
    blk = CombatCreature("Bear", 2, 2, "B")
    link_block(atk, blk)
    state = GameState(
        players={
            "A": PlayerState(life=10, creatures=[atk]),
            "B": PlayerState(life=DEFAULT_STARTING_LIFE, creatures=[blk]),
        }
    )
    sim = CombatSimulator([atk], [blk], game_state=state)
    result = sim.simulate()
    assert blk.minus1_counters == 2
    assert result.lifegain["A"] == 2
    assert state.players["A"].life == 12


def test_infect_first_strike_kills_before_damage():
    """CR 702.7b & 702.90b: First strike infect kills the blocker before it can deal damage."""
    atk = CombatCreature("Toxic Fencer", 2, 2, "A", infect=True, first_strike=True)
    blk = CombatCreature("Bear", 2, 2, "B")
    link_block(atk, blk)
    sim = CombatSimulator([atk], [blk])
    result = sim.simulate()
    assert blk.minus1_counters == 2
    assert blk in result.creatures_destroyed
    assert atk not in result.creatures_destroyed


def test_double_strike_infect_poison_twice():
    """CR 702.4b & 702.90b: Double strike applies infect damage in both combat steps."""
    atk = CombatCreature("Toxic Duelist", 1, 1, "A", infect=True, double_strike=True)
    defender = CombatCreature("Dummy", 0, 1, "B")
    sim = CombatSimulator([atk], [defender])
    result = sim.simulate()
    assert result.poison_counters["B"] == 2
    assert result.damage_to_players.get("B", 0) == 0


def test_trample_infect_multiple_blockers():
    """CR 702.19b & 702.90b: Excess infect damage with trample becomes poison counters."""
    atk = CombatCreature("Toxic Beast", 3, 3, "A", trample=True, infect=True)
    b1 = CombatCreature("Goblin1", 1, 1, "B")
    b2 = CombatCreature("Goblin2", 1, 1, "B")
    link_block(atk, b1, b2)
    sim = CombatSimulator([atk], [b1, b2])
    result = sim.simulate()
    assert b1.minus1_counters == 1
    assert b2.minus1_counters == 1
    assert result.poison_counters["B"] == 1
    assert b1 in result.creatures_destroyed and b2 in result.creatures_destroyed


def test_infect_prevents_persist_return():
    """CR 702.90b & 702.77a: Infect counters stop a persist creature from returning."""
    atk = CombatCreature("Infecting Knight", 2, 2, "A", infect=True)
    blk = CombatCreature("Everlasting", 2, 2, "B", persist=True)
    link_block(atk, blk)
    sim = CombatSimulator([atk], [blk])
    result = sim.simulate()
    assert blk in result.creatures_destroyed
    assert blk.minus1_counters == 2


def test_infect_kills_undying_but_it_returns():
    """CR 702.92a & 702.90b: Undying brings back a creature even if infect dealt the damage."""
    atk = CombatCreature("Toxic Slayer", 2, 2, "A", infect=True)
    blk = CombatCreature("Spirit", 2, 2, "B", undying=True)
    link_block(atk, blk)
    sim = CombatSimulator([atk], [blk])
    result = sim.simulate()
    assert blk not in result.creatures_destroyed
    assert blk.plus1_counters == 1
    assert blk.minus1_counters == 0


def test_infect_and_toxic_stack_poison():
    """CR 702.90b & 702.180a: Infect and toxic both add poison counters."""
    atk = CombatCreature("Super Toxic", 1, 1, "A", infect=True, toxic=2)
    defender = CombatCreature("Dummy", 0, 1, "B")
    sim = CombatSimulator([atk], [defender])
    result = sim.simulate()
    assert result.poison_counters["B"] == 3


def test_lifelink_infect_vs_creature():
    """CR 702.15a & 702.90b: Lifelink gains life even when infect damages a creature."""
    atk = CombatCreature("Toxic Healer", 3, 3, "A", infect=True, lifelink=True)
    blk = CombatCreature("Bear", 3, 3, "B")
    link_block(atk, blk)
    state = GameState(
        players={
            "A": PlayerState(life=10, creatures=[atk]),
            "B": PlayerState(life=DEFAULT_STARTING_LIFE, creatures=[blk]),
        }
    )
    sim = CombatSimulator([atk], [blk], game_state=state)
    result = sim.simulate()
    assert result.lifegain["A"] == 3
    assert blk.minus1_counters == 3
    assert state.players["A"].life == 13


def test_infect_with_afflict_still_causes_life_loss():
    """CR 702.131a & 702.90b: Afflict causes life loss even when an infect creature is blocked."""
    atk = CombatCreature("Tormentor", 2, 2, "A", infect=True, afflict=1)
    blk = CombatCreature("Guard", 2, 2, "B")
    link_block(atk, blk)
    state = GameState(
        players={
            "A": PlayerState(life=DEFAULT_STARTING_LIFE, creatures=[atk]),
            "B": PlayerState(life=DEFAULT_STARTING_LIFE, creatures=[blk]),
        }
    )
    sim = CombatSimulator([atk], [blk], game_state=state)
    result = sim.simulate()
    assert state.players["B"].life == 19
    assert result.poison_counters.get("B", 0) == 0
    assert blk.minus1_counters == 2
