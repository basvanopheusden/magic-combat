import pytest

from magic_combat import CombatCreature, CombatSimulator
from tests.conftest import link_block


def test_basic_mentor_counter():
    """CR 702.121a: Mentor puts a +1/+1 counter on a weaker attacker."""
    mentor = CombatCreature("Mentor", 3, 3, "A", mentor=True)
    pupil = CombatCreature("Pupil", 2, 2, "A")
    sim = CombatSimulator([mentor, pupil], [], mentor_map={mentor: pupil})
    result = sim.simulate()
    assert pupil.plus1_counters == 1
    assert result.damage_to_players["defender"] == 6


def test_no_mentor_map_no_counter():
    """CR 702.121a: Without a target, mentor adds no counters."""
    mentor = CombatCreature("Mentor", 3, 3, "A", mentor=True)
    pupil = CombatCreature("Pupil", 2, 2, "A")
    sim = CombatSimulator([mentor, pupil], [])
    result = sim.simulate()
    assert pupil.plus1_counters == 0
    assert result.damage_to_players["defender"] == 5


def test_mentor_target_equal_power_illegal():
    """CR 702.121a: The target must have lesser power."""
    mentor = CombatCreature("Mentor", 3, 3, "A", mentor=True)
    target = CombatCreature("Peer", 3, 3, "A")
    with pytest.raises(ValueError):
        CombatSimulator([mentor, target], [], mentor_map={mentor: target}).apply_precombat_triggers()


def test_mentor_target_stronger_illegal():
    """CR 702.121a: Mentor can't target a creature with greater power."""
    mentor = CombatCreature("Mentor", 2, 2, "A", mentor=True)
    target = CombatCreature("Strong", 3, 3, "A")
    sim = CombatSimulator([mentor, target], [], mentor_map={mentor: target})
    with pytest.raises(ValueError):
        sim.apply_precombat_triggers()


def test_mentor_key_not_attacking():
    """CR 702.121a: Only attacking mentors may target a creature."""
    mentor = CombatCreature("Mentor", 3, 3, "A", mentor=True)
    idle = CombatCreature("Idle", 2, 2, "A")
    sim = CombatSimulator([idle], [], mentor_map={mentor: idle})
    with pytest.raises(ValueError):
        sim.apply_precombat_triggers()


def test_mentor_target_not_attacking():
    """CR 702.121a: The chosen creature must be attacking."""
    mentor = CombatCreature("Mentor", 3, 3, "A", mentor=True)
    pupil = CombatCreature("Pupil", 2, 2, "A")
    defender = CombatCreature("Guard", 2, 2, "B")
    sim = CombatSimulator([mentor], [defender], mentor_map={mentor: pupil})
    with pytest.raises(ValueError):
        sim.apply_precombat_triggers()


def test_mentor_key_without_ability():
    """CR 702.121a: Only creatures with mentor may mentor others."""
    not_mentor = CombatCreature("Soldier", 3, 3, "A")
    pupil = CombatCreature("Pupil", 2, 2, "A")
    sim = CombatSimulator([not_mentor, pupil], [], mentor_map={not_mentor: pupil})
    with pytest.raises(ValueError):
        sim.apply_precombat_triggers()


def test_multiple_mentors_same_target():
    """CR 702.121a: Counters stack if multiple mentors target the same creature."""
    m1 = CombatCreature("M1", 3, 3, "A", mentor=True)
    m2 = CombatCreature("M2", 4, 4, "A", mentor=True)
    pupil = CombatCreature("Pupil", 2, 2, "A")
    sim = CombatSimulator([m1, m2, pupil], [], mentor_map={m1: pupil, m2: pupil})
    sim.simulate()
    assert pupil.plus1_counters == 2


def test_multiple_mentors_different_targets():
    """CR 702.121a: Each mentor can target a different weaker attacker."""
    m1 = CombatCreature("M1", 3, 3, "A", mentor=True)
    m2 = CombatCreature("M2", 4, 4, "A", mentor=True)
    p1 = CombatCreature("P1", 2, 2, "A")
    p2 = CombatCreature("P2", 1, 1, "A")
    sim = CombatSimulator(
        [m1, m2, p1, p2],
        [],
        mentor_map={m1: p1, m2: p2},
    )
    sim.simulate()
    assert p1.plus1_counters == 1
    assert p2.plus1_counters == 1


def test_training_and_mentor_both_add_counters():
    """CR 702.138a & 702.121a: Training and mentor each add one counter."""
    mentor = CombatCreature("Mentor", 3, 3, "A", mentor=True)
    trainee = CombatCreature("Trainee", 2, 2, "A", training=True)
    ally = CombatCreature("Big", 4, 4, "A")
    sim = CombatSimulator(
        [mentor, trainee, ally],
        [],
        mentor_map={mentor: trainee},
    )
    sim.simulate()
    assert trainee.plus1_counters == 2


