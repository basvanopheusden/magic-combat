import time

import pytest

from magic_combat import Color
from magic_combat import CombatCreature
from magic_combat import CombatSimulator
from magic_combat import GameState
from magic_combat import PlayerState
from magic_combat import decide_optimal_blocks
from magic_combat.constants import DEFAULT_STARTING_LIFE


def test_optimal_ai_respects_provoke():
    """CR 702.40a: Provoke requires the chosen creature to block if able."""
    atk = CombatCreature("Taunter", 2, 2, "A", provoke=True)
    blk = CombatCreature("Guard", 2, 2, "B")
    state = GameState(
        players={
            "A": PlayerState(life=20, creatures=[atk]),
            "B": PlayerState(life=20, creatures=[blk]),
        }
    )
    decide_optimal_blocks(game_state=state, provoke_map={atk: blk})
    sim = CombatSimulator([atk], [blk], game_state=state, provoke_map={atk: blk})
    sim.validate_blocking()
    assert blk.blocking is atk
    assert atk.blocked_by == [blk]


def test_optimal_ai_provoke_untaps_tapped_blocker():
    """CR 702.39a: Provoke untaps the target before it blocks."""
    atk = CombatCreature("Needler", 1, 1, "A", provoke=True)
    blk = CombatCreature("Sentry", 2, 2, "B", tapped=True)
    state = GameState(
        players={
            "A": PlayerState(life=20, creatures=[atk]),
            "B": PlayerState(life=20, creatures=[blk]),
        }
    )
    blk.tapped = False
    decide_optimal_blocks(game_state=state, provoke_map={atk: blk})
    sim = CombatSimulator([atk], [blk], game_state=state, provoke_map={atk: blk})
    sim.validate_blocking()
    assert blk.blocking is atk


def test_optimal_ai_respects_multiple_provoke():
    """CR 702.40a: Each provoked creature must block its chosen attacker."""
    atk1 = CombatCreature("Taunter1", 2, 2, "A", provoke=True)
    atk2 = CombatCreature("Taunter2", 3, 3, "A", provoke=True)
    blk1 = CombatCreature("Guard1", 2, 2, "B")
    blk2 = CombatCreature("Guard2", 3, 3, "B")
    provoke_map = {atk1: blk1, atk2: blk2}
    state = GameState(
        players={
            "A": PlayerState(life=20, creatures=[atk1, atk2]),
            "B": PlayerState(life=20, creatures=[blk1, blk2]),
        }
    )
    decide_optimal_blocks(game_state=state, provoke_map=provoke_map)
    sim = CombatSimulator(
        [atk1, atk2], [blk1, blk2], game_state=state, provoke_map=provoke_map
    )
    sim.validate_blocking()


def test_optimal_ai_blocks_provoke_target_favorably():
    """CR 702.40a: Provoke forces a creature to block if able."""
    atk1 = CombatCreature("Taunter", 2, 2, "A", provoke=True)
    atk2 = CombatCreature("Brute", 4, 4, "A")
    blk1 = CombatCreature("Guard1", 2, 2, "B")
    blk2 = CombatCreature("Guard2", 4, 4, "B")
    state = GameState(
        players={
            "A": PlayerState(life=20, creatures=[atk1, atk2]),
            "B": PlayerState(life=20, creatures=[blk1, blk2]),
        }
    )
    decide_optimal_blocks(game_state=state, provoke_map={atk1: blk1})
    assert blk1.blocking is atk1
    assert blk2.blocking is atk2


def test_ai_blocks_to_prevent_lethal():
    """CR 104.3a: A player with 0 or less life loses the game."""
    atk = CombatCreature("Ogre", 3, 3, "A")
    blk = CombatCreature("Guard", 1, 1, "B")
    state = GameState(
        players={
            "A": PlayerState(life=DEFAULT_STARTING_LIFE, creatures=[atk]),
            "B": PlayerState(life=2, creatures=[blk]),
        }
    )
    decide_optimal_blocks(game_state=state)
    assert blk.blocking is atk
    assert atk.blocked_by == [blk]
    sim = CombatSimulator([atk], [blk], game_state=state)
    result = sim.simulate()
    assert result.damage_to_players.get("B", 0) == 0


