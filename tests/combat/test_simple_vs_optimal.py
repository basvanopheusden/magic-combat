import copy

from magic_combat import Color
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
        CombatCreature("A0", 3, 3, "A", infect=True, first_strike=True),
        CombatCreature("A1", 4, 4, "A", trample=True, double_strike=True),
        CombatCreature("A2", 5, 5, "A", trample=True, deathtouch=True),
        CombatCreature("A3", 6, 6, "A", infect=True, flying=True),
    ]
    blk = [
        CombatCreature("B0", 2, 2, "B", trample=True, reach=True),
        CombatCreature("B1", 3, 3, "B", wither=True, skulk=True),
        CombatCreature("B2", 4, 4, "B", menace=True, daunt=True, vigilance=True),
        CombatCreature(
            "B3", 5, 5, "B", menace=True, intimidate=True, protection_colors={Color.RED}
        ),
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

    atk = [
        CombatCreature("A0", 3, 3, "A", bushido=1),
        CombatCreature("A1", 4, 4, "A", flanking=1),
        CombatCreature("A2", 5, 5, "A", rampage=1),
        CombatCreature("A3", 2, 2, "A", exalted_count=1),
    ]
    blk = [
        CombatCreature("B0", 2, 2, "B", battle_cry_count=1),
        CombatCreature("B1", 3, 3, "B", melee=True),
        CombatCreature("B2", 4, 4, "B", training=True),
        CombatCreature("B3", 5, 5, "B", mentor=True),
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


def test_ai_diff_keywords_extra_4() -> None:
    """CR 509.1a: The defending player chooses how creatures block."""
    atk = [
        CombatCreature("A0", 2, 2, "A", frenzy=1),
        CombatCreature("A1", 3, 3, "A", battalion=True),
        CombatCreature("A2", 4, 4, "A", dethrone=True),
        CombatCreature("A3", 5, 5, "A", undying=True),
    ]
    blk = [
        CombatCreature("B0", 2, 2, "B", persist=True),
        CombatCreature("B1", 3, 3, "B", indestructible=True),
        CombatCreature("B2", 4, 4, "B", toxic=1),
        CombatCreature("B3", 5, 5, "B", provoke=True),
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


def test_ai_diff_keywords_extra_5() -> None:
    """CR 509.1a: The defending player chooses how creatures block."""
    atk = [
        CombatCreature("A0", 3, 3, "A"),
        CombatCreature("A1", 4, 4, "A", afflict=1),
        CombatCreature("A2", 5, 5, "A", provoke=True),
        CombatCreature("A3", 6, 6, "A", infect=True),
    ]
    blk = [
        CombatCreature("B0", 2, 2, "B", lifelink=True),
        CombatCreature("B1", 3, 3, "B", first_strike=True),
        CombatCreature("B2", 4, 4, "B", menace=True),
        CombatCreature("B3", 5, 5, "B", wither=True, defender=True),
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
