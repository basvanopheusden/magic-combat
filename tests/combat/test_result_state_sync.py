"""Additional tests for state and result consistency."""

from copy import deepcopy

from magic_combat import CombatCreature
from magic_combat import CombatSimulator
from magic_combat import GameState
from magic_combat import PlayerState
from magic_combat.block_utils import evaluate_block_assignment
from magic_combat.gamestate import has_player_lost
from magic_combat.limits import IterationCounter


def _total_value(creatures: list[CombatCreature]) -> float:
    return sum(c.value() for c in creatures)


def _total_mana(creatures: list[CombatCreature]) -> int:
    return sum(c.mana_value for c in creatures)


def test_result_matches_state_diff():
    """CR 119.3: Life totals adjust when players gain or lose life."""

    atk_lifelink = CombatCreature(
        "Toxic Cleric",
        2,
        2,
        "A",
        infect=True,
        lifelink=True,
        mana_cost="{2}",
    )
    atk_warrior = CombatCreature("Warrior", 3, 3, "A", mana_cost="{3}")
    blk = CombatCreature("Guard", 2, 2, "B", mana_cost="{2}")

    state = GameState(
        players={
            "A": PlayerState(life=20, creatures=[atk_lifelink, atk_warrior]),
            "B": PlayerState(life=20, creatures=[blk]),
        }
    )

    start = deepcopy(state)

    score, new_state = evaluate_block_assignment(
        [atk_lifelink, atk_warrior], [blk], [1], state, IterationCounter(10)
    )
    assert new_state is not None

    atk_c = deepcopy([atk_lifelink, atk_warrior])
    blk_c = deepcopy([blk])
    blk_c[0].blocking = atk_c[1]
    atk_c[1].blocked_by.append(blk_c[0])
    sim = CombatSimulator(atk_c, blk_c, game_state=deepcopy(state))
    result = sim.simulate()

    attacker = "A"
    defender = "B"

    assert score[:-1] == result.score(attacker, defender)

    val_a_start = _total_value(start.players[attacker].creatures)
    val_b_start = _total_value(start.players[defender].creatures)
    val_a_end = _total_value(new_state.players[attacker].creatures)
    val_b_end = _total_value(new_state.players[defender].creatures)

    value_diff = (val_b_start - val_b_end) - (val_a_start - val_a_end)

    cnt_a_start = len(start.players[attacker].creatures)
    cnt_b_start = len(start.players[defender].creatures)
    cnt_a_end = len(new_state.players[attacker].creatures)
    cnt_b_end = len(new_state.players[defender].creatures)

    count_diff = (cnt_b_start - cnt_b_end) - (cnt_a_start - cnt_a_end)

    mana_a_start = _total_mana(start.players[attacker].creatures)
    mana_b_start = _total_mana(start.players[defender].creatures)
    mana_a_end = _total_mana(new_state.players[attacker].creatures)
    mana_b_end = _total_mana(new_state.players[defender].creatures)

    mana_diff = (mana_b_start - mana_b_end) - (mana_a_start - mana_a_end)

    life_a_change = new_state.players[attacker].life - start.players[attacker].life
    life_b_change = new_state.players[defender].life - start.players[defender].life
    life_component = -(life_b_change - life_a_change)

    poison_a_change = (
        new_state.players[attacker].poison - start.players[attacker].poison
    )
    poison_b_change = (
        new_state.players[defender].poison - start.players[defender].poison
    )
    poison_diff = poison_b_change - poison_a_change

    expected_numeric = (
        1 if has_player_lost(new_state, defender) else 0,
        value_diff,
        count_diff,
        mana_diff,
        life_component,
        poison_diff,
    )

    assert score[:-1] == expected_numeric
    assert result.lifegain.get(attacker, 0) == life_a_change
    assert result.poison_counters.get(defender, 0) == poison_b_change
