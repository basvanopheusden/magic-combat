import asyncio
import random
from typing import List
from typing import Optional

import numpy as np
import openai

from magic_combat import CombatResult
from magic_combat import IllegalBlockError
from magic_combat import build_value_map
from magic_combat import compute_card_statistics
from magic_combat import decide_simple_blocks
from magic_combat import generate_random_scenario
from magic_combat import load_cards
from magic_combat.block_utils import evaluate_block_assignment
from magic_combat.create_llm_prompt import create_llm_prompt
from magic_combat.create_llm_prompt import parse_block_assignments
from magic_combat.exceptions import UnparsableLLMOutputError
from magic_combat.gamestate import PlayerState
from magic_combat.limits import IterationCounter
from magic_combat.llm_cache import LLMCache
from magic_combat.text_utils import summarize_creature


def _format_value(value: tuple[float, float, float, float, int]) -> str:
    """Return a human-friendly string for ``value``."""

    life, poison, creature_diff, value_diff, mana_diff = value
    return (
        f"life lost {life}, poison {poison}, "
        f"creature diff {creature_diff}, value diff {value_diff}, "
        f"mana diff {mana_diff}"
    )


def _print_player_state(
    label: str, ps: PlayerState, *, include_colors: bool = False
) -> None:
    """Display the player's life total and creatures."""

    print(f"{label}: {ps.life} life, {ps.poison} poison")
    if ps.creatures:
        for creature in ps.creatures:
            summary = summarize_creature(creature, include_colors=include_colors)
            print(f"  {summary}")
    else:
        print("  no creatures")


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
        short = prompt.splitlines()[0][:30]
        print(f"Using cached LLM response for: {short}...")
        return cached

    response = await client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
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
    cards: list[dict[str, object]],
    stats: dict[str, object],
    values: dict[int, float],
    *,
    seed: int = 0,
    semaphore: asyncio.Semaphore,
    cache: Optional[LLMCache] = None,
) -> None:
    print("Generating scenario", idx + 1)
    (
        state,
        provoke_map,
        mentor_map,
        opt_map,
        simple_map,
    ) = next(
        generate_random_scenario(
            cards,
            values,
            stats,
            generated_cards=False,
            seed=seed + idx,
            unique_optimal=True,
        )
    )

    prompt = create_llm_prompt(state)
    attackers = list(state.players["A"].creatures)
    blockers = list(state.players["B"].creatures)

    attempts = 0
    max_attempts = 3
    while True:
        try:
            async with semaphore:
                print("Calling OpenAI model for scenario", idx + 1)
                llm_response = await call_openai_model(
                    [prompt],
                    seed=seed + idx,
                    model="o3-2025-04-16",
                    temperature=1.0,
                    cache=cache,
                )
                print("Model response received for scenario", idx + 1)
        except Exception as exc:  # pragma: no cover - network failure
            print(f"Failed to query model: {exc}")
            continue
        try:
            parsed, invalid = parse_block_assignments(llm_response, blockers, attackers)
        except UnparsableLLMOutputError:
            attempts += 1
            if attempts > max_attempts:
                print("Unparseable response; giving up")
                break
            print("Unparseable response; retrying...")
            continue

        if invalid:
            print("Response contained illegal block assignments")
        llm_map: list[Optional[int]] = []
        for blk in blockers:
            target = parsed.get(blk.name)
            idx_choice = None
            if target is not None:
                for i, atk in enumerate(attackers):
                    if atk.name == target:
                        idx_choice = i
                        break
            llm_map.append(idx_choice)
        try:
            llm_result, _ = evaluate_block_assignment(
                {
                    blockers[i]: attackers[choice]
                    for i, choice in enumerate(llm_map)
                    if choice is not None
                },
                state,
                IterationCounter(),
                provoke_map=provoke_map,
                mentor_map=mentor_map,
                damage_order=None,
            )
        except IllegalBlockError as exc:
            print(f"Error evaluating LLM assignment: {exc}")
            llm_result = CombatResult({}, [], {})
        # print(f"Correct assignments: {correct}/{len(blockers)}")
        print("\nModel response:\n", llm_response)
        # print("\nLLM blocks:", {b: parsed.get(b) for b in optimal})
        print(llm_result)
        iteration_counter = IterationCounter()

        simple_block_dict = {
            blockers[blk_idx]: attackers[choice]
            for blk_idx, choice in enumerate(simple_map or ())
            if choice is not None
        }
        simple_result, _ = evaluate_block_assignment(
            simple_block_dict,
            state,
            iteration_counter,
            provoke_map=provoke_map,
            mentor_map=mentor_map,
            damage_order=None,
        )
        optimal_block_dict = {
            blockers[blk_idx]: attackers[choice]
            for blk_idx, choice in enumerate(opt_map)
            if choice is not None
        }
        opt_result, _ = evaluate_block_assignment(
            optimal_block_dict,
            state,
            iteration_counter,
            provoke_map=provoke_map,
            mentor_map=mentor_map,
            damage_order=None,
        )

        print(f"\n=== Scenario {idx + 1} ===")
        print("Initial game state:")
        all_creatures = state.players["A"].creatures + state.players["B"].creatures
        include_colors = any(
            c.fear or c.intimidate or c.protection_colors for c in all_creatures
        )
        prov_map_display = (
            {a.name: b.name for a, b in provoke_map.items()} if provoke_map else None
        )
        mentor_map_display = (
            {m.name: t.name for m, t in mentor_map.items()} if mentor_map else None
        )
        _print_player_state(
            "Player A", state.players["A"], include_colors=include_colors
        )
        _print_player_state(
            "Player B", state.players["B"], include_colors=include_colors
        )
        if prov_map_display:
            print("Provoke targets:", prov_map_display)
        if mentor_map_display:
            print("Mentor targets:", mentor_map_display)
        for blocker, attacker in simple_block_dict.items():
            print(
                f"{blocker.name} ({blocker.power}/{blocker.toughness}) "
                f"blocks {attacker.name} ({attacker.power}/{attacker.toughness})"
            )
        print(simple_result)
        if simple_result is not None:
            print(simple_result.score("A", "B"))
        for blocker, attacker in optimal_block_dict.items():
            print(
                f"{blocker.name} ({blocker.power}/{blocker.toughness}) "
                f"blocks {attacker.name} ({attacker.power}/{attacker.toughness})"
            )
        print(opt_result)
        if opt_result is not None:
            print(opt_result.score("A", "B"))
        decide_simple_blocks(
            game_state=state,
            provoke_map=provoke_map,
            mentor_map=mentor_map,
        )
        break


async def evaluate_random_scenarios(
    n: int,
    cards_path: str,
    *,
    seed: int = 0,
    cache: Optional[LLMCache] = None,
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
                cache=cache,
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
    parser.add_argument(
        "--cache",
        help="Path to JSONL cache file for LLM responses",
    )
    args = parser.parse_args()

    cache = LLMCache(args.cache) if args.cache else None
    asyncio.run(
        evaluate_random_scenarios(args.n, args.cards, seed=args.seed, cache=cache)
    )


if __name__ == "__main__":
    main()
