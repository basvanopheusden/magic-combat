import copy

from magic_combat import CombatCreature
from magic_combat import CombatSimulator
from magic_combat import GameState
from magic_combat import PlayerState
from magic_combat.block_utils import evaluate_block_assignment
from magic_combat.limits import IterationCounter
from tests.conftest import link_block


def _score_from_states(
    start: GameState, end: GameState | None, attacker: str, defender: str
) -> tuple[int, float, int, int, int, int]:
    assert end is not None
    lost = 1 if end.has_player_lost(defender) else 0
    start_att = start.players[attacker].creatures
    start_def = start.players[defender].creatures
    end_att_names = {c.name for c in end.players[attacker].creatures}
    end_def_names = {c.name for c in end.players[defender].creatures}
    att_lost = [c for c in start_att if c.name not in end_att_names]
    def_lost = [c for c in start_def if c.name not in end_def_names]
    end_map = {
        c.name: c
        for c in end.players[attacker].creatures + end.players[defender].creatures
    }
    att_delta = sum(
        end_map[c.name].value() - c.value()
        for c in start_att
        if c.name in end_att_names
    )
    def_delta = sum(
        end_map[c.name].value() - c.value()
        for c in start_def
        if c.name in end_def_names
    )
    val_diff = (sum(c.value() for c in def_lost) - sum(c.value() for c in att_lost)) + (
        att_delta - def_delta
    )
    cnt_diff = len(def_lost) - len(att_lost)
    mana_diff = sum(c.mana_value for c in def_lost) - sum(
        c.mana_value for c in att_lost
    )
    life_diff = (start.players[defender].life - end.players[defender].life) - (
        start.players[attacker].life - end.players[attacker].life
    )
    poison_diff = (end.players[defender].poison - start.players[defender].poison) - (
        end.players[attacker].poison - start.players[attacker].poison
    )
    return lost, val_diff, cnt_diff, mana_diff, life_diff, poison_diff


def test_persist_undying_state_value():
    """CR 702.77a & 702.92a: Persist and undying return creatures
    that died without counters."""
    atk = CombatCreature("Phoenix", 2, 2, "A", undying=True, mana_cost="{2}{R}")
    blk = CombatCreature("Spirit", 2, 2, "B", persist=True, mana_cost="{2}{W}")
    link_block(atk, blk)
    start = GameState(
        players={
            "A": PlayerState(life=20, creatures=[atk]),
            "B": PlayerState(life=20, creatures=[blk]),
        }
    )
    state_for_sim = copy.deepcopy(start)
    sim = CombatSimulator(
        [state_for_sim.players["A"].creatures[0]],
        [state_for_sim.players["B"].creatures[0]],
        game_state=state_for_sim,
    )
    sim_result = sim.simulate()
    expected = _score_from_states(start, state_for_sim, "A", "B")
    assert sim_result.score("A", "B") == expected
    # Reset blocking on the original objects before evaluation
    atk.blocked_by.clear()
    blk.blocking = None
    eval_result, end_state = evaluate_block_assignment(
        {blk: atk}, start, IterationCounter(10)
    )
    assert eval_result is not None
    assert _score_from_states(start, end_state, "A", "B") == expected
    score = eval_result.score("A", "B") + ((0,),)
    assert score == expected + ((0,),)
    assert end_state is not None
    p_creature = end_state.players["A"].creatures[0]
    s_creature = end_state.players["B"].creatures[0]
    assert p_creature.name == "Phoenix"
    assert p_creature.plus1_counters == 1
    assert s_creature.name == "Spirit"
    assert s_creature.minus1_counters == 1


def test_lifelink_infect_state_changes():
    """CR 702.90b & 702.15a: Infect deals poison counters and
    lifelink gains that much life."""
    atk = CombatCreature("Infecter", 2, 2, "A", infect=True, lifelink=True)
    defender = CombatCreature("Dummy", 0, 1, "B")
    start = GameState(
        players={
            "A": PlayerState(life=10, creatures=[atk]),
            "B": PlayerState(life=10, creatures=[defender], poison=8),
        }
    )
    state_for_sim = copy.deepcopy(start)
    sim = CombatSimulator(
        [state_for_sim.players["A"].creatures[0]],
        [state_for_sim.players["B"].creatures[0]],
        game_state=state_for_sim,
    )
    sim_result = sim.simulate()
    expected = _score_from_states(start, state_for_sim, "A", "B")
    assert sim_result.score("A", "B") == expected
    eval_result, end_state = evaluate_block_assignment({}, start, IterationCounter(10))
    assert eval_result is not None
    assert _score_from_states(start, end_state, "A", "B") == expected
    score = eval_result.score("A", "B") + ((1,),)
    assert score == expected + ((1,),)
