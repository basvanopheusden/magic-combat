from magic_combat import CombatCreature
from magic_combat import CombatSimulator
from tests.conftest import link_block

# Rampage tests


def test_rampage_bonus_with_extra_blockers():
    """CR 702.23a: Rampage gives +N/+N for each creature blocking it beyond the first."""
    atk = CombatCreature("Beast", 2, 2, "A", rampage=1)
    b1 = CombatCreature("B1", 2, 2, "B")
    b2 = CombatCreature("B2", 2, 2, "B")
    link_block(atk, b1, b2)
    sim = CombatSimulator([atk], [b1, b2])
    result = sim.simulate()
    dead = {c.name for c in result.creatures_destroyed}
    assert atk.name in dead
    assert (b1.name in dead) != (b2.name in dead)


def test_rampage_no_bonus_single_blocker():
    """CR 702.23a doesn't provide a bonus with only one blocker."""
    atk = CombatCreature("Beast", 2, 2, "A", rampage=2)
    blk = CombatCreature("Wall", 0, 3, "B")
    link_block(atk, blk)
    sim = CombatSimulator([atk], [blk])
    result = sim.simulate()
    assert result.creatures_destroyed == []


# Bushido tests


def test_bushido_on_attacker():
    """CR 702.46a: Bushido grants +N/+N when blocked."""
    atk = CombatCreature("Samurai", 2, 2, "A", bushido=2)
    blk = CombatCreature("Ogre", 3, 3, "B")
    link_block(atk, blk)
    sim = CombatSimulator([atk], [blk])
    result = sim.simulate()
    assert blk in result.creatures_destroyed
    assert atk not in result.creatures_destroyed


def test_bushido_on_blocker():
    """CR 702.46a applies when the creature blocks or becomes blocked."""
    atk = CombatCreature("Bear", 2, 2, "A")
    blk = CombatCreature("Samurai", 2, 2, "B", bushido=1)
    link_block(atk, blk)
    sim = CombatSimulator([atk], [blk])
    result = sim.simulate()
    assert atk in result.creatures_destroyed
    assert blk not in result.creatures_destroyed


# Exalted tests


def test_exalted_single_attacker():
    """CR 702.90a: Exalted gives +1/+1 if a creature attacks alone."""
    atk = CombatCreature("Champion", 2, 2, "A", exalted_count=1)
    blk = CombatCreature("Soldier", 2, 2, "B")
    link_block(atk, blk)
    sim = CombatSimulator([atk], [blk])
    result = sim.simulate()
    assert blk in result.creatures_destroyed
    assert atk not in result.creatures_destroyed


def test_exalted_multiple_instances_stack():
    """CR 702.90a: Multiple instances of exalted each apply."""
    atk = CombatCreature("Hero", 2, 2, "A", exalted_count=2)
    blk = CombatCreature("Giant", 3, 3, "B")
    link_block(atk, blk)
    sim = CombatSimulator([atk], [blk])
    result = sim.simulate()
    assert blk in result.creatures_destroyed
    assert atk not in result.creatures_destroyed


def test_exalted_no_bonus_with_multiple_attackers():
    """CR 702.90a: Exalted triggers only if exactly one creature attacks."""
    atk = CombatCreature("Lone", 2, 2, "A", exalted_count=1)
    ally = CombatCreature("Ally", 2, 2, "A")
    blk = CombatCreature("Guard", 2, 2, "B")
    link_block(atk, blk)
    sim = CombatSimulator([atk, ally], [blk])
    result = sim.simulate()
    assert blk in result.creatures_destroyed
    assert atk in result.creatures_destroyed


# Battle cry tests


def test_battle_cry_boosts_other_attacker():
    """CR 702.92a: Battle cry gives each other attacking creature +1/+0."""
    leader = CombatCreature("Leader", 2, 2, "A", battle_cry_count=1)
    ally = CombatCreature("Ally", 2, 2, "A")
    sim = CombatSimulator([leader, ally], [])
    result = sim.simulate()
    assert result.damage_to_players["defender"] == 5


def test_battle_cry_stacks_from_multiple():
    """CR 702.92a: Multiple battle cry abilities stack."""
    c1 = CombatCreature("Warcaller1", 2, 2, "A", battle_cry_count=1)
    c2 = CombatCreature("Warcaller2", 2, 2, "A", battle_cry_count=1)
    ally = CombatCreature("Ally", 2, 2, "A")
    sim = CombatSimulator([c1, c2, ally], [])
    result = sim.simulate()
    assert result.damage_to_players["defender"] == 10


def test_battle_cry_does_not_boost_self():
    """CR 702.92a: The creature with battle cry doesn't pump itself."""
    leader = CombatCreature("Warleader", 2, 2, "A", battle_cry_count=1)
    sim = CombatSimulator([leader], [])
    result = sim.simulate()
    assert result.damage_to_players["defender"] == 2


# Melee tests


def test_melee_bonus_when_attacking():
    """CR 702.111a: Melee gives +1/+1 while attacking a player."""
    atk = CombatCreature("Soldier", 2, 2, "A", melee=True)
    blk = CombatCreature("Guard", 2, 2, "B")
    link_block(atk, blk)
    sim = CombatSimulator([atk], [blk])
    result = sim.simulate()
    assert blk in result.creatures_destroyed
    assert atk not in result.creatures_destroyed


def test_melee_multiple_attackers_each_gain():
    """CR 702.111a: Each melee creature gets +1/+1."""
    m1 = CombatCreature("M1", 2, 2, "A", melee=True)
    m2 = CombatCreature("M2", 2, 2, "A", melee=True)
    sim = CombatSimulator([m1, m2], [])
    result = sim.simulate()
    assert result.damage_to_players["defender"] == 6


# Training tests


def test_training_with_stronger_ally():
    """CR 702.138a: Training puts a +1/+1 counter if it attacks with a creature of greater power."""
    trainee = CombatCreature("Trainee", 2, 2, "A", training=True)
    mentor = CombatCreature("Mentor", 4, 4, "A")
    sim = CombatSimulator([trainee, mentor], [])
    result = sim.simulate()
    assert trainee.plus1_counters == 1
    assert result.damage_to_players["defender"] == 7


def test_training_no_bonus_when_alone():
    """CR 702.138a doesn't trigger without a stronger attacker."""
    trainee = CombatCreature("Trainee", 2, 2, "A", training=True)
    sim = CombatSimulator([trainee], [])
    result = sim.simulate()
    assert trainee.plus1_counters == 0
    assert result.damage_to_players["defender"] == 2


# Battalion tests


# Combination test


def test_rampage_and_bushido_stack():
    """CR 702.23a & 702.46a: Rampage and bushido bonuses are cumulative."""
    atk = CombatCreature("Warrior", 2, 2, "A", rampage=1, bushido=1)
    b1 = CombatCreature("B1", 2, 2, "B")
    b2 = CombatCreature("B2", 2, 2, "B")
    link_block(atk, b1, b2)
    sim = CombatSimulator([atk], [b1, b2])
    result = sim.simulate()
    assert b1 in result.creatures_destroyed
    assert b2 in result.creatures_destroyed
    assert atk in result.creatures_destroyed
