from pathlib import Path

from magic_combat import load_cards
from magic_combat.random_scenario import build_value_map
from magic_combat.random_scenario import generate_random_scenario

# Path to the sample card data used for random scenario generation
DATA_PATH = Path(__file__).resolve().parents[1] / "data" / "example_test_cards.json"


def test_generate_random_scenario_seed():
    cards = load_cards(str(DATA_PATH))
    values = build_value_map(cards)
    res1 = generate_random_scenario(cards, values, seed=123)
    res2 = generate_random_scenario(cards, values, seed=123)

    atk1 = [c.name for c in res1[1]]
    atk2 = [c.name for c in res2[1]]
    blk1 = [c.name for c in res1[2]]
    blk2 = [c.name for c in res2[2]]

    assert atk1 == atk2
    assert blk1 == blk2
    assert res1[0].players["A"].life == res2[0].players["A"].life
    assert res1[0].players["B"].life == res2[0].players["B"].life
    assert res1[5] == res2[5]
    assert res1[7] == res2[7]
