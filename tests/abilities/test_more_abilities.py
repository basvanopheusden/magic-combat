import pytest
from magic_combat import CombatCreature, CombatSimulator, GameState, PlayerState, Color
from tests.conftest import link_block



def test_intimidate_same_color_blocker_allowed():
    """CR 702.13a: Intimidate allows blocking by a creature that shares a color."""
    atk = CombatCreature("Rogue", 2, 2, "A", intimidate=True, colors={Color.RED})
    blk = CombatCreature("Guard", 2, 2, "B", colors={Color.RED})
    link_block(atk, blk)
    sim = CombatSimulator([atk], [blk])
    sim.validate_blocking()


def test_intimidate_artifact_blocker_allowed():
    """CR 702.13a: Artifacts can block a creature with intimidate."""
    atk = CombatCreature("Rogue", 2, 2, "A", intimidate=True, colors={Color.BLUE})
    blk = CombatCreature("Golem", 2, 2, "B", artifact=True)
    link_block(atk, blk)
    sim = CombatSimulator([atk], [blk])
    sim.validate_blocking()


def test_training_no_counter_without_stronger_ally():
    """CR 702.138a: Training checks for another attacking creature with greater power."""
    trainee = CombatCreature("Trainee", 2, 2, "A", training=True)
    ally = CombatCreature("Helper", 2, 2, "A")
    sim = CombatSimulator([trainee, ally], [])
    sim.simulate()
    assert trainee.plus1_counters == 0


def test_training_ignores_bushido_increase():
    """CR 702.138a & 702.46a: Bushido bonuses happen too late to satisfy training."""
    trainee = CombatCreature("Student", 2, 2, "A", training=True)
    samurai = CombatCreature("Samurai", 2, 2, "A", bushido=1)
    blocker = CombatCreature("Guard", 2, 2, "B")
    link_block(samurai, blocker)
    sim = CombatSimulator([trainee, samurai], [blocker])
    sim.simulate()
    assert trainee.plus1_counters == 0


def test_afflict_double_strike_triggers_once():
    """CR 702.131a: Afflict causes life loss once when the creature becomes blocked."""
    atk = CombatCreature("Tormentor", 2, 2, "A", afflict=2, double_strike=True)
    blk = CombatCreature("Guard", 2, 2, "B")
    link_block(atk, blk)
    sim = CombatSimulator([atk], [blk])
    result = sim.simulate()
    assert result.damage_to_players["B"] == 2


def test_afflict_not_unblocked():
    """CR 702.131a: Afflict doesn't trigger if the creature isn't blocked."""
    atk = CombatCreature("Tormentor", 2, 2, "A", afflict=2)
    defender = CombatCreature("Dummy", 0, 1, "B")
    sim = CombatSimulator([atk], [defender])
    result = sim.simulate()
    assert result.damage_to_players["B"] == 2


def test_afflict_triggers_even_if_killed_first_strike():
    """CR 702.131a & 702.7b: Afflict triggers even if a first strike blocker kills the attacker."""
    atk = CombatCreature("Tormentor", 2, 2, "A", afflict=2)
    blk = CombatCreature("Duelist", 2, 2, "B", first_strike=True)
    link_block(atk, blk)
    sim = CombatSimulator([atk], [blk])
    result = sim.simulate()
    assert atk in result.creatures_destroyed
    assert blk not in result.creatures_destroyed
    assert result.damage_to_players["B"] == 2


def test_undying_with_counter_does_not_return():
    """CR 702.92a: Undying doesn't return a creature that already had a +1/+1 counter."""
    atk = CombatCreature("Slayer", 3, 3, "A")
    blk = CombatCreature("Phoenix", 2, 2, "B", undying=True)
    blk.plus1_counters = 1
    link_block(atk, blk)
    sim = CombatSimulator([atk], [blk])
    result = sim.simulate()
    assert blk in result.creatures_destroyed


