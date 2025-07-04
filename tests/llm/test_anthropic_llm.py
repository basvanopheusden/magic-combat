"""Tests for the Anthropic LLM helper functions."""

import asyncio

from llms.llm import call_anthropic_model
from llms.llm_cache import LLMCache
from llms.llm_cache import MockLLMCache


class DummyBlock:
    def __init__(self, text: str):
        self.text = text


class DummyResponse:
    def __init__(self, content: str):
        self.content = [DummyBlock(content)]


class DummyMessages:
    def __init__(self) -> None:
        self.calls = 0

    async def create(self, model, messages, temperature=0.0, max_tokens=0):
        self.calls += 1
        prompt = messages[0]["content"]
        return DummyResponse(f"response to {prompt}")


class DummyClient:
    def __init__(self) -> None:
        self.messages = DummyMessages()

    async def close(self) -> None:
        pass


def test_call_anthropic_model(monkeypatch):
    monkeypatch.setattr("anthropic.AsyncAnthropic", lambda: DummyClient())
    res = asyncio.run(call_anthropic_model(["p1", "p2"]))
    assert res == ["response to p1", "response to p2"]


def test_anthropic_cache_hit(monkeypatch):
    monkeypatch.setattr("anthropic.AsyncAnthropic", lambda: DummyClient())
    cache = MockLLMCache()
    res1 = asyncio.run(
        call_anthropic_model(["p1"], model="m", temperature=0.3, seed=1, cache=cache)
    )
    res2 = asyncio.run(
        call_anthropic_model(["p1"], model="m", temperature=0.3, seed=1, cache=cache)
    )
    assert res1 == res2
    assert cache.entries[0]["response"] == res1[0]
    assert len(cache.entries) == 1


def test_anthropic_cache_miss(monkeypatch):
    monkeypatch.setattr("anthropic.AsyncAnthropic", lambda: DummyClient())
    cache = MockLLMCache()
    asyncio.run(
        call_anthropic_model(["p1"], model="m", temperature=0.3, seed=1, cache=cache)
    )
    asyncio.run(
        call_anthropic_model(["p1"], model="m2", temperature=0.3, seed=1, cache=cache)
    )
    asyncio.run(
        call_anthropic_model(["p1"], model="m", temperature=0.4, seed=1, cache=cache)
    )
    asyncio.run(
        call_anthropic_model(["p1"], model="m", temperature=0.3, seed=2, cache=cache)
    )
    assert len(cache.entries) == 4


def test_anthropic_cache_file_hit(monkeypatch, tmp_path):
    dummy = DummyClient()
    monkeypatch.setattr("anthropic.AsyncAnthropic", lambda: dummy)
    cache_path = tmp_path / "cache.jsonl"
    cache = LLMCache(str(cache_path))
    res1 = asyncio.run(
        call_anthropic_model(["p1"], model="m", temperature=0.3, seed=1, cache=cache)
    )
    cache2 = LLMCache(str(cache_path))
    res2 = asyncio.run(
        call_anthropic_model(["p1"], model="m", temperature=0.3, seed=1, cache=cache2)
    )
    assert res1 == res2
    assert dummy.messages.calls == 1
