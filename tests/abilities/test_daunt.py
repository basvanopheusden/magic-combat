import pytest

from magic_combat import CombatCreature, CombatSimulator, Color
from tests.conftest import link_block


# 1


def test_daunt_small_blocker_illegal():
    """CR 702.163a: Daunt means creatures with power 2 or less can't block."""
    atk = CombatCreature("Brute", 3, 3, "A", daunt=True)
    blk = CombatCreature("Goblin", 2, 2, "B")
    link_block(atk, blk)
    sim = CombatSimulator([atk], [blk])
    with pytest.raises(ValueError):
        sim.validate_blocking()


# 2


def test_daunt_large_blocker_allowed():
    """CR 702.163a allows blocking with a creature of power 3 or more."""
    atk = CombatCreature("Brute", 3, 3, "A", daunt=True)
    blk = CombatCreature("Ogre", 3, 3, "B")
    link_block(atk, blk)
    sim = CombatSimulator([atk], [blk])
    sim.validate_blocking()


# 3


def test_daunt_plus1_counter_allows_block():
    """CR 702.163a: A +1/+1 counter raising power above 2 enables blocking."""
    atk = CombatCreature("Brute", 3, 3, "A", daunt=True)
    blk = CombatCreature("Elf", 2, 2, "B")
    blk.plus1_counters = 1
    link_block(atk, blk)
    sim = CombatSimulator([atk], [blk])
    sim.validate_blocking()


# 4


def test_daunt_minus1_counter_prevents_block():
    """CR 702.163a: A -1/-1 counter dropping power to 2 forbids blocking."""
    atk = CombatCreature("Brute", 3, 3, "A", daunt=True)
    blk = CombatCreature("Ogre", 3, 3, "B")
    blk.minus1_counters = 1
    link_block(atk, blk)
    sim = CombatSimulator([atk], [blk])
    with pytest.raises(ValueError):
        sim.validate_blocking()


# 5


def test_daunt_menace_two_big_blockers_required():
    """CR 702.163a & 702.110b: Daunt menace attackers need two blockers with power over 2."""
    atk = CombatCreature("Terror", 4, 4, "A", daunt=True, menace=True)
    b1 = CombatCreature("Guard1", 3, 3, "B")
    b2 = CombatCreature("Guard2", 3, 3, "B")
    link_block(atk, b1, b2)
    sim = CombatSimulator([atk], [b1, b2])
    sim.validate_blocking()


# 6


def test_daunt_menace_small_blocker_illegal():
    """CR 702.163a & 702.110b: A small creature can't satisfy menace with daunt."""
    atk = CombatCreature("Terror", 4, 4, "A", daunt=True, menace=True)
    big = CombatCreature("Giant", 4, 4, "B")
    small = CombatCreature("Goblin", 2, 2, "B")
    link_block(atk, big, small)
    sim = CombatSimulator([atk], [big, small])
    with pytest.raises(ValueError):
        sim.validate_blocking()


# 7


def test_daunt_flying_small_flyer_illegal():
    """CR 702.163a & 702.9b: A small flyer can't block a daunt flyer."""
    atk = CombatCreature("Dragon", 4, 4, "A", daunt=True, flying=True)
    blk = CombatCreature("Bird", 2, 2, "B", flying=True)
    link_block(atk, blk)
    sim = CombatSimulator([atk], [blk])
    with pytest.raises(ValueError):
        sim.validate_blocking()


# 8


def test_daunt_flying_reach_large_allowed():
    """CR 702.163a & 702.9c: A reach creature with power 3 can block a daunt flyer."""
    atk = CombatCreature("Dragon", 4, 4, "A", daunt=True, flying=True)
    blk = CombatCreature("Archer", 3, 3, "B", reach=True)
    link_block(atk, blk)
    sim = CombatSimulator([atk], [blk])
    sim.validate_blocking()


# 9


def test_daunt_skulk_large_blocker_illegal():
    """CR 702.163a & 702.72a: Skulk also prevents blocks by larger creatures."""
    atk = CombatCreature("Sneak", 2, 2, "A", daunt=True, skulk=True)
    blk = CombatCreature("Ogre", 4, 4, "B")
    link_block(atk, blk)
    sim = CombatSimulator([atk], [blk])
    with pytest.raises(ValueError):
        sim.validate_blocking()


# 10


def test_daunt_skulk_small_blocker_illegal():
    """CR 702.163a: Even if skulk allows it, daunt stops small blockers."""
    atk = CombatCreature("Sneak", 2, 2, "A", daunt=True, skulk=True)
    blk = CombatCreature("Sprite", 1, 1, "B")
    link_block(atk, blk)
    sim = CombatSimulator([atk], [blk])
    with pytest.raises(ValueError):
        sim.validate_blocking()


# 11


