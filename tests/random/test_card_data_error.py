# pylint: disable=missing-function-docstring, missing-module-docstring
import pytest

from magic_combat.exceptions import CardDataError
from magic_combat.random_scenario import build_value_map
from magic_combat.random_scenario import ensure_cards
from magic_combat.random_scenario import sample_balanced


def test_ensure_cards_download_failure(monkeypatch, tmp_path):
    def fail_fetch():
        raise RuntimeError("boom")

    monkeypatch.setattr(
        "magic_combat.random_scenario.fetch_french_vanilla_cards", fail_fetch
    )
    path = tmp_path / "cards.json"
    with pytest.raises(CardDataError):
        ensure_cards(str(path))


def test_build_value_map_no_creatures():
    with pytest.raises(CardDataError):
        build_value_map([])


def test_sample_balanced_not_enough_cards():
    with pytest.raises(CardDataError):
        sample_balanced([], {}, 1, 1)
