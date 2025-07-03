import pytest

from magic_combat import CombatCreature
from magic_combat import CombatSimulator
from tests.conftest import link_block


def test_persist_revival_value_drop():
    """CR 702.77a: Persist returns with a -1/-1 counter reducing its value."""
    atk = CombatCreature("Giant", 3, 3, "A")
    blk = CombatCreature("Spirit", 2, 2, "B", persist=True)
    link_block(atk, blk)
    result = CombatSimulator([atk], [blk]).simulate()
    assert blk.minus1_counters == 1
    assert blk not in result.creatures_destroyed
    assert result.score("A", "B")[1] == pytest.approx(2.5)


def test_infect_kills_persist_full_value_loss():
    """CR 702.90a & 702.77a: Infect counters keep a persist creature from returning
    when lethal damage destroys both combatants."""
    atk = CombatCreature("Infector", 2, 2, "A", infect=True)
    blk = CombatCreature("Spirit", 2, 2, "B", persist=True)
    link_block(atk, blk)
    result = CombatSimulator([atk], [blk]).simulate()
    assert blk in result.creatures_destroyed
    assert atk in result.creatures_destroyed
    assert result.score("A", "B")[1] == pytest.approx(0.0)


def test_persist_survives_infect_counter():
    """CR 702.90a: Infect damage leaves -1/-1 counters when not lethal."""
    atk = CombatCreature("Infector", 1, 1, "A", infect=True)
    blk = CombatCreature("Spirit", 2, 2, "B", persist=True)
    link_block(atk, blk)
    result = CombatSimulator([atk], [blk]).simulate()
    assert blk.minus1_counters == 1
    assert blk not in result.creatures_destroyed
    assert result.score("A", "B")[1] == pytest.approx(0.0)


def test_wither_annihilates_plus_one_counter():
    """CR 704.5q: Wither counters remove existing +1/+1 counters."""
    atk = CombatCreature("Witherer", 1, 1, "A", wither=True)
    blk = CombatCreature("Spirit", 2, 2, "B", persist=True)
    blk.plus1_counters = 1
    link_block(atk, blk)
    result = CombatSimulator([atk], [blk]).simulate()
    assert blk.plus1_counters == 0 and blk.minus1_counters == 0
    assert result.score("A", "B")[1] == pytest.approx(-0.5)


def test_wither_kills_persist_with_plus_one():
    """CR 702.90a & 702.77a: Wither damage can prevent persist from returning
    when both creatures die."""
    atk = CombatCreature("Witherer", 3, 3, "A", wither=True)
    blk = CombatCreature("Spirit", 2, 2, "B", persist=True)
    blk.plus1_counters = 1
    link_block(atk, blk)
    result = CombatSimulator([atk], [blk]).simulate()
    assert blk in result.creatures_destroyed
    assert atk in result.creatures_destroyed
    assert result.score("A", "B")[1] == pytest.approx(0.0)


def test_undying_returns_after_infect():
    """CR 702.92a & 702.90a: Undying returns even if infect dealt the damage."""
    atk = CombatCreature("Infector", 2, 2, "A", infect=True)
    blk = CombatCreature("Phoenix", 2, 2, "B", undying=True)
    link_block(atk, blk)
    result = CombatSimulator([atk], [blk]).simulate()
    assert blk.plus1_counters == 1
    assert blk not in result.creatures_destroyed
    assert result.score("A", "B")[1] == pytest.approx(-4.0)


def test_undying_no_return_with_plus_one():
    """CR 702.92a: A creature with a +1/+1 counter doesn't return with undying."""
    atk = CombatCreature("Giant", 3, 3, "A")
    blk = CombatCreature("Phoenix", 2, 2, "B", undying=True)
    blk.plus1_counters = 1
    link_block(atk, blk)
    result = CombatSimulator([atk], [blk]).simulate()
    assert blk in result.creatures_destroyed
    assert result.score("A", "B")[1] == pytest.approx(-2.0)


def test_infect_survivor_value_drop():
    """CR 702.90a: Creatures surviving infect suffer -1/-1 counters reducing value."""
    atk = CombatCreature("Infector", 1, 1, "A", infect=True)
    blk = CombatCreature("Bear", 2, 2, "B")
    link_block(atk, blk)
    result = CombatSimulator([atk], [blk]).simulate()
    assert blk.minus1_counters == 1
    assert blk not in result.creatures_destroyed
    assert result.score("A", "B")[1] == pytest.approx(-0.5)


def test_wither_survivor_value_drop():
    """CR 702.90a: Wither damage weakens a creature that survives combat."""
    atk = CombatCreature("Witherer", 1, 1, "A", wither=True)
    blk = CombatCreature("Bear", 2, 2, "B")
    link_block(atk, blk)
    result = CombatSimulator([atk], [blk]).simulate()
    assert blk.minus1_counters == 1
    assert blk not in result.creatures_destroyed
    assert result.score("A", "B")[1] == pytest.approx(-0.5)


def test_infect_annihilates_plus_one():
    """CR 704.5q: Infect counters remove existing +1/+1 counters."""
    atk = CombatCreature("Infector", 1, 1, "A", infect=True)
    blk = CombatCreature("Bear", 2, 2, "B")
    blk.plus1_counters = 1
    link_block(atk, blk)
    result = CombatSimulator([atk], [blk]).simulate()
    assert blk.plus1_counters == 0 and blk.minus1_counters == 0
    assert result.score("A", "B")[1] == pytest.approx(-0.5)


def test_multiple_counters_annihilate():
    """CR 704.5q: All matched +1/+1 and -1/-1 counters are removed."""
    atk = CombatCreature("Witherer", 2, 2, "A", wither=True)
    blk = CombatCreature("Veteran", 2, 2, "B")
    blk.plus1_counters = 2
    link_block(atk, blk)
    result = CombatSimulator([atk], [blk]).simulate()
    assert blk.plus1_counters == 0 and blk.minus1_counters == 0
    assert result.score("A", "B")[1] == pytest.approx(-0.5)
