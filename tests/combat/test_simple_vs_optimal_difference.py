import pytest
from magic_combat import (
    CombatCreature,
    GameState,
    PlayerState,
    decide_simple_blocks,
    decide_optimal_blocks,
    Color,
)


def _reset(*creatures):
    for c in creatures:
        c.blocking = None
        c.blocked_by.clear()


def test_seed10_deathtouch_first_strike():
    """CR 702.2b & 702.7b: Deathtouch is lethal and first strike deals damage earlier."""
    a0 = CombatCreature("A0", 1, 4, "A", deathtouch=True)
    a1 = CombatCreature("A1", 5, 1, "A", lifelink=True)
    b0 = CombatCreature("B0", 4, 4, "B", first_strike=True)
    b1 = CombatCreature("B1", 3, 2, "B")
    state = GameState(
        players={
            "A": PlayerState(life=20, creatures=[a0, a1]),
            "B": PlayerState(life=17, creatures=[b0, b1]),
        }
    )
    decide_simple_blocks([a0, a1], [b0, b1], game_state=state)
    assert b0.blocking is a1
    assert b1.blocking is None
    _reset(a0, a1, b0, b1)
    _, opt = decide_optimal_blocks([a0, a1], [b0, b1], game_state=state)
    assert opt == 1
    assert b0.blocking is a0
    assert b1.blocking is a1


def test_seed13_double_strike_trample():
    """CR 702.4b & 702.19b: Double strike and trample affect combat damage."""
    a0 = CombatCreature("A0", 3, 2, "A", double_strike=True)
    a1 = CombatCreature("A1", 2, 2, "A", trample=True)
    b0 = CombatCreature("B0", 2, 2, "B")
    b1 = CombatCreature("B1", 1, 5, "B", first_strike=True)
    state = GameState(
        players={
            "A": PlayerState(life=20, creatures=[a0, a1]),
            "B": PlayerState(life=10, creatures=[b0, b1]),
        }
    )
    decide_simple_blocks([a0, a1], [b0, b1], game_state=state)
    assert b0.blocking is None
    assert b1.blocking is a1
    _reset(a0, a1, b0, b1)
    _, opt = decide_optimal_blocks([a0, a1], [b0, b1], game_state=state)
    assert opt == 1
    assert b0.blocking is a1
    assert b1.blocking is a1


def test_seed21_first_strike_trample():
    """CR 702.7b & 702.19b: First strike and trample interact during combat."""
    a0 = CombatCreature("A0", 4, 4, "A", first_strike=True)
    a1 = CombatCreature("A1", 3, 4, "A", trample=True)
    b0 = CombatCreature("B0", 2, 4, "B")
    b1 = CombatCreature("B1", 5, 2, "B")
    state = GameState(
        players={
            "A": PlayerState(life=20, creatures=[a0, a1]),
            "B": PlayerState(life=17, creatures=[b0, b1]),
        }
    )
    decide_simple_blocks([a0, a1], [b0, b1], game_state=state)
    assert b0.blocking is None
    assert b1.blocking is a1
    _reset(a0, a1, b0, b1)
    _, opt = decide_optimal_blocks([a0, a1], [b0, b1], game_state=state)
    assert opt == 1
    assert b0.blocking is a1
    assert b1.blocking is a1


def test_seed26_trample_lifelink():
    """CR 702.19b & 702.15a: Trample and lifelink influence block priorities."""
    a0 = CombatCreature("A0", 2, 2, "A", trample=True)
    a1 = CombatCreature("A1", 5, 5, "A", lifelink=True)
    b0 = CombatCreature("B0", 2, 4, "B", flying=True)
    b1 = CombatCreature("B1", 5, 5, "B", flying=True)
    state = GameState(
        players={
            "A": PlayerState(life=20, creatures=[a0, a1]),
            "B": PlayerState(life=14, creatures=[b0, b1]),
        }
    )
    decide_simple_blocks([a0, a1], [b0, b1], game_state=state)
    assert b0.blocking is None
    assert b1.blocking is a0
    _reset(a0, a1, b0, b1)
    _, opt = decide_optimal_blocks([a0, a1], [b0, b1], game_state=state)
    assert opt == 1
    assert b0.blocking is a0
    assert b1.blocking is a1


