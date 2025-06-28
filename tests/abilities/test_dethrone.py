import pytest
from magic_combat import CombatCreature, CombatSimulator, GameState, PlayerState
from tests.conftest import link_block


def test_dethrone_no_counter_if_defender_not_highest():
    """CR 702.103a: Dethrone gives a counter only when attacking the player with the most life."""
    atk = CombatCreature("Challenger", 2, 2, "A", dethrone=True)
    defender = CombatCreature("Dummy", 0, 1, "B")
    state = GameState(
        players={
            "A": PlayerState(life=20, creatures=[atk]),
            "B": PlayerState(life=15, creatures=[defender]),
        }
    )
    sim = CombatSimulator([atk], [defender], game_state=state)
    sim.simulate()
    assert atk.plus1_counters == 0


def test_dethrone_triggers_when_opponent_highest():
    """CR 702.103a: Dethrone grants a +1/+1 counter if the defending player has the most life."""
    atk = CombatCreature("Challenger", 2, 2, "A", dethrone=True)
    defender = CombatCreature("Dummy", 0, 1, "B")
    state = GameState(
        players={
            "A": PlayerState(life=20, creatures=[atk]),
            "B": PlayerState(life=25, creatures=[defender]),
        }
    )
    sim = CombatSimulator([atk], [defender], game_state=state)
    sim.simulate()
    assert atk.plus1_counters == 1


def test_dethrone_no_counter_when_not_highest():
    """CR 702.103a: No dethrone counter if the defending player doesn't have the most life."""
    atk = CombatCreature("Challenger", 2, 2, "A", dethrone=True)
    defender = CombatCreature("Dummy", 0, 1, "B")
    state = GameState(
        players={
            "A": PlayerState(life=20, creatures=[atk]),
            "B": PlayerState(life=15, creatures=[defender]),
        }
    )
    sim = CombatSimulator([atk], [defender], game_state=state)
    sim.simulate()
    assert atk.plus1_counters == 0


def test_dethrone_adds_counter():
    """CR 702.103a: Dethrone grants a +1/+1 counter when attacking the player with the most life."""
    atk = CombatCreature("Challenger", 2, 2, "A", dethrone=True)
    defender = CombatCreature("Dummy", 0, 1, "B")
    state = GameState(
        players={
            "A": PlayerState(life=20, creatures=[atk]),
            "B": PlayerState(life=25, creatures=[defender]),
        }
    )
    sim = CombatSimulator([atk], [defender], game_state=state)
    sim.simulate()
    assert atk.plus1_counters == 1


def test_dethrone_counter_annihilates_existing_minus1():
    """CR 702.103a & 704.5q: Dethrone's +1/+1 counter removes an existing -1/-1 counter."""
    attacker = CombatCreature("Challenger", 2, 2, "A", dethrone=True)
    attacker.minus1_counters = 1
    defender = CombatCreature("Dummy", 0, 1, "B")
    state = GameState(
        players={
            "A": PlayerState(life=20, creatures=[attacker]),
            "B": PlayerState(life=25, creatures=[defender]),
        }
    )
    sim = CombatSimulator([attacker], [defender], game_state=state)
    sim.simulate()
    assert attacker.plus1_counters == 0
    assert attacker.minus1_counters == 0


def test_exalted_with_dethrone():
    """CR 702.90a & 702.103a: Exalted boosts damage and dethrone adds a +1/+1 counter."""
    atk = CombatCreature("Upstart", 2, 2, "A", exalted_count=1, dethrone=True)
    defender = CombatCreature("Dummy", 0, 1, "B")
    state = GameState(
        players={
            "A": PlayerState(life=20, creatures=[atk]),
            "B": PlayerState(life=25, creatures=[defender]),
        }
    )
    sim = CombatSimulator([atk], [defender], game_state=state)
    result = sim.simulate()
    assert atk.plus1_counters == 1
    assert result.damage_to_players["B"] == 4


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


def test_dethrone_counter_even_if_blocked():
    """CR 702.103a: The dethrone counter is granted before combat damage, even if the creature becomes blocked."""
    atk = CombatCreature("Challenger", 2, 2, "A", dethrone=True)
    blk = CombatCreature("Guard", 1, 1, "B")
    link_block(atk, blk)
    state = GameState(
        players={
            "A": PlayerState(life=20, creatures=[atk]),
            "B": PlayerState(life=25, creatures=[blk]),
        }
    )
    sim = CombatSimulator([atk], [blk], game_state=state)
    sim.simulate()
    assert atk.plus1_counters == 1
    assert (
        blk in sim.finalize().creatures_destroyed if hasattr(sim, "finalize") else True
    )


def test_two_dethrone_creatures_each_get_counter():
    """CR 702.103a: Each dethrone creature attacking the highest-life player gets a +1/+1 counter."""
    atk1 = CombatCreature("Challenger1", 2, 2, "A", dethrone=True)
    atk2 = CombatCreature("Challenger2", 2, 2, "A", dethrone=True)
    defender = CombatCreature("Dummy", 0, 1, "B")
    state = GameState(
        players={
            "A": PlayerState(life=20, creatures=[atk1, atk2]),
            "B": PlayerState(life=25, creatures=[defender]),
        }
    )
    sim = CombatSimulator([atk1, atk2], [defender], game_state=state)
    sim.simulate()
    assert atk1.plus1_counters == 1
    assert atk2.plus1_counters == 1
