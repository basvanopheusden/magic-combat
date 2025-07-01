import random
from itertools import product

import pytest

from magic_combat import CombatCreature
from magic_combat import CombatSimulator
from magic_combat import GameState
from magic_combat import PlayerState
from magic_combat import decide_optimal_blocks
from magic_combat.block_utils import evaluate_block_assignment
from magic_combat.limits import IterationCounter
from magic_combat.utils import can_block
from tests.conftest import link_block


def test_optimal_damage_prefers_high_value_blocker():
    """CR 510.1a: The attacking player chooses damage assignment order."""
    atk = CombatCreature("Crusher", 4, 4, "A", trample=True)
    small = CombatCreature("Squire", 2, 2, "B")
    big = CombatCreature("Knight", 3, 3, "B")
    link_block(atk, small, big)
    sim = CombatSimulator([atk], [small, big])
    result = sim.simulate()
    dead = {c.name for c in result.creatures_destroyed}
    assert dead == {"Knight", "Crusher"}
    assert small not in result.creatures_destroyed
    assert result.damage_to_players.get("B", 0) == 0


def test_ai_uses_deathtouch_on_biggest_attacker():
    """CR 702.2b: Any nonzero damage from a creature with deathtouch is lethal."""
    giant = CombatCreature("Giant", 6, 6, "A")
    goblin = CombatCreature("Goblin", 2, 2, "A")
    snake = CombatCreature("Snake", 2, 2, "B", deathtouch=True)
    knight = CombatCreature("Knight", 4, 4, "B")
    state = GameState(
        players={
            "A": PlayerState(life=20, creatures=[giant, goblin]),
            "B": PlayerState(life=20, creatures=[snake, knight]),
        }
    )
    decide_optimal_blocks(game_state=state)
    assert snake.blocking is giant
    assert knight.blocking is goblin
    sim = CombatSimulator([giant, goblin], [snake, knight], game_state=state)
    result = sim.simulate()
    dead = {c.name for c in result.creatures_destroyed}
    assert dead == {"Giant", "Snake", "Goblin"}


def _compute_best_assignment(atk, blk, state):
    counter = IterationCounter(1000)
    options = []
    for b in blk:
        opts = [None] + [i for i, a in enumerate(atk) if can_block(a, b)]
        options.append(opts)
    best = None
    best_score = None
    for ass in product(*options):
        block_map = {
            blk[i]: atk[choice] for i, choice in enumerate(ass) if choice is not None
        }
        result, _ = evaluate_block_assignment(block_map, state, counter)
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
def test_fuzz_blocking_optimal(seed):
    """CR 509.1a: The defending player chooses how creatures block."""
    rng = random.Random(seed)
    attackers = [
        CombatCreature(f"A{i}", rng.randint(1, 5), rng.randint(1, 5), "A")
        for i in range(2)
    ]
    blockers = [
        CombatCreature(f"B{i}", rng.randint(1, 5), rng.randint(1, 5), "B")
        for i in range(2)
    ]
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
