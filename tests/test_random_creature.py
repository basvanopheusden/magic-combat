from pathlib import Path
from magic_combat import (
    load_cards,
    compute_card_statistics,
    generate_random_creature,
    CombatCreature,
)

DATA_PATH = Path(__file__).with_name("example_test_cards.json")


def test_compute_statistics_means():
    """CR 109.3: Power and toughness are characteristics of creatures."""
    cards = load_cards(str(DATA_PATH))
    stats = compute_card_statistics(cards)
    assert abs(stats["power_mean"] - 2.34) < 0.01
    assert abs(stats["toughness_mean"] - 2.36) < 0.01


def test_generate_random_creature_basic():
    """CR 109.3: A creature has a name, power, toughness, and abilities."""
    cards = load_cards(str(DATA_PATH))
    stats = compute_card_statistics(cards)
    creature = generate_random_creature(stats, controller="A")
    assert isinstance(creature, CombatCreature)
    assert isinstance(creature.power, int)
    assert isinstance(creature.toughness, int)
    assert creature.name
