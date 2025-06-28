import asyncio
import copy
import random
from typing import List
from typing import Optional

import numpy as np
import openai

from magic_combat import CombatSimulator
from magic_combat import build_value_map
from magic_combat import compute_card_statistics
from magic_combat import generate_random_scenario
from magic_combat import load_cards
from magic_combat.create_llm_prompt import create_llm_prompt
from magic_combat.create_llm_prompt import parse_block_assignments
from magic_combat.damage import score_combat_result
from magic_combat.llm_cache import LLMCache


def _value_for_assignment(
    attackers: List,
    blockers: List,
    assignment: List[Optional[int]],
    state,
    provoke_map: dict,
    mentor_map: dict,
) -> tuple[int, int, int, float]:
    atk = copy.deepcopy(attackers)
    blk = copy.deepcopy(blockers)
    state_copy = copy.deepcopy(state)
    for idx, choice in enumerate(assignment):
        if choice is not None:
            blk[idx].blocking = atk[choice]
            atk[choice].blocked_by.append(blk[idx])
    sim = CombatSimulator(
        atk,
        blk,
        game_state=state_copy,
        provoke_map=provoke_map,
        mentor_map=mentor_map,
    )
    result = sim.simulate()
    score = score_combat_result(result, "A", "B")
    return (score[4], score[5], score[2], score[1])


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
    raw = response.choices[0].message.content or ""
    text = raw.strip()
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


async def _evaluate_single_scenario(
    idx: int,
    cards: list,
    stats,
    values,
    *,
    seed: int = 0,
    semaphore: asyncio.Semaphore,
) -> None:
    (
        state,
        attackers,
        blockers,
        provoke_map,
        mentor_map,
        opt_map,
        simple_map,
        opt_value,
    ) = generate_random_scenario(
        cards,
        values,
        stats,
        generated_cards=False,
        seed=seed + idx,
    )

    optimal = {
        blk.name: (attackers[choice].name if choice is not None else None)
        for blk, choice in zip(blockers, opt_map)
    }
    simple = {
        blk.name: (attackers[choice].name if choice is not None else None)
        for blk, choice in zip(blockers, simple_map or [])
    }

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
            async with semaphore:
                llm_response = await call_openai_model([prompt], seed=seed + idx)
        except Exception as exc:  # pragma: no cover - network failure
            print(f"Failed to query model: {exc}")
            continue
        try:
            parsed, invalid = parse_block_assignments(llm_response, blockers, attackers)
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
        llm_map = []
        for blk in blockers:
            target = parsed.get(blk.name)
            idx_choice = None
            if target is not None:
                for i, atk in enumerate(attackers):
                    if atk.name == target:
                        idx_choice = i
                        break
            llm_map.append(idx_choice)
        llm_value = _value_for_assignment(
            attackers,
            blockers,
            llm_map,
            state,
            provoke_map,
            mentor_map,
        )
        simple_value = (
            _value_for_assignment(
                attackers,
                blockers,
                list(simple_map),
                state,
                provoke_map,
                mentor_map,
            )
            if simple_map is not None
            else None
        )
        diff = tuple(lv - ov for lv, ov in zip(llm_value, opt_value))
        print(f"Correct assignments: {correct}/{len(blockers)}")
        print("Simple blocks:", simple)
        print("Optimal blocks:", optimal)
        print("LLM blocks:", {b: parsed.get(b) for b in optimal})
        if simple_value is not None:
            print("Simple value:", simple_value)
        print("Optimal value:", opt_value)
        print("LLM value:", llm_value)
        print("Difference:", diff)
        break


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

    semaphore = asyncio.Semaphore(50)
    tasks = [
        asyncio.create_task(
            _evaluate_single_scenario(
                idx,
                cards,
                stats,
                values,
                seed=seed,
                semaphore=semaphore,
            )
        )
        for idx in range(n)
    ]
    await asyncio.gather(*tasks)


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
