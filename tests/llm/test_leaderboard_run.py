import argparse
import asyncio

from llms.llm import LanguageModelName
from llms.llm_cache import LLMCache
from llms.llm_cache import MockLLMCache
from scripts.leaderboard import evaluate_models
from scripts.leaderboard import run_leaderboard


def test_evaluate_models_default_models(monkeypatch):
    calls = []

    async def dummy(path: str, *, model: LanguageModelName, **kwargs):
        calls.append(model)
        return [True]

    monkeypatch.setattr("scripts.leaderboard.evaluate_dataset", dummy)
    results = asyncio.run(evaluate_models("d.jsonl"))
    assert set(calls) == set(LanguageModelName)
    assert set(results) == set(LanguageModelName)


def test_evaluate_models_subset(monkeypatch):
    calls = []

    async def dummy(path: str, *, model: LanguageModelName, **kwargs):
        calls.append(model)
        return [True]

    monkeypatch.setattr("scripts.leaderboard.evaluate_dataset", dummy)
    models = [LanguageModelName.GPT_4O, LanguageModelName.GPT_4_1]
    results = asyncio.run(evaluate_models("d.jsonl", models))
    assert calls == models
    assert set(results) == set(models)


def test_run_leaderboard_prints_table(monkeypatch, capsys):
    async def dummy_eval_models(*args, **kwargs):
        return {LanguageModelName.GPT_4O: [True]}

    monkeypatch.setattr("scripts.leaderboard.evaluate_models", dummy_eval_models)
    monkeypatch.setattr("scripts.leaderboard.count_items", lambda x: 1)
    monkeypatch.setattr(
        "scripts.leaderboard.format_accuracy_table", lambda results, n: "TABLE"
    )
    args = argparse.Namespace(dataset="d.jsonl", seed=0, concurrency=1, cache=None)
    asyncio.run(run_leaderboard(args))
    captured = capsys.readouterr()
    assert "TABLE" in captured.out


def test_run_leaderboard_passes_args(monkeypatch):
    passed = {}

    async def dummy_eval_models(
        dataset: str, *, seed: int, concurrency: int, cache=None, models=None
    ):
        passed.update(
            {
                "dataset": dataset,
                "seed": seed,
                "concurrency": concurrency,
                "cache": cache,
            }
        )
        return {LanguageModelName.GPT_4O: [True]}

    monkeypatch.setattr("scripts.leaderboard.evaluate_models", dummy_eval_models)
    monkeypatch.setattr("scripts.leaderboard.count_items", lambda x: 1)
    monkeypatch.setattr(
        "scripts.leaderboard.format_accuracy_table", lambda results, n: "TABLE"
    )
    args = argparse.Namespace(dataset="d.jsonl", seed=3, concurrency=7, cache="c")
    asyncio.run(run_leaderboard(args))
    assert passed["dataset"] == "d.jsonl"
    assert passed["seed"] == 3
    assert passed["concurrency"] == 7
    assert isinstance(passed["cache"], LLMCache)


def test_evaluate_models_passes_arguments(monkeypatch):
    captured = {}

    async def dummy(
        path: str,
        *,
        model: LanguageModelName,
        seed: int,
        concurrency: int,
        cache,
        **kwargs,
    ):
        captured[model] = (seed, concurrency, cache)
        return [True]

    monkeypatch.setattr("scripts.leaderboard.evaluate_dataset", dummy)
    cache = MockLLMCache()
    asyncio.run(
        evaluate_models(
            "d.jsonl",
            [LanguageModelName.GPT_4O],
            seed=5,
            concurrency=3,
            cache=cache,
        )
    )
    assert captured[LanguageModelName.GPT_4O] == (5, 3, cache)
