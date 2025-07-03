from magic_combat import CombatCreature
from magic_combat import CombatSimulator
from magic_combat import GameState
from magic_combat import PlayerState
from magic_combat.constants import DEFAULT_STARTING_LIFE
from magic_combat.constants import POISON_LOSS_THRESHOLD
from tests.conftest import link_block


def test_afflict_lethal_when_blocked():
    """CR 702.131a & 104.3a: Afflict causes life loss when this creature becomes blocked; a player with 0 or less life loses the game."""
    atk = CombatCreature("Tormentor", 2, 2, "A", afflict=2)
    blk = CombatCreature("Guard", 2, 2, "B")
    link_block(atk, blk)
    state = GameState(
        players={
            "A": PlayerState(life=DEFAULT_STARTING_LIFE, creatures=[atk]),
            "B": PlayerState(life=2, creatures=[blk]),
        }
    )
    sim = CombatSimulator([atk], [blk], game_state=state)
    sim.simulate()
    assert state.players["B"].life == 0
    assert state.has_player_lost("B")
    assert "B" in sim.players_lost


def test_afflict_and_trample_combined_lethal():
    """CR 702.131a, 702.19b & 104.3a: Afflict reduces life before damage and excess trample damage can finish a player off."""
    atk = CombatCreature("Rager", 2, 2, "A", afflict=2, trample=True)
    blk = CombatCreature("Chump", 1, 1, "B")
    link_block(atk, blk)
    state = GameState(
        players={
            "A": PlayerState(life=DEFAULT_STARTING_LIFE, creatures=[atk]),
            "B": PlayerState(life=3, creatures=[blk]),
        }
    )
    sim = CombatSimulator([atk], [blk], game_state=state)
    sim.simulate()
    assert state.players["B"].life == 0
    assert state.has_player_lost("B")
    assert "B" in sim.players_lost


def test_toxic_three_poison_counters_causes_loss():
    """CR 702.180a & 104.3c: Toxic gives that many poison counters; a player with ten or more poison counters loses."""
    atk = CombatCreature("Stinger", 1, 1, "A", toxic=3)
    defender = CombatCreature("Dummy", 0, 1, "B")
    state = GameState(
        players={
            "A": PlayerState(life=DEFAULT_STARTING_LIFE, creatures=[atk]),
            "B": PlayerState(
                life=DEFAULT_STARTING_LIFE, creatures=[defender], poison=8
            ),
        }
    )
    sim = CombatSimulator([atk], [defender], game_state=state)
    sim.simulate()
    assert state.players["B"].poison == 11
    assert state.has_player_lost("B")
    assert "B" in sim.players_lost


def test_infect_and_toxic_exactly_ten_poison():
    """CR 702.90b & 104.3c: Infect and toxic together can give enough poison counters for a player to lose."""
    atk = CombatCreature("Toxic Infector", 2, 2, "A", infect=True, toxic=2)
    defender = CombatCreature("Dummy", 0, 1, "B")
    state = GameState(
        players={
            "A": PlayerState(life=DEFAULT_STARTING_LIFE, creatures=[atk]),
            "B": PlayerState(
                life=DEFAULT_STARTING_LIFE, creatures=[defender], poison=6
            ),
        }
    )
    sim = CombatSimulator([atk], [defender], game_state=state)
    sim.simulate()
    assert state.players["B"].poison == POISON_LOSS_THRESHOLD
    assert state.has_player_lost("B")
    assert "B" in sim.players_lost


def test_double_strike_infect_first_step_loss():
    """CR 702.4b, 702.90b & 104.3c: Double strike with infect can cause a player to lose after the first combat damage step."""
    atk = CombatCreature("Toxic Duelist", 1, 1, "A", infect=True, double_strike=True)
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
    assert state.players["B"].poison == 11
    assert state.has_player_lost("B")
    assert "B" in sim.players_lost


