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

def test_double_strike_trample_hits_player_twice():
    """CR 702.4b & 702.19b: Double strike deals damage in two steps and trample lets excess hit the defending player."""
    atk = CombatCreature("Crusher", 3, 3, "A", double_strike=True, trample=True)
    blk = CombatCreature("Bear", 2, 2, "B")
    atk.blocked_by.append(blk)
    blk.blocking = atk
    sim = CombatSimulator([atk], [blk])
    result = sim.simulate()
    assert blk in result.creatures_destroyed
    assert atk not in result.creatures_destroyed
    assert result.damage_to_players["B"] == 4


def test_double_strike_deathtouch_kills_all_blockers_first():
    """CR 702.2b & 702.4b: Deathtouch makes any damage lethal, so a double-striker can slay multiple blockers before they deal damage."""
    atk = CombatCreature("Assassin", 2, 2, "A", double_strike=True, deathtouch=True)
    b1 = CombatCreature("Guard1", 2, 2, "B")
    b2 = CombatCreature("Guard2", 2, 2, "B")
    atk.blocked_by.extend([b1, b2])
    b1.blocking = atk
    b2.blocking = atk
    sim = CombatSimulator([atk], [b1, b2])
    result = sim.simulate()
    assert b1 in result.creatures_destroyed
    assert b2 in result.creatures_destroyed
    assert atk not in result.creatures_destroyed
    assert result.damage_to_players.get("B", 0) == 0
