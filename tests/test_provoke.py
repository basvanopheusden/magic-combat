import pytest

from magic_combat import CombatCreature, CombatSimulator, Color


def test_provoke_target_blocks_successfully():
    """CR 702.40a: Provoke forces the chosen creature to block if able."""
    atk = CombatCreature("Taunter", 2, 2, "A")
    blk = CombatCreature("Guard", 2, 2, "B")
    atk.blocked_by.append(blk)
    blk.blocking = atk
    sim = CombatSimulator([atk], [blk], provoke_map={atk: blk})
    sim.validate_blocking()
    result = sim.simulate()
    assert atk in result.creatures_destroyed
    assert blk in result.creatures_destroyed


def test_provoke_target_must_block():
    """CR 702.40a: Provoke requires the chosen creature to block if able."""
    atk = CombatCreature("Taunter", 2, 2, "A")
    blk = CombatCreature("Guard", 2, 2, "B")
    sim = CombatSimulator([atk], [blk], provoke_map={atk: blk})
    with pytest.raises(ValueError):
        sim.validate_blocking()


def test_provoke_target_not_defender():
    """CR 702.40a: Provoke targets a creature the defending player controls."""
    atk = CombatCreature("Taunter", 2, 2, "A")
    defender = CombatCreature("Blocker", 2, 2, "B")
    other = CombatCreature("Bystander", 2, 2, "C")
    sim = CombatSimulator([atk], [defender], provoke_map={atk: other})
    with pytest.raises(ValueError):
        sim.validate_blocking()


def test_provoke_menace_single_blocker_fails():
    """CR 702.40a & 702.110b: Provoke doesn't override menace's two-blocker requirement."""
    atk = CombatCreature("Menacing", 2, 2, "A", menace=True)
    blk = CombatCreature("Goblin", 2, 2, "B")
    atk.blocked_by.append(blk)
    blk.blocking = atk
    sim = CombatSimulator([atk], [blk], provoke_map={atk: blk})
    with pytest.raises(ValueError):
        sim.validate_blocking()


def test_provoke_menace_two_blockers_ok():
    """CR 702.40a & 702.110b: Provoke with menace is legal when two creatures including the target block."""
    atk = CombatCreature("Menacing", 2, 2, "A", menace=True)
    blk1 = CombatCreature("Goblin1", 2, 2, "B")
    blk2 = CombatCreature("Goblin2", 2, 2, "B")
    atk.blocked_by.extend([blk1, blk2])
    blk1.blocking = atk
    blk2.blocking = atk
    sim = CombatSimulator([atk], [blk1, blk2], provoke_map={atk: blk1})
    sim.validate_blocking()
    result = sim.simulate()
    assert atk in result.creatures_destroyed


def test_provoke_unblockable_attacker():
    """CR 702.40a & 509.1b: Provoke can't force a block on an unblockable creature."""
    atk = CombatCreature("Sneak", 2, 2, "A", unblockable=True)
    blk = CombatCreature("Guard", 2, 2, "B")
    atk.blocked_by.append(blk)
    blk.blocking = atk
    sim = CombatSimulator([atk], [blk], provoke_map={atk: blk})
    with pytest.raises(ValueError):
        sim.validate_blocking()


def test_provoke_flying_needs_reach():
    """CR 702.40a & 702.9b: A provoked creature without flying or reach can't block a flyer."""
    atk = CombatCreature("Dragon", 3, 3, "A", flying=True)
    blk = CombatCreature("Bear", 2, 2, "B")
    atk.blocked_by.append(blk)
    blk.blocking = atk
    sim = CombatSimulator([atk], [blk], provoke_map={atk: blk})
    with pytest.raises(ValueError):
        sim.validate_blocking()


def test_provoke_flying_with_reach_success():
    """CR 702.40a & 702.9c: Reach lets a provoked creature block a flyer."""
    atk = CombatCreature("Dragon", 3, 3, "A", flying=True)
    blk = CombatCreature("Spider", 1, 4, "B", reach=True)
    atk.blocked_by.append(blk)
    blk.blocking = atk
    sim = CombatSimulator([atk], [blk], provoke_map={atk: blk})
    sim.validate_blocking()
    result = sim.simulate()
    assert atk not in result.creatures_destroyed
    assert blk not in result.creatures_destroyed


