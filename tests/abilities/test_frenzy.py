import pytest

from magic_combat import CombatCreature, CombatSimulator
from tests.conftest import link_block


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


def test_provoke_allows_frenzy_attacker_unblocked():
    """CR 702.35a & 702.40a: Forcing a block elsewhere lets a frenzy attacker hit unblocked for extra damage."""
    provoker = CombatCreature("Taunter", 2, 2, "A")
    frenzy_attacker = CombatCreature("Berserker", 2, 2, "A", frenzy=2)
    blk = CombatCreature("Guard", 2, 2, "B")
    provoker.blocked_by.append(blk)
    blk.blocking = provoker
    sim = CombatSimulator(
        [provoker, frenzy_attacker], [blk], provoke_map={provoker: blk}
    )
    result = sim.simulate()
    assert result.damage_to_players["B"] == 4


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


def test_frenzy_unblocked_bonus_three():
    """CR 702.35a: Frenzy 3 adds three power when unblocked."""
    atk = CombatCreature("Berserker", 2, 2, "A", frenzy=3)
    defender = CombatCreature("Dummy", 0, 1, "B")
    sim = CombatSimulator([atk], [defender])
    result = sim.simulate()
    assert result.damage_to_players["B"] == 5


def test_frenzy_multiple_creatures_each_get_bonus():
    """CR 702.35a: Each unblocked frenzy creature gets its own bonus."""
    atk1 = CombatCreature("Berserker1", 2, 2, "A", frenzy=1)
    atk2 = CombatCreature("Berserker2", 2, 2, "A", frenzy=2)
    defender = CombatCreature("Dummy", 0, 1, "B")
    sim = CombatSimulator([atk1, atk2], [defender])
    result = sim.simulate()
    assert result.damage_to_players["B"] == 7


def test_frenzy_bonus_recorded_after_combat():
    """CR 702.35a: The frenzy bonus is applied as a temporary power boost."""
    atk = CombatCreature("Berserker", 2, 2, "A", frenzy=2)
    defender = CombatCreature("Dummy", 0, 1, "B")
    sim = CombatSimulator([atk], [defender])
    sim.simulate()
    assert atk.temp_power == 2


def test_frenzy_blocked_by_two_no_bonus():
    """CR 702.35a: Being blocked by multiple creatures still prevents the frenzy bonus."""
    atk = CombatCreature("Berserker", 2, 2, "A", frenzy=2)
    b1 = CombatCreature("Guard1", 2, 2, "B")
    b2 = CombatCreature("Guard2", 2, 2, "B")
    link_block(atk, b1, b2)
    sim = CombatSimulator([atk], [b1, b2])
    result = sim.simulate()
    assert atk in result.creatures_destroyed
    # Attacker assigns all damage to one blocker, leaving the other alive
    assert (b1 in result.creatures_destroyed) != (b2 in result.creatures_destroyed)


def test_frenzy_trample_unblocked():
    """CR 702.35a & 702.19b: Trample doesn't interfere with frenzy when unblocked."""
    atk = CombatCreature("Beast", 3, 3, "A", frenzy=2, trample=True)
    defender = CombatCreature("Dummy", 0, 1, "B")
    sim = CombatSimulator([atk], [defender])
    result = sim.simulate()
    assert result.damage_to_players["B"] == 5


def test_frenzy_lifelink_unblocked():
    """CR 702.35a & 702.15a: Frenzy increases damage dealt with lifelink."""
    atk = CombatCreature("Berserker", 2, 2, "A", frenzy=2, lifelink=True)
    defender = CombatCreature("Dummy", 0, 1, "B")
    sim = CombatSimulator([atk], [defender])
    result = sim.simulate()
    assert result.damage_to_players["B"] == 4
    assert result.lifegain["A"] == 4
