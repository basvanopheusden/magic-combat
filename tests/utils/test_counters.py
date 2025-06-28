import pytest

from magic_combat import (DEFAULT_STARTING_LIFE, CombatCreature,
                          CombatSimulator, GameState, PlayerState)
from tests.conftest import link_block


def test_effective_stats_with_plus1_counters():
    """CR 122.1a: +1/+1 counters modify a creature's power and toughness."""
    creature = CombatCreature("Scute", 1, 1, "A", _plus1_counters=2)
    assert creature.effective_power() == 3
    assert creature.effective_toughness() == 3


def test_effective_stats_with_minus1_counters():
    """CR 122.1a: -1/-1 counters lower a creature's power and toughness."""
    creature = CombatCreature("Weakling", 3, 3, "A", _minus1_counters=1)
    assert creature.effective_power() == 2
    assert creature.effective_toughness() == 2


def test_plus1_and_minus1_counters_net():
    """CR 122.1a: Different counters stack algebraically on stats."""
    creature = CombatCreature("Mixed", 2, 2, "A", _plus1_counters=2, _minus1_counters=1)
    assert creature.effective_power() == 3
    assert creature.effective_toughness() == 3


def test_training_cancels_minus1_counter():
    """CR 702.138a & 704.5q: Training adds a +1/+1 counter which cancels a -1/-1 counter."""
    trainee = CombatCreature("Trainee", 2, 2, "A", training=True)
    trainee.minus1_counters = 1
    mentor = CombatCreature("Mentor", 3, 3, "A")
    sim = CombatSimulator([trainee, mentor], [])
    sim.simulate()
    assert trainee.plus1_counters == 0
    assert trainee.minus1_counters == 0


def test_dethrone_counter_annihilates_existing_minus1():
    """CR 702.103a & 704.5q: Dethrone's +1/+1 counter removes an existing -1/-1 counter."""
    attacker = CombatCreature("Challenger", 2, 2, "A", dethrone=True)
    attacker.minus1_counters = 1
    defender = CombatCreature("Dummy", 0, 1, "B")
    state = GameState(
        players={
            "A": PlayerState(life=DEFAULT_STARTING_LIFE, creatures=[attacker]),
            "B": PlayerState(life=25, creatures=[defender]),
        }
    )
    sim = CombatSimulator([attacker], [defender], game_state=state)
    sim.simulate()
    assert attacker.plus1_counters == 0
    assert attacker.minus1_counters == 0


def test_wither_damage_gives_minus1_counters():
    """CR 702.90a: Damage from a creature with wither applies -1/-1 counters."""
    atk = CombatCreature("Corrosive", 2, 2, "A", wither=True)
    blk = CombatCreature("Wall", 2, 2, "B")
    link_block(atk, blk)
    sim = CombatSimulator([atk], [blk])
    result = sim.simulate()
    assert blk.minus1_counters == 2
    assert blk in result.creatures_destroyed


def test_persist_returns_with_counter():
    """CR 702.77a: Persist returns a creature that died without -1/-1 counters."""
    atk = CombatCreature("Crusher", 5, 5, "A")
    blk = CombatCreature("Spirit", 3, 3, "B", persist=True)
    link_block(atk, blk)
    sim = CombatSimulator([atk], [blk])
    result = sim.simulate()
    assert blk not in result.creatures_destroyed
    assert blk.minus1_counters == 1


def test_undying_returns_with_counter():
    """CR 702.92a: Undying returns the creature with a +1/+1 counter if it had none."""
    atk = CombatCreature("Phoenix", 2, 2, "A", undying=True)
    blk = CombatCreature("Bear", 2, 2, "B")
    link_block(atk, blk)
    sim = CombatSimulator([atk], [blk])
    result = sim.simulate()
    assert blk in result.creatures_destroyed
    assert atk.plus1_counters == 1
    assert atk not in result.creatures_destroyed


def test_persist_returns_clean_and_untapped():
    """CR 400.7 & 702.77a: A persist creature returns as a new object untapped with only one -1/-1 counter."""
    atk = CombatCreature("Crusher", 5, 5, "A")
    blk = CombatCreature("Spirit", 3, 3, "B", persist=True)
    blk.plus1_counters = 2
    blk.tapped = True
    link_block(atk, blk)
    sim = CombatSimulator([atk], [blk])
    sim.simulate()
    assert blk.plus1_counters == 0
    assert blk.minus1_counters == 1
    assert not blk.tapped


def test_undying_returns_clean_and_untapped():
    """CR 400.7 & 702.92a: An undying creature returns untapped with only one +1/+1 counter."""
    atk = CombatCreature("Phoenix", 2, 2, "A", undying=True)
    blk = CombatCreature("Bear", 2, 2, "B")
    atk.minus1_counters = 1
    atk.tapped = True
    link_block(atk, blk)
    sim = CombatSimulator([atk], [blk])
    sim.simulate()
    assert atk.minus1_counters == 0
    assert atk.plus1_counters == 1
    assert not atk.tapped


def test_annihilation_plus1_then_wither():
    """CR 704.5q: A +1/+1 counter and a -1/-1 counter destroy each other."""
    atk = CombatCreature("Witherer", 1, 1, "A", wither=True)
    blk = CombatCreature("Veteran", 1, 1, "B")
    blk.plus1_counters = 1
    link_block(atk, blk)
    sim = CombatSimulator([atk], [blk])
    sim.simulate()
    assert blk.plus1_counters == 0
    assert blk.minus1_counters == 0


def test_annihilation_multiple_pairs():
    """CR 704.5q: All matching pairs of counters are removed."""
    atk = CombatCreature("Witherer", 3, 3, "A", wither=True)
    blk = CombatCreature("Hero", 2, 2, "B")
    blk.plus1_counters = 2
    link_block(atk, blk)
    sim = CombatSimulator([atk], [blk])
    sim.simulate()
    assert blk.plus1_counters == 0
    assert blk.minus1_counters == 1


def test_apply_counter_annihilation():
    """CR 704.5q: +1/+1 and -1/-1 counters annihilate one another."""
    cr = CombatCreature("Test", 2, 2, "A")
    cr.plus1_counters = 3
    cr.minus1_counters = 1
    cr.apply_counter_annihilation()
    assert cr.plus1_counters == 2
    assert cr.minus1_counters == 0
