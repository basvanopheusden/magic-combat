# pylint: disable=missing-function-docstring, missing-module-docstring
from pathlib import Path

from magic_combat import CombatCreature
from magic_combat import compute_card_statistics
from magic_combat import generate_random_creature
from magic_combat import load_cards

# Sample creature card data for random creature generation
DATA_PATH = Path(__file__).resolve().parents[1] / "data" / "example_test_cards.json"


def test_compute_statistics_means():
    cards = load_cards(str(DATA_PATH))
    stats = compute_card_statistics(cards)
    assert abs(stats["power_mean"] - 2.2) < 0.01
    assert abs(stats["toughness_mean"] - 2.0) < 0.01


def test_generate_random_creature_basic():
    cards = load_cards(str(DATA_PATH))
    stats = compute_card_statistics(cards)
    creature = generate_random_creature(stats, controller="A")
    assert isinstance(creature, CombatCreature)
    assert isinstance(creature.power, int)
    assert isinstance(creature.toughness, int)
    assert creature.name
