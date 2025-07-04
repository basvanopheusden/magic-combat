"""Tests for leaderboard generation script."""

import asyncio

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


async def dummy_evaluate_dataset(path: str, *, model: str = "", **kwargs) -> list[bool]:
    return {"m1": [True, False], "m2": [True, True]}[model]


def test_evaluate_models(monkeypatch):
    monkeypatch.setattr("scripts.leaderboard.evaluate_dataset", dummy_evaluate_dataset)
    res = asyncio.run(evaluate_models("d.jsonl", ["m1", "m2"]))
    assert res == {"m1": [True, False], "m2": [True, True]}