def test_ai_prefers_best_value_trade():
    """CR 509.1a: The defending player chooses how creatures block."""
    a1 = CombatCreature("Giant", 5, 5, "A")
    a2 = CombatCreature("Goblin", 2, 2, "A")
    b1 = CombatCreature("Knight", 3, 3, "B")
    b2 = CombatCreature("Soldier", 2, 2, "B")
    state = GameState(
        players={
            "A": PlayerState(life=DEFAULT_STARTING_LIFE, creatures=[a1, a2]),
            "B": PlayerState(life=DEFAULT_STARTING_LIFE, creatures=[b1, b2]),
        }
    )
    decide_optimal_blocks(game_state=state)
    # The heuristic keeps the Soldier back and has Knight trade with Goblin
    assert b2.blocking is None
    assert b1.blocking is a2
    assert a1.blocked_by == []
    assert a2.blocked_by == [b1]
    sim = CombatSimulator([a1, a2], [b1, b2], game_state=state)
    result = sim.simulate()
    # Only the Goblin should die
    dead = {c.name for c in result.creatures_destroyed}
    assert dead == {"Goblin"}


def test_ai_saves_creature_when_blocking_is_bad():
    """CR 509.1a: The defending player may choose not to block."""
    atk = CombatCreature("Brute", 3, 3, "A")
    blk = CombatCreature("Squire", 2, 2, "B")
    state = GameState(
        players={
            "A": PlayerState(life=DEFAULT_STARTING_LIFE, creatures=[atk]),
            "B": PlayerState(life=10, creatures=[blk]),
        }
    )
    decide_optimal_blocks(game_state=state)
    assert blk.blocking is None


def test_ai_chump_block_to_prevent_lethal():
    """CR 104.3a: A player with 0 or less life loses the game."""
    atk = CombatCreature("Giant", 6, 6, "A")
    blk = CombatCreature("Peasant", 1, 1, "B")
    state = GameState(
        players={
            "A": PlayerState(life=DEFAULT_STARTING_LIFE, creatures=[atk]),
            "B": PlayerState(life=5, creatures=[blk]),
        }
    )
    decide_optimal_blocks(game_state=state)
    assert blk.blocking is atk


def test_ai_selects_correct_blocker_with_multiple_attackers():
    """CR 509.1a: The defending player chooses how creatures block."""
    a1 = CombatCreature("Orc", 4, 4, "A")
    a2 = CombatCreature("Ogre", 3, 3, "A")
    blk = CombatCreature("Guard", 4, 4, "B")
    state = GameState(
        players={
            "A": PlayerState(life=DEFAULT_STARTING_LIFE, creatures=[a1, a2]),
            "B": PlayerState(life=DEFAULT_STARTING_LIFE, creatures=[blk]),
        }
    )
    decide_optimal_blocks(game_state=state)
    assert blk.blocking is a2


def test_ai_double_blocks_big_attacker_to_kill():
    """CR 509.1a: The defending player can assign multiple blockers."""
    atk = CombatCreature("Colossus", 5, 5, "A")
    b1 = CombatCreature("Soldier1", 3, 3, "B")
    b2 = CombatCreature("Soldier2", 3, 3, "B")
    state = GameState(
        players={
            "A": PlayerState(life=DEFAULT_STARTING_LIFE, creatures=[atk]),
            "B": PlayerState(life=DEFAULT_STARTING_LIFE, creatures=[b1, b2]),
        }
    )
    decide_optimal_blocks(game_state=state)
    assert b1.blocking is atk and b2.blocking is atk


