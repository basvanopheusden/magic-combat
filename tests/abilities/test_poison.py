import pytest

from magic_combat import (
    DEFAULT_STARTING_LIFE,
    POISON_LOSS_THRESHOLD,
    CombatCreature,
    CombatSimulator,
    GameState,
    PlayerState,
    has_player_lost,
)
from tests.conftest import link_block


def test_infect_creature_gets_minus1_counters():
    """CR 702.90a: Damage from a creature with infect gives -1/-1 counters to creatures."""
    atk = CombatCreature("Agent", 2, 2, "A", infect=True)
    blk = CombatCreature("Target", 2, 2, "B")
    link_block(atk, blk)
    sim = CombatSimulator([atk], [blk])
    result = sim.simulate()
    assert blk.minus1_counters == 2
    assert blk in result.creatures_destroyed


def test_infect_lifelink_vs_creature():
    """CR 702.90a & 702.15a: Infect still deals damage for lifelink purposes."""
    atk = CombatCreature("Toxic Healer", 2, 2, "A", infect=True, lifelink=True)
    blk = CombatCreature("Guard", 2, 2, "B")
    link_block(atk, blk)
    state = GameState(
        players={
            "A": PlayerState(life=DEFAULT_STARTING_LIFE, creatures=[atk]),
            "B": PlayerState(life=DEFAULT_STARTING_LIFE, creatures=[blk]),
        }
    )
    sim = CombatSimulator([atk], [blk], game_state=state)
    result = sim.simulate()
    assert blk.minus1_counters == 2
    assert result.lifegain["A"] == 2
    assert state.players["A"].life == 22


def test_trample_infect_lifelink_poison_and_life():
    """CR 702.19b, 702.90b & 702.15a: Trample with infect gives poison counters for excess and lifelink gains that much life."""
    atk = CombatCreature(
        "Plague Rhino", 3, 3, "A", infect=True, lifelink=True, trample=True
    )
    blk = CombatCreature("Chump", 1, 1, "B")
    link_block(atk, blk)
    state = GameState(
        players={
            "A": PlayerState(life=DEFAULT_STARTING_LIFE, creatures=[atk]),
            "B": PlayerState(life=DEFAULT_STARTING_LIFE, creatures=[blk]),
        }
    )
    sim = CombatSimulator([atk], [blk], game_state=state)
    result = sim.simulate()
    assert blk.minus1_counters == 1
    assert state.players["B"].poison == 2
    assert result.poison_counters["B"] == 2
    assert result.lifegain["A"] == 3
    assert state.players["A"].life == 23


def test_double_strike_infect_creature_counters_accumulate():
    """CR 702.4b & 702.90a: An infect creature with double strike deals counters in both damage steps."""
    atk = CombatCreature("Toxic Duelist", 1, 1, "A", infect=True, double_strike=True)
    blk = CombatCreature("Giant", 3, 3, "B")
    link_block(atk, blk)
    sim = CombatSimulator([atk], [blk])
    result = sim.simulate()
    assert blk.minus1_counters == 2
    assert blk not in result.creatures_destroyed


def test_first_strike_infect_weakens_before_hit_back():
    """CR 702.7b & 702.90a: First strike infect damage is dealt before normal damage."""
    atk = CombatCreature("Plague Knight", 2, 2, "A", infect=True, first_strike=True)
    blk = CombatCreature("Ogre", 3, 3, "B")
    link_block(atk, blk)
    sim = CombatSimulator([atk], [blk])
    result = sim.simulate()
    assert blk.minus1_counters == 2
    assert atk.damage_marked == 1
    assert atk not in result.creatures_destroyed
    assert blk not in result.creatures_destroyed


def test_infect_kills_persist_creature_without_return():
    """CR 702.90a & 702.77a: A creature killed with -1/-1 counters doesn't return with persist."""
    atk = CombatCreature("Blighted", 2, 2, "A", infect=True)
    blk = CombatCreature("Undying Wall", 2, 2, "B", persist=True)
    link_block(atk, blk)
    sim = CombatSimulator([atk], [blk])
    result = sim.simulate()
    assert blk in result.creatures_destroyed
    assert blk.minus1_counters == 2


def test_infect_and_toxic_stack_poison():
    """CR 702.90b & 702.180a: Infect and toxic add poison counters together."""
    atk = CombatCreature("Venomous", 2, 2, "A", infect=True, toxic=1)
    defender = CombatCreature("Dummy", 0, 1, "B")
    state = GameState(
        players={
            "A": PlayerState(life=DEFAULT_STARTING_LIFE, creatures=[atk]),
            "B": PlayerState(life=DEFAULT_STARTING_LIFE, creatures=[defender]),
        }
    )
    sim = CombatSimulator([atk], [defender], game_state=state)
    result = sim.simulate()
    assert state.players["B"].poison == 3
    assert result.poison_counters["B"] == 3


