from magic_combat import CombatCreature
from magic_combat import GameState
from magic_combat import PlayerState
from magic_combat import decide_optimal_blocks
from magic_combat.block_utils import evaluate_block_assignment
from magic_combat.limits import IterationCounter
from magic_combat.text_utils import summarize_creature


def main():
    attackers = [
        CombatCreature(
            name="Attacker 1",
            power=2,
            toughness=2,
            controller="A",
            persist=True,
        ),
    ]
    blockers = [
        CombatCreature(
            name="Blocker 1",
            power=2,
            toughness=3,
            controller="B",
        ),
    ]
    game_state = GameState(
        players={
            "A": PlayerState(life=20, creatures=attackers, poison=0),
            "B": PlayerState(life=20, creatures=blockers, poison=0),
        }
    )
    print(game_state)
    decide_optimal_blocks(
        game_state=game_state,
        provoke_map={},
    )
    assignment = [attackers.index(b.blocking) if b.blocking else None for b in blockers]
    iteration_counter = IterationCounter(max_iterations=1000)
    result, _ = evaluate_block_assignment(
        assignment=assignment,
        state=game_state,
        counter=iteration_counter,  # No iteration counter needed for this example
    )
    assert result is not None
    score = result.score("A", "B") + (tuple(assignment),)
    for attacker in attackers:
        print("----")
        print("attacker:", summarize_creature(attacker))
        for creature in attacker.blocked_by:
            print("\tblocked by:", summarize_creature(creature))
    print(score)
    print(game_state)


if __name__ == "__main__":
    main()
