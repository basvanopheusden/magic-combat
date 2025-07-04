#!/usr/bin/env python
"""Generate a leaderboard for multiple LLM models."""

from __future__ import annotations

import argparse
import asyncio
import math
from pathlib import Path
from typing import Optional
from typing import Sequence

from tabulate import tabulate

from llms.llm import LanguageModelName
from llms.llm_cache import LLMCache
from scripts.evaluate_llm_accuracy import evaluate_dataset


def count_items(path: str) -> int:
    """Return the number of non-empty lines in ``path``."""
    n = 0
    with Path(path).open(encoding="utf8") as fh:
        for line in fh:
            if line.strip():
                n += 1
    return n


def standard_error(acc: float, n: int) -> float:
    """Return the standard error of ``acc`` for ``n`` items."""
    return math.sqrt(acc * (1.0 - acc) / n) if n else 0.0


def two_proportion_p_value(results1: Sequence[bool], results2: Sequence[bool]) -> float:
    """Return p-value from McNemar's test for two result lists."""
    n01 = 0
    n10 = 0
    for a, b in zip(results1, results2):
        if a and not b:
            n10 += 1
        elif b and not a:
            n01 += 1

    n = n01 + n10
    if n == 0:
        return 1.0
    k = min(n01, n10)
    prob = 0.0
    for i in range(k + 1):
        prob += math.comb(n, i) * 0.5**n
    p = min(1.0, 2 * prob)
    return p


def format_accuracy_table(
    results: dict[LanguageModelName, list[bool]],
    n: int,
) -> str:
    """Return a formatted accuracy table."""
    sortable = [
        (model, sum(vals) / len(vals) if vals else 0.0)
        for model, vals in results.items()
    ]
    rows = []
    for model, acc in sorted(sortable, key=lambda x: x[1], reverse=True):
        se = standard_error(acc, n)
        rows.append([model.value, f"{acc:.3f}", f"{se:.3f}"])
    return tabulate(rows, headers=["Model", "Accuracy", "StdErr"], tablefmt="github")


def format_pvalue_table(results: dict[LanguageModelName, list[bool]]) -> str:
    """Return a formatted pairwise p-values table."""
    models = list(results.keys())
    headers = [""] + [m.value for m in models]
    table_rows = []
    for m1 in models:
        row = [m1.value]
        for m2 in models:
            if m1 == m2:
                row.append("-")
            else:
                p = two_proportion_p_value(results[m1], results[m2])
                row.append(f"{p:.3f}")
        table_rows.append(row)
    return tabulate(table_rows, headers=headers, tablefmt="github")


async def evaluate_models(
    dataset: str,
    models: Sequence[LanguageModelName] | None = None,
    *,
    seed: int = 0,
    concurrency: int = 20,
    cache: Optional[LLMCache] = None,
) -> dict[LanguageModelName, list[bool]]:
    """Return per-item correctness for each model in ``models``."""
    if models is None:
        models = list(LanguageModelName)
    results: dict[LanguageModelName, list[bool]] = {}
    for model in models:
        # if model in {LanguageModelName.O3_PRO}:
        #     # Skip O3 Pro as it is not available through the chat API.
        #     continue
        item_results = await evaluate_dataset(
            dataset,
            model=model,
            seed=seed,
            concurrency=concurrency,
            cache=cache,
            return_item_results=True,
        )
        results[model] = item_results
    return results


async def run_leaderboard(args: argparse.Namespace) -> None:
    """Execute leaderboard generation using ``args``."""
    n = count_items(args.dataset)
    cache = LLMCache(args.cache) if args.cache else None
    results = await evaluate_models(
        args.dataset,
        seed=args.seed,
        concurrency=args.concurrency,
        cache=cache,
    )

    print(format_accuracy_table(results, n))

    print("\nPairwise p-values:")
    print(format_pvalue_table(results))


def main() -> None:
    parser = argparse.ArgumentParser(description="Create an LLM leaderboard")
    parser.add_argument("dataset", help="Path to dataset JSONL")
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--concurrency", type=int, default=20)
    parser.add_argument("--cache", help="Path to cache file")
    args = parser.parse_args()

    asyncio.run(run_leaderboard(args))


if __name__ == "__main__":
    main()
