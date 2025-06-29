from magic_combat import CombatCreature
from magic_combat import GameState
from magic_combat import PlayerState
from magic_combat import decide_simple_blocks
from scripts.random_combat import summarize_creature


def main():
    attackers = [
        CombatCreature(
            name="Attacker 1",
            power=2,
            toughness=2,
            controller="Player A",
            double_strike=True,
        ),
        CombatCreature(
            name="Attacker 2",
            power=3,
            toughness=3,
            controller="Player A",
            flying=True,
        ),
        CombatCreature(
            name="Attacker 3",
            power=1,
            toughness=1,
            controller="Player A",
            trample=True,
        ),
    ]
    blockers = [
        CombatCreature(
            name="Blocker 1",
            power=2,
            toughness=3,
            controller="Player B",
        ),
        CombatCreature(
            name="Blocker 2",
            power=3,
            toughness=3,
            controller="Player B",
        ),
    ]
    game_state = GameState(
        players={
            "Player A": PlayerState(life=20, creatures=attackers, poison=0),
            "Player B": PlayerState(life=20, creatures=blockers, poison=0),
        }
    )
    print(game_state)
    decide_simple_blocks(
        attackers=attackers,
        blockers=blockers,
        game_state=game_state,
        provoke_map={},
    )
    for attacker in attackers:
        print("----")
        print("attacker:", summarize_creature(attacker))
        for creature in attacker.blocked_by:
            print("\tblocked by:", summarize_creature(creature))


if __name__ == "__main__":
    main()
