#!/usr/bin/env python
"""Generate a leaderboard for multiple LLM models."""

from __future__ import annotations

import argparse
import asyncio
import math
import random
from pathlib import Path
from typing import Optional
from typing import Sequence

import numpy as np
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


def format_leaderboard_table(
    results: dict[LanguageModelName, list[bool]],
    n: int,
    elo: dict[LanguageModelName, float],
    elo_err: dict[LanguageModelName, float] | None = None,
    value_loss: dict[LanguageModelName, float] | None = None,
) -> str:
    """Return a formatted leaderboard table with accuracy and Elo ratings."""
    rows: list[list[str]] = []
    for model, model_results in results.items():
        acc = sum(model_results) / n if n else 0.0
        se = standard_error(acc, n)
        elo_rating = elo[model]
        if elo_err is not None:
            rating_str = f"{elo_rating:.2f}±{elo_err[model]:.2f}"
        else:
            rating_str = f"{elo_rating:.2f}"
        loss = value_loss[model] if value_loss is not None else 0.0
        rows.append([model.value, f"{acc:.3f}±{se:.3f}", rating_str, f"{loss:.3f}"])

    def sort_key(row: list[str]) -> float:
        return float(row[2].split("±")[0])

    rows.sort(key=sort_key, reverse=True)
    return tabulate(
        rows,
        headers=["Model", "Accuracy", "Elo", "Value Lost"],
        tablefmt="github",
    )


def format_elo_table(
    elo: dict[LanguageModelName, float],
    elo_err: dict[LanguageModelName, float] | None = None,
) -> str:
    """Return a formatted Elo ratings table."""
    rows: list[list[str]] = []
    for model, rating in elo.items():
        if elo_err is not None:
            rating_str = f"{rating:.2f}±{elo_err[model]:.2f}"
        else:
            rating_str = f"{rating:.2f}"
        rows.append([model.value, rating_str])

    def sort_key(row: list[str]) -> float:
        return float(row[1].split("±")[0])

    rows.sort(key=sort_key, reverse=True)
    return tabulate(rows, headers=["Model", "Elo"], tablefmt="github")


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


def compute_elo_ratings(
    results: dict[LanguageModelName, list[bool]],
    *,
    base: float = 1000.0,
    k: float = 5.0,
) -> dict[LanguageModelName, float]:
    """Return Elo ratings computed from ``results``.

    ``results`` maps each model to a list of per-item correctness values.
    All lists must have equal length.
    """
    models = list(results.keys())
    n = len(next(iter(results.values()))) if results else 0
    ratings = {m: float(base) for m in models}

    for idx in range(n):
        for i, m1 in enumerate(models):
            for m2 in models[i + 1 :]:
                r1 = results[m1][idx]
                r2 = results[m2][idx]
                if r1 == r2:
                    s1 = s2 = 0.5
                elif r1:
                    s1, s2 = 1.0, 0.0
                else:
                    s1, s2 = 0.0, 1.0
                e1 = 1 / (1 + 10 ** ((ratings[m2] - ratings[m1]) / 400))
                e2 = 1 - e1
                ratings[m1] += k * (s1 - e1)
                ratings[m2] += k * (s2 - e2)

    return ratings


def compute_elo_error_bars(
    results: dict[LanguageModelName, list[bool]],
    *,
    base: float = 1000.0,
    k: float = 5.0,
    reps: int = 100,
    seed: int | None = None,
) -> dict[LanguageModelName, float]:
    """Return standard deviation of Elo ratings via bootstrap.

    ``reps`` determines the number of bootstrap shuffles. ``seed`` controls
    the randomization.
    """
    models = list(results.keys())
    n = len(next(iter(results.values()))) if results else 0
    rng = random.Random(seed)
    samples: dict[LanguageModelName, list[float]] = {m: [] for m in models}

    indices = list(range(n))
    for _ in range(reps):
        rng.shuffle(indices)
        shuffled = {m: [results[m][i] for i in indices] for m in models}
        ratings = compute_elo_ratings(shuffled, base=base, k=k)
        for m in models:
            samples[m].append(ratings[m])

    return {m: float(np.std(vals, ddof=1)) for m, vals in samples.items()}


async def evaluate_models(
    dataset: str,
    models: Sequence[LanguageModelName] | None = None,
    *,
    seed: int = 0,
    concurrency: int = 20,
    cache: Optional[LLMCache] = None,
) -> tuple[dict[LanguageModelName, list[bool]], dict[LanguageModelName, list[float]]]:
    """Return per-item correctness and value lost for each model."""
    if models is None:
        models = list(LanguageModelName)
    results: dict[LanguageModelName, list[bool]] = {}
    losses: dict[LanguageModelName, list[float]] = {}
    for model in models:
        item_results, item_losses = await evaluate_dataset(
            dataset,
            model=model,
            seed=seed,
            concurrency=concurrency,
            cache=cache,
            return_item_results=True,
        )
        results[model] = item_results
        losses[model] = item_losses
    return results, losses


async def run_leaderboard(args: argparse.Namespace) -> None:
    """Execute leaderboard generation using ``args``."""
    n = count_items(args.dataset)
    cache = LLMCache(args.cache) if args.cache else None
    results, losses = await evaluate_models(
        args.dataset,
        seed=args.seed,
        concurrency=args.concurrency,
        cache=cache,
    )

    elo = compute_elo_ratings(results)
    elo_err = compute_elo_error_bars(results, seed=args.seed)
    avg_loss = {m: sum(lst) / len(lst) if lst else 0.0 for m, lst in losses.items()}
    print(format_leaderboard_table(results, n, elo, elo_err, avg_loss))
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
