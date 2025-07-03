import asyncio
from typing import Optional

import openai

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
