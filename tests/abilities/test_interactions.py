import pytest


from magic_combat import CombatCreature, CombatSimulator, Color, GameState, PlayerState, DEFAULT_STARTING_LIFE
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
    state = GameState(players={"A": PlayerState(life=DEFAULT_STARTING_LIFE, creatures=[atk]), "B": PlayerState(life=25, creatures=[defender])})
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

