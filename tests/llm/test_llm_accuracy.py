"""Tests for LLM accuracy evaluation."""

import asyncio
import json

from llms.llm import LanguageModelName
from llms.llm import MockLanguageModel
from llms.llm_cache import MockLLMCache
from scripts.evaluate_llm_accuracy import evaluate_dataset


def _patch_build(monkeypatch, responses):
    llm = MockLanguageModel(responses, cache=MockLLMCache())
    monkeypatch.setattr(
        "scripts.evaluate_llm_accuracy.build_language_model",
        lambda model, cache=None, verbose=False, api_concurrency=50: llm,
    )
    return llm


def test_evaluate_dataset(monkeypatch, tmp_path):
    data_path = tmp_path / "data.jsonl"
    items = [
        {"prompt": "p1", "answer": {"blocks": {"B": "A"}}},
        {"prompt": "p2", "answer": {"blocks": {}}},
    ]
    with data_path.open("w", encoding="utf8") as fh:
        for item in items:
            fh.write(json.dumps(item) + "\n")

    llm = _patch_build(monkeypatch, ["- B -> A", "None"])
    acc = asyncio.run(
        evaluate_dataset(str(data_path), model=LanguageModelName.GPT_4O, concurrency=2)
    )
    assert acc == 1.0
    assert len(llm.cache.entries) == 2


def test_evaluate_dataset_return_results(monkeypatch, tmp_path):
    data_path = tmp_path / "data.jsonl"
    items = [
        {"prompt": "p1", "answer": {"blocks": {"B": "A"}}},
        {"prompt": "p2", "answer": {"blocks": {}}},
    ]
    with data_path.open("w", encoding="utf8") as fh:
        for item in items:
            fh.write(json.dumps(item) + "\n")

    _patch_build(monkeypatch, ["- B -> A", "None"])
    results, losses = asyncio.run(
        evaluate_dataset(
            str(data_path),
            model=LanguageModelName.GPT_4O,
            concurrency=2,
            return_item_results=True,
        )
    )
    assert results == [True, True]
    assert losses == [0.0, 0.0]


def test_evaluate_dataset_unparsable(monkeypatch, tmp_path):
    data_path = tmp_path / "data.jsonl"
    items = [
        {"prompt": "p1", "answer": {"blocks": {"B": "A"}}},
        {"prompt": "p2", "answer": {"blocks": {}}},
    ]
    with data_path.open("w", encoding="utf8") as fh:
        for item in items:
            fh.write(json.dumps(item) + "\n")

    _patch_build(monkeypatch, ["- B -> A", "gibberish", "None"])
    acc = asyncio.run(
        evaluate_dataset(str(data_path), model=LanguageModelName.GPT_4O, concurrency=2)
    )
    assert acc == 1.0