def test_ai_double_blocks_first_striker():
    """CR 702.7b: Creatures with first strike deal damage before others."""
    atk1 = CombatCreature("First", 2, 2, "A", first_strike=True)
    atk2 = CombatCreature("Vanilla", 2, 2, "A")
    b1 = CombatCreature("Block1", 2, 2, "B")
    b2 = CombatCreature("Block2", 2, 2, "B")
    state = GameState(
        players={
            "A": PlayerState(life=DEFAULT_STARTING_LIFE, creatures=[atk1, atk2]),
            "B": PlayerState(life=DEFAULT_STARTING_LIFE, creatures=[b1, b2]),
        }
    )
    decide_optimal_blocks(game_state=state)
    assert b1.blocking is atk1 and b2.blocking is atk1


def test_ai_blocks_trample_to_prevent_lethal():
    """CR 702.19b: Trample damage exceeding blockers is dealt to the player."""
    atk = CombatCreature("Crusher", 5, 5, "A", trample=True)
    blk = CombatCreature("Wall", 5, 5, "B")
    state = GameState(
        players={
            "A": PlayerState(life=DEFAULT_STARTING_LIFE, creatures=[atk]),
            "B": PlayerState(life=4, creatures=[blk]),
        }
    )
    decide_optimal_blocks(game_state=state)
    assert blk.blocking is atk


def test_ai_blocks_trample_with_two_when_needed():
    """CR 702.19b: Multiple blockers can absorb trampler damage."""
    atk = CombatCreature("Behemoth", 6, 6, "A", trample=True)
    b1 = CombatCreature("Guard1", 4, 4, "B")
    b2 = CombatCreature("Guard2", 2, 2, "B")
    state = GameState(
        players={
            "A": PlayerState(life=DEFAULT_STARTING_LIFE, creatures=[atk]),
            "B": PlayerState(life=1, creatures=[b1, b2]),
        }
    )
    decide_optimal_blocks(game_state=state)
    assert b1.blocking is atk and b2.blocking is atk


def test_ai_blocks_menace_with_two_blockers():
    """CR 702.110b: A creature with menace must be blocked by two or more creatures."""
    atk = CombatCreature("Scary", 3, 3, "A", menace=True)
    b1 = CombatCreature("B1", 2, 2, "B")
    b2 = CombatCreature("B2", 2, 2, "B")
    state = GameState(
        players={
            "A": PlayerState(life=DEFAULT_STARTING_LIFE, creatures=[atk]),
            "B": PlayerState(life=DEFAULT_STARTING_LIFE, creatures=[b1, b2]),
        }
    )
    decide_optimal_blocks(game_state=state)
    assert b1.blocking is atk and b2.blocking is atk


def test_optimal_ai_ignores_provoke_with_single_blocker():
    """CR 702.40a & 702.110b: Provoke doesn't force a block if menace can't be satisfied."""
    atk = CombatCreature("Tunnel Rogue", 2, 2, "A", menace=True, provoke=True)
    blk = CombatCreature("Goblin", 2, 2, "B")
    state = GameState(
        players={
            "A": PlayerState(life=DEFAULT_STARTING_LIFE, creatures=[atk]),
            "B": PlayerState(life=DEFAULT_STARTING_LIFE, creatures=[blk]),
        }
    )
    decide_optimal_blocks(game_state=state, provoke_map={atk: blk})
    assert blk.blocking is None


def test_ai_blocks_fear_with_correct_color():
    """CR 702.36a: Fear restricts blocking to black or artifact creatures."""
    atk = CombatCreature("Shade", 2, 2, "A", fear=True)
    w = CombatCreature("White", 2, 2, "B", colors={Color.WHITE})
    blk = CombatCreature("Black", 2, 2, "B", colors={Color.BLACK})
    state = GameState(
        players={
            "A": PlayerState(life=DEFAULT_STARTING_LIFE, creatures=[atk]),
            "B": PlayerState(life=DEFAULT_STARTING_LIFE, creatures=[w, blk]),
        }
    )
    decide_optimal_blocks(game_state=state)
    assert w.blocking is None and blk.blocking is atk


