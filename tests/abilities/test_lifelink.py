from magic_combat import CombatCreature
from magic_combat import CombatSimulator
from magic_combat import GameState
from magic_combat import PlayerState
from magic_combat.constants import DEFAULT_STARTING_LIFE
from tests.conftest import link_block


def test_wither_lifelink_blocker_gains_life():
    """CR 702.90a & 702.15a: Wither damage is -1/-1 counters but still causes life gain from lifelink."""
    atk = CombatCreature("Aggressor", 2, 2, "A")
    blk = CombatCreature("Corrosive Guard", 1, 1, "B", wither=True, lifelink=True)
    link_block(atk, blk)
    sim = CombatSimulator([atk], [blk])
    result = sim.simulate()
    assert atk.minus1_counters == 1
    assert blk in result.creatures_destroyed
    assert result.lifegain["B"] == 1


def test_lifelink_blocker_vs_wither_attacker():
    """CR 510.2 & 702.90a: Combat damage is simultaneous, so lifelink uses pre-wither power."""
    atk = CombatCreature("Corrosive Fiend", 2, 2, "A", wither=True)
    blk = CombatCreature("Healer", 3, 3, "B", lifelink=True)
    link_block(atk, blk)
    sim = CombatSimulator([atk], [blk])
    result = sim.simulate()
    assert result.lifegain["B"] == 3
    assert blk.minus1_counters == 2


def test_lifelink_blocker_vs_infect_attacker():
    """CR 510.2 & 702.90b: Infect doesn't reduce damage dealt simultaneously with lifelink."""
    atk = CombatCreature("Plaguebearer", 2, 2, "A", infect=True)
    blk = CombatCreature("Healer", 3, 3, "B", lifelink=True)
    link_block(atk, blk)
    sim = CombatSimulator([atk], [blk])
    result = sim.simulate()
    assert result.lifegain["B"] == 3
    assert blk.minus1_counters == 2


def test_lifelink_attacker_vs_wither_blocker():
    """CR 510.2 & 702.90a: Wither doesn't cut lifelink damage from an attacker."""
    atk = CombatCreature("Paladin", 3, 3, "A", lifelink=True)
    blk = CombatCreature("Corrosive Guard", 1, 3, "B", wither=True)
    link_block(atk, blk)
    sim = CombatSimulator([atk], [blk])
    result = sim.simulate()
    assert result.lifegain["A"] == 3
    assert atk.minus1_counters == 1


def test_lifelink_attacker_vs_infect_blocker():
    """CR 510.2 & 702.90b: Infect counters don't reduce lifelink damage."""
    atk = CombatCreature("Angel", 3, 3, "A", lifelink=True)
    blk = CombatCreature("Toxic Guard", 1, 3, "B", infect=True)
    link_block(atk, blk)
    sim = CombatSimulator([atk], [blk])
    result = sim.simulate()
    assert result.lifegain["A"] == 3
    assert atk.minus1_counters == 1


def test_afflict_lifelink_no_extra_life():
    """CR 702.131a & 702.15a: Afflict causes life loss that isn't damage, so lifelink only counts combat damage."""
    atk = CombatCreature("Tormentor", 3, 3, "A", afflict=2, lifelink=True)
    blk = CombatCreature("Soldier", 2, 2, "B")
    link_block(atk, blk)
    sim = CombatSimulator([atk], [blk])
    result = sim.simulate()
    assert result.damage_to_players["B"] == 2
    assert result.lifegain["A"] == 2


def test_double_strike_trample_lifelink():
    """CR 702.4b, 702.19b & 702.15a: Double strike with trample deals damage twice and lifelink gains that much life."""
    atk = CombatCreature(
        "Champion", 2, 2, "A", double_strike=True, trample=True, lifelink=True
    )
    blk = CombatCreature("Chump", 1, 1, "B")
    link_block(atk, blk)
    sim = CombatSimulator([atk], [blk])
    result = sim.simulate()
    assert result.damage_to_players["B"] == 3
    assert result.lifegain["A"] == 4


def test_first_strike_lifelink_vs_deathtouch():
    """CR 702.7b, 702.2b & 702.15a: First strike lifelink kills a deathtouch blocker before it can deal damage."""
    atk = CombatCreature("Paladin", 2, 2, "A", first_strike=True, lifelink=True)
    blk = CombatCreature("Assassin", 2, 2, "B", deathtouch=True)
    link_block(atk, blk)
    sim = CombatSimulator([atk], [blk])
    result = sim.simulate()
    assert blk in result.creatures_destroyed
    assert atk not in result.creatures_destroyed
    assert result.lifegain["A"] == 2


def test_lifelink_blocker_gains_life():
    """CR 702.15a: A creature with lifelink gains life when dealing combat damage as a blocker."""
    atk = CombatCreature("Brute", 2, 2, "A")
    blk = CombatCreature("Healer", 2, 2, "B", lifelink=True)
    link_block(atk, blk)
    sim = CombatSimulator([atk], [blk])
    result = sim.simulate()
    assert result.lifegain["B"] == 2


def test_multiple_lifelink_attackers_stack():
    """CR 702.15a: Each lifelink creature grants life separately when dealing damage."""
    a1 = CombatCreature("Vampire", 2, 2, "A", lifelink=True)
    a2 = CombatCreature("Cleric", 1, 1, "A", lifelink=True)
    defender = CombatCreature("Dummy", 0, 1, "B")
    sim = CombatSimulator([a1, a2], [defender])
    result = sim.simulate()
    assert result.damage_to_players["B"] == 3
    assert result.lifegain["A"] == 3


