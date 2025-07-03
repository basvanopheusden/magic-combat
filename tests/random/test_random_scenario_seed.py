from pathlib import Path

from magic_combat import load_cards
from magic_combat.random_scenario import build_value_map
from magic_combat.random_scenario import generate_random_scenario

# Path to the sample card data used for random scenario generation
DATA_PATH = Path(__file__).resolve().parents[1] / "data" / "example_test_cards.json"


def test_generate_random_scenario_seed():
    cards = load_cards(str(DATA_PATH))
    values = build_value_map(cards)
    res1 = next(generate_random_scenario(cards, values, seed=123))
    res2 = next(generate_random_scenario(cards, values, seed=123))

    assert res1[0].players["A"].life == res2[0].players["A"].life
    assert res1[0].players["B"].life == res2[0].players["B"].life
    assert res1[3] == res2[3]
    assert res1[4] == res2[4]
