import asyncio
from typing import Callable

import pytest

from llms.llm import LanguageModelName
from llms.llm import call_anthropic_model
from llms.llm import call_gemini_model
from llms.llm import call_openai_model
from llms.llm_cache import LLMCache
from llms.llm_cache import MockLLMCache


class DummyOpenAIChoice:
    def __init__(self, content: str) -> None:
        self.message = type("M", (), {"content": content})()


class DummyOpenAIClient:
    def __init__(self) -> None:
        self.calls = 0
        self.chat = type(
            "Chat",
            (),
            {
                "completions": type(
                    "Completions",
                    (),
                    {
                        "create": self._create,
                    },
                )()
            },
        )()

    async def _create(
        self, model: str, messages: list[dict[str, str]], temperature: float = 0.0
    ):
        self.calls += 1
        prompt = messages[0]["content"]
        return type(
            "R", (), {"choices": [DummyOpenAIChoice(f"response to {prompt}")]}
        )()

    async def close(self) -> None:
        pass


class DummyGeminiResponse:
    def __init__(self, text: str) -> None:
        self.text = text


class DummyGeminiClient:
    def __init__(self) -> None:
        self.calls = 0
        self.aio = type(
            "Aio",
            (),
            {
                "models": type(
                    "Models",
                    (),
                    {
                        "generate_content": self._generate,
                    },
                )()
            },
        )()

    async def _generate(self, model: str, contents: str, config=None):
        self.calls += 1
        return DummyGeminiResponse(f"response to {contents}")


class DummyAnthropicBlock:
    def __init__(self, text: str) -> None:
        self.text = text


class DummyAnthropicClient:
    def __init__(self) -> None:
        self.calls = 0
        self.messages = type(
            "Messages",
            (),
            {
                "create": self._create,
            },
        )()

    async def _create(
        self,
        model: str,
        messages: list[dict[str, str]],
        temperature: float = 0.0,
        max_tokens: int = 0,
    ):
        self.calls += 1
        prompt = messages[0]["content"]
        return type(
            "R", (), {"content": [DummyAnthropicBlock(f"response to {prompt}")]}
        )()

    async def close(self) -> None:
        pass


@pytest.mark.parametrize(
    "call_fn,client_cls,patch_target",
    [
        (call_openai_model, DummyOpenAIClient, "openai.AsyncOpenAI"),
        (call_gemini_model, DummyGeminiClient, "google.genai.Client"),
        (call_anthropic_model, DummyAnthropicClient, "anthropic.AsyncAnthropic"),
    ],
)
def test_call_models(
    monkeypatch, call_fn: Callable, client_cls: type, patch_target: str
):
    dummy = client_cls()
    monkeypatch.setattr(patch_target, lambda: dummy)
    res = asyncio.run(call_fn(["p1", "p2"]))
    assert res == ["response to p1", "response to p2"]
    assert dummy.calls == 2


@pytest.mark.parametrize(
    "call_fn,client_cls,patch_target",
    [
        (call_openai_model, DummyOpenAIClient, "openai.AsyncOpenAI"),
        (call_gemini_model, DummyGeminiClient, "google.genai.Client"),
        (call_anthropic_model, DummyAnthropicClient, "anthropic.AsyncAnthropic"),
    ],
)
def test_llm_cache_hit(
    monkeypatch, call_fn: Callable, client_cls: type, patch_target: str
):
    dummy = client_cls()
    monkeypatch.setattr(patch_target, lambda: dummy)
    cache = MockLLMCache()
    res1 = asyncio.run(
        call_fn(
            ["p1"], model=LanguageModelName.TEST_M, temperature=0.3, seed=1, cache=cache
        )
    )
    res2 = asyncio.run(
        call_fn(
            ["p1"], model=LanguageModelName.TEST_M, temperature=0.3, seed=1, cache=cache
        )
    )
    assert res1 == res2
    assert dummy.calls == 1
    assert len(cache.entries) == 1


@pytest.mark.parametrize(
    "call_fn,client_cls,patch_target",
    [
        (call_openai_model, DummyOpenAIClient, "openai.AsyncOpenAI"),
        (call_gemini_model, DummyGeminiClient, "google.genai.Client"),
        (call_anthropic_model, DummyAnthropicClient, "anthropic.AsyncAnthropic"),
    ],
)
def test_llm_cache_miss(
    monkeypatch, call_fn: Callable, client_cls: type, patch_target: str
):
    dummy = client_cls()
    monkeypatch.setattr(patch_target, lambda: dummy)
    cache = MockLLMCache()
    asyncio.run(
        call_fn(
            ["p1"], model=LanguageModelName.TEST_M, temperature=0.3, seed=1, cache=cache
        )
    )
    asyncio.run(
        call_fn(
            ["p1"],
            model=LanguageModelName.TEST_M2,
            temperature=0.3,
            seed=1,
            cache=cache,
        )
    )
    asyncio.run(
        call_fn(
            ["p1"], model=LanguageModelName.TEST_M, temperature=0.4, seed=1, cache=cache
        )
    )
    asyncio.run(
        call_fn(
            ["p1"], model=LanguageModelName.TEST_M, temperature=0.3, seed=2, cache=cache
        )
    )
    assert dummy.calls == 4
    assert len(cache.entries) == 4


@pytest.mark.parametrize(
    "call_fn,client_cls,patch_target",
    [
        (call_openai_model, DummyOpenAIClient, "openai.AsyncOpenAI"),
        (call_gemini_model, DummyGeminiClient, "google.genai.Client"),
        (call_anthropic_model, DummyAnthropicClient, "anthropic.AsyncAnthropic"),
    ],
)
def test_llm_cache_file_hit(
    monkeypatch, tmp_path, call_fn: Callable, client_cls: type, patch_target: str
):
    dummy = client_cls()
    monkeypatch.setattr(patch_target, lambda: dummy)
    cache_path = tmp_path / "cache.jsonl"
    cache = LLMCache(str(cache_path))
    res1 = asyncio.run(
        call_fn(
            ["p1"], model=LanguageModelName.TEST_M, temperature=0.3, seed=1, cache=cache
        )
    )
    cache2 = LLMCache(str(cache_path))
    res2 = asyncio.run(
        call_fn(
            ["p1"],
            model=LanguageModelName.TEST_M,
            temperature=0.3,
            seed=1,
            cache=cache2,
        )
    )
    assert res1 == res2
    assert dummy.calls == 1
