import copy

from magic_combat import CombatCreature
from magic_combat import GameState
from magic_combat import PlayerState
from magic_combat import decide_optimal_blocks
from magic_combat import decide_simple_blocks


def _assignments(state: GameState) -> list[str | None]:
    return [
        blk.blocking.name if blk.blocking else None
        for blk in state.players["B"].creatures
    ]


def test_ai_diff_scenario_1() -> None:
    """CR 509.1a: The defending player chooses how creatures block."""
    atk = [
        CombatCreature("A0", 3, 3, "A", infect=True),
        CombatCreature("A1", 4, 4, "A", infect=True),
        CombatCreature("A2", 5, 5, "A", trample=True),
        CombatCreature("A3", 6, 6, "A", trample=True),
    ]
    blk = [
        CombatCreature("B0", 2, 2, "B", trample=True),
        CombatCreature("B1", 3, 3, "B", trample=True),
        CombatCreature("B2", 4, 4, "B", trample=True),
        CombatCreature("B3", 5, 5, "B", menace=True),
    ]
    state = GameState(
        players={
            "A": PlayerState(life=20, creatures=atk),
            "B": PlayerState(life=2, poison=1, creatures=blk),
        }
    )
    s_simple = copy.deepcopy(state)
    decide_simple_blocks(game_state=s_simple)
    s_opt = copy.deepcopy(state)
    decide_optimal_blocks(game_state=s_opt)
    assert _assignments(s_simple) != _assignments(s_opt)


def test_ai_diff_scenario_2() -> None:
    """CR 509.1a: The defending player chooses how creatures block."""
    atk = [
        CombatCreature("A0", 3, 3, "A", infect=True),
        CombatCreature("A1", 4, 4, "A", trample=True),
        CombatCreature("A2", 5, 5, "A", trample=True),
        CombatCreature("A3", 6, 6, "A", infect=True),
    ]
    blk = [
        CombatCreature("B0", 2, 2, "B", trample=True),
        CombatCreature("B1", 3, 3, "B", wither=True),
        CombatCreature("B2", 4, 4, "B", menace=True),
        CombatCreature("B3", 5, 5, "B", menace=True),
    ]
    state = GameState(
        players={
            "A": PlayerState(life=20, creatures=atk),
            "B": PlayerState(life=2, poison=1, creatures=blk),
        }
    )
    s_simple = copy.deepcopy(state)
    decide_simple_blocks(game_state=s_simple)
    s_opt = copy.deepcopy(state)
    decide_optimal_blocks(game_state=s_opt)
    assert _assignments(s_simple) != _assignments(s_opt)


def test_ai_diff_scenario_3() -> None:
    """CR 509.1a: The defending player chooses how creatures block."""
    atk = [
        CombatCreature("A0", 3, 3, "A", wither=True),
        CombatCreature("A1", 4, 4, "A", menace=True),
        CombatCreature("A2", 5, 5, "A", infect=True),
        CombatCreature("A3", 6, 6, "A", trample=True),
    ]
    blk = [
        CombatCreature("B0", 2, 2, "B", infect=True),
        CombatCreature("B1", 3, 3, "B", menace=True),
        CombatCreature("B2", 4, 4, "B", wither=True),
        CombatCreature("B3", 5, 5, "B", trample=True),
    ]
    state = GameState(
        players={
            "A": PlayerState(life=20, creatures=atk),
            "B": PlayerState(life=2, poison=1, creatures=blk),
        }
    )
    s_simple = copy.deepcopy(state)
    decide_simple_blocks(game_state=s_simple)
    s_opt = copy.deepcopy(state)
    decide_optimal_blocks(game_state=s_opt)
    assert _assignments(s_simple) != _assignments(s_opt)


def test_ai_diff_scenario_4() -> None:
    """CR 509.1a: The defending player chooses how creatures block."""
    atk = [
        CombatCreature("A0", 3, 3, "A", trample=True),
        CombatCreature("A1", 4, 4, "A", trample=True),
        CombatCreature("A2", 5, 5, "A", infect=True),
        CombatCreature("A3", 6, 6, "A", trample=True),
    ]
    blk = [
        CombatCreature("B0", 2, 2, "B", trample=True),
        CombatCreature("B1", 3, 3, "B", menace=True),
        CombatCreature("B2", 4, 4, "B", menace=True),
        CombatCreature("B3", 5, 5, "B", menace=True),
    ]
    state = GameState(
        players={
            "A": PlayerState(life=20, creatures=atk),
            "B": PlayerState(life=2, poison=9, creatures=blk),
        }
    )
    s_simple = copy.deepcopy(state)
    decide_simple_blocks(game_state=s_simple)
    s_opt = copy.deepcopy(state)
    decide_optimal_blocks(game_state=s_opt)
    assert _assignments(s_simple) != _assignments(s_opt)


