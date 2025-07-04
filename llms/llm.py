import asyncio
from typing import Awaitable
from typing import Callable
from typing import Optional

import anthropic
import openai
from google import genai
from google.genai import types as genai_types

from .llm_cache import LLMCache


async def _call_model_cached(
    prompt: str,
    call: Callable[[], Awaitable[str]],
    *,
    model: str,
    temperature: float,
    seed: int,
    cache: Optional[LLMCache],
    semaphore: Optional[asyncio.Semaphore],
) -> str:
    """Return cached result for ``call`` if available."""

    cached = cache.get(prompt, model, seed, temperature) if cache else None
    if cached is not None:
        short = prompt.splitlines()[0][:30]
        print(f"Using cached LLM response for: {short}...")
        return cached

    async def _run() -> str:
        return await call()

    if semaphore is None:
        text = await _run()
    else:
        async with semaphore:
            text = await _run()

    if cache is not None:
        cache.add(prompt, model, seed, temperature, text)
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
    model: str = "gpt-4o",
    temperature: float = 0.2,
    seed: int = 0,
    cache: Optional[LLMCache] = None,
    semaphore: Optional[asyncio.Semaphore] = None,
) -> str:
    """Return ``prompt`` response from OpenAI, optionally using ``cache``."""

    async def _call() -> str:
        response = await client.chat.completions.create(
            model=model,
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
    model: str = "gpt-4o",
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
    model: str = "gemini-pro",
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
            model=model, contents=prompt, config=generation_config
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
    model: str = "gemini-pro",
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
    model: str = "claude-3-sonnet-20240229",
    temperature: float = 0.2,
    seed: int = 0,
    cache: Optional[LLMCache] = None,
    semaphore: Optional[asyncio.Semaphore] = None,
) -> str:
    """Return ``prompt`` response from Anthropic, optionally using ``cache``."""

    async def _create() -> str:
        response = await client.messages.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
            max_tokens=1024,
        )
        return "".join(block.text for block in response.content).strip()

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
    model: str = "claude-3-sonnet-20240229",
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