def test_seed29_flying_deathtouch():
    """CR 702.9b & 702.2b: Flying and deathtouch affect blocking decisions."""
    a0 = CombatCreature("A0", 1, 3, "A", deathtouch=True)
    a1 = CombatCreature("A1", 5, 3, "A", deathtouch=True)
    b0 = CombatCreature("B0", 5, 3, "B", flying=True)
    b1 = CombatCreature("B1", 4, 1, "B", lifelink=True)
    state = GameState(
        players={
            "A": PlayerState(life=20, creatures=[a0, a1]),
            "B": PlayerState(life=4, creatures=[b0, b1]),
        }
    )
    decide_simple_blocks([a0, a1], [b0, b1], game_state=state)
    assert b0.blocking is a1
    assert b1.blocking is None
    _reset(a0, a1, b0, b1)
    _, opt = decide_optimal_blocks([a0, a1], [b0, b1], game_state=state)
    assert opt == 1
    assert b0.blocking is None
    assert b1.blocking is a1


def test_seed30_deathtouch_flying():
    """CR 702.2b & 702.9b: Deathtouch blocker choices vs a flying attacker."""
    a0 = CombatCreature("A0", 3, 5, "A", deathtouch=True)
    a1 = CombatCreature("A1", 5, 2, "A", flying=True)
    b0 = CombatCreature("B0", 1, 4, "B", double_strike=True)
    b1 = CombatCreature("B1", 2, 1, "B", lifelink=True)
    state = GameState(
        players={
            "A": PlayerState(life=20, creatures=[a0, a1]),
            "B": PlayerState(life=1, creatures=[b0, b1]),
        }
    )
    decide_simple_blocks([a0, a1], [b0, b1], game_state=state)
    assert b0.blocking is None
    assert b1.blocking is a0
    _reset(a0, a1, b0, b1)
    _, opt = decide_optimal_blocks([a0, a1], [b0, b1], game_state=state)
    assert opt == 1
    assert b0.blocking is None
    assert b1.blocking is None


def test_seed31_flying_trample():
    """CR 702.9b & 702.19b: Flying and trample combine for damage calculations."""
    a0 = CombatCreature("A0", 4, 1, "A", flying=True)
    a1 = CombatCreature("A1", 4, 2, "A")
    b0 = CombatCreature("B0", 1, 2, "B", trample=True)
    b1 = CombatCreature("B1", 5, 2, "B", flying=True)
    state = GameState(
        players={
            "A": PlayerState(life=20, creatures=[a0, a1]),
            "B": PlayerState(life=5, creatures=[b0, b1]),
        }
    )
    decide_simple_blocks([a0, a1], [b0, b1], game_state=state)
    assert b0.blocking is None
    assert b1.blocking is a0
    _reset(a0, a1, b0, b1)
    _, opt = decide_optimal_blocks([a0, a1], [b0, b1], game_state=state)
    assert opt == 1
    assert b0.blocking is None
    assert b1.blocking is a1


def test_seed37_trample_vs_deathtouch():
    """CR 702.19b & 702.2b: Trample damage and deathtouch blockers."""
    a0 = CombatCreature("A0", 5, 1, "A", trample=True)
    a1 = CombatCreature("A1", 5, 1, "A", deathtouch=True)
    b0 = CombatCreature("B0", 3, 4, "B", trample=True)
    b1 = CombatCreature("B1", 1, 4, "B", deathtouch=True)
    state = GameState(
        players={
            "A": PlayerState(life=20, creatures=[a0, a1]),
            "B": PlayerState(life=10, creatures=[b0, b1]),
        }
    )
    decide_simple_blocks([a0, a1], [b0, b1], game_state=state)
    assert b0.blocking is None
    assert b1.blocking is a0
    _reset(a0, a1, b0, b1)
    _, opt = decide_optimal_blocks([a0, a1], [b0, b1], game_state=state)
    assert opt == 1
    assert b0.blocking is None
    assert b1.blocking is a1


