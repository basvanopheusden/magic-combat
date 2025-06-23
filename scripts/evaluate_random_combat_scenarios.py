import asyncio
from typing import List

import openai
from magic_combat import (
    load_cards,
    compute_card_statistics,
    decide_optimal_blocks,
    generate_random_scenario,
    build_value_map,
)
from magic_combat.create_llm_prompt import create_llm_prompt, parse_block_assignments


async def call_openai_model_single_prompt(prompt: str, client: openai.AsyncClient) -> str:
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
    client = openai.AsyncClient()
    try:
        tasks = [call_openai_model_single_prompt(prompt, client) for prompt in prompts]
        responses = await asyncio.gather(*tasks)
        return "\n\n".join(responses)
    finally:
        await client.close()


async def evaluate_random_scenarios(n: int, cards_path: str) -> None:

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
        print(prompt)

        try:
            llm_response = await call_openai_model([prompt])
        except Exception as exc:  # pragma: no cover - network failure
            print(f"Failed to query model: {exc}")
            continue

        print("\nModel response:\n", llm_response)
        parsed = parse_block_assignments(llm_response, blockers, attackers)
        correct = sum(1 for b, a in parsed.items() if optimal.get(b) == a)
        print(f"Correct assignments: {correct}/{len(blockers)}")


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Evaluate LLM blocking advice")
    parser.add_argument("-n", type=int, default=1, help="Number of scenarios")
    parser.add_argument(
        "--cards", default="tests/example_test_cards.json", help="Card data JSON"
    )
    args = parser.parse_args()

    asyncio.run(evaluate_random_scenarios(args.n, args.cards))


if __name__ == "__main__":
    main()
