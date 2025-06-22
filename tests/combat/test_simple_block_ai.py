from magic_combat import (
    CombatCreature,
    CombatSimulator,
    GameState,
    PlayerState,
    decide_simple_blocks,
)


def test_simple_ai_respects_provoke():
    """CR 702.40a: Provoke requires the chosen creature to block if able."""
    atk = CombatCreature("Taunter", 2, 2, "A", provoke=True)
    blk = CombatCreature("Guard", 2, 2, "B")
    state = GameState(
        players={
            "A": PlayerState(life=20, creatures=[atk]),
            "B": PlayerState(life=20, creatures=[blk]),
        }
    )
    decide_simple_blocks([atk], [blk], game_state=state, provoke_map={atk: blk})
    sim = CombatSimulator([atk], [blk], game_state=state, provoke_map={atk: blk})
    sim.validate_blocking()
    assert blk.blocking is atk
    assert atk.blocked_by == [blk]