def test_persist_with_minus1_counter_does_not_return():
    """CR 702.77a: Persist only returns if the creature had no -1/-1 counters."""
    atk = CombatCreature("Ogre", 2, 2, "A")
    blk = CombatCreature("Spirit", 2, 2, "B", persist=True)
    blk.minus1_counters = 1
    link_block(atk, blk)
    sim = CombatSimulator([atk], [blk])
    result = sim.simulate()
    assert blk in result.creatures_destroyed


def test_bushido_multiple_instances_stack():
    """CR 702.46a: Multiple instances of bushido each give +1/+1."""
    atk = CombatCreature("Master Samurai", 2, 2, "A", bushido=2)
    blk = CombatCreature("Guard", 2, 2, "B")
    link_block(atk, blk)
    sim = CombatSimulator([atk], [blk])
    result = sim.simulate()
    assert blk in result.creatures_destroyed
    assert atk not in result.creatures_destroyed


def test_battle_cry_from_multiple_sources():
    """CR 702.92a: Each battle cry ability boosts other attackers."""
    leader1 = CombatCreature("Leader1", 2, 2, "A", battle_cry_count=1)
    leader2 = CombatCreature("Leader2", 2, 2, "A", battle_cry_count=1)
    ally = CombatCreature("Ally", 2, 2, "A")
    defender = CombatCreature("Dummy", 0, 1, "B")
    sim = CombatSimulator([leader1, leader2, ally], [defender])
    result = sim.simulate()
    assert result.damage_to_players["B"] == 10


def test_multiple_melee_attackers_each_gain_bonus():
    """CR 702.111a: Each melee creature gets +1/+1 when attacking a player."""
    m1 = CombatCreature("Warrior1", 2, 2, "A", melee=True)
    m2 = CombatCreature("Warrior2", 2, 2, "A", melee=True)
    defender = CombatCreature("Dummy", 0, 1, "B")
    sim = CombatSimulator([m1, m2], [defender])
    result = sim.simulate()
    assert result.damage_to_players["B"] == 6


def test_rampage_no_bonus_with_single_blocker():
    """CR 702.23a: Rampage gives no bonus with only one blocker."""
    atk = CombatCreature("Brute", 3, 3, "A", rampage=2)
    blk = CombatCreature("Bear", 3, 3, "B")
    link_block(atk, blk)
    sim = CombatSimulator([atk], [blk])
    result = sim.simulate()
    assert atk in result.creatures_destroyed
    assert blk in result.creatures_destroyed


def test_rampage_with_battle_cry_and_multiple_blockers():
    """CR 702.23a & 702.92a: Rampage and battle cry bonuses both apply."""
    attacker = CombatCreature("Warlord", 3, 3, "A", rampage=1)
    leader = CombatCreature("Banner", 2, 2, "A", battle_cry_count=1)
    b1 = CombatCreature("B1", 2, 2, "B")
    b2 = CombatCreature("B2", 2, 2, "B")
    link_block(attacker, b1, b2)
    sim = CombatSimulator([attacker, leader], [b1, b2])
    result = sim.simulate()
    assert b1 in result.creatures_destroyed and b2 in result.creatures_destroyed
    assert attacker in result.creatures_destroyed


def test_toxic_trample_excess_poison():
    """CR 702.19b & 702.??: Trample with toxic assigns excess damage and poison counters."""
    atk = CombatCreature("Serpent", 3, 3, "A", trample=True, toxic=2)
    blk = CombatCreature("Wall", 1, 1, "B")
    link_block(atk, blk)
    sim = CombatSimulator([atk], [blk])
    result = sim.simulate()
    assert result.damage_to_players["B"] == 2
    assert result.poison_counters["B"] == 2


def test_multiple_toxic_attackers_stack_poison():
    """CR 702.??: Each instance of toxic adds poison counters to the defending player."""
    t1 = CombatCreature("Snake1", 1, 1, "A", toxic=1)
    t2 = CombatCreature("Snake2", 2, 2, "A", toxic=2)
    defender = CombatCreature("Dummy", 0, 1, "B")
    sim = CombatSimulator([t1, t2], [defender])
    result = sim.simulate()
    assert result.poison_counters["B"] == 3
    assert result.damage_to_players["B"] == 3