def test_daunt_provoke_small_blocker_fails():
    """CR 702.163a & 702.40a: Provoke can't force a small creature to block."""
    atk = CombatCreature("Taunter", 3, 3, "A", daunt=True)
    blk = CombatCreature("Guard", 2, 2, "B")
    sim = CombatSimulator([atk], [blk], provoke_map={atk: blk})
    sim.validate_blocking()


# 12


def test_daunt_provoke_large_blocker_forced():
    """CR 702.163a & 702.40a: Provoke can force a large creature to block."""
    atk = CombatCreature("Taunter", 3, 3, "A", daunt=True, provoke=True)
    blk = CombatCreature("Ogre", 3, 3, "B")
    atk.blocked_by.append(blk)
    blk.blocking = atk
    sim = CombatSimulator([atk], [blk], provoke_map={atk: blk})
    sim.validate_blocking()


# 13


def test_daunt_trample_unblocked_hits_player():
    """CR 702.163a & 702.19b: A small blocker can't stop a daunt trampler."""
    atk = CombatCreature("Rhino", 4, 4, "A", daunt=True, trample=True)
    small = CombatCreature("Goblin", 2, 2, "B")
    link_block(atk, small)
    sim = CombatSimulator([atk], [small])
    with pytest.raises(ValueError):
        sim.validate_blocking()


# 14


def test_daunt_bushido_small_blocker_illegal():
    """CR 702.163a & 702.46a: Bushido bonuses don't allow small creatures to block."""
    atk = CombatCreature("Samurai", 3, 3, "A", daunt=True)
    blk = CombatCreature("Student", 2, 2, "B", bushido=2)
    link_block(atk, blk)
    sim = CombatSimulator([atk], [blk])
    with pytest.raises(ValueError):
        sim.validate_blocking()


# 15


def test_daunt_bushido_big_blocker_allowed():
    """CR 702.163a & 702.46a: A big bushido blocker can block and gets the bonus."""
    atk = CombatCreature("Samurai", 3, 3, "A", daunt=True)
    blk = CombatCreature("Master", 3, 3, "B", bushido=1)
    link_block(atk, blk)
    sim = CombatSimulator([atk], [blk])
    sim.validate_blocking()
    result = sim.simulate()
    assert atk in result.creatures_destroyed
    assert blk not in result.creatures_destroyed


# 16


def test_daunt_defender_small_cant_block():
    """CR 702.163a: Power 0 defender creatures can't block a daunt attacker."""
    atk = CombatCreature("Brute", 3, 3, "A", daunt=True)
    wall = CombatCreature("Wall", 0, 4, "B", defender=True)
    link_block(atk, wall)
    sim = CombatSimulator([atk], [wall])
    with pytest.raises(ValueError):
        sim.validate_blocking()


# 17


def test_daunt_first_strike_big_blocker_kills_attacker():
    """CR 702.163a & 702.7b: A large first-strike blocker can kill before damage."""
    atk = CombatCreature("Brute", 3, 3, "A", daunt=True)
    blk = CombatCreature("Knight", 3, 3, "B", first_strike=True)
    link_block(atk, blk)
    sim = CombatSimulator([atk], [blk])
    result = sim.simulate()
    assert atk in result.creatures_destroyed
    assert blk not in result.creatures_destroyed


# 18


def test_daunt_trample_large_blocker_absorbs_damage():
    """CR 702.163a & 702.19b: A big blocker soaks damage from a daunt trampler."""
    atk = CombatCreature("Beast", 4, 4, "A", daunt=True, trample=True)
    blk = CombatCreature("Ogre", 3, 3, "B")
    link_block(atk, blk)
    sim = CombatSimulator([atk], [blk])
    result = sim.simulate()
    assert blk in result.creatures_destroyed
    assert atk not in result.creatures_destroyed
    assert result.damage_to_players.get("B", 0) == 1


# 19


def test_daunt_intimidate_big_artifact_blocker_ok():
    """CR 702.163a & 702.13a: A big artifact can block an intimidate daunt creature."""
    atk = CombatCreature(
        "Rogue", 3, 3, "A", daunt=True, intimidate=True, colors={Color.BLUE}
    )
    blk = CombatCreature("Golem", 3, 3, "B", artifact=True)
    link_block(atk, blk)
    sim = CombatSimulator([atk], [blk])
    sim.validate_blocking()


# 20


def test_daunt_intimidate_small_artifact_illegal():
    """CR 702.163a & 702.13a: An artifact with power 2 can't block an intimidate daunt creature."""
    atk = CombatCreature(
        "Rogue", 3, 3, "A", daunt=True, intimidate=True, colors={Color.BLUE}
    )
    blk = CombatCreature("Golem", 2, 2, "B", artifact=True)
    link_block(atk, blk)
    sim = CombatSimulator([atk], [blk])
    with pytest.raises(ValueError):
        sim.validate_blocking()
