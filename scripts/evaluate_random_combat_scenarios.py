import asyncio
import copy
import random
from typing import List
from typing import Optional

import numpy as np
import openai

from magic_combat import CombatResult
from magic_combat import CombatSimulator
from magic_combat import build_value_map
from magic_combat import compute_card_statistics
from magic_combat import generate_random_scenario
from magic_combat import load_cards
from magic_combat.create_llm_prompt import create_llm_prompt
from magic_combat.create_llm_prompt import parse_block_assignments
from magic_combat.create_llm_prompt import summarize_creature
from magic_combat.creature import CombatCreature
from magic_combat.exceptions import UnparsableLLMOutputError
from magic_combat.gamestate import GameState
from magic_combat.gamestate import PlayerState
from magic_combat.llm_cache import LLMCache


def _simulate_assignment(
    attackers: List[CombatCreature],
    blockers: List[CombatCreature],
    assignment: List[Optional[int]],
    state: GameState,
    provoke_map: dict[CombatCreature, CombatCreature],
    mentor_map: dict[CombatCreature, CombatCreature],
) -> CombatResult:
    """Return the combat result for ``assignment``."""

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
    return sim.simulate()


def _value_for_assignment(
    attackers: List[CombatCreature],
    blockers: List[CombatCreature],
    assignment: List[Optional[int]],
    state: GameState,
    provoke_map: dict[CombatCreature, CombatCreature],
    mentor_map: dict[CombatCreature, CombatCreature],
) -> tuple[int, int, int, float]:
    result = _simulate_assignment(
        attackers,
        blockers,
        assignment,
        state,
        provoke_map,
        mentor_map,
    )
    score = result.score("A", "B")
    return (score[4], score[5], score[2], score[1])


def _format_value(value: tuple[float, float, float, float]) -> str:
    """Return a human-friendly string for ``value``."""

    life, poison, creature_diff, value_diff = value
    return (
        f"life lost {life}, poison {poison}, "
        f"creature diff {creature_diff}, value diff {value_diff}"
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
        unique_optimal=True,
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
        correct = sum(1 for b, a in parsed.items() if optimal.get(b) == a)
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
            llm_value = _value_for_assignment(
                attackers,
                blockers,
                llm_map,
                state,
                provoke_map,
                mentor_map,
            )
            llm_result = _simulate_assignment(
                attackers,
                blockers,
                llm_map,
                state,
                provoke_map,
                mentor_map,
            )
        except ValueError as exc:
            print(f"Error evaluating LLM assignment: {exc}")
            llm_value = (0, 0, 0, float("inf"))
            llm_result = CombatResult({}, [], {})
        if simple_map is not None:
            simple_value = _value_for_assignment(
                attackers,
                blockers,
                list(simple_map),
                state,
                provoke_map,
                mentor_map,
            )
            simple_result = _simulate_assignment(
                attackers,
                blockers,
                list(simple_map),
                state,
                provoke_map,
                mentor_map,
            )
        else:
            simple_value = None
            simple_result = None
        opt_result = _simulate_assignment(
            attackers,
            blockers,
            list(opt_map),
            state,
            provoke_map,
            mentor_map,
        )
        diff: tuple[float, float, float, float] = (
            llm_value[0] - opt_value[0],
            llm_value[1] - opt_value[1],
            llm_value[2] - opt_value[2],
            llm_value[3] - opt_value[3],
        )
        print(f"\n=== Scenario {idx + 1} ===")
        print("Initial game state:")
        all_creatures = state.players["A"].creatures + state.players["B"].creatures
        include_colors = any(
            c.fear or c.intimidate or c.protection_colors for c in all_creatures
        )
        _print_player_state(
            "Player A", state.players["A"], include_colors=include_colors
        )
        _print_player_state(
            "Player B", state.players["B"], include_colors=include_colors
        )
        print()
        print(f"Correct assignments: {correct}/{len(blockers)}")
        if simple_result is not None and simple_value is not None:
            print("\nSimple blocks:", simple)
            print(simple_result)
            print("Simple value:", _format_value(simple_value))
        print("\nOptimal blocks:", optimal)
        print(opt_result)
        print("Optimal value:", _format_value(opt_value))
        print("\nModel response:\n", llm_response)
        print("\nLLM blocks:", {b: parsed.get(b) for b in optimal})
        print(llm_result)
        print("LLM value:", _format_value(llm_value))
        print("Difference:", _format_value(diff))
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