def test_mentor_cancels_minus1_counter():
    """CR 702.121a & 704.5q: A mentor counter can remove a -1/-1 counter."""
    mentor = CombatCreature("Mentor", 3, 3, "A", mentor=True)
    pupil = CombatCreature("Pupil", 2, 2, "A", _minus1_counters=1)
    sim = CombatSimulator([mentor, pupil], [], mentor_map={mentor: pupil})
    sim.simulate()
    assert pupil.plus1_counters == 0
    assert pupil.minus1_counters == 0


def test_mentor_with_battle_cry():
    """CR 702.92a & 702.121a: Battle cry can boost a mentor while it mentors."""
    leader = CombatCreature("Leader", 2, 2, "A", battle_cry_count=1, mentor=True)
    pupil = CombatCreature("Pupil", 1, 1, "A")
    sim = CombatSimulator([leader, pupil], [], mentor_map={leader: pupil})
    result = sim.simulate()
    assert pupil.plus1_counters == 1
    assert result.damage_to_players["defender"] == 5


def test_mentor_target_with_training_stronger_after_counter():
    """CR 702.138a & 702.121a: Mentor can target a trainee before its counter."""
    mentor = CombatCreature("Mentor", 3, 3, "A", mentor=True)
    trainee = CombatCreature("Trainee", 2, 2, "A", training=True)
    big = CombatCreature("Big", 4, 4, "A")
    sim = CombatSimulator([mentor, trainee, big], [], mentor_map={mentor: trainee})
    sim.simulate()
    assert trainee.plus1_counters == 2


def test_mentor_target_multiple_times_over_turn():
    """CR 702.121a: A creature can receive counters from several mentors."""
    m1 = CombatCreature("M1", 3, 3, "A", mentor=True)
    m2 = CombatCreature("M2", 3, 3, "A", mentor=True)
    pupil = CombatCreature("Pupil", 1, 1, "A")
    sim = CombatSimulator([m1, m2, pupil], [], mentor_map={m1: pupil, m2: pupil})
    result = sim.simulate()
    assert pupil.plus1_counters == 2
    assert result.damage_to_players["defender"] == 9


def test_mentor_with_blockers_counter_applies_before_damage():
    """CR 702.121a: Mentor triggers before combat damage is assigned."""
    mentor = CombatCreature("Mentor", 3, 3, "A", mentor=True)
    pupil = CombatCreature("Pupil", 1, 1, "A")
    blocker = CombatCreature("Wall", 0, 2, "B")
    link_block(mentor, blocker)
    sim = CombatSimulator([mentor, pupil], [blocker], mentor_map={mentor: pupil})
    result = sim.simulate()
    assert pupil.plus1_counters == 1
    assert blocker in result.creatures_destroyed


def test_mentor_combines_with_melee_temp_bonus():
    """CR 702.111a & 702.121a: Melee and mentor both improve attackers."""
    mentor = CombatCreature("Mentor", 3, 3, "A", mentor=True)
    melee = CombatCreature("Melee", 2, 2, "A", melee=True)
    sim = CombatSimulator(
        [mentor, melee],
        [],
        mentor_map={mentor: melee},
    )
    result = sim.simulate()
    assert melee.plus1_counters == 1
    assert result.damage_to_players["defender"] == 7


def test_mentor_target_with_existing_plus1_counter():
    """CR 702.121a: Mentor adds an additional counter even if one is present."""
    mentor = CombatCreature("Mentor", 5, 5, "A", mentor=True)
    pupil = CombatCreature("Pupil", 3, 3, "A", _plus1_counters=1)
    sim = CombatSimulator([mentor, pupil], [], mentor_map={mentor: pupil})
    sim.simulate()
    assert pupil.plus1_counters == 2


def test_blocked_mentor_still_counters():
    """CR 702.121a: Mentor resolves even if the mentor becomes blocked."""
    mentor = CombatCreature("Mentor", 3, 3, "A", mentor=True)
    pupil = CombatCreature("Pupil", 1, 1, "A")
    blocker = CombatCreature("Bear", 2, 2, "B")
    link_block(mentor, blocker)
    sim = CombatSimulator([mentor, pupil], [blocker], mentor_map={mentor: pupil})
    result = sim.simulate()
    assert pupil.plus1_counters == 1
    assert blocker in result.creatures_destroyed


def test_mentor_with_provoke():
    """CR 702.40a & 702.121a: Provoke doesn't stop mentor from adding counters."""
    mentor = CombatCreature("Mentor", 3, 3, "A", mentor=True)
    provoker = CombatCreature("Taunter", 2, 2, "A", provoke=True)
    guard = CombatCreature("Guard", 2, 2, "B")
    link_block(provoker, guard)
    sim = CombatSimulator(
        [mentor, provoker],
        [guard],
        mentor_map={mentor: provoker},
        provoke_map={provoker: guard},
    )
    result = sim.simulate()
    assert provoker.plus1_counters == 1
    assert guard in result.creatures_destroyed


def test_mentor_illegal_mapping_key_without_attackers():
    """CR 702.121a: Mapping a noncombat creature causes an error."""
    mentor = CombatCreature("Mentor", 3, 3, "A", mentor=True)
    other = CombatCreature("Other", 2, 2, "A")
    with pytest.raises(ValueError):
        sim = CombatSimulator([], [], mentor_map={mentor: other})
        sim.apply_precombat_triggers()


