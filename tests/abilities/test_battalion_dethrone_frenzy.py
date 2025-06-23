from magic_combat import CombatCreature, CombatSimulator, GameState, PlayerState
from tests.conftest import link_block


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


def test_battalion_requires_three_attackers():
    """CR 702.101a: Battalion triggers when it and at least two other creatures attack."""
    leader = CombatCreature("Leader", 2, 2, "A", battalion=True)
    ally1 = CombatCreature("Ally1", 2, 2, "A")
    ally2 = CombatCreature("Ally2", 2, 2, "A")
    sim = CombatSimulator([leader, ally1, ally2], [])
    result = sim.simulate()
    assert result.damage_to_players["defender"] == 7


def test_battalion_fewer_than_three_no_bonus():
    """CR 702.101a: Battalion doesn't trigger with fewer than three attackers."""
    leader = CombatCreature("Leader", 2, 2, "A", battalion=True)
    ally = CombatCreature("Ally", 2, 2, "A")
    sim = CombatSimulator([leader, ally], [])
    result = sim.simulate()
    assert result.damage_to_players["defender"] == 4


def test_dethrone_triggers_when_opponent_highest():
    """CR 702.103a: Dethrone grants a +1/+1 counter if the defending player has the most life."""
    atk = CombatCreature("Challenger", 2, 2, "A", dethrone=True)
    defender = CombatCreature("Dummy", 0, 1, "B")
    state = GameState(players={
        "A": PlayerState(life=20, creatures=[atk]),
        "B": PlayerState(life=25, creatures=[defender]),
    })
    sim = CombatSimulator([atk], [defender], game_state=state)
    sim.simulate()
    assert atk.plus1_counters == 1


def test_dethrone_no_counter_when_not_highest():
    """CR 702.103a: No dethrone counter if the defending player doesn't have the most life."""
    atk = CombatCreature("Challenger", 2, 2, "A", dethrone=True)
    defender = CombatCreature("Dummy", 0, 1, "B")
    state = GameState(players={
        "A": PlayerState(life=20, creatures=[atk]),
        "B": PlayerState(life=15, creatures=[defender]),
    })
    sim = CombatSimulator([atk], [defender], game_state=state)
    sim.simulate()
    assert atk.plus1_counters == 0


def test_frenzy_unblocked_bonus():
    """CR 702.35a: Frenzy gives +N/+0 if the creature isn't blocked."""
    atk = CombatCreature("Berserker", 2, 2, "A", frenzy=2)
    defender = CombatCreature("Dummy", 0, 1, "B")
    sim = CombatSimulator([atk], [defender])
    result = sim.simulate()
    assert result.damage_to_players["B"] == 4


def test_frenzy_blocked_no_bonus():
    """CR 702.35a: Frenzy has no effect if the creature is blocked."""
    atk = CombatCreature("Berserker", 2, 2, "A", frenzy=3)
    blk = CombatCreature("Guard", 3, 3, "B")
    link_block(atk, blk)
    sim = CombatSimulator([atk], [blk])
    result = sim.simulate()
    assert atk in result.creatures_destroyed
    assert blk not in result.creatures_destroyed
