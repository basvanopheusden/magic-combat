"""Tests for leaderboard generation script."""

import asyncio

from llms.llm import LanguageModelName
from scripts.leaderboard import count_items
from scripts.leaderboard import evaluate_models
from scripts.leaderboard import standard_error
from scripts.leaderboard import two_proportion_p_value


def test_count_items(tmp_path):
    path = tmp_path / "d.jsonl"
    path.write_text("{}\n{}\n", encoding="utf8")
    assert count_items(str(path)) == 2


def test_standard_error():
    assert abs(standard_error(0.5, 100) - 0.05) < 1e-6


def test_two_proportion_p_value():
    r1 = [True] * 10
    r2 = [False] * 10
    p = two_proportion_p_value(r1, r2)
    assert p < 0.05


async def dummy_evaluate_dataset(
    path: str, *, model: LanguageModelName = LanguageModelName.TEST_M1, **kwargs
) -> list[bool]:
    return {
        LanguageModelName.TEST_M1: [True, False],
        LanguageModelName.TEST_M2: [True, True],
    }[model]


def test_evaluate_models(monkeypatch):
    monkeypatch.setattr("scripts.leaderboard.evaluate_dataset", dummy_evaluate_dataset)
    res = asyncio.run(
        evaluate_models(
            "d.jsonl",
            [LanguageModelName.TEST_M1, LanguageModelName.TEST_M2],
        )
    )
    assert res == {
        LanguageModelName.TEST_M1: [True, False],
        LanguageModelName.TEST_M2: [True, True],
    }
