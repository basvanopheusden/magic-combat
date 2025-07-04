import asyncio
from typing import Optional

import anthropic
import openai
from google import genai
from google.genai import types as genai_types

from .llm_cache import LLMCache


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
