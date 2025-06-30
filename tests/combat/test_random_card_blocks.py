import random
from itertools import product
from pathlib import Path

import pytest

from magic_combat import GameState
from magic_combat import PlayerState
from magic_combat import card_to_creature
from magic_combat import decide_optimal_blocks
from magic_combat import load_cards
from magic_combat.block_utils import evaluate_block_assignment
from magic_combat.blocking_ai import can_block
from magic_combat.limits import IterationCounter

# Card data used when generating random blocking scenarios
DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "example_test_cards.json"


def _compute_best_assignment(atk, blk, state):
    counter = IterationCounter(1000)
    options = []
    for b in blk:
        opts = [None] + [i for i, a in enumerate(atk) if can_block(a, b)]
        options.append(opts)
    best = None
    best_score = None
    for ass in product(*options):
        result, _ = evaluate_block_assignment(ass, state, counter)
        if result is None:
            continue
        score = result.score("A", "B") + (
            tuple(len(atk) if choice is None else choice for choice in ass),
        )
        if best_score is None or score < best_score:
            best_score = score
            best = ass
    return best


@pytest.mark.parametrize("seed", [0, 1, 2, 3, 4])
def test_random_card_blocks_optimal(seed):
    """CR 509.1a: The defending player chooses how creatures block."""
    rng = random.Random(seed)
    cards = load_cards(str(DATA_PATH))
    atk_pool = [c for c in cards if "Defender" not in c.get("keywords", [])]
    atk_cards = rng.sample(atk_pool, 2)
    blk_cards = rng.sample(cards, 2)
    attackers = [card_to_creature(c, "A") for c in atk_cards]
    blockers = [card_to_creature(c, "B") for c in blk_cards]
    state = GameState(
        players={
            "A": PlayerState(life=20, creatures=list(attackers)),
            "B": PlayerState(life=20, creatures=list(blockers)),
        }
    )
    expected = _compute_best_assignment(attackers, blockers, state)
    decide_optimal_blocks(game_state=state)
    chosen = tuple(
        attackers.index(b.blocking) if b.blocking is not None else None
        for b in blockers
    )
    assert chosen == expected