def test_seed39_first_strike_flying():
    """CR 702.7b & 702.9b: First strike and flying influence combat choices."""
    a0 = CombatCreature("A0", 3, 4, "A", first_strike=True)
    a1 = CombatCreature("A1", 2, 2, "A", flying=True)
    b0 = CombatCreature("B0", 5, 1, "B", lifelink=True)
    b1 = CombatCreature("B1", 3, 3, "B", trample=True)
    state = GameState(
        players={
            "A": PlayerState(life=20, creatures=[a0, a1]),
            "B": PlayerState(life=1, creatures=[b0, b1]),
        }
    )
    decide_simple_blocks([a0, a1], [b0, b1], game_state=state)
    assert b0.blocking is None
    assert b1.blocking is a0
    _reset(a0, a1, b0, b1)
    _, opt = decide_optimal_blocks([a0, a1], [b0, b1], game_state=state)
    assert opt == 1
    assert b0.blocking is None
    assert b1.blocking is None


def test_seed40_lifelink_trample():
    """CR 702.15a & 702.19b: Lifelink attackers blocked optimally."""
    a0 = CombatCreature("A0", 5, 5, "A", lifelink=True)
    a1 = CombatCreature("A1", 2, 3, "A", flying=True)
    b0 = CombatCreature("B0", 2, 2, "B", trample=True)
    b1 = CombatCreature("B1", 3, 3, "B")
    state = GameState(
        players={
            "A": PlayerState(life=20, creatures=[a0, a1]),
            "B": PlayerState(life=1, creatures=[b0, b1]),
        }
    )
    decide_simple_blocks([a0, a1], [b0, b1], game_state=state)
    assert b0.blocking is a0
    assert b1.blocking is None
    _reset(a0, a1, b0, b1)
    _, opt = decide_optimal_blocks([a0, a1], [b0, b1], game_state=state)
    assert opt == 1
    assert b0.blocking is a0
    assert b1.blocking is a0


def test_seed46_flying_deathtouch():
    """CR 702.9b & 702.2b: Deathtouch blockers prioritized differently."""
    a0 = CombatCreature("A0", 4, 1, "A", flying=True)
    a1 = CombatCreature("A1", 5, 2, "A", deathtouch=True)
    b0 = CombatCreature("B0", 5, 2, "B", trample=True)
    b1 = CombatCreature("B1", 5, 1, "B", deathtouch=True)
    state = GameState(
        players={
            "A": PlayerState(life=20, creatures=[a0, a1]),
            "B": PlayerState(life=3, creatures=[b0, b1]),
        }
    )
    decide_simple_blocks([a0, a1], [b0, b1], game_state=state)
    assert b0.blocking is a1
    assert b1.blocking is None
    _reset(a0, a1, b0, b1)
    _, opt = decide_optimal_blocks([a0, a1], [b0, b1], game_state=state)
    assert opt == 1
    assert b0.blocking is None
    assert b1.blocking is a1


def test_seed48_deathtouch_trample():
    """CR 702.2b & 702.19b: Deathtouch attackers versus trampling blocker."""
    a0 = CombatCreature("A0", 3, 2, "A", deathtouch=True)
    a1 = CombatCreature("A1", 5, 3, "A", deathtouch=True)
    b0 = CombatCreature("B0", 5, 2, "B")
    b1 = CombatCreature("B1", 4, 2, "B", trample=True)
    state = GameState(
        players={
            "A": PlayerState(life=20, creatures=[a0, a1]),
            "B": PlayerState(life=4, creatures=[b0, b1]),
        }
    )
    decide_simple_blocks([a0, a1], [b0, b1], game_state=state)
    assert b0.blocking is a1
    assert b1.blocking is None
    _reset(a0, a1, b0, b1)
    _, opt = decide_optimal_blocks([a0, a1], [b0, b1], game_state=state)
    assert opt == 1
    assert b0.blocking is None
    assert b1.blocking is a1


