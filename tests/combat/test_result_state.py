from copy import deepcopy

from magic_combat import CombatCreature
from magic_combat import CombatSimulator
from magic_combat import GameState
from magic_combat import PlayerState
from tests.conftest import link_block


def test_combat_result_matches_state_difference() -> None:
    """CR 120.3f: Damage dealt by a source with lifelink causes life gain."""

    atk1 = CombatCreature("Lifelink", 2, 2, "A", lifelink=True, mana_cost="{2}")
    atk2 = CombatCreature("Infector", 1, 1, "A", infect=True, mana_cost="{G}")
    blk = CombatCreature("Blocker", 2, 2, "B", mana_cost="{2}")
    link_block(atk1, blk)

    start = GameState(
        players={
            "A": PlayerState(life=10, creatures=[atk1, atk2]),
            "B": PlayerState(life=20, creatures=[blk]),
        }
    )
    state = deepcopy(start)
    sim = CombatSimulator([atk1, atk2], [blk], game_state=state)
    result = sim.simulate()

    def total_value(creatures):
        return sum(c.value() for c in creatures)

    def total_mana(creatures):
        return sum(c.mana_value for c in creatures)

    start_atk = start.players["A"].creatures
    start_blk = start.players["B"].creatures
    end_atk = [c for c in start_atk if c not in result.creatures_destroyed]
    end_blk = [c for c in start_blk if c not in result.creatures_destroyed]

    value_diff = (
        total_value(start_blk)
        - total_value(end_blk)
        - (total_value(start_atk) - total_value(end_atk))
    )
    count_diff = len(start_blk) - len(end_blk) - (len(start_atk) - len(end_atk))
    mana_diff = (
        total_mana(start_blk)
        - total_mana(end_blk)
        - (total_mana(start_atk) - total_mana(end_atk))
    )

    a_life = state.players["A"].life - start.players["A"].life
    b_life = state.players["B"].life - start.players["B"].life
    life_diff = a_life - b_life

    a_poison = state.players["A"].poison - start.players["A"].poison
    b_poison = state.players["B"].poison - start.players["B"].poison
    poison_diff = b_poison - a_poison

    score = result.score("A", "B")
    assert score[1] == value_diff
    assert score[2] == count_diff
    assert score[3] == mana_diff
    assert score[4] == life_diff
    assert score[5] == poison_diff