def test_provoke_skulk_high_power_blocker():
    """CR 702.40a & 702.72a: Skulk prevents blocks by higher-power creatures even if provoked."""
    atk = CombatCreature("Sneak", 1, 1, "A", skulk=True)
    blk = CombatCreature("Ogre", 3, 3, "B")
    atk.blocked_by.append(blk)
    blk.blocking = atk
    sim = CombatSimulator([atk], [blk], provoke_map={atk: blk})
    with pytest.raises(ValueError):
        sim.validate_blocking()


def test_provoke_protection_from_color():
    """CR 702.40a & 702.16b: Protection prevents the provoked creature from blocking."""
    atk = CombatCreature("Paladin", 2, 2, "A", protection_colors={Color.RED})
    blk = CombatCreature("Orc", 2, 2, "B", colors={Color.RED})
    atk.blocked_by.append(blk)
    blk.blocking = atk
    sim = CombatSimulator([atk], [blk], provoke_map={atk: blk})
    with pytest.raises(ValueError):
        sim.validate_blocking()


def test_provoke_afflict_damage_triggers():
    """CR 702.40a & 702.131a: A provoked attacker with afflict still causes life loss when blocked."""
    atk = CombatCreature("Tormentor", 2, 2, "A", afflict=2)
    blk = CombatCreature("Guard", 2, 2, "B")
    atk.blocked_by.append(blk)
    blk.blocking = atk
    sim = CombatSimulator([atk], [blk], provoke_map={atk: blk})
    result = sim.simulate()
    assert result.damage_to_players["B"] == 2
    assert atk in result.creatures_destroyed
    assert blk in result.creatures_destroyed


def test_provoke_first_strike_kills_before_damage():
    """CR 702.7b & 702.40a: First strike damage is dealt before the provoked creature can respond."""
    atk = CombatCreature("Duelist", 2, 2, "A", first_strike=True)
    blk = CombatCreature("Guard", 2, 2, "B")
    atk.blocked_by.append(blk)
    blk.blocking = atk
    sim = CombatSimulator([atk], [blk], provoke_map={atk: blk})
    result = sim.simulate()
    assert blk in result.creatures_destroyed
    assert atk not in result.creatures_destroyed


def test_provoke_trample_excess_damage_to_player():
    """CR 702.19b & 702.40a: Trample assigns excess damage even when provoking a block."""
    atk = CombatCreature("Rhino", 4, 4, "A", trample=True)
    blk = CombatCreature("Wall", 1, 1, "B")
    atk.blocked_by.append(blk)
    blk.blocking = atk
    sim = CombatSimulator([atk], [blk], provoke_map={atk: blk})
    result = sim.simulate()
    assert result.damage_to_players["B"] == 3
    assert blk in result.creatures_destroyed


def test_provoke_bushido_bonus_saves_attacker():
    """CR 702.46a & 702.40a: Bushido grants +1/+1 when the provoked creature blocks."""
    atk = CombatCreature("Samurai", 2, 2, "A", bushido=1)
    blk = CombatCreature("Soldier", 2, 2, "B")
    atk.blocked_by.append(blk)
    blk.blocking = atk
    sim = CombatSimulator([atk], [blk], provoke_map={atk: blk})
    result = sim.simulate()
    assert blk in result.creatures_destroyed
    assert atk not in result.creatures_destroyed


def test_provoke_rampage_bonus_with_multiple_blockers():
    """CR 702.23a & 702.40a: Rampage increases stats when multiple blockers including the target block."""
    atk = CombatCreature("Warlord", 3, 3, "A", rampage=2)
    blk1 = CombatCreature("Guard1", 2, 2, "B")
    blk2 = CombatCreature("Guard2", 2, 2, "B")
    atk.blocked_by.extend([blk1, blk2])
    blk1.blocking = atk
    blk2.blocking = atk
    sim = CombatSimulator([atk], [blk1, blk2], provoke_map={atk: blk1})
    result = sim.simulate()
    assert blk1 in result.creatures_destroyed
    assert blk2 in result.creatures_destroyed
    assert atk not in result.creatures_destroyed


