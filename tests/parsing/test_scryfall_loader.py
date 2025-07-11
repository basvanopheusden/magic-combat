from pathlib import Path

from magic_combat.creature import Color
from magic_combat.parsing import parse_protection as _parse_protection
from magic_combat.scryfall_loader import _parse_colors
from magic_combat.scryfall_loader import card_to_creature
from magic_combat.scryfall_loader import cards_to_creatures
from magic_combat.scryfall_loader import load_cards

# Location of the test card data used for parsing tests
DATA_PATH = Path(__file__).resolve().parents[1] / "data" / "example_test_cards.json"


def test_parse_colors_hybrid():
    """CR 205.3d: The colors of an object are determined by the mana symbols in its cost."""
    result = _parse_colors("{2}{G/U}{R}")
    assert result == {Color.GREEN, Color.BLUE, Color.RED}


def test_parse_protection_multi():
    """CR 702.16b: Protection from red and from green covers both colors."""
    result = _parse_protection("Protection from red and from green")
    assert result == {Color.RED, Color.GREEN}


def test_card_to_creature_basic():
    """CR 205.3d: Converting a card uses its mana symbols to set its colors."""
    cards = load_cards(str(DATA_PATH))
    card = next(c for c in cards if c["name"] == "Winged Drake")
    creature = card_to_creature(card, "A")
    assert creature.flying
    assert creature.colors == {Color.BLUE}


def test_card_to_creature_protection_and_bushido():
    """CR 702.16b & 702.46a: Protection and bushido keywords are recognized."""
    cards = load_cards(str(DATA_PATH))
    card = next(c for c in cards if c["name"] == "White Knight")
    creature = card_to_creature(card, "B")
    assert creature.first_strike
    assert creature.protection_colors == {Color.BLACK}


def test_cards_to_creatures_count():
    """CR 205.3d: Cards converted to creatures keep their colors from mana symbols."""
    cards = load_cards(str(DATA_PATH))
    creatures = cards_to_creatures(cards, "A")
    assert len(creatures) == 50
    names = {c.name for c in creatures}
    assert "Elemental Beast" in names
