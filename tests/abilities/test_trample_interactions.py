from magic_combat import Color
from magic_combat import CombatCreature
from magic_combat import CombatSimulator
from tests.conftest import link_block


def test_trample_basic_single_blocker():
    """CR 702.19b: Excess damage is assigned to the player."""
    atk = CombatCreature("Rhino", 4, 4, "A", trample=True)
    blk = CombatCreature("Wall", 0, 2, "B")
    link_block(atk, blk)
    sim = CombatSimulator([atk], [blk])
    result = sim.simulate()
    assert result.damage_to_players["B"] == 2
    assert blk in result.creatures_destroyed


def test_trample_multiple_blockers_order():
    """CR 510.2: The attacking player orders multiple blockers for damage."""
    atk = CombatCreature("Giant", 5, 5, "A", trample=True)
    b1 = CombatCreature("Soldier", 2, 2, "B")
    b2 = CombatCreature("Guard", 2, 2, "B")
    link_block(atk, b1, b2)
    sim = CombatSimulator([atk], [b1, b2])
    result = sim.simulate()
    assert b1 in result.creatures_destroyed
    assert b2 in result.creatures_destroyed
    assert result.damage_to_players["B"] == 1


def test_trample_deathtouch_single_blocker():
    """CR 702.2c: Any nonzero damage from deathtouch is lethal."""
    atk = CombatCreature("Serpent", 3, 3, "A", trample=True, deathtouch=True)
    blk = CombatCreature("Bear", 3, 3, "B")
    link_block(atk, blk)
    sim = CombatSimulator([atk], [blk])
    result = sim.simulate()
    assert result.damage_to_players["B"] == 2
    assert blk in result.creatures_destroyed


def test_trample_deathtouch_multiple_blockers():
    """CR 702.2c & 702.19b: Only 1 damage is assigned to each blocker."""
    atk = CombatCreature("Hydra", 4, 4, "A", trample=True, deathtouch=True)
    b1 = CombatCreature("B1", 2, 2, "B")
    b2 = CombatCreature("B2", 2, 2, "B")
    link_block(atk, b1, b2)
    sim = CombatSimulator([atk], [b1, b2])
    result = sim.simulate()
    assert result.damage_to_players["B"] == 2
    assert b1 in result.creatures_destroyed
    assert b2 in result.creatures_destroyed


def test_trample_indestructible_without_deathtouch():
    """CR 702.12b: Indestructible creatures still require lethal damage."""
    atk = CombatCreature("Crusher", 5, 5, "A", trample=True)
    blk = CombatCreature("Guardian", 3, 3, "B", indestructible=True)
    link_block(atk, blk)
    sim = CombatSimulator([atk], [blk])
    result = sim.simulate()
    assert result.damage_to_players["B"] == 2
    assert blk not in result.creatures_destroyed


def test_trample_deathtouch_indestructible():
    """CR 702.2c & 702.12b: Deathtouch lowers lethal even for indestructible."""
    atk = CombatCreature("Venom", 5, 5, "A", trample=True, deathtouch=True)
    blk = CombatCreature("Guardian", 3, 3, "B", indestructible=True)
    link_block(atk, blk)
    sim = CombatSimulator([atk], [blk])
    result = sim.simulate()
    assert result.damage_to_players["B"] == 4
    assert blk not in result.creatures_destroyed


def test_trample_protection_block():
    """CR 702.16e: Damage from a protected color is prevented."""
    atk = CombatCreature("Knight", 4, 4, "A", trample=True, colors={Color.RED})
    blk = CombatCreature(
        "Paladin", 2, 2, "B", colors={Color.WHITE}, protection_colors={Color.RED}
    )
    link_block(atk, blk)
    sim = CombatSimulator([atk], [blk])
    result = sim.simulate()
    assert result.damage_to_players["B"] == 2
    assert blk in result.creatures_destroyed


def test_trample_first_strike_blocker_kills_attacker():
    """CR 702.7b: A first strike blocker can kill before trample damage."""
    atk = CombatCreature("Boar", 2, 2, "A", trample=True)
    blk = CombatCreature("Elite", 3, 3, "B", first_strike=True)
    link_block(atk, blk)
    sim = CombatSimulator([atk], [blk])
    result = sim.simulate()
    assert atk in result.creatures_destroyed
    assert result.damage_to_players.get("B", 0) == 0