def test_ai_diff_scenario_5() -> None:
    """CR 509.1a: The defending player chooses how creatures block."""
    atk = [
        CombatCreature("A0", 3, 3, "A", infect=True),
        CombatCreature("A1", 4, 4, "A", wither=True),
        CombatCreature("A2", 5, 5, "A", infect=True),
        CombatCreature("A3", 6, 6, "A", trample=True),
    ]
    blk = [
        CombatCreature("B0", 2, 2, "B", wither=True),
        CombatCreature("B1", 3, 3, "B", infect=True),
        CombatCreature("B2", 4, 4, "B", menace=True),
        CombatCreature("B3", 5, 5, "B", trample=True),
    ]
    state = GameState(
        players={
            "A": PlayerState(life=20, creatures=atk),
            "B": PlayerState(life=2, poison=1, creatures=blk),
        }
    )
    s_simple = copy.deepcopy(state)
    decide_simple_blocks(game_state=s_simple)
    s_opt = copy.deepcopy(state)
    decide_optimal_blocks(game_state=s_opt)
    assert _assignments(s_simple) != _assignments(s_opt)


def test_ai_diff_scenario_6() -> None:
    """CR 509.1a: The defending player chooses how creatures block."""
    atk = [
        CombatCreature("A0", 3, 3, "A", trample=True),
        CombatCreature("A1", 4, 4, "A", infect=True),
        CombatCreature("A2", 5, 5, "A", trample=True),
        CombatCreature("A3", 6, 6, "A", trample=True),
    ]
    blk = [
        CombatCreature("B0", 2, 2, "B", wither=True),
        CombatCreature("B1", 3, 3, "B", infect=True),
        CombatCreature("B2", 4, 4, "B", trample=True),
        CombatCreature("B3", 5, 5, "B", wither=True),
    ]
    state = GameState(
        players={
            "A": PlayerState(life=20, creatures=atk),
            "B": PlayerState(life=2, poison=1, creatures=blk),
        }
    )
    s_simple = copy.deepcopy(state)
    decide_simple_blocks(game_state=s_simple)
    s_opt = copy.deepcopy(state)
    decide_optimal_blocks(game_state=s_opt)
    assert _assignments(s_simple) != _assignments(s_opt)


def test_ai_diff_scenario_7() -> None:
    """CR 509.1a: The defending player chooses how creatures block."""
    atk = [
        CombatCreature("A0", 3, 3, "A", infect=True),
        CombatCreature("A1", 4, 4, "A", trample=True),
        CombatCreature("A2", 5, 5, "A", wither=True),
        CombatCreature("A3", 6, 6, "A", infect=True),
    ]
    blk = [
        CombatCreature("B0", 2, 2, "B", wither=True),
        CombatCreature("B1", 3, 3, "B", infect=True),
        CombatCreature("B2", 4, 4, "B", trample=True),
        CombatCreature("B3", 5, 5, "B", wither=True),
    ]
    state = GameState(
        players={
            "A": PlayerState(life=20, creatures=atk),
            "B": PlayerState(life=2, poison=1, creatures=blk),
        }
    )
    s_simple = copy.deepcopy(state)
    decide_simple_blocks(game_state=s_simple)
    s_opt = copy.deepcopy(state)
    decide_optimal_blocks(game_state=s_opt)
    assert _assignments(s_simple) != _assignments(s_opt)


def test_ai_diff_scenario_8() -> None:
    """CR 509.1a: The defending player chooses how creatures block."""
    atk = [
        CombatCreature("A0", 3, 3, "A", infect=True),
        CombatCreature("A1", 4, 4, "A", infect=True),
        CombatCreature("A2", 5, 5, "A", trample=True),
        CombatCreature("A3", 6, 6, "A", infect=True),
    ]
    blk = [
        CombatCreature("B0", 2, 2, "B", wither=True),
        CombatCreature("B1", 3, 3, "B", trample=True),
        CombatCreature("B2", 4, 4, "B", wither=True),
        CombatCreature("B3", 5, 5, "B", menace=True),
    ]
    state = GameState(
        players={
            "A": PlayerState(life=20, creatures=atk),
            "B": PlayerState(life=2, poison=9, creatures=blk),
        }
    )
    s_simple = copy.deepcopy(state)
    decide_simple_blocks(game_state=s_simple)
    s_opt = copy.deepcopy(state)
    decide_optimal_blocks(game_state=s_opt)
    assert _assignments(s_simple) != _assignments(s_opt)


