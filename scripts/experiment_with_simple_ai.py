from magic_combat import CombatCreature, decide_simple_blocks, GameState, PlayerState


def main():
    atk1 = CombatCreature(
        name="Attacker 1",
        power=2,
        toughness=2,
        controller="Player A",
        double_strike=True,
    )
    blk1 = CombatCreature(
        name="Blocker 1",
        power=2,
        toughness=3,
        controller="Player B",
    )
    blk2 = CombatCreature(
        name="Blocker 2",
        power=3,
        toughness=3,
        controller="Player B",
    )
    game_state = GameState(
        players={
            "Player A": PlayerState(
                life=20, creatures=[atk1], poison=0
            ),
            "Player B": PlayerState(
                life=, creatures=[blk1], poison=0
            ),
        }
    )
    decide_simple_blocks(
        attackers=[atk1],
        blockers=[blk1],
        game_state=game_state,
        provoke_map={},
    )
    print(atk1.blocked_by)

if __name__ == "__main__":
    main()
