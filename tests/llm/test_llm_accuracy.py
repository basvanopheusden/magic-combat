"""Tests for LLM accuracy evaluation script."""

import asyncio
import json

from llms.llm_cache import MockLLMCache
from scripts.evaluate_llm_accuracy import evaluate_dataset


class DummyMessage:
    def __init__(self, content):
        self.content = content


class DummyChoice:
    def __init__(self, content):
        self.message = DummyMessage(content)


class DummyResponse:
    def __init__(self, content):
        self.choices = [DummyChoice(content)]


class DummyCompletions:
    def __init__(self, responses):
        self.responses = responses
        self.calls = 0

    async def create(self, model, messages, temperature=0.0):
        res = self.responses[self.calls]
        self.calls += 1
        return DummyResponse(res)


class DummyChat:
    def __init__(self, responses):
        self.completions = DummyCompletions(responses)


class DummyClient:
    def __init__(self, responses):
        self.chat = DummyChat(responses)

    async def close(self):
        pass


def test_evaluate_dataset(monkeypatch, tmp_path):
    data_path = tmp_path / "data.jsonl"
    items = [
        {"prompt": "p1", "answer": {"blocks": {"B": "A"}}},
        {"prompt": "p2", "answer": {"blocks": {}}},
    ]
    with data_path.open("w", encoding="utf8") as fh:
        for item in items:
            fh.write(json.dumps(item) + "\n")
    responses = ["- B -> A", "None"]
    monkeypatch.setattr("openai.AsyncOpenAI", lambda: DummyClient(responses))
    cache = MockLLMCache()
    acc = asyncio.run(
        evaluate_dataset(str(data_path), model="m", concurrency=2, cache=cache)
    )
    assert acc == 1.0
    assert len(cache.entries) == 2


def test_evaluate_dataset_return_results(monkeypatch, tmp_path):
    data_path = tmp_path / "data.jsonl"
    items = [
        {"prompt": "p1", "answer": {"blocks": {"B": "A"}}},
        {"prompt": "p2", "answer": {"blocks": {}}},
    ]
    with data_path.open("w", encoding="utf8") as fh:
        for item in items:
            fh.write(json.dumps(item) + "\n")
    responses = ["- B -> A", "None"]
    monkeypatch.setattr("openai.AsyncOpenAI", lambda: DummyClient(responses))
    results = asyncio.run(
        evaluate_dataset(
            str(data_path),
            model="m",
            concurrency=2,
            return_item_results=True,
        )
    )
    assert results == [True, True]


def test_evaluate_dataset_unparsable(monkeypatch, tmp_path):
    data_path = tmp_path / "data.jsonl"
    items = [
        {"prompt": "p1", "answer": {"blocks": {"B": "A"}}},
        {"prompt": "p2", "answer": {"blocks": {}}},
    ]
    with data_path.open("w", encoding="utf8") as fh:
        for item in items:
            fh.write(json.dumps(item) + "\n")

    responses = ["- B -> A", "gibberish"]
    monkeypatch.setattr("openai.AsyncOpenAI", lambda: DummyClient(responses))
    cache = MockLLMCache()
    acc = asyncio.run(
        evaluate_dataset(str(data_path), model="m", concurrency=2, cache=cache)
    )
    assert acc == 0.5
