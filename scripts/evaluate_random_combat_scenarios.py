import asyncio
import random
from typing import List, Optional

import numpy as np

import openai
from magic_combat import (
    load_cards,
    compute_card_statistics,
    decide_optimal_blocks,
    generate_random_scenario,
    build_value_map,
)
from magic_combat.create_llm_prompt import (
    create_llm_prompt,
    parse_block_assignments,
)
from magic_combat.llm_cache import LLMCache


async def call_openai_model_single_prompt(
    prompt: str,
    client: openai.AsyncOpenAI,
    *,
    model: str = "gpt-4o",
    temperature: float = 0.2,
    seed: int = 0,
    cache: Optional[LLMCache] = None,
) -> str:
    """
    Call the OpenAI model with a single prompt and return the response.

    Args:
        prompt (str): The prompt to send to the OpenAI model.
        client (openai.AsyncOpenAI): The OpenAI client instance.

    Returns:
        str: The response from the OpenAI model.
    """
    cached = None
    if cache is not None:
        cached = cache.get(prompt, model, seed, temperature)
    if cached is not None:
        return cached

    response = await client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=1500,
        temperature=temperature,
    )
    text = response.choices[0].message.content.strip()
    if cache is not None:
        cache.add(prompt, model, seed, temperature, text)
    return text


async def call_openai_model(
    prompts: List[str],
    *,
    model: str = "gpt-4o",
    temperature: float = 0.2,
    seed: int = 0,
    cache: Optional[LLMCache] = None,
) -> str:
    client = openai.AsyncOpenAI()
    try:
        tasks = [
            call_openai_model_single_prompt(
                prompt,
                client,
                model=model,
                temperature=temperature,
                seed=seed,
                cache=cache,
            )
            for prompt in prompts
        ]
        responses = await asyncio.gather(*tasks)
        return "\n\n".join(responses)
    finally:
        await client.close()


async def evaluate_random_scenarios(
    n: int,
    cards_path: str,
    *,
    seed: int = 0,
) -> None:

    random.seed(seed)
    np.random.seed(seed)

    cards = load_cards(cards_path)
    stats = compute_card_statistics(cards)
    values = build_value_map(cards)

    for idx in range(n):
        (
            state,
            attackers,
            blockers,
            _,
            _,
        ) = generate_random_scenario(
            cards,
            values,
            stats,
            generated_cards=False,
            seed=seed + idx,
        )

        # Determine optimal blocks for comparison
        decide_optimal_blocks(attackers, blockers, game_state=state)
        optimal = {b.name: b.blocking.name if b.blocking else None for b in blockers}

        # Clear assignments for the LLM prompt
        for atk in attackers:
            atk.blocked_by.clear()
        for blk in blockers:
            blk.blocking = None

        prompt = create_llm_prompt(state, attackers, blockers)
        print(f"\n=== Scenario {idx+1} ===")
        # print(prompt)

        attempts = 0
        max_attempts = 3
        while True:
            try:
                llm_response = await call_openai_model([prompt], seed=seed + idx)
            except Exception as exc:  # pragma: no cover - network failure
                print(f"Failed to query model: {exc}")
                continue
            try:
                parsed, invalid = parse_block_assignments(
                    llm_response, blockers, attackers
                )
            except ValueError:
                attempts += 1
                if attempts > max_attempts:
                    print("Unparseable response; giving up")
                    break
                print("Unparseable response; retrying...")
                continue

            print("\nModel response:\n", llm_response)
            if invalid:
                print("Response contained illegal block assignments")
            correct = sum(1 for b, a in parsed.items() if optimal.get(b) == a)
            print(f"Correct assignments: {correct}/{len(blockers)}")
            break


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Evaluate LLM blocking advice")
    parser.add_argument("-n", type=int, default=1, help="Number of scenarios")
    parser.add_argument(
        "--cards",
        default="tests/data/example_test_cards.json",
        help="Card data JSON",
    )
    parser.add_argument(
        "--seed", type=int, default=0, help="Random seed controlling sampling"
    )
    args = parser.parse_args()

    asyncio.run(evaluate_random_scenarios(args.n, args.cards, seed=args.seed))


if __name__ == "__main__":
    main()
