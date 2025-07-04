import asyncio
from enum import Enum
from typing import Optional

import anthropic
import openai
from google import genai
from google.genai import types as genai_types

from .llm_cache import LLMCache

class LanguageModelName(Enum):
    GEMINI_2_5_PRO = "gemini-2.5-pro"
    GEMINI_2_5_FLASH = "gemini-2.5-flash"
    GEMINI_2_0_PRO = "gemini-2.0-pro"
    GEMINI_2_0_FLASH = "gemini-2.0-flash"
    GPT_4O = "gpt-4o"
    GPT_4_1 = "gpt-4.1"
    O3 = "o3-2025-04-16"
    O3_PRO = "o3-pro-2025-06-10"
    CLAUDE_3_7_SONNET = "claude-3-sonnet-20240229"
    CLAUDE_3_7_OPUS = "claude-3-opus-20240229"
    CLAUDE_4_SONNET = "claude-3-sonnet-20240229"
    CLAUDE_4_OPUS = "claude-4-opus-20240229"

def get_default_temperature(model: LanguageModelName) -> float:
    """Return the default temperature for the given model."""
    if model == LanguageModelName.O3_PRO:
        return 1.0
    return 0.2

CALL_METHOD_BY_MODEL = {
    LanguageModelName.GEMINI_2_5_PRO: call_gemini_model,
    LanguageModelName.GEMINI_2_5_FLASH: call_gemini_model,
    LanguageModelName.GEMINI_2_0_PRO: call_gemini_model,
    LanguageModelName.GEMINI_2_0_FLASH: call_gemini_model,
    LanguageModelName.GPT_4O: call_openai_model,
    LanguageModelName.GPT_4_1: call_openai_model,
    LanguageModelName.O3: call_openai_model,
    LanguageModelName.O3_PRO: call_openai_model,
    LanguageModelName.CLAUDE_3_7_SONNET: call_anthropic_model,
    LanguageModelName.CLAUDE_3_7_OPUS: call_anthropic_model,
    LanguageModelName.CLAUDE_4_SONNET: call_anthropic_model,
    LanguageModelName.CLAUDE_4_OPUS: call_anthropic_model,
}


async def call_openai_model_single_prompt(
    prompt: str,
    client: openai.AsyncOpenAI,
    *,
    model: str = "gpt-4o",
    temperature: float = 0.2,
    seed: int = 0,
    cache: Optional[LLMCache] = None,
    semaphore: Optional[asyncio.Semaphore] = None,
) -> str:
    """Return ``prompt`` response from OpenAI, optionally using ``cache``."""
    cached = None
    if cache is not None:
        cached = cache.get(prompt, model, seed, temperature)
    if cached is not None:
        short = prompt.splitlines()[0][:30]
        print(f"Using cached LLM response for: {short}...")
        return cached

    if semaphore is None:
        response = await client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
        )
    else:
        async with semaphore:
            response = await client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
            )

    text = (response.choices[0].message.content or "").strip()
    if cache is not None:
        cache.add(prompt, model, seed, temperature, text)
    return text


async def call_openai_model(
    prompts: list[str],
    *,
    model: str = "gpt-4o",
    temperature: float = 0.2,
    seed: int = 0,
    cache: Optional[LLMCache] = None,
    concurrency: int | None = None,
) -> list[str]:
    """Return responses for ``prompts``."""
    client = openai.AsyncOpenAI()
    try:
        semaphore = asyncio.Semaphore(concurrency) if concurrency else None
        tasks = [
            call_openai_model_single_prompt(
                prompt,
                client,
                model=model,
                temperature=temperature,
                seed=seed,
                cache=cache,
                semaphore=semaphore,
            )
            for prompt in prompts
        ]
        responses = await asyncio.gather(*tasks)
        return list(responses)
    finally:
        await client.close()


async def call_gemini_model_single_prompt(
    prompt: str,
    *,
    model: str = "gemini-pro",
    temperature: float = 0.2,
    seed: int = 0,
    cache: Optional[LLMCache] = None,
    semaphore: Optional[asyncio.Semaphore] = None,
) -> str:
    """Return ``prompt`` response from Gemini, optionally using ``cache``."""
    cached = None
    if cache is not None:
        cached = cache.get(prompt, model, seed, temperature)
    if cached is not None:
        short = prompt.splitlines()[0][:30]
        print(f"Using cached LLM response for: {short}...")
        return cached

    client = genai.Client()
    generation_config = genai_types.GenerateContentConfig(
        temperature=temperature, seed=seed
    )

    async def _call() -> str:
        response = await client.aio.models.generate_content(
            model=model, contents=prompt, config=generation_config
        )
        return (response.text or "").strip()

    if semaphore is None:
        text = await _call()
    else:
        async with semaphore:
            text = await _call()
    if cache is not None:
        cache.add(prompt, model, seed, temperature, text)
    return text


async def call_gemini_model(
    prompts: list[str],
    *,
    model: str = "gemini-pro",
    temperature: float = 0.2,
    seed: int = 0,
    cache: Optional[LLMCache] = None,
    concurrency: int | None = None,
) -> list[str]:
    """Return responses for ``prompts`` using Gemini."""
    semaphore = asyncio.Semaphore(concurrency) if concurrency else None
    tasks = [
        call_gemini_model_single_prompt(
            prompt,
            model=model,
            temperature=temperature,
            seed=seed,
            cache=cache,
            semaphore=semaphore,
        )
        for prompt in prompts
    ]
    responses = await asyncio.gather(*tasks)
    return list(responses)


async def call_anthropic_model_single_prompt(
    prompt: str,
    client: anthropic.AsyncAnthropic,
    *,
    model: str = "claude-3-sonnet-20240229",
    temperature: float = 0.2,
    seed: int = 0,
    cache: Optional[LLMCache] = None,
    semaphore: Optional[asyncio.Semaphore] = None,
) -> str:
    """Return ``prompt`` response from Anthropic, optionally using ``cache``."""
    cached = None
    if cache is not None:
        cached = cache.get(prompt, model, seed, temperature)
    if cached is not None:
        short = prompt.splitlines()[0][:30]
        print(f"Using cached LLM response for: {short}...")
        return cached

    async def _create():
        return await client.messages.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
            max_tokens=1024,
        )

    if semaphore is None:
        response = await _create()
    else:
        async with semaphore:
            response = await _create()

    text = "".join(block.text for block in response.content).strip()
    if cache is not None:
        cache.add(prompt, model, seed, temperature, text)
    return text


async def call_anthropic_model(
    prompts: list[str],
    *,
    model: str = "claude-3-sonnet-20240229",
    temperature: float = 0.2,
    seed: int = 0,
    cache: Optional[LLMCache] = None,
    concurrency: int | None = None,
) -> list[str]:
    """Return responses for ``prompts`` using Anthropic models."""
    client = anthropic.AsyncAnthropic()
    try:
        semaphore = asyncio.Semaphore(concurrency) if concurrency else None
        tasks = [
            call_anthropic_model_single_prompt(
                prompt,
                client,
                model=model,
                temperature=temperature,
                seed=seed,
                cache=cache,
                semaphore=semaphore,
            )
            for prompt in prompts
        ]
        responses = await asyncio.gather(*tasks)
        return list(responses)
    finally:
        await client.close()