def test_ai_blocks_infect_when_poison_would_be_lethal():
    """CR 104.3c: A player with ten or more poison counters loses the game."""
    atk = CombatCreature("Infecter", 1, 1, "A", infect=True)
    big = CombatCreature("Brute", 4, 4, "A")
    blk = CombatCreature("Guard", 4, 4, "B")
    state = GameState(
        players={
            "A": PlayerState(life=DEFAULT_STARTING_LIFE, creatures=[atk, big]),
            "B": PlayerState(life=10, creatures=[blk], poison=9),
        }
    )
    decide_optimal_blocks(game_state=state)
    assert blk.blocking is atk


def test_ai_blocks_flying_with_reach_creature():
    """CR 702.9b: A creature with reach can block creatures with flying."""
    flyer = CombatCreature("Hawk", 2, 2, "A", flying=True)
    ground = CombatCreature("Bear", 2, 2, "A")
    reacher = CombatCreature("Archer", 1, 3, "B", reach=True)
    state = GameState(
        players={
            "A": PlayerState(life=DEFAULT_STARTING_LIFE, creatures=[flyer, ground]),
            "B": PlayerState(life=DEFAULT_STARTING_LIFE, creatures=[reacher]),
        }
    )
    decide_optimal_blocks(game_state=state)
    assert reacher.blocking is flyer


def test_ai_spreads_blocks_for_max_value():
    """CR 509.1a: The defending player chooses how creatures block."""
    a1 = CombatCreature("A1", 3, 3, "A")
    a2 = CombatCreature("A2", 2, 2, "A")
    b1 = CombatCreature("B1", 3, 3, "B")
    b2 = CombatCreature("B2", 2, 2, "B")
    b3 = CombatCreature("B3", 2, 2, "B")
    state = GameState(
        players={
            "A": PlayerState(life=DEFAULT_STARTING_LIFE, creatures=[a1, a2]),
            "B": PlayerState(life=DEFAULT_STARTING_LIFE, creatures=[b1, b2, b3]),
        }
    )
    decide_optimal_blocks(game_state=state)
    assert sum(blk.blocking is not None for blk in (b1, b2, b3)) >= 2


def test_ai_blocks_three_attackers_prioritize_biggest():
    """CR 509.1a: The defending player chooses how creatures block."""
    a1 = CombatCreature("Small", 1, 1, "A")
    a2 = CombatCreature("Medium", 3, 3, "A")
    a3 = CombatCreature("Large", 5, 5, "A")
    b1 = CombatCreature("Blocker1", 5, 5, "B")
    b2 = CombatCreature("Blocker2", 2, 2, "B")
    state = GameState(
        players={
            "A": PlayerState(life=DEFAULT_STARTING_LIFE, creatures=[a1, a2, a3]),
            "B": PlayerState(life=DEFAULT_STARTING_LIFE, creatures=[b1, b2]),
        }
    )
    decide_optimal_blocks(game_state=state)
    assert b1.blocking is a2 and b2.blocking is a1


def test_ai_blocks_to_minimize_life_loss():
    """CR 509.1a: The defending player chooses how creatures block."""
    a1 = CombatCreature("Heavy", 4, 4, "A")
    a2 = CombatCreature("Light", 1, 1, "A")
    blk = CombatCreature("Wall", 4, 4, "B")
    state = GameState(
        players={
            "A": PlayerState(life=DEFAULT_STARTING_LIFE, creatures=[a1, a2]),
            "B": PlayerState(life=5, creatures=[blk]),
        }
    )
    decide_optimal_blocks(game_state=state)
    assert blk.blocking is a2


def test_ai_no_block_when_survival_and_bad_trade():
    """CR 509.1a: Blocking is optional."""
    atk = CombatCreature("Brute", 4, 4, "A")
    blk = CombatCreature("Weakling", 1, 1, "B")
    state = GameState(
        players={
            "A": PlayerState(life=DEFAULT_STARTING_LIFE, creatures=[atk]),
            "B": PlayerState(life=10, creatures=[blk]),
        }
    )
    decide_optimal_blocks(game_state=state)
    assert blk.blocking is None


