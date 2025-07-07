"""Helpers for computing aggregate combat scores."""

from __future__ import annotations

from typing import Iterable
from typing import Tuple

AGGREGATE_WEIGHTS: Tuple[float, float, float, float, float, float] = (
    20.0,  # losing the game outweighs everything else
    1.0,  # creature value difference
    2.0,  # creature count difference
    1.0,  # mana value difference
    0.5,  # life total difference (up to ~20)
    2.0,  # poison counter difference (up to 10)
)


def compute_aggregate_score(
    score_vec: Iterable[float | int],
    best_score: Iterable[float | int],
    weights: Iterable[float] = AGGREGATE_WEIGHTS,
) -> float:
    """Return weighted aggregate difference between ``score_vec`` and ``best_score``."""

    diff = [
        w * abs(float(s) - float(b)) for s, b, w in zip(score_vec, best_score, weights)
    ]
    return -sum(diff)
