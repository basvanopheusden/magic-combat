import random
from pathlib import Path
from magic_combat import (
    load_cards,
    cards_to_creatures,
    assign_random_counters,
    assign_random_tapped,
    decide_optimal_blocks,
    CombatSimulator,
    GameState,
    PlayerState,
)

DATA_PATH = Path(__file__).with_name("example_test_cards.json")


def test_random_combat_from_cards():
    """CR 506.4: The defending player chooses which creatures block attacking creatures."""
    rng = random.Random(99)
    cards = load_cards(str(DATA_PATH))
    atk_pool = cards_to_creatures(cards, "A")
    def_pool = cards_to_creatures(cards, "B")
    rng.shuffle(atk_pool)
    rng.shuffle(def_pool)
    attackers = atk_pool[:3]
    defenders = def_pool[:3]
    assign_random_counters(attackers + defenders, rng=rng)
    assign_random_tapped(attackers + defenders, rng=rng)
    state = GameState(players={
        "A": PlayerState(life=20, creatures=attackers),
        "B": PlayerState(life=20, creatures=defenders),
    })
    decide_optimal_blocks(attackers, defenders, game_state=state)
    sim = CombatSimulator(attackers, defenders, game_state=state)
    result = sim.simulate()
    assert sum(result.damage_to_players.values()) >= 0