def test_ai_blocks_lifelink_attacker_to_stop_gain():
    """CR 702.15a: Lifelink causes its controller to gain that much life."""
    atk = CombatCreature("Priest", 2, 2, "A", lifelink=True)
    blk = CombatCreature("Bear", 2, 2, "B")
    state = GameState(
        players={
            "A": PlayerState(life=DEFAULT_STARTING_LIFE, creatures=[atk]),
            "B": PlayerState(life=DEFAULT_STARTING_LIFE, creatures=[blk]),
        }
    )
    decide_optimal_blocks(game_state=state)
    assert blk.blocking is atk


def test_ai_deterministic_tiebreaker():
    """CR 509.1a: With equal outcomes, the choice should be deterministic."""
    a1 = CombatCreature("A1", 2, 2, "A")
    a2 = CombatCreature("A2", 2, 2, "A")
    b1 = CombatCreature("B1", 2, 2, "B")
    b2 = CombatCreature("B2", 2, 2, "B")
    state = GameState(
        players={
            "A": PlayerState(life=DEFAULT_STARTING_LIFE, creatures=[a1, a2]),
            "B": PlayerState(life=DEFAULT_STARTING_LIFE, creatures=[b1, b2]),
        }
    )
    decide_optimal_blocks(game_state=state)
    assert (b1.blocking, b2.blocking) == (a1, a2)


def test_ai_blocks_creature_with_first_strike_over_vanilla():
    """CR 702.7b: First strike makes that attacker more dangerous."""
    a1 = CombatCreature("First", 2, 2, "A", first_strike=True)
    a2 = CombatCreature("Vanilla", 2, 2, "A")
    blk = CombatCreature("Guard", 2, 2, "B")
    state = GameState(
        players={
            "A": PlayerState(life=DEFAULT_STARTING_LIFE, creatures=[a1, a2]),
            "B": PlayerState(life=DEFAULT_STARTING_LIFE, creatures=[blk]),
        }
    )
    decide_optimal_blocks(game_state=state)
    assert blk.blocking is a2


def test_ai_prefers_blocking_to_kill_more_mana():
    """CR 509.1a: The defending player chooses how creatures block."""
    a1 = CombatCreature("A1", 4, 4, "A", mana_cost="{6}")
    a2 = CombatCreature("A2", 2, 2, "A", mana_cost="{2}")
    b1 = CombatCreature("B1", 4, 4, "B", mana_cost="{5}")
    b2 = CombatCreature("B2", 4, 4, "B", mana_cost="{1}")
    state = GameState(
        players={
            "A": PlayerState(life=DEFAULT_STARTING_LIFE, creatures=[a1, a2]),
            "B": PlayerState(life=4, creatures=[b1, b2]),
        }
    )
    decide_optimal_blocks(game_state=state)
    assert b1.blocking is a2 and b2.blocking is a1


def test_iteration_limit_triggers():
    """CR 509.1a: The defending player chooses how creatures block."""
    atk = CombatCreature("Big", 5, 5, "A")
    b1 = CombatCreature("B1", 2, 2, "B")
    b2 = CombatCreature("B2", 2, 2, "B")
    state = GameState(
        players={
            "A": PlayerState(life=DEFAULT_STARTING_LIFE, creatures=[atk]),
            "B": PlayerState(life=DEFAULT_STARTING_LIFE, creatures=[b1, b2]),
        }
    )
    from magic_combat import IterationLimitError

    with pytest.raises(IterationLimitError):
        decide_optimal_blocks(game_state=state, max_iterations=1)


def test_iteration_limit_allows_fast_run():
    """CR 509.1a: The defending player chooses how creatures block."""
    a1 = CombatCreature("A1", 3, 3, "A")
    a2 = CombatCreature("A2", 3, 3, "A")
    b1 = CombatCreature("B1", 3, 3, "B")
    b2 = CombatCreature("B2", 3, 3, "B")
    state = GameState(
        players={
            "A": PlayerState(life=DEFAULT_STARTING_LIFE, creatures=[a1, a2]),
            "B": PlayerState(life=DEFAULT_STARTING_LIFE, creatures=[b1, b2]),
        }
    )
    start = time.perf_counter()
    decide_optimal_blocks(
        game_state=state,
        max_iterations=1000,
    )
    duration = time.perf_counter() - start
    assert duration < 2


