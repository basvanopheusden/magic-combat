import asyncio

from llms.llm import AnthropicLanguageModel
from llms.llm import GeminiLanguageModel
from llms.llm import LanguageModelName
from llms.llm import MockLanguageModel
from llms.llm import OpenAILanguageModel
from llms.llm import TogetherLanguageModel
from llms.llm import build_language_model
from llms.llm_cache import MockLLMCache


def test_language_model_cache_hit():
    cache = MockLLMCache()
    llm = MockLanguageModel(["r1"], cache=cache)
    res1 = asyncio.run(llm.call("p1", temperature=0.3, seed=1))
    res2 = asyncio.run(llm.call("p1", temperature=0.3, seed=1))
    assert res1 == res2
    assert llm.calls == 1
    assert len(cache.entries) == 1


def test_language_model_cache_miss():
    cache = MockLLMCache()
    llm = MockLanguageModel(["r1", "r2", "r3", "r4"], cache=cache)
    asyncio.run(llm.call("p1", temperature=0.3, seed=1))
    asyncio.run(llm.call("p1", temperature=0.3, seed=2))
    asyncio.run(llm.call("p1", temperature=0.4, seed=1))
    asyncio.run(llm.call("p2", temperature=0.3, seed=1))
    assert llm.calls == 4
    assert len(cache.entries) == 4


def test_build_language_model_types(monkeypatch):
    monkeypatch.setattr("openai.AsyncOpenAI", lambda: object())
    monkeypatch.setattr("anthropic.AsyncAnthropic", lambda: object())
    monkeypatch.setattr("google.genai.Client", lambda: object())
    monkeypatch.setattr("together.AsyncTogether", lambda: object())
    assert isinstance(
        build_language_model(LanguageModelName.GPT_4O), OpenAILanguageModel
    )
    assert isinstance(
        build_language_model(LanguageModelName.GEMINI_2_5_PRO), GeminiLanguageModel
    )
    assert isinstance(
        build_language_model(LanguageModelName.CLAUDE_4_OPUS), AnthropicLanguageModel
    )
    assert isinstance(
        build_language_model(LanguageModelName.DEEPSEEK_R1), TogetherLanguageModel
    )