def test_provoke_flanking_debuffs_target():
    """CR 702.25a & 702.40a: Flanking gives the provoked creature -1/-1."""
    atk = CombatCreature("Lancer", 2, 2, "A", flanking=1)
    blk = CombatCreature("Knight", 2, 2, "B")
    atk.blocked_by.append(blk)
    blk.blocking = atk
    sim = CombatSimulator([atk], [blk], provoke_map={atk: blk})
    result = sim.simulate()
    assert blk in result.creatures_destroyed
    assert atk not in result.creatures_destroyed


def test_provoke_training_counter_added():
    """CR 702.138a & 702.40a: Training grants a +1/+1 counter when a stronger ally attacks with the provoker."""
    trainee = CombatCreature("Recruit", 2, 2, "A", training=True)
    ally = CombatCreature("Veteran", 3, 3, "A")
    blk = CombatCreature("Guard", 2, 2, "B")
    trainee.blocked_by.append(blk)
    blk.blocking = trainee
    sim = CombatSimulator([trainee, ally], [blk], provoke_map={trainee: blk})
    result = sim.simulate()
    assert trainee.plus1_counters == 1
    assert blk in result.creatures_destroyed


def test_provoke_exalted_no_bonus_with_multiple_attackers():
    """CR 702.90a & 702.40a: Exalted doesn't trigger when more than one creature attacks."""
    exalter = CombatCreature("Monk", 2, 2, "A", exalted_count=1)
    ally = CombatCreature("Helper", 3, 3, "A")
    blk = CombatCreature("Guard", 2, 2, "B")
    exalter.blocked_by.append(blk)
    blk.blocking = exalter
    sim = CombatSimulator([exalter, ally], [blk], provoke_map={exalter: blk})
    result = sim.simulate()
    assert exalter in result.creatures_destroyed
    assert blk in result.creatures_destroyed


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


def test_provoke_battle_cry_buffs_ally():
    """CR 702.92a & 702.40a: Battle cry still pumps other attackers when provoking a block."""
    leader = CombatCreature("Warcry", 2, 2, "A", battle_cry_count=1)
    ally = CombatCreature("Soldier", 2, 2, "A")
    blk = CombatCreature("Guard", 2, 2, "B")
    leader.blocked_by.append(blk)
    blk.blocking = leader
    sim = CombatSimulator([leader, ally], [blk], provoke_map={leader: blk})
    result = sim.simulate()
    assert result.damage_to_players["B"] == 3
    assert blk in result.creatures_destroyed


def test_provoke_lifelink_attacker_gains_life():
    """CR 702.15a & 702.40a: Lifelink causes life gain when the provoker deals damage."""
    atk = CombatCreature("Vampire", 2, 2, "A", lifelink=True)
    blk = CombatCreature("Guard", 2, 2, "B")
    atk.blocked_by.append(blk)
    blk.blocking = atk
    sim = CombatSimulator([atk], [blk], provoke_map={atk: blk})
    result = sim.simulate()
    assert result.lifegain["A"] == 2
    assert blk in result.creatures_destroyed


def test_provoke_wither_applies_counters():
    """CR 702.90a & 702.40a: Wither deals damage as -1/-1 counters to the provoked creature."""
    atk = CombatCreature("Corrosive", 2, 2, "A", wither=True)
    blk = CombatCreature("Guard", 2, 2, "B")
    atk.blocked_by.append(blk)
    blk.blocking = atk
    sim = CombatSimulator([atk], [blk], provoke_map={atk: blk})
    result = sim.simulate()
    assert blk.minus1_counters == 2
    assert blk in result.creatures_destroyed


def test_provoke_target_cannot_block():
    """CR 702.40a: The chosen creature blocks if able; otherwise nothing happens."""
    atk = CombatCreature("Dragon", 3, 3, "A", flying=True, provoke=True)
    blk = CombatCreature("Bear", 2, 2, "B")
    sim = CombatSimulator([atk], [blk], provoke_map={atk: blk})
    sim.validate_blocking()
    sim.simulate()
