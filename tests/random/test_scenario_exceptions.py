# pylint: disable=missing-function-docstring, missing-module-docstring
from pathlib import Path

import pytest

from magic_combat import MissingStatisticsError
from magic_combat import ScenarioGenerationError
from magic_combat import build_value_map
from magic_combat import generate_random_scenario
from magic_combat import load_cards

DATA_PATH = Path(__file__).resolve().parents[1] / "data" / "example_test_cards.json"


def test_missing_statistics_error():
    cards = load_cards(str(DATA_PATH))
    values = build_value_map(cards)
    with pytest.raises(MissingStatisticsError):
        generate_random_scenario(cards, values, generated_cards=True)


def test_scenario_generation_error():
    with pytest.raises(ScenarioGenerationError):
        generate_random_scenario([], {})
