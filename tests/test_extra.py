import pytest

from magic_combat import CombatCreature, CombatSimulator, DamageAssignmentStrategy

def test_invalid_power_and_toughness():
    """CR 302.4b states a creature with 0 or less toughness is put into its owner's graveyard."""
    with pytest.raises(ValueError):
        CombatCreature(name="Bad", power=-1, toughness=1, controller="A")
    with pytest.raises(ValueError):
        CombatCreature(name="Bad", power=1, toughness=0, controller="A")

def test_damage_marked_non_negative():
    """CR 120.3d: Damage can't be negative."""
    with pytest.raises(ValueError):
        CombatCreature(name="Bad", power=1, toughness=1, controller="A", damage_marked=-1)

def test_has_protection():
    """CR 702.16b: Protection from a color stops effects of that color."""
    c = CombatCreature(name="Knight", power=2, toughness=2, controller="A", protection_colors={"black"})
    assert c.has_protection_from("black")
    assert not c.has_protection_from("red")

def test_str_representation():
    """CR 208.1: A creature's power and toughness are written as "x/y"."""
    c = CombatCreature(name="Bear", power=2, toughness=2, controller="A")
    assert str(c) == "Bear (2/2)"

def test_counters_modify_stats():
    """CR 122.1a: +1/+1 and -1/-1 counters modify power and toughness."""
    c = CombatCreature(name="Elf", power=1, toughness=1, controller="A")
    c.plus1_counters = 2
    c.minus1_counters = 1
    assert c.effective_power() == 2
    assert c.effective_toughness() == 2

def test_base_damage_strategy_order():
    """CR 510.1: The attacking player announces damage assignment order."""
    strat = DamageAssignmentStrategy()
    c1 = CombatCreature("A", 1, 1, "A")
    c2 = CombatCreature("B", 1, 1, "A")
    assert strat.order_blockers(c1, [c1, c2]) == [c1, c2]


def test_validate_blocking_errors():
    """CR 509.1a: A creature can block only a creature that's attacking."""
    attacker = CombatCreature("Att", 2, 2, "A")
    blocker = CombatCreature("Block", 2, 2, "B")
    blocker.blocking = CombatCreature("Other", 2, 2, "A")
    sim = CombatSimulator([attacker], [blocker])
    with pytest.raises(ValueError):
        sim.validate_blocking()

    attacker2 = CombatCreature("Att2", 2, 2, "A")
    blocker.blocking = attacker2
    attacker.blocked_by.append(blocker)
    sim = CombatSimulator([attacker, attacker2], [blocker])
    with pytest.raises(ValueError):
        sim.validate_blocking()
