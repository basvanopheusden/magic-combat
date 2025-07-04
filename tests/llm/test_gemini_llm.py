import asyncio

from llms.llm import call_gemini_model
from llms.llm_cache import LLMCache
from llms.llm_cache import MockLLMCache


class DummyResponse:
    def __init__(self, text: str) -> None:
        self.text = text


class DummyModels:
    def __init__(self) -> None:
        self.calls = 0

    async def generate_content(self, model, contents, config=None):
        self.calls += 1
        return DummyResponse(f"response to {contents}")


class DummyAio:
    def __init__(self) -> None:
        self.models = DummyModels()


class DummyClient:
    def __init__(self) -> None:
        self.aio = DummyAio()


def test_call_gemini_model(monkeypatch):
    monkeypatch.setattr("google.genai.Client", lambda: DummyClient())
    res = asyncio.run(call_gemini_model(["p1", "p2"]))
    assert res == ["response to p1", "response to p2"]


def test_gemini_cache_hit(monkeypatch):
    monkeypatch.setattr("google.genai.Client", lambda: DummyClient())
    cache = MockLLMCache()
    res1 = asyncio.run(
        call_gemini_model(["p1"], model="m", temperature=0.3, seed=1, cache=cache)
    )
    res2 = asyncio.run(
        call_gemini_model(["p1"], model="m", temperature=0.3, seed=1, cache=cache)
    )
    assert res1 == res2
    assert cache.entries[0]["response"] == res1[0]
    assert len(cache.entries) == 1


def test_gemini_cache_miss(monkeypatch):
    monkeypatch.setattr("google.genai.Client", lambda: DummyClient())
    cache = MockLLMCache()
    asyncio.run(
        call_gemini_model(["p1"], model="m", temperature=0.3, seed=1, cache=cache)
    )
    asyncio.run(
        call_gemini_model(["p1"], model="m2", temperature=0.3, seed=1, cache=cache)
    )
    asyncio.run(
        call_gemini_model(["p1"], model="m", temperature=0.4, seed=1, cache=cache)
    )
    asyncio.run(
        call_gemini_model(["p1"], model="m", temperature=0.3, seed=2, cache=cache)
    )
    assert len(cache.entries) == 4


def test_gemini_cache_file_hit(monkeypatch, tmp_path):
    dummy = DummyClient()
    monkeypatch.setattr("google.genai.Client", lambda: dummy)
    cache_path = tmp_path / "cache.jsonl"
    cache = LLMCache(str(cache_path))
    res1 = asyncio.run(
        call_gemini_model(["p1"], model="m", temperature=0.3, seed=1, cache=cache)
    )
    cache2 = LLMCache(str(cache_path))
    res2 = asyncio.run(
        call_gemini_model(["p1"], model="m", temperature=0.3, seed=1, cache=cache2)
    )
    assert res1 == res2
    assert dummy.aio.models.calls == 1