def test_double_strike_trample_overkill():
    """CR 702.4b, 702.19b & 104.3a: Damage from both combat steps of a double strike trampler can reduce a player's life below zero."""
    atk = CombatCreature("Crusher", 3, 3, "A", double_strike=True, trample=True)
    blk = CombatCreature("Blocker", 1, 1, "B")
    link_block(atk, blk)
    state = GameState(
        players={
            "A": PlayerState(life=DEFAULT_STARTING_LIFE, creatures=[atk]),
            "B": PlayerState(life=3, creatures=[blk]),
        }
    )
    sim = CombatSimulator([atk], [blk], game_state=state)
    sim.simulate()
    assert state.players["B"].life == -2
    assert state.has_player_lost("B")
    assert "B" in sim.players_lost


def test_first_strike_blocker_barely_survives():
    """CR 702.7b & 104.3a: A blocker with first strike can kill the attacker before it deals damage, letting a low-life player survive."""
    atk = CombatCreature("Brute", 2, 2, "A")
    blk = CombatCreature("Savior", 2, 2, "B", first_strike=True)
    link_block(atk, blk)
    state = GameState(
        players={
            "A": PlayerState(life=DEFAULT_STARTING_LIFE, creatures=[atk]),
            "B": PlayerState(life=1, creatures=[blk]),
        }
    )
    sim = CombatSimulator([atk], [blk], game_state=state)
    sim.simulate()
    assert state.players["B"].life == 1
    assert not state.has_player_lost("B")
    assert "B" not in sim.players_lost


def test_trample_lifelink_kills_player():
    """CR 702.19b, 702.15a & 104.3a: Trample can assign lethal damage to the player and lifelink gains that much life for the attacker."""
    atk = CombatCreature("Juggernaut", 4, 4, "A", trample=True, lifelink=True)
    blk = CombatCreature("Chump", 1, 1, "B")
    link_block(atk, blk)
    state = GameState(
        players={
            "A": PlayerState(life=10, creatures=[atk]),
            "B": PlayerState(life=3, creatures=[blk]),
        }
    )
    sim = CombatSimulator([atk], [blk], game_state=state)
    sim.simulate()
    assert state.players["B"].life == 0
    assert state.players["A"].life == 14
    assert state.has_player_lost("B")
    assert "B" in sim.players_lost


def test_lifelink_cannot_prevent_poison_loss():
    """CR 702.15a, 702.90b & 104.3c: Lifelink doesn't stop a player from losing to poison counters inflicted by infect."""
    atk = CombatCreature("Toxic Vampire", 1, 1, "A", infect=True, lifelink=True)
    defender = CombatCreature("Dummy", 0, 1, "B")
    state = GameState(
        players={
            "A": PlayerState(life=5, creatures=[atk]),
            "B": PlayerState(
                life=DEFAULT_STARTING_LIFE, creatures=[defender], poison=9
            ),
        }
    )
    sim = CombatSimulator([atk], [defender], game_state=state)
    sim.simulate()
    assert state.players["A"].life == 6
    assert state.players["B"].poison == POISON_LOSS_THRESHOLD
    assert state.has_player_lost("B")
    assert "B" in sim.players_lost


def test_afflict_lethal_before_lifelink_can_save():
    """CR 702.131a & 104.3a: Afflict resolves before combat damage. If it drops a player to 0 life, they lose before lifelink damage occurs."""
    atk = CombatCreature("Menace", 2, 2, "A", afflict=1)
    blk = CombatCreature("Healer", 2, 2, "B", lifelink=True)
    link_block(atk, blk)
    state = GameState(
        players={
            "A": PlayerState(life=DEFAULT_STARTING_LIFE, creatures=[atk]),
            "B": PlayerState(life=1, creatures=[blk]),
        }
    )
    sim = CombatSimulator([atk], [blk], game_state=state)
    sim.simulate()
    assert state.players["B"].life == 2
    assert "B" in sim.players_lost
