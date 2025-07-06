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
from llms.llm import LanguageModelName, LanguageModel
from llms.llm import build_language_model
from llms.llm import get_default_temperature
from llms.llm_cache import LLMCache
from magic_combat.dataset import ReferenceAnswer
from magic_combat.exceptions import UnparsableLLMOutputError


@overload
async def evaluate_dataset(
    path: str,
    *,
    model: LanguageModelName = LanguageModelName.GPT_4O,
    seed: int = 0,
    concurrency: int = 20,
    cache: Optional[LLMCache] = None,
    return_item_results: Literal[False] = False,
    verbose: bool = False,
) -> float:
    ...


@overload
async def evaluate_dataset(
    path: str,
    *,
    model: LanguageModelName = LanguageModelName.GPT_4O,
    seed: int = 0,
    concurrency: int = 20,
    cache: Optional[LLMCache] = None,
    return_item_results: Literal[True],
    verbose: bool = False,
) -> List[bool]:
    ...


async def evaluate_single_item(
    idx: int,
    item: dict[str, Any],
    *,
    model: LanguageModelName = LanguageModelName.GPT_4O,
    seed: int = 0,
    semaphore: asyncio.Semaphore,
    llm: LanguageModel,
    temperature: float = 1.0,
    max_attempts=3
):
    prompt = cast(str, item["prompt"])
    ref_data = cast(dict[str, str], item["answer"])
    ref = ReferenceAnswer.model_validate(ref_data)
    blk_names = ref.blocks.keys()
    atk_names = ref.blocks.values()
    parsed = None
    for attempt in range(max_attempts):
        try:
            async with semaphore:
                print(f"Calling model {model} for scenario {idx + 1} (attempt {attempt + 1})")
                response = await llm.call(
                    prompt,
                    temperature=temperature,
                    seed=seed + attempt,
                )
                print(f"Response for scenario {idx + 1}, attempt {attempt + 1}")

            parsed, _ = parse_block_assignments(response, blk_names, atk_names)
            break
        except UnparsableLLMOutputError as exc:
            print(
                f"Unparseable response for model {model} on scenario {idx + 1}; retrying..."
            )
        except Exception as exc:  # pragma: no cover - network failure
            print(f"Error calling model {model}: {exc}")
            break
    if parsed is None:
        print(f"Failed to parse response for scenario {idx + 1} after {max_attempts} attempts")
        return False
    pred = ReferenceAnswer(blocks=parsed)
    return pred == ref

async def evaluate_dataset(
    path: str,
    *,
    model: LanguageModelName = LanguageModelName.GPT_4O,
    seed: int = 0,
    concurrency: int = 20,
    cache: Optional[LLMCache] = None,
    return_item_results: bool = False,
    verbose: bool = False,
) -> float | List[bool]:
    """Return accuracy or per-item results for prompts in ``path``."""
    items: List[dict[str, Any]] = []
    with Path(path).open(encoding="utf8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            items.append(json.loads(line))

    temperature = get_default_temperature(model)
    semaphore = asyncio.Semaphore(concurrency)
    llm = build_language_model(model, cache=cache, verbose=verbose)

    results: List[bool] = await asyncio.gather(*[
        evaluate_single_item(
            idx,
            item,
            model=model,
            seed=seed,
            semaphore=semaphore,
            llm=llm,
            temperature=temperature,
        )
        for idx, item in enumerate(items)
    ])


    if return_item_results:
        return results

    correct = sum(results)
    return correct / len(results) if results else 0.0


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate LLM accuracy")
    parser.add_argument("dataset", help="Path to dataset JSONL")
    parser.add_argument("--model", default="gpt-4o", help="Model name")
    parser.add_argument("--seed", type=int, default=0, help="Base random seed")
    parser.add_argument(
        "--concurrency",
        type=int,
        default=20,
        help="Concurrent requests",
    )
    parser.add_argument("--cache", help="Path to cache file")
    parser.add_argument("--verbose", action="store_true", help="Print prompts")
    args = parser.parse_args()

    cache = LLMCache(args.cache) if args.cache else None
    accuracy = asyncio.run(
        evaluate_dataset(
            args.dataset,
            model=LanguageModelName(args.model),
            seed=args.seed,
            concurrency=args.concurrency,
            cache=cache,
            verbose=args.verbose,
        )
    )
    print(f"Accuracy: {accuracy:.3f}")


if __name__ == "__main__":
    main()
