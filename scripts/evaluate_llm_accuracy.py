import argparse
import asyncio
import json
from pathlib import Path
from typing import Any
from typing import List
from typing import Literal
from typing import Optional
from typing import Tuple
from typing import cast
from typing import overload

from llms.create_llm_prompt import parse_block_assignments
from llms.llm import LanguageModel
from llms.llm import LanguageModelName
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
) -> Tuple[List[bool], List[float]]:
    ...


async def evaluate_dataset(
    path: str,
    *,
    model: LanguageModelName = LanguageModelName.GPT_4O,
    seed: int = 0,
    concurrency: int = 20,
    cache: Optional[LLMCache] = None,
    return_item_results: bool = False,
    verbose: bool = False,
) -> float | Tuple[List[bool], List[float]] | List[bool]:
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
    llm = build_language_model(
        model, cache=cache, verbose=verbose, api_concurrency=concurrency
    )

    results: List[Tuple[bool, float]] = await asyncio.gather(
        *[
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
        ]
    )
    if return_item_results:
        return [r[0] for r in results], [r[1] for r in results]

    correct = sum(r[0] for r in results)
    return correct / len(results) if results else 0.0


def _encode_mapping(mapping: dict[str, str]) -> str:
    """Return a stable string key for a block assignment mapping."""
    return json.dumps(dict(sorted(mapping.items())), sort_keys=True)


async def evaluate_single_item(
    idx: int,
    item: dict[str, Any],
    *,
    model: LanguageModelName = LanguageModelName.GPT_4O,
    seed: int = 0,
    semaphore: asyncio.Semaphore,
    llm: LanguageModel,
    temperature: float = 1.0,
    max_attempts: int = 3,
) -> Tuple[bool, float]:
    """Return correctness and value lost for ``llm`` on ``item``."""
    prompt = cast(str, item["prompt"])
    ref_data = cast(dict[str, str], item["answer"])
    ref = ReferenceAnswer.model_validate(ref_data)
    blk_names = ref.blocks.keys()
    atk_names = ref.blocks.values()
    parsed = None
    response = ""
    for attempt in range(max_attempts):
        try:
            async with semaphore:
                print(
                    f"Calling model {model} for scenario {idx + 1} "
                    f"(attempt {attempt + 1})"
                )
                response = await llm.call(
                    prompt,
                    temperature=temperature,
                    seed=seed + attempt,
                )
                print(f"Response for scenario {idx + 1}, " f"attempt {attempt + 1}")

            parsed, _ = parse_block_assignments(response, blk_names, atk_names)
            break
        except UnparsableLLMOutputError:
            print(
                f"Unparseable response for model {model} on scenario "
                f"{idx + 1}; retrying..."
            )
            print(f"Response: {repr(response)}")
        except Exception as exc:  # pragma: no cover - network failure
            print(f"Error calling model {model}: {exc}")
            break
    if parsed is None:
        return False, 0.0
    pred = ReferenceAnswer(blocks=parsed)
    correct = pred == ref
    score_data = cast(dict[str, dict[str, float]], item.get("score", {}))
    value_lost = 0.0
    if score_data:
        pred_key = _encode_mapping(pred.blocks)
        opt_key = _encode_mapping(ref.blocks)
        opt_score = score_data.get(opt_key, {"aggregate": 0.0}).get("aggregate", 0.0)
        pred_score = score_data.get(
            pred_key,
            {"aggregate": min(v.get("aggregate", 0.0) for v in score_data.values())},
        ).get("aggregate", 0.0)
        value_lost = opt_score - pred_score
    return correct, value_lost


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
