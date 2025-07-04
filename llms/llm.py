import asyncio
from enum import Enum
from typing import Any
from typing import Awaitable
from typing import Callable
from typing import Optional
from typing import cast

import anthropic
import openai
import together  # type: ignore
from google import genai
from google.genai import types as genai_types

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
    DEEPSEEK_CODER_33B = "deepseek-coder-33b-instruct"
    LLAMA_3_70B = "llama-3-70b-instruct"
    TEST_M = "m"
    TEST_M1 = "m1"
    TEST_M2 = "m2"


def get_default_temperature(model: LanguageModelName) -> float:
    """Return the default temperature for the given model."""
    if model in {
        LanguageModelName.O3_PRO,
        LanguageModelName.O3,
        LanguageModelName.O4_MINI,
    }:
        return 1.0
    return 0.2


async def _call_model_cached(
    prompt: str,
    call: Callable[[], Awaitable[str]],
    *,
    model: LanguageModelName,
    temperature: float,
    seed: int,
    cache: Optional[LLMCache],
    semaphore: Optional[asyncio.Semaphore],
) -> str:
    """Return cached result for ``call`` if available."""

    cached = cache.get(prompt, model.value, seed, temperature) if cache else None
    if cached is not None:
        short = prompt.splitlines()[0][:30]
        print(
            f"Using cached LLM response for: {short}, {model.value}, seed={seed}, temperature={temperature}"
        )
        return cached

    async def _run() -> str:
        return await call()

    if semaphore is None:
        text = await _run()
    else:
        async with semaphore:
            text = await _run()

    if cache is not None:
        cache.add(prompt, model.value, seed, temperature, text)
    return text


async def _call_model(
    prompts: list[str],
    call_single: Callable[[str, Optional[asyncio.Semaphore]], Awaitable[str]],
    concurrency: int | None,
) -> list[str]:
    semaphore = asyncio.Semaphore(concurrency) if concurrency else None
    tasks = [call_single(prompt, semaphore) for prompt in prompts]
    responses = await asyncio.gather(*tasks)
    return list(responses)


async def call_openai_model_single_prompt(
    prompt: str,
    client: openai.AsyncOpenAI,
    *,
    model: LanguageModelName = LanguageModelName.GPT_4O,
    temperature: float = 0.2,
    seed: int = 0,
    cache: Optional[LLMCache] = None,
    semaphore: Optional[asyncio.Semaphore] = None,
) -> str:
    """Return ``prompt`` response from OpenAI, optionally using ``cache``."""

    async def _call() -> str:
        response = await client.chat.completions.create(
            model=model.value,
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
        )
        return (response.choices[0].message.content or "").strip()

    return await _call_model_cached(
        prompt,
        _call,
        model=model,
        temperature=temperature,
        seed=seed,
        cache=cache,
        semaphore=semaphore,
    )


async def call_openai_model(
    prompts: list[str],
    *,
    model: LanguageModelName = LanguageModelName.GPT_4O,
    temperature: float = 0.2,
    seed: int = 0,
    cache: Optional[LLMCache] = None,
    concurrency: int | None = None,
) -> list[str]:
    """Return responses for ``prompts``."""
    client = openai.AsyncOpenAI()

    async def _call_single(prompt: str, sem: Optional[asyncio.Semaphore]) -> str:
        return await call_openai_model_single_prompt(
            prompt,
            client,
            model=model,
            temperature=temperature,
            seed=seed,
            cache=cache,
            semaphore=sem,
        )

    try:
        return await _call_model(prompts, _call_single, concurrency)
    finally:
        await client.close()


async def call_gemini_model_single_prompt(
    prompt: str,
    *,
    model: LanguageModelName = LanguageModelName.GEMINI_2_5_PRO,
    temperature: float = 0.2,
    seed: int = 0,
    cache: Optional[LLMCache] = None,
    semaphore: Optional[asyncio.Semaphore] = None,
) -> str:
    """Return ``prompt`` response from Gemini, optionally using ``cache``."""

    client = genai.Client()
    generation_config = genai_types.GenerateContentConfig(
        temperature=temperature, seed=seed
    )

    async def _call() -> str:
        response = await client.aio.models.generate_content(
            model=model.value, contents=prompt, config=generation_config
        )
        return (response.text or "").strip()

    return await _call_model_cached(
        prompt,
        _call,
        model=model,
        temperature=temperature,
        seed=seed,
        cache=cache,
        semaphore=semaphore,
    )


async def call_gemini_model(
    prompts: list[str],
    *,
    model: LanguageModelName = LanguageModelName.GEMINI_2_5_PRO,
    temperature: float = 0.2,
    seed: int = 0,
    cache: Optional[LLMCache] = None,
    concurrency: int | None = None,
) -> list[str]:
    """Return responses for ``prompts`` using Gemini."""

    async def _call_single(prompt: str, sem: Optional[asyncio.Semaphore]) -> str:
        return await call_gemini_model_single_prompt(
            prompt,
            model=model,
            temperature=temperature,
            seed=seed,
            cache=cache,
            semaphore=sem,
        )

    return await _call_model(prompts, _call_single, concurrency)