def test_seed109_double_strike_choice():
    """CR 702.4b: Double strike attackers can require multiple blockers."""
    a0 = CombatCreature("A0", 2, 4, "A", double_strike=True)
    a1 = CombatCreature("A1", 5, 1, "A", lifelink=True)
    b0 = CombatCreature("B0", 2, 5, "B", flying=True)
    b1 = CombatCreature("B1", 3, 5, "B", lifelink=True)
    state = GameState(
        players={
            "A": PlayerState(life=20, creatures=[a0, a1]),
            "B": PlayerState(life=3, creatures=[b0, b1]),
        }
    )
    decide_simple_blocks([a0, a1], [b0, b1], game_state=state)
    assert b0.blocking is a1
    assert b1.blocking is a0
    _reset(a0, a1, b0, b1)
    _, opt = decide_optimal_blocks([a0, a1], [b0, b1], game_state=state)
    assert opt == 1
    assert b0.blocking is a0
    assert b1.blocking is a0


def test_seed114_first_double_strike():
    """CR 702.7b & 702.4b: First strike and double strike together."""
    a0 = CombatCreature("A0", 5, 1, "A", first_strike=True)
    a1 = CombatCreature("A1", 2, 5, "A", double_strike=True)
    b0 = CombatCreature("B0", 2, 5, "B", flying=True)
    b1 = CombatCreature("B1", 5, 3, "B", deathtouch=True)
    state = GameState(
        players={
            "A": PlayerState(life=20, creatures=[a0, a1]),
            "B": PlayerState(life=3, creatures=[b0, b1]),
        }
    )
    decide_simple_blocks([a0, a1], [b0, b1], game_state=state)
    assert b0.blocking is a1
    assert b1.blocking is a0
    _reset(a0, a1, b0, b1)
    _, opt = decide_optimal_blocks([a0, a1], [b0, b1], game_state=state)
    assert opt == 1
    assert b0.blocking is a0
    assert b1.blocking is a1


def test_seed118_trample_double_block():
    """CR 702.19b: Trample favors blocking with multiple creatures."""
    a0 = CombatCreature("A0", 2, 3, "A", trample=True)
    a1 = CombatCreature("A1", 3, 3, "A", flying=True)
    b0 = CombatCreature("B0", 1, 3, "B")
    b1 = CombatCreature("B1", 1, 5, "B", double_strike=True)
    state = GameState(
        players={
            "A": PlayerState(life=20, creatures=[a0, a1]),
            "B": PlayerState(life=17, creatures=[b0, b1]),
        }
    )
    decide_simple_blocks([a0, a1], [b0, b1], game_state=state)
    assert b0.blocking is None
    assert b1.blocking is a0
    _reset(a0, a1, b0, b1)
    _, opt = decide_optimal_blocks([a0, a1], [b0, b1], game_state=state)
    assert opt == 1
    assert b0.blocking is a0
    assert b1.blocking is a0


def test_seed119_double_strike_vs_trample():
    """CR 702.4b & 702.19b: Balancing double strike and trample threats."""
    a0 = CombatCreature("A0", 2, 5, "A", double_strike=True)
    a1 = CombatCreature("A1", 5, 4, "A", trample=True)
    b0 = CombatCreature("B0", 1, 4, "B", flying=True)
    b1 = CombatCreature("B1", 2, 2, "B", trample=True)
    state = GameState(
        players={
            "A": PlayerState(life=20, creatures=[a0, a1]),
            "B": PlayerState(life=9, creatures=[b0, b1]),
        }
    )
    decide_simple_blocks([a0, a1], [b0, b1], game_state=state)
    assert b0.blocking is None
    assert b1.blocking is None
    _reset(a0, a1, b0, b1)
    _, opt = decide_optimal_blocks([a0, a1], [b0, b1], game_state=state)
    assert opt == 1
    assert b0.blocking is None
    assert b1.blocking is a0


def test_seed125_many_double_strikes():
    """CR 702.4b: Double strike matchups can be counterintuitive."""
    a0 = CombatCreature("A0", 2, 5, "A", first_strike=True)
    a1 = CombatCreature("A1", 5, 2, "A", double_strike=True)
    b0 = CombatCreature("B0", 2, 5, "B", double_strike=True)
    b1 = CombatCreature("B1", 5, 1, "B", double_strike=True)
    state = GameState(
        players={
            "A": PlayerState(life=20, creatures=[a0, a1]),
            "B": PlayerState(life=5, creatures=[b0, b1]),
        }
    )
    decide_simple_blocks([a0, a1], [b0, b1], game_state=state)
    assert b0.blocking is a1
    assert b1.blocking is a0
    _reset(a0, a1, b0, b1)
    _, opt = decide_optimal_blocks([a0, a1], [b0, b1], game_state=state)
    assert opt == 1
    assert b0.blocking is a0
    assert b1.blocking is a1


