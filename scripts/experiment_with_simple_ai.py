import argparse

from magic_combat import CombatCreature
from magic_combat import GameState
from magic_combat import PlayerState
from magic_combat import decide_optimal_blocks
from magic_combat.block_utils import evaluate_block_assignment
from magic_combat.block_utils import reset_block_assignments
from magic_combat.limits import IterationCounter
from magic_combat.text_utils import summarize_creature


def main() -> None:
    parser = argparse.ArgumentParser(description="Run simple blocking example")
    parser.add_argument(
        "--top-k",
        type=int,
        default=1,
        help="Number of top blocking assignments to compute",
    )
    args = parser.parse_args()

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
    assignments, _ = decide_optimal_blocks(
        game_state=game_state,
        provoke_map={},
        k=args.top_k,
    )
    print("Top assignments:", assignments)
    reset_block_assignments(game_state)
    block_map = {blk: blk.blocking for blk in blockers if blk.blocking is not None}
    iteration_counter = IterationCounter(max_iterations=1000)
    result, _ = evaluate_block_assignment(
        assignment=block_map,
        state=game_state,
        counter=iteration_counter,  # No iteration counter needed for this example
    )
    assert result is not None
    assignment_tuple = tuple(
        attackers.index(blk.blocking) if blk.blocking is not None else None
        for blk in blockers
    )
    score = result.score("A", "B") + (assignment_tuple,)
    for attacker in attackers:
        print("----")
        print("attacker:", summarize_creature(attacker))
        for creature in attacker.blocked_by:
            print("\tblocked by:", summarize_creature(creature))
    print(score)
    print(game_state)


if __name__ == "__main__":
    main()