def test_infect_counters_kill_indestructible():
    """CR 702.90a & 702.12b: Indestructible doesn't prevent death from 0 toughness."""
    atk = CombatCreature("Corruptor", 1, 1, "A", infect=True)
    blk = CombatCreature("Steel Golem", 1, 1, "B", indestructible=True)
    link_block(atk, blk)
    sim = CombatSimulator([atk], [blk])
    result = sim.simulate()
    assert blk in result.creatures_destroyed
    assert blk.minus1_counters == 1


def test_player_loses_at_ten_poison():
    """CR 104.3c: A player with ten or more poison counters loses the game."""
    atk = CombatCreature("Infector", 1, 1, "A", infect=True)
    defender = CombatCreature("Dummy", 0, 1, "B")
    state = GameState(
        players={
            "A": PlayerState(life=DEFAULT_STARTING_LIFE, creatures=[atk]),
            "B": PlayerState(
                life=DEFAULT_STARTING_LIFE, creatures=[defender], poison=9
            ),
        }
    )
    sim = CombatSimulator([atk], [defender], game_state=state)
    sim.simulate()
    assert state.players["B"].poison == POISON_LOSS_THRESHOLD
    assert has_player_lost(state, "B")
    assert "B" in sim.players_lost


def test_infect_against_multiple_blockers():
    """CR 702.90a: Infect assigns -1/-1 counters to each blocker in order."""
    atk = CombatCreature("Plague Bear", 3, 3, "A", infect=True)
    b1 = CombatCreature("B1", 2, 2, "B")
    b2 = CombatCreature("B2", 2, 2, "B")
    link_block(atk, b1, b2)
    sim = CombatSimulator([atk], [b1, b2])
    result = sim.simulate()
    counters = sorted([b1.minus1_counters, b2.minus1_counters])
    assert counters == [1, 2]
    dead = {c.name for c in result.creatures_destroyed}
    assert "Plague Bear" in dead
    assert (b1.name in dead) != (b2.name in dead)


def test_infect_with_afflict_still_deals_life_loss():
    """CR 702.131 & 702.90a: Afflict damage is normal even if the creature has infect."""
    atk = CombatCreature("Torturer", 2, 2, "A", infect=True, afflict=2)
    blk = CombatCreature("Guard", 2, 2, "B")
    link_block(atk, blk)
    state = GameState(
        players={
            "A": PlayerState(life=DEFAULT_STARTING_LIFE, creatures=[atk]),
            "B": PlayerState(life=DEFAULT_STARTING_LIFE, creatures=[blk]),
        }
    )
    sim = CombatSimulator([atk], [blk], game_state=state)
    result = sim.simulate()
    assert result.damage_to_players["B"] == 2
    assert state.players["B"].life == 18
    assert blk.minus1_counters == 2


def test_infect_unblocked_poison_to_player():
    """CR 702.90b: Infect damage to a player gives poison counters instead of life loss."""
    atk = CombatCreature("Agent", 2, 2, "A", infect=True)
    defender = CombatCreature("Dummy", 0, 1, "B")
    sim = CombatSimulator([atk], [defender])
    result = sim.simulate()
    assert result.poison_counters["B"] == 2
    assert result.damage_to_players.get("B", 0) == 0


def test_infect_unblocked_lifelink_gains_life():
    """CR 702.15a & 702.90b: Lifelink triggers even when infect damage becomes poison counters."""
    atk = CombatCreature("Healer", 2, 2, "A", infect=True, lifelink=True)
    defender = CombatCreature("Dummy", 0, 1, "B")
    state = GameState(
        players={
            "A": PlayerState(life=10, creatures=[atk]),
            "B": PlayerState(life=DEFAULT_STARTING_LIFE, creatures=[defender]),
        }
    )
    sim = CombatSimulator([atk], [defender], game_state=state)
    result = sim.simulate()
    assert result.poison_counters["B"] == 2
    assert result.lifegain["A"] == 2
    assert state.players["A"].life == 12


def test_first_strike_infect_kills_before_damage():
    """CR 702.7b & 702.90b: First strike infect can kill a blocker before it assigns damage."""
    atk = CombatCreature("Fencer", 2, 2, "A", infect=True, first_strike=True)
    blk = CombatCreature("Bear", 2, 2, "B")
    link_block(atk, blk)
    sim = CombatSimulator([atk], [blk])
    result = sim.simulate()
    assert blk.minus1_counters == 2
    assert blk in result.creatures_destroyed
    assert atk not in result.creatures_destroyed


def test_double_strike_infect_poison_twice():
    """CR 702.4b & 702.90b: Double strike with infect gives poison counters in each damage step."""
    atk = CombatCreature("Duelist", 1, 1, "A", infect=True, double_strike=True)
    defender = CombatCreature("Dummy", 0, 1, "B")
    sim = CombatSimulator([atk], [defender])
    result = sim.simulate()
    assert result.poison_counters["B"] == 2
    assert result.damage_to_players.get("B", 0) == 0