def test_trample_first_strike_attacker_hits_in_first_step():
    """CR 702.7b: First strike trampler deals damage before blocker."""
    atk = CombatCreature("Rider", 3, 3, "A", trample=True, first_strike=True)
    blk = CombatCreature("Bear", 2, 2, "B")
    link_block(atk, blk)
    sim = CombatSimulator([atk], [blk])
    result = sim.simulate()
    assert result.damage_to_players["B"] == 1
    assert blk in result.creatures_destroyed


def test_trample_double_strike_attacker_assigns_twice():
    """CR 702.4b: Double strike trampler deals damage in both steps."""
    atk = CombatCreature("Duelist", 3, 3, "A", trample=True, double_strike=True)
    blk = CombatCreature("Peasant", 1, 1, "B")
    link_block(atk, blk)
    sim = CombatSimulator([atk], [blk])
    result = sim.simulate()
    assert result.damage_to_players["B"] == 5
    assert blk in result.creatures_destroyed


def test_trample_lifelink_gain_from_overflow():
    """CR 702.15b: Lifelink gains life equal to damage dealt."""
    atk = CombatCreature("Healer", 4, 4, "A", trample=True, lifelink=True)
    blk = CombatCreature("Wall", 0, 3, "B")
    link_block(atk, blk)
    sim = CombatSimulator([atk], [blk])
    result = sim.simulate()
    assert result.lifegain["A"] == 4
    assert result.damage_to_players["B"] == 1


def test_trample_deathtouch_lifelink_indestructible():
    """CR 702.2c, 702.12b & 702.15b: Deathtouch trampler gains life even when the blocker lives."""
    atk = CombatCreature(
        "Predator", 5, 5, "A", trample=True, deathtouch=True, lifelink=True
    )
    blk = CombatCreature("Wall", 3, 3, "B", indestructible=True)
    link_block(atk, blk)
    sim = CombatSimulator([atk], [blk])
    result = sim.simulate()
    assert result.damage_to_players["B"] == 4
    assert blk not in result.creatures_destroyed
    assert result.lifegain["A"] == 5


def test_trample_with_wither_counters():
    """CR 702.90a: Wither with trample assigns counters then excess."""
    atk = CombatCreature("Crusher", 2, 2, "A", trample=True, wither=True)
    blk = CombatCreature("Chump", 1, 1, "B")
    link_block(atk, blk)
    sim = CombatSimulator([atk], [blk])
    result = sim.simulate()
    assert blk.minus1_counters == 1
    assert result.damage_to_players["B"] == 1


def test_trample_with_infect_poison():
    """CR 702.90b: Infect with trample gives poison counters for excess."""
    atk = CombatCreature("Plague", 2, 2, "A", trample=True, infect=True)
    blk = CombatCreature("Chump", 1, 1, "B")
    link_block(atk, blk)
    sim = CombatSimulator([atk], [blk])
    result = sim.simulate()
    assert result.poison_counters["B"] == 1
    assert blk.minus1_counters == 1


def test_trample_blocker_with_existing_damage():
    """CR 702.19b: Lethal damage accounts for prior damage."""
    atk = CombatCreature("Boar", 4, 4, "A", trample=True)
    blk = CombatCreature("Bear", 3, 3, "B")
    blk.damage_marked = 2
    link_block(atk, blk)
    sim = CombatSimulator([atk], [blk])
    result = sim.simulate()
    assert result.damage_to_players["B"] == 3
    assert blk in result.creatures_destroyed


def test_trample_deathtouch_second_step_lethal_zero():
    """CR 702.2b: Damage from deathtouch earlier makes lethal zero."""
    atk = CombatCreature(
        "Slayer", 2, 2, "A", double_strike=True, deathtouch=True, trample=True
    )
    blk = CombatCreature("Giant", 4, 4, "B")
    link_block(atk, blk)
    sim = CombatSimulator([atk], [blk])
    result = sim.simulate()
    assert result.damage_to_players["B"] == 3
    assert blk in result.creatures_destroyed
