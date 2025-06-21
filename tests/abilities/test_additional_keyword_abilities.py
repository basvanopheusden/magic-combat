import pytest

from magic_combat import (
    CombatCreature,
    CombatSimulator,
    GameState,
    PlayerState,
    DEFAULT_STARTING_LIFE,
    Color,
)
from tests.conftest import link_block


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
    atk.provoke_target = blocker
    sim = CombatSimulator([atk], [blocker])
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
    """CR 702.??: Toxic gives poison counters in addition to damage."""
    atk = CombatCreature("Viper", 1, 1, "A", toxic=2)
    defender = CombatCreature("Dummy", 0, 1, "B")
    sim = CombatSimulator([atk], [defender])
    result = sim.simulate()
    assert result.damage_to_players["B"] == 1
    assert result.poison_counters["B"] == 2

