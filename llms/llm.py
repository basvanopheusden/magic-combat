from abc import ABC
from abc import abstractmethod
from enum import Enum
from typing import Any
from typing import Optional

import anthropic
import openai
import together  # type: ignore
from google import genai
from google.genai import types as genai_types
from openai.types.responses import Response
from xai_sdk import chat as xai_chat  # type: ignore
from xai_sdk.aio.client import Client as XAIClient  # type: ignore

from .llm_cache import LLMCache


class LanguageModelName(Enum):
    GEMINI_2_5_PRO = "gemini-2.5-pro"
    GEMINI_2_5_FLASH = "gemini-2.5-flash"
    GEMINI_2_0_FLASH = "gemini-2.0-flash"
    GPT_4O = "gpt-4o"
    GPT_4_1 = "gpt-4.1"
    O4_MINI = "o4-mini-2025-04-16"
    O3 = "o3-2025-04-16"
    O3_PRO = "o3-pro-2025-06-10"
    CLAUDE_3_7_SONNET = "claude-3-7-sonnet-20250219"
    CLAUDE_3_5_SONNET = "claude-3-5-sonnet-20241022"
    CLAUDE_4_SONNET = "claude-sonnet-4-20250514"
    CLAUDE_4_OPUS = "claude-opus-4-20250514"
    CLAUDE_4_SONNET_THINKING = "claude-sonnet-4-20250514-thinking"
    CLAUDE_4_OPUS_THINKING = "claude-opus-4-20250514-thinking"
    DEEPSEEK_R1 = "deepseek-ai/DeepSeek-R1"
    LLAMA_4_MAVERICK = "meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8"
    LLAMA_4_SCOUT = "meta-llama/Llama-4-Scout-17B-16E-Instruct"
    GROK_3 = "grok-3"
    GROK_3_MINI = "grok-3-mini"
    QWEN_3_235B = "Qwen/Qwen3-235B-A22B-fp8-tput"


def get_default_temperature(model: LanguageModelName) -> float:
    """Return the default temperature for ``model``."""
    if model in {
        LanguageModelName.O3_PRO,
        LanguageModelName.O3,
        LanguageModelName.O4_MINI,
        LanguageModelName.CLAUDE_4_OPUS_THINKING,
        LanguageModelName.CLAUDE_4_SONNET_THINKING,
    }:
        return 1.0
    return 0.2


def get_short_prompt(prompt: str) -> str:
    """Return a short version of ``prompt`` for logging."""
    key_str = "The current game state is as follows:"
    rules_str = "# Relevant Rules"
    if key_str in prompt and rules_str in prompt:
        parts = prompt.split(key_str, 1)
        return parts[1].split(rules_str, 1)[0].strip()
    return prompt.splitlines()[0][:30]


class LanguageModel(ABC):
    """Base language model wrapper."""

    def __init__(
        self,
        model: LanguageModelName,
        *,
        cache: Optional[LLMCache] = None,
        verbose: bool = False,
        max_tokens: int = 8192,
    ) -> None:
        self.model = model
        self.cache = cache
        self.verbose = verbose
        self.default_temperature = get_default_temperature(model)
        self.max_tokens = max_tokens

    async def call(
        self,
        prompt: str,
        *,
        temperature: Optional[float] = None,
        seed: int = 0,
        max_tokens: Optional[int] = None,
    ) -> str:
        """Return the model's response to ``prompt``."""
        temp = self.default_temperature if temperature is None else temperature
        if self.verbose:
            print("Calling model for:", get_short_prompt(prompt))
        cached = (
            self.cache.get(prompt, self.model.value, seed, temp) if self.cache else None
        )
        if cached is not None:
            if self.verbose:
                print("Cached response:", cached)
            return cached
        text = await self._call_api_model(
            prompt,
            temperature=temp,
            seed=seed,
            max_tokens=self.max_tokens if max_tokens is None else max_tokens,
        )
        if self.cache is not None:
            self.cache.add(prompt, self.model.value, seed, temp, text)
        if self.verbose:
            print("Model output:", text)
        return text

    @abstractmethod
    async def _call_api_model(
        self, prompt: str, *, temperature: float, seed: int, max_tokens: int
    ) -> str:
        """Call the underlying API and return its response."""

    async def close(self) -> None:  # pragma: no cover - subclasses may override
        """Close any open client resources."""
        return None


