import random

import numpy as np

from magic_combat import CombatCreature
from magic_combat import CombatSimulator
from magic_combat import GameState
from magic_combat import PlayerState
from magic_combat import build_value_map
from magic_combat import compute_card_statistics
from magic_combat import decide_optimal_blocks
from magic_combat import decide_simple_blocks
from magic_combat import generate_random_scenario
from magic_combat import load_cards
from magic_combat.block_utils import reset_block_assignments


def main() -> None:
    attackers = [
        CombatCreature("Elemental Beast", 3, 3, "A", trample=True),
        CombatCreature("Toxic Lizard", 2, 1, "A", toxic=2),
    ]
    blockers = [
        CombatCreature(
            "Ferocious Charger", 3, 3, "B", trample=True, melee=True, horsemanship=True
        )
    ]
    state = GameState(
        players={
            "A": PlayerState(life=11, poison=9, creatures=attackers),
            "B": PlayerState(life=17, poison=9, creatures=blockers),
        }
    )
    print(state)
    assignments, _ = decide_optimal_blocks(
        game_state=state,
        provoke_map={},
        k=5,
    )
    for score, assignment in assignments:
        print("----")
        for blk_idx, choice in enumerate(assignment):
            if choice is not None:
                attacker = blockers[blk_idx]
                blocker = attackers[choice]
                print(
                    f"{attacker.name} ({attacker.power}/{attacker.toughness}) "
                    f"blocks {blocker.name} ({blocker.power}/{blocker.toughness})"
                )
            else:
                print(f"{blockers[blk_idx].name} does not block")
        print(score)

    reset_block_assignments(game_state=state)
    decide_simple_blocks(
        game_state=state,
        provoke_map={},
    )
    for blk in blockers:
        if blk.blocking:
            print(
                f"{blk.name} ({blk.power}/{blk.toughness}) "
                f"blocks {blk.blocking.name} "
                f"({blk.blocking.power}/{blk.blocking.toughness})"
            )
        else:
            print(f"{blk.name} does not block")
    result = CombatSimulator(attackers, blockers, game_state=state).simulate()
    print(result)


def generate_scenario():
    seed = 0
    idx = 3
    random.seed(seed)
    np.random.seed(seed)

    cards_path = "tests/data/example_test_cards.json"
    cards = load_cards(cards_path)
    stats = compute_card_statistics(cards)
    values = build_value_map(cards)

    (
        state,
        provoke_map,
        mentor_map,
        opt_map,
        simple_map,
        opt_value,
    ) = generate_random_scenario(
        cards,
        values,
        stats,
        generated_cards=False,
        seed=seed + idx,
        unique_optimal=True,
    )
    print(f"Scenario {idx}:")
    print(state)
    print("Optimal blocks:")
    attackers = state.players["A"].creatures
    blockers = state.players["B"].creatures
    for blk_idx, choice in enumerate(opt_map):
        if choice is not None:
            attacker = blockers[blk_idx]
            blocker = attackers[choice]
            print(
                f"{attacker.name} ({attacker.power}/{attacker.toughness}) "
                f"blocks {blocker.name} ({blocker.power}/{blocker.toughness})"
            )
        else:
            print(f"{blockers[blk_idx].name} does not block")
    print("Simple blocks:")
    for blk_idx, choice in enumerate(simple_map):
        if choice is not None:
            attacker = blockers[blk_idx]
            blocker = attackers[choice]
            print(
                f"{attacker.name} ({attacker.power}/{attacker.toughness}) "
                f"blocks {blocker.name} ({blocker.power}/{blocker.toughness})"
            )
        else:
            print(f"{blockers[blk_idx].name} does not block")
    print(opt_value)
    reset_block_assignments(game_state=state)
    decide_simple_blocks(
        game_state=state,
        provoke_map=provoke_map,
    )
    for blk in blockers:
        if blk.blocking:
            print(
                f"{blk.name} ({blk.power}/{blk.toughness}) "
                f"blocks {blk.blocking.name} "
                f"({blk.blocking.power}/{blk.blocking.toughness})"
            )
        else:
            print(f"{blk.name} does not block")


if __name__ == "__main__":
    generate_scenario()
