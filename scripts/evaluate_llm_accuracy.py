import argparse
import asyncio
import json
from pathlib import Path
from typing import Any
from typing import List
from typing import Literal
from typing import Optional
from typing import cast
from typing import overload

from llms.create_llm_prompt import parse_block_assignments
from llms.llm import call_anthropic_model
from llms.llm import call_openai_model
from llms.llm_cache import LLMCache
from magic_combat.dataset import ReferenceAnswer
from magic_combat.exceptions import UnparsableLLMOutputError


@overload
async def evaluate_dataset(
    path: str,
    *,
    model: str = "gpt-4o",
    temperature: float = 0.2,
    seed: int = 0,
    concurrency: int = 20,
    cache: Optional[LLMCache] = None,
    return_item_results: Literal[False] = False,
) -> float:
    ...


@overload
async def evaluate_dataset(
    path: str,
    *,
    model: str = "gpt-4o",
    temperature: float = 0.2,
    seed: int = 0,
    concurrency: int = 20,
    cache: Optional[LLMCache] = None,
    return_item_results: Literal[True],
) -> list[bool]:
    ...


async def evaluate_dataset(
    path: str,
    *,
    model: str = "gpt-4o",
    temperature: float = 0.2,
    seed: int = 0,
    concurrency: int = 20,
    cache: Optional[LLMCache] = None,
    return_item_results: bool = False,
) -> float | list[bool]:
    """Return accuracy or per-item results for prompts in ``path``."""
    items: List[dict[str, Any]] = []
    with Path(path).open(encoding="utf8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            items.append(json.loads(line))

    prompts = [cast(str, item["prompt"]) for item in items]
    call = call_anthropic_model if model.startswith("claude") else call_openai_model
    responses = await call(
        prompts,
        model=model,
        temperature=temperature,
        seed=seed,
        cache=cache,
        concurrency=concurrency,
    )

    results: list[bool] = []
    for item, response in zip(items, responses):
        ref_data = cast(dict[str, str], item["answer"])
        ref = ReferenceAnswer.model_validate(ref_data)
        blk_names = ref.blocks.keys()
        atk_names = ref.blocks.values()
        try:
            parsed, _ = parse_block_assignments(response, blk_names, atk_names)
        except UnparsableLLMOutputError:
            results.append(False)
            continue
        pred = ReferenceAnswer(blocks=parsed)
        results.append(pred == ref)

    if return_item_results:
        return results

    correct = sum(results)
    return correct / len(results) if results else 0.0


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate LLM accuracy")
    parser.add_argument("dataset", help="Path to dataset JSONL")
    parser.add_argument("--model", default="gpt-4o", help="Model name")
    parser.add_argument(
        "--temperature",
        type=float,
        default=0.2,
        help="Sampling temperature",
    )
    parser.add_argument("--seed", type=int, default=0, help="Base random seed")
    parser.add_argument(
        "--concurrency",
        type=int,
        default=20,
        help="Concurrent requests",
    )
    parser.add_argument("--cache", help="Path to cache file")
    args = parser.parse_args()

    cache = LLMCache(args.cache) if args.cache else None
    accuracy = asyncio.run(
        evaluate_dataset(
            args.dataset,
            model=args.model,
            temperature=args.temperature,
            seed=args.seed,
            concurrency=args.concurrency,
            cache=cache,
        )
    )
    print(f"Accuracy: {accuracy:.3f}")


if __name__ == "__main__":
    main()
