import pytest
from magic_combat import (
    CombatCreature,
    CombatSimulator,
    GameState,
    PlayerState,
    STARTING_LIFE_TOTAL,
)


# Rampage tests

def test_rampage_bonus_with_extra_blockers():
    """CR 702.23a: Rampage gives +N/+N for each creature blocking it beyond the first."""
    atk = CombatCreature("Beast", 2, 2, "A", rampage=1)
    b1 = CombatCreature("B1", 2, 2, "B")
    b2 = CombatCreature("B2", 2, 2, "B")
    atk.blocked_by.extend([b1, b2])
    b1.blocking = atk
    b2.blocking = atk
    sim = CombatSimulator([atk], [b1, b2])
    result = sim.simulate()
    assert b1 in result.creatures_destroyed
    assert b2 not in result.creatures_destroyed
    assert atk in result.creatures_destroyed

def test_rampage_no_bonus_single_blocker():
    """CR 702.23a doesn't provide a bonus with only one blocker."""
    atk = CombatCreature("Beast", 2, 2, "A", rampage=2)
    blk = CombatCreature("Wall", 0, 3, "B")
    atk.blocked_by.append(blk)
    blk.blocking = atk
    sim = CombatSimulator([atk], [blk])
    result = sim.simulate()
    assert result.creatures_destroyed == []

# Bushido tests

def test_bushido_on_attacker():
    """CR 702.46a: Bushido grants +N/+N when blocked."""
    atk = CombatCreature("Samurai", 2, 2, "A", bushido=2)
    blk = CombatCreature("Ogre", 3, 3, "B")
    atk.blocked_by.append(blk)
    blk.blocking = atk
    sim = CombatSimulator([atk], [blk])
    result = sim.simulate()
    assert blk in result.creatures_destroyed
    assert atk not in result.creatures_destroyed

def test_bushido_on_blocker():
    """CR 702.46a applies when the creature blocks or becomes blocked."""
    atk = CombatCreature("Bear", 2, 2, "A")
    blk = CombatCreature("Samurai", 2, 2, "B", bushido=1)
    atk.blocked_by.append(blk)
    blk.blocking = atk
    sim = CombatSimulator([atk], [blk])
    result = sim.simulate()
    assert atk in result.creatures_destroyed
    assert blk not in result.creatures_destroyed

# Exalted tests

def test_exalted_single_attacker():
    """CR 702.90a: Exalted gives +1/+1 if a creature attacks alone."""
    atk = CombatCreature("Champion", 2, 2, "A", exalted_count=1)
    blk = CombatCreature("Soldier", 2, 2, "B")
    atk.blocked_by.append(blk)
    blk.blocking = atk
    sim = CombatSimulator([atk], [blk])
    result = sim.simulate()
    assert blk in result.creatures_destroyed
    assert atk not in result.creatures_destroyed

def test_exalted_multiple_instances_stack():
    """CR 702.90a: Multiple instances of exalted each apply."""
    atk = CombatCreature("Hero", 2, 2, "A", exalted_count=2)
    blk = CombatCreature("Giant", 3, 3, "B")
    atk.blocked_by.append(blk)
    blk.blocking = atk
    sim = CombatSimulator([atk], [blk])
    result = sim.simulate()
    assert blk in result.creatures_destroyed
    assert atk not in result.creatures_destroyed

def test_exalted_no_bonus_with_multiple_attackers():
    """CR 702.90a: Exalted triggers only if exactly one creature attacks."""
    atk = CombatCreature("Lone", 2, 2, "A", exalted_count=1)
    ally = CombatCreature("Ally", 2, 2, "A")
    blk = CombatCreature("Guard", 2, 2, "B")
    atk.blocked_by.append(blk)
    blk.blocking = atk
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
    atk.blocked_by.append(blk)
    blk.blocking = atk
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

def test_battalion_triggers_with_three_attackers():
    """CR 702.101a: Battalion triggers when it and at least two other creatures attack."""
    leader = CombatCreature("Leader", 2, 2, "A", battalion=True)
    ally1 = CombatCreature("Ally1", 2, 2, "A")
    ally2 = CombatCreature("Ally2", 2, 2, "A")
    sim = CombatSimulator([leader, ally1, ally2], [])
    result = sim.simulate()
    assert result.damage_to_players["defender"] == 7


def test_battalion_not_with_two_attackers():
    """CR 702.101a: Battalion doesn't trigger with fewer than three attackers."""
    leader = CombatCreature("Leader", 2, 2, "A", battalion=True)
    ally = CombatCreature("Ally", 2, 2, "A")
    sim = CombatSimulator([leader, ally], [])
    result = sim.simulate()
    assert result.damage_to_players["defender"] == 4

# Dethrone tests

def test_dethrone_when_opponent_highest_life():
    """CR 702.103a: Dethrone gives a +1/+1 counter if the defending player has the most life."""
    atk = CombatCreature("Challenger", 2, 2, "A", dethrone=True)
    defender = CombatCreature("Dummy", 0, 1, "B")
    state = GameState(players={"A": PlayerState(life=STARTING_LIFE_TOTAL, creatures=[atk]), "B": PlayerState(life=25, creatures=[defender])})
    sim = CombatSimulator([atk], [defender], game_state=state)
    sim.simulate()
    assert atk.plus1_counters == 1


def test_dethrone_no_counter_when_not_highest():
    """CR 702.103a: No dethrone counter if defender doesn't have the most life."""
    atk = CombatCreature("Challenger", 2, 2, "A", dethrone=True)
    defender = CombatCreature("Dummy", 0, 1, "B")
    state = GameState(players={"A": PlayerState(life=STARTING_LIFE_TOTAL, creatures=[atk]), "B": PlayerState(life=15, creatures=[defender])})
    sim = CombatSimulator([atk], [defender], game_state=state)
    sim.simulate()
    assert atk.plus1_counters == 0

# Frenzy tests

def test_frenzy_unblocked_bonus():
    """CR 702.35a: Frenzy gives +N/+0 if the creature isn't blocked."""
    atk = CombatCreature("Berserker", 2, 2, "A", frenzy=2)
    defender = CombatCreature("Dummy", 0, 1, "B")
    sim = CombatSimulator([atk], [defender])
    result = sim.simulate()
    assert result.damage_to_players["B"] == 4


def test_frenzy_no_bonus_when_blocked():
    """CR 702.35a: Frenzy has no effect if the creature is blocked."""
    atk = CombatCreature("Berserker", 2, 2, "A", frenzy=3)
    blk = CombatCreature("Guard", 3, 3, "B")
    atk.blocked_by.append(blk)
    blk.blocking = atk
    sim = CombatSimulator([atk], [blk])
    result = sim.simulate()
    assert atk in result.creatures_destroyed
    assert blk not in result.creatures_destroyed

# Combination test

def test_rampage_and_bushido_stack():
    """CR 702.23a & 702.46a: Rampage and bushido bonuses are cumulative."""
    atk = CombatCreature("Warrior", 2, 2, "A", rampage=1, bushido=1)
    b1 = CombatCreature("B1", 2, 2, "B")
    b2 = CombatCreature("B2", 2, 2, "B")
    atk.blocked_by.extend([b1, b2])
    b1.blocking = atk
    b2.blocking = atk
    sim = CombatSimulator([atk], [b1, b2])
    result = sim.simulate()
    assert b1 in result.creatures_destroyed
    assert b2 in result.creatures_destroyed
    assert atk in result.creatures_destroyed
