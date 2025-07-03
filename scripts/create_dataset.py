"""Generate a dataset of LLM prompts and reference answers."""

from __future__ import annotations

import argparse
import json
import random
from pathlib import Path

import numpy as np

from magic_combat import build_value_map
from magic_combat import compute_card_statistics
from magic_combat import create_llm_prompt
from magic_combat import generate_random_scenario
from magic_combat import load_cards
from magic_combat.dataset import ReferenceAnswer


def _dump(path: Path, data: list[dict[str, object]]) -> None:
    """Write ``data`` as JSONL to ``path``."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        for item in data:
            json.dump(item, fh)
            fh.write("\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="Create training dataset")
    parser.add_argument("-n", type=int, default=1, help="Number of scenarios")
    parser.add_argument(
        "--cards", default="tests/data/example_test_cards.json", help="Card data JSON"
    )
    parser.add_argument("--seed", type=int, default=0, help="Base random seed")
    parser.add_argument("--output", required=True, help="Output JSONL file")
    args = parser.parse_args()

    random.seed(args.seed)
    np.random.seed(args.seed)

    cards = load_cards(args.cards)
    stats = compute_card_statistics(cards)
    values = build_value_map(cards)

    items: list[dict[str, object]] = []
    for i in range(args.n):
        state, _, _, opt_map, _ = generate_random_scenario(
            cards, values, stats, seed=args.seed + i
        )
        prompt = create_llm_prompt(state)
        attackers = list(state.players["A"].creatures)
        blockers = list(state.players["B"].creatures)
        mapping = {
            blockers[idx].name: attackers[a_idx].name
            for idx, a_idx in enumerate(opt_map)
            if a_idx is not None
        }
        answer = ReferenceAnswer.from_state(mapping, state)
        items.append({"prompt": prompt, "answer": answer.model_dump()})

    _dump(Path(args.output), items)


if __name__ == "__main__":
    main()
