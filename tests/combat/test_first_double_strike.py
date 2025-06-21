from magic_combat import CombatCreature, CombatSimulator


def test_first_strike_vs_first_strike_trade():
    """CR 702.7b: Creatures with first strike deal combat damage in a special step before creatures without it."""
    atk = CombatCreature("Duelist", 2, 2, "A", first_strike=True)
    blk = CombatCreature("Guard", 2, 2, "B", first_strike=True)
    atk.blocked_by.append(blk)
    blk.blocking = atk
    sim = CombatSimulator([atk], [blk])
    result = sim.simulate()
    assert atk in result.creatures_destroyed
    assert blk in result.creatures_destroyed


def test_double_strike_vs_first_strike_both_die_first_step():
    """CR 702.4b: A creature with double strike deals damage in both first-strike and regular steps, but only if it survives the first."""
    atk = CombatCreature("Champion", 2, 2, "A", double_strike=True)
    blk = CombatCreature("Veteran", 2, 2, "B", first_strike=True)
    atk.blocked_by.append(blk)
    blk.blocking = atk
    sim = CombatSimulator([atk], [blk])
    result = sim.simulate()
    assert atk in result.creatures_destroyed
    assert blk in result.creatures_destroyed


def test_double_strike_blocked_no_damage_to_player():
    """CR 506.4: A blocked creature remains blocked even if its blockers are removed from combat."""
    atk = CombatCreature("Blade", 2, 2, "A", double_strike=True)
    blk = CombatCreature("Bear", 2, 2, "B")
    atk.blocked_by.append(blk)
    blk.blocking = atk
    sim = CombatSimulator([atk], [blk])
    result = sim.simulate()
    assert blk in result.creatures_destroyed
    assert atk not in result.creatures_destroyed
    assert result.damage_to_players.get("B", 0) == 0


def test_double_strike_kills_first_striker_no_damage_to_player():
    """CR 702.4b & 506.4: A double strike creature that kills its blocker in the first-strike step is still blocked and deals no damage to the player."""
    atk = CombatCreature("Champion", 2, 2, "A", double_strike=True)
    blk = CombatCreature("Squire", 1, 1, "B", first_strike=True)
    atk.blocked_by.append(blk)
    blk.blocking = atk
    sim = CombatSimulator([atk], [blk])
    result = sim.simulate()
    assert blk in result.creatures_destroyed
    assert atk not in result.creatures_destroyed
    assert result.damage_to_players.get("B", 0) == 0


def test_double_strike_unblocked_hits_player_twice():
    """CR 702.4b & 510.1c: A double strike creature unblocked deals damage twice to the defending player."""
    atk = CombatCreature("Warrior", 3, 3, "A", double_strike=True)
    defender = CombatCreature("Dummy", 0, 1, "B")
    sim = CombatSimulator([atk], [defender])
    result = sim.simulate()
    assert result.damage_to_players["B"] == 6
    assert result.creatures_destroyed == []