def test_ai_optimal_count_ignores_tiebreaker():
    """CR 509.1a: The defending player chooses how creatures block."""
    a1 = CombatCreature("A1", 2, 2, "A")
    a2 = CombatCreature("A2", 2, 2, "A")
    b1 = CombatCreature("B1", 2, 2, "B")
    b2 = CombatCreature("B2", 2, 2, "B")
    state = GameState(
        players={
            "A": PlayerState(life=DEFAULT_STARTING_LIFE, creatures=[a1, a2]),
            "B": PlayerState(life=DEFAULT_STARTING_LIFE, creatures=[b1, b2]),
        }
    )
    assns, opt = decide_optimal_blocks(game_state=state, k=2)
    assert opt == 2
    assert len(assns) >= 2


def test_ai_ignores_tapped_blocker():
    """CR 509.1a: The chosen creatures must be untapped."""

    atk = CombatCreature("Bear", 2, 2, "A")
    blk = CombatCreature("Exhausted", 2, 2, "B", tapped=True)
    state = GameState(
        players={
            "A": PlayerState(life=20, creatures=[atk]),
            "B": PlayerState(life=1, creatures=[blk]),
        }
    )
    decide_optimal_blocks(game_state=state)
    assert blk.blocking is None


def test_ai_blocks_persist_when_free():
    """CR 702.77a & 509.1a: Optimal blocking kills a persist attacker if able."""
    atk = CombatCreature("Spirit", 2, 2, "A", persist=True)
    blk = CombatCreature("Giant", 3, 3, "B")
    state = GameState(
        players={
            "A": PlayerState(life=DEFAULT_STARTING_LIFE, creatures=[atk]),
            "B": PlayerState(life=DEFAULT_STARTING_LIFE, creatures=[blk]),
        }
    )
    decide_optimal_blocks(game_state=state)
    assert blk.blocking is atk


def test_ai_blocks_undying_when_free():
    """CR 702.92a & 509.1a: Optimal blocking kills an undying attacker if able."""
    atk = CombatCreature("Phoenix", 2, 2, "A", undying=True)
    blk = CombatCreature("Giant", 3, 3, "B")
    state = GameState(
        players={
            "A": PlayerState(life=DEFAULT_STARTING_LIFE, creatures=[atk]),
            "B": PlayerState(life=DEFAULT_STARTING_LIFE, creatures=[blk]),
        }
    )
    decide_optimal_blocks(game_state=state)
    assert blk.blocking is None


def test_optimal_ai_accounts_for_mentor_map():
    """CR 702.134a: Mentor gives counters to a weaker attacker."""

    mentor = CombatCreature("Mentor", 2, 2, "A", mentor=True)
    pupil = CombatCreature("Pupil", 1, 1, "A")
    blk1 = CombatCreature("Blocker", 2, 2, "B")
    state1 = GameState(
        players={
            "A": PlayerState(life=DEFAULT_STARTING_LIFE, creatures=[mentor, pupil]),
            "B": PlayerState(life=DEFAULT_STARTING_LIFE, creatures=[blk1]),
        }
    )
    decide_optimal_blocks(game_state=state1)
    assert blk1.blocking is pupil

    mentor = CombatCreature("Mentor", 2, 2, "A", mentor=True)
    pupil = CombatCreature("Pupil", 1, 1, "A")
    blk2 = CombatCreature("Blocker", 2, 2, "B")
    state2 = GameState(
        players={
            "A": PlayerState(life=DEFAULT_STARTING_LIFE, creatures=[mentor, pupil]),
            "B": PlayerState(life=DEFAULT_STARTING_LIFE, creatures=[blk2]),
        }
    )
    decide_optimal_blocks(game_state=state2, mentor_map={mentor: pupil})
    assert blk2.blocking is mentor