def test_infect_lifelink_blocker():
    """CR 702.90b & 702.15a: Infect damage from a lifelink blocker still grants life."""
    atk = CombatCreature("Attacker", 3, 3, "A")
    blk = CombatCreature("Toxic Guard", 1, 1, "B", infect=True, lifelink=True)
    link_block(atk, blk)
    sim = CombatSimulator([atk], [blk])
    result = sim.simulate()
    assert atk.minus1_counters == 1
    assert result.lifegain["B"] == 1


def test_deathtouch_lifelink_blocker():
    """CR 702.2b & 702.15a: Deathtouch from a lifelink blocker destroys and also grants life."""
    atk = CombatCreature("Charger", 2, 2, "A")
    blk = CombatCreature("Venomous", 1, 1, "B", deathtouch=True, lifelink=True)
    link_block(atk, blk)
    sim = CombatSimulator([atk], [blk])
    result = sim.simulate()
    assert atk in result.creatures_destroyed
    assert blk in result.creatures_destroyed
    assert result.lifegain["B"] == 1


def test_toxic_lifelink_unblocked():
    """CR 702.15a & 702.180a: Toxic adds poison counters while lifelink gains life from the damage."""
    atk = CombatCreature("Viper", 1, 1, "A", toxic=2, lifelink=True)
    defender = CombatCreature("Dummy", 0, 1, "B")
    sim = CombatSimulator([atk], [defender])
    result = sim.simulate()
    assert result.damage_to_players["B"] == 1
    assert result.poison_counters["B"] == 2
    assert result.lifegain["A"] == 1


def test_lifelink_on_both_sides():
    """CR 702.15a: When both creatures have lifelink, each controller gains life for the damage their creature deals."""
    atk = CombatCreature("Angel", 2, 2, "A", lifelink=True)
    blk = CombatCreature("Cleric", 2, 2, "B", lifelink=True)
    link_block(atk, blk)
    sim = CombatSimulator([atk], [blk])
    result = sim.simulate()
    assert result.lifegain["A"] == 2
    assert result.lifegain["B"] == 2


def test_lifelink_blocker_keeps_player_alive():
    """CR 510.2, 702.15b & 104.3b: Lifelink life gain happens with damage, so
    state-based actions see the gained life."""
    a1 = CombatCreature("Raider", 2, 2, "A")
    a2 = CombatCreature("Brute", 2, 2, "A")
    blk = CombatCreature("Healer", 1, 1, "B", lifelink=True)
    link_block(a1, blk)
    state = GameState(
        players={
            "A": PlayerState(life=DEFAULT_STARTING_LIFE, creatures=[a1, a2]),
            "B": PlayerState(life=2, creatures=[blk]),
        }
    )
    sim = CombatSimulator([a1, a2], [blk], game_state=state)
    result = sim.simulate()
    assert result.damage_to_players["B"] == 2
    assert result.lifegain["B"] == 1
    assert state.players["B"].life == 1
    assert "B" not in sim.players_lost


def test_first_strike_lethal_before_lifelink():
    """CR 702.7b & 702.15b: Lifelink can't save a player from lethal first strike damage."""
    fs = CombatCreature("Swiftblade", 2, 2, "A", first_strike=True)
    atk = CombatCreature("Raider", 2, 2, "A")
    blk = CombatCreature("Cleric", 1, 1, "B", lifelink=True)
    link_block(atk, blk)
    state = GameState(
        players={
            "A": PlayerState(life=DEFAULT_STARTING_LIFE, creatures=[fs, atk]),
            "B": PlayerState(life=2, creatures=[blk]),
        }
    )
    sim = CombatSimulator([fs, atk], [blk], game_state=state)
    sim.simulate()
    assert "B" in sim.players_lost


def test_double_strike_lifelink_blocker_hits_twice():
    """CR 702.4b & 702.15b: Double strike lifelink deals damage in both steps."""
    atk = CombatCreature("Brute", 3, 3, "A")
    blk = CombatCreature("Guardian", 1, 1, "B", lifelink=True, double_strike=True)
    link_block(atk, blk)
    sim = CombatSimulator([atk], [blk])
    result = sim.simulate()
    assert result.lifegain["B"] == 2


def test_persist_lifelink_attacker_returns_after_damage():
    """CR 702.77a & 702.15b: Persist returns the creature after lifelink damage."""
    atk = CombatCreature("Undying Cleric", 2, 2, "A", lifelink=True, persist=True)
    blk = CombatCreature("Bear", 2, 2, "B")
    link_block(atk, blk)
    sim = CombatSimulator([atk], [blk])
    result = sim.simulate()
    assert result.lifegain["A"] == 2
    assert atk.minus1_counters == 1
    assert atk not in result.creatures_destroyed


def test_undying_lifelink_attacker_returns_after_damage():
    """CR 702.92a & 702.15b: Undying returns after lifelink damage is dealt."""
    atk = CombatCreature("Resilient Monk", 2, 2, "A", lifelink=True, undying=True)
    blk = CombatCreature("Bear", 2, 2, "B")
    link_block(atk, blk)
    sim = CombatSimulator([atk], [blk])
    result = sim.simulate()
    assert result.lifegain["A"] == 2
    assert atk.plus1_counters == 1
    assert atk not in result.creatures_destroyed


def test_deathtouch_trample_lifelink_assignment():
    """CR 702.2b, 702.19b & 702.15b: Deathtouch trample lifelink assigns minimal blocker damage."""
    atk = CombatCreature(
        "Predator", 5, 5, "A", deathtouch=True, trample=True, lifelink=True
    )
    blk = CombatCreature("Wall", 5, 5, "B")
    link_block(atk, blk)
    sim = CombatSimulator([atk], [blk])
    result = sim.simulate()
    assert result.damage_to_players["B"] == 4
    assert result.lifegain["A"] == 5