def test_trample_infect_multiple_blockers():
    """CR 702.19b & 702.90b: Excess infect damage with trample becomes poison counters."""
    atk = CombatCreature("Beast", 3, 3, "A", trample=True, infect=True)
    b1 = CombatCreature("Goblin1", 1, 1, "B")
    b2 = CombatCreature("Goblin2", 1, 1, "B")
    link_block(atk, b1, b2)
    sim = CombatSimulator([atk], [b1, b2])
    result = sim.simulate()
    assert b1.minus1_counters == 1
    assert b2.minus1_counters == 1
    assert result.poison_counters["B"] == 1
    assert b1 in result.creatures_destroyed and b2 in result.creatures_destroyed


def test_infect_kills_undying_but_it_returns():
    """CR 702.92a & 702.90b: Undying returns a creature even if infect dealt the damage."""
    atk = CombatCreature("Slayer", 2, 2, "A", infect=True)
    blk = CombatCreature("Spirit", 2, 2, "B", undying=True)
    link_block(atk, blk)
    sim = CombatSimulator([atk], [blk])
    result = sim.simulate()
    assert blk not in result.creatures_destroyed
    assert blk.plus1_counters == 1
    assert blk.minus1_counters == 0


def test_infect_kills_creature_with_counters():
    """CR 702.90b: Infect damage to a creature is dealt as -1/-1 counters."""
    atk = CombatCreature("Toxic Bear", 3, 3, "A", infect=True)
    blk = CombatCreature("Wall", 2, 2, "B")
    link_block(atk, blk)
    sim = CombatSimulator([atk], [blk])
    result = sim.simulate()
    assert blk.minus1_counters == 2
    assert blk in result.creatures_destroyed


def test_infect_lifelink_vs_blocker():
    """CR 702.90b & 702.15a: Infect gives counters and lifelink gains that much life."""
    atk = CombatCreature("Toxic Cleric", 2, 2, "A", infect=True, lifelink=True)
    blk = CombatCreature("Bear", 2, 2, "B")
    link_block(atk, blk)
    state = GameState(
        players={
            "A": PlayerState(life=10, creatures=[atk]),
            "B": PlayerState(life=DEFAULT_STARTING_LIFE, creatures=[blk]),
        }
    )
    sim = CombatSimulator([atk], [blk], game_state=state)
    result = sim.simulate()
    assert blk.minus1_counters == 2
    assert result.lifegain["A"] == 2
    assert state.players["A"].life == 12


def test_infect_first_strike_kills_before_damage():
    """CR 702.7b & 702.90b: First strike infect kills the blocker before it can deal damage."""
    atk = CombatCreature("Toxic Fencer", 2, 2, "A", infect=True, first_strike=True)
    blk = CombatCreature("Bear", 2, 2, "B")
    link_block(atk, blk)
    sim = CombatSimulator([atk], [blk])
    result = sim.simulate()
    assert blk.minus1_counters == 2
    assert blk in result.creatures_destroyed
    assert atk not in result.creatures_destroyed


def test_infect_prevents_persist_return():
    """CR 702.90b & 702.77a: Infect counters stop a persist creature from returning."""
    atk = CombatCreature("Infecting Knight", 2, 2, "A", infect=True)
    blk = CombatCreature("Everlasting", 2, 2, "B", persist=True)
    link_block(atk, blk)
    sim = CombatSimulator([atk], [blk])
    result = sim.simulate()
    assert blk in result.creatures_destroyed
    assert blk.minus1_counters == 2


def test_lifelink_infect_vs_creature():
    """CR 702.15a & 702.90b: Lifelink gains life even when infect damages a creature."""
    atk = CombatCreature("Toxic Healer", 3, 3, "A", infect=True, lifelink=True)
    blk = CombatCreature("Bear", 3, 3, "B")
    link_block(atk, blk)
    state = GameState(
        players={
            "A": PlayerState(life=10, creatures=[atk]),
            "B": PlayerState(life=DEFAULT_STARTING_LIFE, creatures=[blk]),
        }
    )
    sim = CombatSimulator([atk], [blk], game_state=state)
    result = sim.simulate()
    assert result.lifegain["A"] == 3
    assert blk.minus1_counters == 3
    assert state.players["A"].life == 13


def test_infect_with_afflict_still_causes_life_loss():
    """CR 702.131a & 702.90b: Afflict causes life loss even when an infect creature is blocked."""
    atk = CombatCreature("Tormentor", 2, 2, "A", infect=True, afflict=1)
    blk = CombatCreature("Guard", 2, 2, "B")
    link_block(atk, blk)
    state = GameState(
        players={
            "A": PlayerState(life=DEFAULT_STARTING_LIFE, creatures=[atk]),
            "B": PlayerState(life=DEFAULT_STARTING_LIFE, creatures=[blk]),
        }
    )
    sim = CombatSimulator([atk], [blk], game_state=state)
    result = sim.simulate()
    assert state.players["B"].life == 19
    assert result.poison_counters.get("B", 0) == 0
    assert blk.minus1_counters == 2
