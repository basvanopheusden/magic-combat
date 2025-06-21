import pytest

from magic_combat import (
    CombatCreature,
    CombatSimulator,
    GameState,
    PlayerState,
    STARTING_LIFE_TOTAL,
    Color,
)


def test_wither_prevents_persist_return():
    """CR 702.90a & 702.77a: Wither gives -1/-1 counters so persist won't return if a creature dies with one."""
    attacker = CombatCreature("Corrosive Archer", 2, 2, "A", wither=True)
    blocker = CombatCreature("Everlasting", 2, 2, "B", persist=True)
    attacker.blocked_by.append(blocker)
    blocker.blocking = attacker
    sim = CombatSimulator([attacker], [blocker])
    result = sim.simulate()
    assert blocker in result.creatures_destroyed
    assert blocker.minus1_counters == 2


def test_persist_creature_returns_with_counter():
    """CR 702.77a: Persist returns a creature that died without -1/-1 counters."""
    attacker = CombatCreature("Giant", 3, 3, "A")
    blocker = CombatCreature("Undying Wall", 2, 2, "B", persist=True)
    attacker.blocked_by.append(blocker)
    blocker.blocking = attacker
    sim = CombatSimulator([attacker], [blocker])
    result = sim.simulate()
    assert blocker not in result.creatures_destroyed
    assert blocker.minus1_counters == 1


def test_deathtouch_infect_trample_assigns_poison():
    """CR 702.19b, 702.2b & 702.90b: Deathtouch with trample and infect assigns minimal damage to the blocker and the rest as poison counters."""
    attacker = CombatCreature(
        "Toxic Crusher", 3, 3, "A", trample=True, deathtouch=True, infect=True
    )
    blocker = CombatCreature("Wall", 2, 2, "B")
    attacker.blocked_by.append(blocker)
    blocker.blocking = attacker
    sim = CombatSimulator([attacker], [blocker])
    result = sim.simulate()
    assert result.poison_counters["B"] == 2
    assert blocker.minus1_counters == 1
    assert blocker in result.creatures_destroyed


def test_double_strike_infect_toxic_lifelink():
    """CR 702.4b, 702.15a & 702.90b: Double strike with infect and toxic deals poison twice and grants lifelink."""
    attacker = CombatCreature(
        "Toxic Angel", 1, 1, "A", double_strike=True, infect=True, toxic=1, lifelink=True
    )
    defender = CombatCreature("Dummy", 0, 1, "B")
    state = GameState(
        players={
            "A": PlayerState(life=STARTING_LIFE_TOTAL, creatures=[attacker]),
            "B": PlayerState(life=STARTING_LIFE_TOTAL, creatures=[defender]),
        }
    )
    sim = CombatSimulator([attacker], [defender], game_state=state)
    result = sim.simulate()
    assert result.poison_counters["B"] == 4
    assert result.lifegain["A"] == 2
    assert state.players["A"].life == 22


def test_rampage_battle_cry_melee_combo():
    """CR 702.23a, 702.92a & 702.111a: Rampage, battle cry, and melee bonuses stack before combat damage."""
    warleader = CombatCreature("Warleader", 3, 3, "A", rampage=1, melee=True)
    commander = CombatCreature("Commander", 2, 2, "A", battle_cry_count=1, lifelink=True)
    b1 = CombatCreature("B1", 2, 2, "B")
    b2 = CombatCreature("B2", 2, 2, "B")
    warleader.blocked_by.extend([b1, b2])
    b1.blocking = warleader
    b2.blocking = warleader
    sim = CombatSimulator([warleader, commander], [b1, b2])
    result = sim.simulate()
    assert b1 in result.creatures_destroyed
    assert b2 in result.creatures_destroyed
    assert warleader not in result.creatures_destroyed
    assert commander not in result.creatures_destroyed
    assert result.damage_to_players["B"] == 2
    assert result.lifegain["A"] == 2


def test_skulk_flanking_bushido_precombat_death():
    """CR 702.72a, 702.25a & 702.46a: Flanking and bushido bonuses apply before damage when a skulk attacker is blocked."""
    attacker = CombatCreature("Sneaky Knight", 2, 2, "A", skulk=True, flanking=1, bushido=1)
    blocker = CombatCreature("Guard", 1, 1, "B")
    attacker.blocked_by.append(blocker)
    blocker.blocking = attacker
    sim = CombatSimulator([attacker], [blocker])
    result = sim.simulate()
    assert blocker in result.creatures_destroyed
    assert attacker not in result.creatures_destroyed


def test_provoke_and_menace_insufficient_blockers():
    """CR 702.40a & 702.110b: Provoke requires the targeted creature to block, but menace demands two blockers."""
    attacker = CombatCreature("Taunting Brute", 2, 2, "A", menace=True)
    blocker = CombatCreature("Goblin", 2, 2, "B")
    attacker.blocked_by.append(blocker)
    blocker.blocking = attacker
    attacker.provoke_target = blocker
    sim = CombatSimulator([attacker], [blocker])
    with pytest.raises(ValueError):
        sim.validate_blocking()


def test_undying_and_persist_prefers_undying():
    """CR 702.92a & 702.77a: A creature with undying and persist returns with a +1/+1 counter."""
    attacker = CombatCreature("Slayer", 3, 3, "A")
    blocker = CombatCreature("Spirit", 2, 2, "B", undying=True, persist=True)
    attacker.blocked_by.append(blocker)
    blocker.blocking = attacker
    sim = CombatSimulator([attacker], [blocker])
    result = sim.simulate()
    assert blocker not in result.creatures_destroyed
    assert blocker.plus1_counters == 1
    assert blocker.minus1_counters == 0


def test_exalted_melee_no_training_when_alone():
    """CR 702.90a, 702.111a & 702.138a: Exalted and melee boost a lone attacker but training does nothing without a stronger ally."""
    attacker = CombatCreature(
        "Student Champion", 2, 2, "A", exalted_count=1, melee=True, training=True
    )
    defender = CombatCreature("Dummy", 0, 1, "B")
    sim = CombatSimulator([attacker], [defender])
    result = sim.simulate()
    assert result.damage_to_players["B"] == 4
    assert attacker.plus1_counters == 0


def test_fear_and_intimidate_require_artifact_and_color():
    """CR 702.36b & 702.13a: A creature with fear and intimidate can be blocked only by an artifact that also shares its color."""
    attacker = CombatCreature("Shadow Rogue", 2, 2, "A", fear=True, intimidate=True, colors={Color.RED})
    blk = CombatCreature("Shade", 2, 2, "B", colors={Color.BLACK})
    attacker.blocked_by.append(blk)
    blk.blocking = attacker
    sim = CombatSimulator([attacker], [blk])
    with pytest.raises(ValueError):
        sim.validate_blocking()

    artifact = CombatCreature("Golem", 2, 2, "B", artifact=True)
    attacker.blocked_by = [artifact]
    artifact.blocking = attacker
    sim = CombatSimulator([attacker], [artifact])
    sim.validate_blocking()