def test_seed126_deathtouch_priority():
    """CR 702.2b: Deathtouch attackers threaten trades."""
    a0 = CombatCreature("A0", 1, 5, "A", deathtouch=True)
    a1 = CombatCreature("A1", 4, 2, "A", deathtouch=True)
    b0 = CombatCreature("B0", 2, 4, "B", trample=True)
    b1 = CombatCreature("B1", 2, 2, "B", lifelink=True)
    state = GameState(
        players={
            "A": PlayerState(life=20, creatures=[a0, a1]),
            "B": PlayerState(life=16, creatures=[b0, b1]),
        }
    )
    decide_simple_blocks([a0, a1], [b0, b1], game_state=state)
    assert b0.blocking is a1
    assert b1.blocking is None
    _reset(a0, a1, b0, b1)
    _, opt = decide_optimal_blocks([a0, a1], [b0, b1], game_state=state)
    assert opt == 1
    assert b0.blocking is None
    assert b1.blocking is a1


def test_seed129_deathtouch_vs_double_strike():
    """CR 702.2b & 702.4b: Deathtouch trades versus double strike blocker."""
    a0 = CombatCreature("A0", 5, 3, "A", deathtouch=True)
    a1 = CombatCreature("A1", 4, 2, "A", flying=True)
    b0 = CombatCreature("B0", 2, 1, "B", double_strike=True)
    b1 = CombatCreature("B1", 5, 2, "B", trample=True)
    state = GameState(
        players={
            "A": PlayerState(life=20, creatures=[a0, a1]),
            "B": PlayerState(life=9, creatures=[b0, b1]),
        }
    )
    decide_simple_blocks([a0, a1], [b0, b1], game_state=state)
    assert b0.blocking is None
    assert b1.blocking is a0
    _reset(a0, a1, b0, b1)
    _, opt = decide_optimal_blocks([a0, a1], [b0, b1], game_state=state)
    assert opt == 1
    assert b0.blocking is a0
    assert b1.blocking is None


def test_seed132_lifelink_flyer_split():
    """CR 702.15a & 702.9b: Lifelink and flying require careful blocks."""
    a0 = CombatCreature("A0", 2, 4, "A", lifelink=True)
    a1 = CombatCreature("A1", 2, 1, "A", flying=True)
    b0 = CombatCreature("B0", 1, 5, "B", double_strike=True)
    b1 = CombatCreature("B1", 2, 4, "B", flying=True)
    state = GameState(
        players={
            "A": PlayerState(life=20, creatures=[a0, a1]),
            "B": PlayerState(life=7, creatures=[b0, b1]),
        }
    )
    decide_simple_blocks([a0, a1], [b0, b1], game_state=state)
    assert b0.blocking is a0
    assert b1.blocking is a1
    _reset(a0, a1, b0, b1)
    _, opt = decide_optimal_blocks([a0, a1], [b0, b1], game_state=state)
    assert opt == 1
    assert b0.blocking is a0
    assert b1.blocking is a0


def test_reach_blocks_flyer_double():
    """CR 702.9b: Reach allows creatures to block flying attackers."""
    flyer = CombatCreature("Flyer", 3, 3, "A", flying=True)
    big = CombatCreature("Big", 4, 4, "A")
    reach = CombatCreature("Reach", 2, 2, "B", reach=True)
    wall = CombatCreature("Wall", 3, 3, "B")
    state = GameState(
        players={
            "A": PlayerState(life=20, creatures=[flyer, big]),
            "B": PlayerState(life=20, creatures=[reach, wall]),
        }
    )
    decide_simple_blocks([flyer, big], [reach, wall], game_state=state)
    assert reach.blocking is None
    assert wall.blocking is None
    _reset(flyer, big, reach, wall)
    _, opt = decide_optimal_blocks([flyer, big], [reach, wall], game_state=state)
    assert opt == 1
    assert reach.blocking is big
    assert wall.blocking is big