def test_ai_diff_scenario_9() -> None:
    """CR 509.1a: The defending player chooses how creatures block."""
    atk = [
        CombatCreature("A0", 3, 3, "A", wither=True),
        CombatCreature("A1", 4, 4, "A", wither=True),
        CombatCreature("A2", 5, 5, "A", trample=True),
        CombatCreature("A3", 6, 6, "A", trample=True),
    ]
    blk = [
        CombatCreature("B0", 2, 2, "B", wither=True),
        CombatCreature("B1", 3, 3, "B", infect=True),
        CombatCreature("B2", 4, 4, "B", trample=True),
        CombatCreature("B3", 5, 5, "B", infect=True),
    ]
    state = GameState(
        players={
            "A": PlayerState(life=20, creatures=atk),
            "B": PlayerState(life=2, poison=1, creatures=blk),
        }
    )
    s_simple = copy.deepcopy(state)
    decide_simple_blocks(game_state=s_simple)
    s_opt = copy.deepcopy(state)
    decide_optimal_blocks(game_state=s_opt)
    assert _assignments(s_simple) != _assignments(s_opt)


def test_ai_diff_scenario_10() -> None:
    """CR 509.1a: The defending player chooses how creatures block."""
    atk = [
        CombatCreature("A0", 3, 3, "A", infect=True),
        CombatCreature("A1", 4, 4, "A", trample=True),
        CombatCreature("A2", 5, 5, "A", wither=True),
        CombatCreature("A3", 6, 6, "A", infect=True),
    ]
    blk = [
        CombatCreature("B0", 2, 2, "B", infect=True),
        CombatCreature("B1", 3, 3, "B", wither=True),
        CombatCreature("B2", 4, 4, "B", trample=True),
        CombatCreature("B3", 5, 5, "B", menace=True),
    ]
    state = GameState(
        players={
            "A": PlayerState(life=20, creatures=atk),
            "B": PlayerState(life=2, poison=1, creatures=blk),
        }
    )
    s_simple = copy.deepcopy(state)
    decide_simple_blocks(game_state=s_simple)
    s_opt = copy.deepcopy(state)
    decide_optimal_blocks(game_state=s_opt)
    assert _assignments(s_simple) != _assignments(s_opt)


# Lifelink scenario ensuring defensive lifelink is covered


def test_ai_diff_scenario_lifelink() -> None:
    """CR 509.1a: The defending player chooses how creatures block."""
    atk = [
        CombatCreature("A0", 3, 3, "A", infect=True),
        CombatCreature("A1", 4, 4, "A", wither=True),
        CombatCreature("A2", 5, 5, "A", menace=True),
    ]
    blk = [
        CombatCreature("B0", 2, 2, "B", trample=True, lifelink=True),
        CombatCreature("B1", 3, 3, "B", infect=True),
        CombatCreature("B2", 4, 4, "B", wither=True),
    ]
    state = GameState(
        players={
            "A": PlayerState(life=20, creatures=atk),
            "B": PlayerState(life=1, creatures=blk),
        }
    )
    s_simple = copy.deepcopy(state)
    decide_simple_blocks(game_state=s_simple)
    s_opt = copy.deepcopy(state)
    decide_optimal_blocks(game_state=s_opt)
    assert _assignments(s_simple) != _assignments(s_opt)


def test_ai_diff_keywords() -> None:
    """CR 509.1a: The defending player chooses how creatures block."""
    atk = [
        CombatCreature(
            "A0",
            3,
            3,
            "A",
            infect=True,
            deathtouch=True,
            indestructible=True,
            melee=True,
        ),
        CombatCreature(
            "A1", 4, 4, "A", wither=True, training=True, mentor=True, battalion=True
        ),
        CombatCreature(
            "A2", 5, 5, "A", infect=True, exalted_count=1, battle_cry_count=1, frenzy=1
        ),
        CombatCreature("A3", 6, 6, "A", trample=True, toxic=1, afflict=1, rampage=1),
    ]
    blk = [
        CombatCreature("B0", 2, 2, "B", wither=True, persist=True),
        CombatCreature("B1", 3, 3, "B", infect=True, provoke=True),
        CombatCreature("B2", 4, 4, "B", menace=True, intimidate=True, defender=True),
        CombatCreature("B3", 5, 5, "B", trample=True, dethrone=True, undying=True),
    ]
    state = GameState(
        players={
            "A": PlayerState(life=20, creatures=atk),
            "B": PlayerState(life=2, poison=1, creatures=blk),
        }
    )
    s_simple = copy.deepcopy(state)
    decide_simple_blocks(game_state=s_simple)
    s_opt = copy.deepcopy(state)
    decide_optimal_blocks(game_state=s_opt)
    assert _assignments(s_simple) != _assignments(s_opt)
