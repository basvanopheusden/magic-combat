import pytest

from magic_combat import CombatCreature, CombatSimulator, DamageAssignmentStrategy, MostCreaturesKilledStrategy

def test_effective_power_toughness():
    """CR 121.1a: Each +1/+1 counter on a creature gives it +1/+1."""
    c = CombatCreature("Buffed", 2, 2, "A")
    c.plus1_counters = 2
    c.minus1_counters = 1
    assert c.effective_power() == 3
    assert c.effective_toughness() == 3

def test_has_protection_from():
    """CR 702.16b: A creature with protection from a color can't be damaged by sources of that color."""
    c = CombatCreature("Paladin", 2, 2, "A", protection_colors={"black"})
    assert c.has_protection_from("black")
    assert not c.has_protection_from("red")

def test_is_destroyed_by_damage_indestructible():
    """CR 702.12b: Indestructible permanents aren't destroyed by lethal damage."""
    c = CombatCreature("Guardian", 2, 2, "A", indestructible=True)
    c.damage_marked = 5
    assert not c.is_destroyed_by_damage()

def test_string_representation():
    """CR 108.1: A creature's name and stats are public information."""
    c = CombatCreature("Ogre", 3, 3, "A")
    assert str(c) == "Ogre (3/3)"

def test_validate_blocking_unknown_attacker():
    """CR 509.1a: A creature can block only a creature that's attacking the player or planeswalker it's defending."""
    atk = CombatCreature("Attacker", 2, 2, "A")
    blk = CombatCreature("Blocker", 1, 1, "B")
    blk.blocking = CombatCreature("Other", 2, 2, "A")
    sim = CombatSimulator([atk], [blk])
    with pytest.raises(ValueError):
        sim.validate_blocking()

def test_validate_blocking_inconsistent_assignments():
    """CR 509.2: Each blocker must actually block the creature it's declared to block."""
    atk = CombatCreature("Attacker", 2, 2, "A")
    blk = CombatCreature("Blocker", 1, 1, "B")
    atk.blocked_by.append(blk)
    # blocker is not set to block attacker
    sim = CombatSimulator([atk], [blk])
    with pytest.raises(ValueError):
        sim.validate_blocking()

def test_strategy_called_for_ordering(monkeypatch):
    """CR 510.1a: The attacking creature's controller orders blockers for assigning damage."""
    atk = CombatCreature("Attacker", 3, 3, "A")
    b1 = CombatCreature("B1", 1, 1, "B")
    b2 = CombatCreature("B2", 2, 2, "B")
    atk.blocked_by.extend([b1, b2])
    b1.blocking = atk
    b2.blocking = atk

    called = []

    class TestStrategy(DamageAssignmentStrategy):
        def order_blockers(self, attacker, blockers):
            called.append(True)
            # reverse order to prove strategy used
            return list(reversed(blockers))

    sim = CombatSimulator([atk], [b1, b2], strategy=TestStrategy())
    sim.simulate()
    assert called
    assert b2.damage_marked > 0  # first in reversed order

def test_most_creatures_killed_strategy_sort():
    """CR 510.1a: Damage is assigned in the order chosen by the attacker."""
    atk = CombatCreature("Attacker", 4, 4, "A")
    w1 = CombatCreature("Wall1", 0, 4, "B")
    w2 = CombatCreature("Wall2", 0, 1, "B")
    strategy = MostCreaturesKilledStrategy()
    ordered = strategy.order_blockers(atk, [w1, w2])
    assert ordered == [w2, w1]


def test_unblocked_without_defenders():
    """CR 510.1c: An unblocked creature deals damage to the player it's attacking."""
    atk = CombatCreature("Attacker", 2, 2, "A")
    sim = CombatSimulator([atk], [])
    result = sim.simulate()
    assert result.damage_to_players["defender"] == 2

