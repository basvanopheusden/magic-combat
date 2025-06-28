from magic_combat import CombatCreature
from magic_combat import CombatSimulator
from tests.conftest import link_block


def setup_vanilla():
    attacker = CombatCreature("Bear", 2, 2, "A")
    blocker = CombatCreature("Piker", 3, 1, "B")
    link_block(attacker, blocker)
    return attacker, blocker


def test_simple_trade():
    """CR 510.2: combat damage is dealt simultaneously."""
    a, b = setup_vanilla()
    sim = CombatSimulator([a], [b])
    result = sim.simulate()
    assert a in result.creatures_destroyed
    assert b in result.creatures_destroyed


def test_double_block_simple():
    """Two 1/1 creatures trade with a 2/2 attacker."""
    a = CombatCreature("Bear", 2, 2, "A")
    b1 = CombatCreature("Goblin", 1, 1, "B")
    b2 = CombatCreature("Goblin2", 1, 1, "B")
    link_block(a, b1, b2)
    sim = CombatSimulator([a], [b1, b2])
    result = sim.simulate()
    assert a in result.creatures_destroyed
    assert b1 in result.creatures_destroyed
    assert b2 in result.creatures_destroyed


def test_most_creatures_killed_ordering():
    a = CombatCreature("Beast", 3, 3, "A")
    wall = CombatCreature("Wall", 0, 4, "B")
    goblin = CombatCreature("Goblin", 1, 1, "B")
    link_block(a, wall, goblin)
    sim = CombatSimulator([a], [wall, goblin])
    result = sim.simulate()
    assert goblin in result.creatures_destroyed
    assert wall not in result.creatures_destroyed
    assert a not in result.creatures_destroyed


def test_unblocked_attacker_hits_player():
    """CR 510.1c: An unblocked creature deals damage to the player it's attacking."""
    attacker = CombatCreature("Bear", 2, 2, "A")
    defender = CombatCreature("Dummy", 0, 1, "B")
    sim = CombatSimulator([attacker], [defender])
    result = sim.simulate()
    assert result.damage_to_players["B"] == 2
    assert result.creatures_destroyed == []


def test_blocker_survives_nonlethal_damage():
    """CR 704.5g: Creatures with damage less than toughness aren't destroyed."""
    attacker = CombatCreature("Bear", 2, 2, "A")
    blocker = CombatCreature("Wall", 1, 3, "B")
    link_block(attacker, blocker)
    sim = CombatSimulator([attacker], [blocker])
    result = sim.simulate()
    assert result.creatures_destroyed == []


def test_attacker_survives_and_kills_blocker():
    """CR 704.5g: A creature with lethal damage is destroyed."""
    attacker = CombatCreature("Ogre", 3, 3, "A")
    blocker = CombatCreature("Goblin", 2, 2, "B")
    link_block(attacker, blocker)
    sim = CombatSimulator([attacker], [blocker])
    result = sim.simulate()
    assert blocker in result.creatures_destroyed
    assert attacker not in result.creatures_destroyed


def test_zero_power_attacker_deals_no_damage():
    """CR 120.3d: A creature with 0 power deals no combat damage."""
    attacker = CombatCreature("Pacifist", 0, 2, "A")
    defender = CombatCreature("Dummy", 0, 1, "B")
    sim = CombatSimulator([attacker], [defender])
    result = sim.simulate()
    assert result.damage_to_players.get("B", 0) == 0
    assert result.creatures_destroyed == []


def test_indestructible_creature_survives_lethal_damage():
    """CR 702.12b: Indestructible permanents aren't destroyed by lethal damage."""
    attacker = CombatCreature("Giant", 5, 5, "A")
    blocker = CombatCreature("Guardian", 2, 2, "B", indestructible=True)
    link_block(attacker, blocker)
    sim = CombatSimulator([attacker], [blocker])
    result = sim.simulate()
    assert attacker not in result.creatures_destroyed
    assert blocker not in result.creatures_destroyed


def test_first_strike_kills_before_normal_damage():
    """CR 702.7b: Creatures with first strike deal combat damage before creatures without it."""
    attacker = CombatCreature("Swift", 2, 2, "A", first_strike=True)
    blocker = CombatCreature("Bear", 2, 2, "B")
    link_block(attacker, blocker)
    sim = CombatSimulator([attacker], [blocker])
    result = sim.simulate()
    assert blocker in result.creatures_destroyed
    assert attacker not in result.creatures_destroyed


def test_multiple_attackers_damage_added():
    """CR 510.2: All combat damage is dealt simultaneously."""
    a1 = CombatCreature("Goblin1", 2, 2, "A")
    a2 = CombatCreature("Goblin2", 2, 2, "A")
    defender = CombatCreature("Dummy", 0, 1, "B")
    sim = CombatSimulator([a1, a2], [defender])
    result = sim.simulate()
    assert result.damage_to_players["B"] == 4
    assert result.creatures_destroyed == []


def test_damage_order_prefers_value_over_kills():
    """CR 510.1a: The attacking player chooses damage assignment order."""
    attacker = CombatCreature("Warrior", 5, 5, "A")
    big = CombatCreature("Big", 4, 4, "B")
    small1 = CombatCreature("S1", 1, 1, "B")
    small2 = CombatCreature("S2", 1, 1, "B")
    link_block(attacker, big, small1, small2)
    sim = CombatSimulator([attacker], [big, small1, small2])
    result = sim.simulate()
    dead = {c.name for c in result.creatures_destroyed}
    assert "Warrior" in dead and "Big" in dead
    assert ("S1" in dead) != ("S2" in dead)