async def call_anthropic_model_single_prompt(
    prompt: str,
    client: anthropic.AsyncAnthropic,
    *,
    model: LanguageModelName = LanguageModelName.CLAUDE_4_OPUS,
    temperature: float = 0.2,
    seed: int = 0,
    cache: Optional[LLMCache] = None,
    semaphore: Optional[asyncio.Semaphore] = None,
) -> str:
    """Return ``prompt`` response from Anthropic, optionally using ``cache``."""

    async def _create() -> str:
        response = await client.messages.create(
            model=model.value,
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
            max_tokens=1024,
        )
        return "".join(block.text for block in response.content).strip()  # type: ignore[attr-defined,union-attr]

    return await _call_model_cached(
        prompt,
        _create,
        model=model,
        temperature=temperature,
        seed=seed,
        cache=cache,
        semaphore=semaphore,
    )


async def call_anthropic_model(
    prompts: list[str],
    *,
    model: LanguageModelName = LanguageModelName.CLAUDE_4_OPUS,
    temperature: float = 0.2,
    seed: int = 0,
    cache: Optional[LLMCache] = None,
    concurrency: int | None = None,
) -> list[str]:
    """Return responses for ``prompts`` using Anthropic models."""
    client = anthropic.AsyncAnthropic()

    async def _call_single(prompt: str, sem: Optional[asyncio.Semaphore]) -> str:
        return await call_anthropic_model_single_prompt(
            prompt,
            client,
            model=model,
            temperature=temperature,
            seed=seed,
            cache=cache,
            semaphore=sem,
        )

    try:
        return await _call_model(prompts, _call_single, concurrency)
    finally:
        await client.close()


async def call_together_model_single_prompt(
    prompt: str,
    client: together.AsyncClient,
    *,
    model: LanguageModelName = LanguageModelName.LLAMA_3_70B,
    temperature: float = 0.2,
    seed: int = 0,
    cache: Optional[LLMCache] = None,
    semaphore: Optional[asyncio.Semaphore] = None,
) -> str:
    """Return ``prompt`` response from Together API, optionally using ``cache``."""

    async def _create() -> str:
        response = await client.chat.completions.create(
            model=model.value,
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
            seed=seed,
        )
        resp = cast(Any, response)
        return (resp.choices[0].message.content or "").strip()

    return await _call_model_cached(
        prompt,
        _create,
        model=model,
        temperature=temperature,
        seed=seed,
        cache=cache,
        semaphore=semaphore,
    )


async def call_together_model(
    prompts: list[str],
    *,
    model: LanguageModelName = LanguageModelName.LLAMA_3_70B,
    temperature: float = 0.2,
    seed: int = 0,
    cache: Optional[LLMCache] = None,
    concurrency: int | None = None,
) -> list[str]:
    """Return responses for ``prompts`` using Together-hosted models."""

    client = together.AsyncClient()

    async def _call_single(prompt: str, sem: Optional[asyncio.Semaphore]) -> str:
        return await call_together_model_single_prompt(
            prompt,
            client,
            model=model,
            temperature=temperature,
            seed=seed,
            cache=cache,
            semaphore=sem,
        )

    return await _call_model(prompts, _call_single, concurrency)


CALL_METHOD_BY_MODEL = {
    LanguageModelName.GEMINI_2_5_PRO: call_gemini_model,
    LanguageModelName.GEMINI_2_5_FLASH: call_gemini_model,
    LanguageModelName.GEMINI_2_0_FLASH: call_gemini_model,
    LanguageModelName.GPT_4O: call_openai_model,
    LanguageModelName.GPT_4_1: call_openai_model,
    LanguageModelName.O4_MINI: call_openai_model,
    LanguageModelName.O3: call_openai_model,
    LanguageModelName.O3_PRO: call_openai_model,
    LanguageModelName.CLAUDE_3_7_SONNET: call_anthropic_model,
    LanguageModelName.CLAUDE_3_5_SONNET: call_anthropic_model,
    LanguageModelName.CLAUDE_4_SONNET: call_anthropic_model,
    LanguageModelName.CLAUDE_4_OPUS: call_anthropic_model,
    LanguageModelName.DEEPSEEK_CODER_33B: call_together_model,
    LanguageModelName.LLAMA_3_70B: call_together_model,
    LanguageModelName.TEST_M: call_openai_model,
    LanguageModelName.TEST_M1: call_openai_model,
    LanguageModelName.TEST_M2: call_openai_model,
}