class OpenAILanguageModel(LanguageModel):
    def __init__(
        self,
        model: LanguageModelName,
        *,
        cache: Optional[LLMCache] = None,
        verbose: bool = False,
        max_tokens: int = 8192,
    ) -> None:
        super().__init__(model, cache=cache, verbose=verbose, max_tokens=max_tokens)
        self.client = openai.AsyncOpenAI()

    async def _call_api_model(
        self, prompt: str, *, temperature: float, seed: int, max_tokens: int
    ) -> str:
        if self.model == LanguageModelName.O3_PRO:
            client: Any = self.client
            resp: Response = (
                await client.responses.create(  # pyright: ignore[reportCallIssue]
                    model=self.model.value,
                    input=prompt,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
            )
            return (resp.output_text or "").strip()
        chat_resp = await self.client.chat.completions.create(
            model=self.model.value,
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return (chat_resp.choices[0].message.content or "").strip()

    async def close(self) -> None:
        await self.client.close()


class GeminiLanguageModel(LanguageModel):
    def __init__(
        self,
        model: LanguageModelName,
        *,
        cache: Optional[LLMCache] = None,
        verbose: bool = False,
        max_tokens: int = 8192,
    ) -> None:
        super().__init__(model, cache=cache, verbose=verbose, max_tokens=max_tokens)
        self.client = genai.Client()

    async def _call_api_model(
        self, prompt: str, *, temperature: float, seed: int, max_tokens: int
    ) -> str:
        config = genai_types.GenerateContentConfig(
            temperature=temperature, seed=seed, max_output_tokens=max_tokens
        )
        response = await self.client.aio.models.generate_content(
            model=self.model.value, contents=prompt, config=config
        )
        return (response.text or "").strip()


class AnthropicLanguageModel(LanguageModel):
    def __init__(
        self,
        model: LanguageModelName,
        *,
        cache: Optional[LLMCache] = None,
        verbose: bool = False,
        max_tokens: int = 8192,
    ) -> None:
        super().__init__(model, cache=cache, verbose=verbose, max_tokens=max_tokens)
        self.client = anthropic.AsyncAnthropic()

    async def _call_api_model(
        self, prompt: str, *, temperature: float, seed: int, max_tokens: int
    ) -> str:
        thinking = self.model.value.endswith("-thinking")
        thinking_type = "enabled" if thinking else "disabled"
        response = await self.client.messages.create(  # type: ignore[call-overload]
            model=self.model.value.removesuffix("-thinking"),
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
            max_tokens=max_tokens,
            thinking={
                "type": thinking_type,
                "budget_tokens": int(max_tokens / 2),
            },  # pyright: ignore[reportArgumentType]
        )
        return "".join(getattr(b, "text", "") for b in response.content).strip()

    async def close(self) -> None:
        await self.client.close()


class TogetherLanguageModel(LanguageModel):
    def __init__(
        self,
        model: LanguageModelName,
        *,
        cache: Optional[LLMCache] = None,
        verbose: bool = False,
        max_tokens: int = 8192,
    ) -> None:
        super().__init__(model, cache=cache, verbose=verbose, max_tokens=max_tokens)
        self.client = together.AsyncTogether()

    async def _call_api_model(
        self, prompt: str, *, temperature: float, seed: int, max_tokens: int
    ) -> str:
        response = await self.client.chat.completions.create(
            model=self.model.value,
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
            max_tokens=max_tokens,
        )
        choice = response.choices[0]  # type: ignore[index]
        message = choice.message
        content = ""
        if message and isinstance(message.content, str):
            content = message.content
        return content.strip()


class XAILanguageModel(LanguageModel):
    def __init__(
        self,
        model: LanguageModelName,
        *,
        cache: Optional[LLMCache] = None,
        verbose: bool = False,
        max_tokens: int = 8192,
    ) -> None:
        super().__init__(model, cache=cache, verbose=verbose, max_tokens=max_tokens)
        self.client = XAIClient()

    async def _call_api_model(
        self, prompt: str, *, temperature: float, seed: int, max_tokens: int
    ) -> str:
        if self.model == LanguageModelName.GROK_3_MINI:
            max_tokens = 32768
            chat = self.client.chat.create(
                model=self.model.value,
                temperature=temperature,
                seed=seed + 1,  # XAI seeds must be > 0
                max_tokens=max_tokens,
                reasoning_effort="high",
            )
        else:
            chat = self.client.chat.create(
                model=self.model.value,
                temperature=temperature,
                seed=seed + 1,  # XAI seeds must be > 0
                max_tokens=max_tokens,
            )
        chat.append(xai_chat.user(prompt))
        response = await chat.sample()
        # print("XAI response:", response)
        return (response.content or "").strip()


class MockLanguageModel(LanguageModel):
    """Simple in-memory mock model for tests."""

    def __init__(
        self,
        responses: list[str],
        *,
        cache: Optional[LLMCache] = None,
        verbose: bool = False,
        max_tokens: int = 8192,
    ) -> None:
        super().__init__(
            LanguageModelName.GPT_4O,
            cache=cache,
            verbose=verbose,
            max_tokens=max_tokens,
        )
        self.responses = responses
        self.calls = 0

    async def _call_api_model(
        self, prompt: str, *, temperature: float, seed: int, max_tokens: int
    ) -> str:
        response = self.responses[self.calls]
        self.calls += 1
        return response


_MAX_TOKENS_BY_MODEL_NAME: dict[LanguageModelName, int] = {
    LanguageModelName.GROK_3_MINI: 32768,
    LanguageModelName.GEMINI_2_5_PRO: 8192,
    LanguageModelName.GEMINI_2_5_FLASH: 8192,
    LanguageModelName.GEMINI_2_0_FLASH: 8192,
    LanguageModelName.GPT_4O: 8192,
    LanguageModelName.GPT_4_1: 8192,
    LanguageModelName.O4_MINI: 8192,
    LanguageModelName.O3: 8192,
    LanguageModelName.O3_PRO: 8192,
    LanguageModelName.CLAUDE_3_7_SONNET: 8192,
    LanguageModelName.CLAUDE_3_5_SONNET: 8192,
    LanguageModelName.CLAUDE_4_SONNET: 8192,
    LanguageModelName.CLAUDE_4_OPUS: 8192,
    LanguageModelName.CLAUDE_4_SONNET_THINKING: 8192,
    LanguageModelName.CLAUDE_4_OPUS_THINKING: 8192,
    LanguageModelName.DEEPSEEK_R1: 8192,
    LanguageModelName.LLAMA_4_MAVERICK: 8192,
    LanguageModelName.LLAMA_4_SCOUT: 8192,
    LanguageModelName.GROK_3: 8192,
    LanguageModelName.QWEN_3_235B: 8192,
}


_MODEL_CLASS_BY_NAME: dict[LanguageModelName, type[LanguageModel]] = {
    LanguageModelName.GEMINI_2_5_PRO: GeminiLanguageModel,
    LanguageModelName.GEMINI_2_5_FLASH: GeminiLanguageModel,
    LanguageModelName.GEMINI_2_0_FLASH: GeminiLanguageModel,
    LanguageModelName.GPT_4O: OpenAILanguageModel,
    LanguageModelName.GPT_4_1: OpenAILanguageModel,
    LanguageModelName.O4_MINI: OpenAILanguageModel,
    LanguageModelName.O3: OpenAILanguageModel,
    LanguageModelName.O3_PRO: OpenAILanguageModel,
    LanguageModelName.CLAUDE_3_7_SONNET: AnthropicLanguageModel,
    LanguageModelName.CLAUDE_3_5_SONNET: AnthropicLanguageModel,
    LanguageModelName.CLAUDE_4_SONNET: AnthropicLanguageModel,
    LanguageModelName.CLAUDE_4_OPUS: AnthropicLanguageModel,
    LanguageModelName.CLAUDE_4_SONNET_THINKING: AnthropicLanguageModel,
    LanguageModelName.CLAUDE_4_OPUS_THINKING: AnthropicLanguageModel,
    LanguageModelName.DEEPSEEK_R1: TogetherLanguageModel,
    LanguageModelName.LLAMA_4_MAVERICK: TogetherLanguageModel,
    LanguageModelName.LLAMA_4_SCOUT: TogetherLanguageModel,
    LanguageModelName.GROK_3: XAILanguageModel,
    LanguageModelName.GROK_3_MINI: XAILanguageModel,
    LanguageModelName.QWEN_3_235B: TogetherLanguageModel,
}


def build_language_model(
    model: LanguageModelName,
    *,
    cache: Optional[LLMCache] = None,
    verbose: bool = False,
) -> LanguageModel:
    """Instantiate a language model for ``model``."""
    if model not in _MODEL_CLASS_BY_NAME:
        raise ValueError(f"Unsupported model: {model}")
    cls = _MODEL_CLASS_BY_NAME[model]
    max_tokens = _MAX_TOKENS_BY_MODEL_NAME.get(model, 8192)
    return cls(model, cache=cache, verbose=verbose, max_tokens=max_tokens)
