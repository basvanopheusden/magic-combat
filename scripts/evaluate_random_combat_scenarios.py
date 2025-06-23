import asyncio
from typing import List

import openai


async def call_openai_model_single_prompt(prompt: str, client: openai.Client) -> str:
    """
    Call the OpenAI model with a single prompt and return the response.

    Args:
        prompt (str): The prompt to send to the OpenAI model.
        client (openai.Client): The OpenAI client instance.

    Returns:
        str: The response from the OpenAI model.
    """
    response = await client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=1500,
        temperature=0.2,
    )
    return response.choices[0].message.content.strip()


async def call_openai_model(prompts: List[str]) -> str:
    client = openai.Client()
    tasks = [call_openai_model_single_prompt(prompt, client) for prompt in prompts]
    responses = await asyncio.gather(*tasks)
    return "\n\n".join(responses)
