"""Generate a dataset of LLM prompts and reference answers."""

from __future__ import annotations

import argparse
import json
import random
from pathlib import Path
from typing import cast

import numpy as np

from llms.create_llm_prompt import create_llm_prompt
from magic_combat import IllegalBlockError
from magic_combat import build_value_map
from magic_combat import compute_card_statistics
from magic_combat import generate_random_scenario
from magic_combat import load_cards
from magic_combat.block_utils import evaluate_block_assignment
from magic_combat.blocking_ai import (
    _get_all_assignments,  # pyright: ignore[reportPrivateUsage]
)
from magic_combat.blocking_ai import (
    _get_block_options,  # pyright: ignore[reportPrivateUsage]
)
from magic_combat.dataset import ReferenceAnswer
from magic_combat.limits import IterationCounter
from magic_combat.scoring import compute_aggregate_score
from magic_combat.text_utils import summarize_creature


def _dump(path: Path, data: list[dict[str, object]]) -> None:
    """Write ``data`` as JSONL to ``path``."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        for item in data:
            json.dump(item, fh)
            fh.write("\n")


def _encode_mapping(mapping: dict[str, str]) -> str:
    """Return a stable string key for a block assignment mapping."""
    return json.dumps(dict(sorted(mapping.items())), sort_keys=True)


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
    scenario_generator = generate_random_scenario(
        cards,
        values,
        stats,
        seed=args.seed,
        max_iterations=int(1e4),
        generated_cards=False,
    )

    items: list[dict[str, object]] = []
    for i in range(args.n):
        state, provoke_map, mentor_map, opt_map, _ = next(scenario_generator)
        prompt = create_llm_prompt(state)
        attackers = list(state.players["A"].creatures)
        blockers = list(state.players["B"].creatures)
        mapping = {
            blockers[idx].name: attackers[a_idx].name
            for idx, a_idx in enumerate(opt_map)
            if a_idx is not None
        }
        answer = ReferenceAnswer.from_state(mapping, state)

        score_map: dict[str, dict[str, object]] = {}
        options = _get_block_options(state, provoke_map)
        assignments = _get_all_assignments(options)
        best_score: tuple[int, float, int, int, int, int] | None = None

        for assignment in assignments:
            block_dict = {
                blockers[idx]: attackers[a]
                for idx, a in enumerate(assignment)
                if a is not None
            }
            try:
                result, _ = evaluate_block_assignment(
                    block_dict,
                    state,
                    IterationCounter(int(1e4)),
                    provoke_map=provoke_map,
                    mentor_map=mentor_map,
                )
            except IllegalBlockError:
                # Skip illegal assignments
                continue
            if result is None:
                continue
            score_vec = result.score("A", "B")
            if best_score is None or score_vec < best_score:
                best_score = score_vec
            name_map = {
                blockers[idx].name: attackers[a].name
                for idx, a in enumerate(assignment)
                if a is not None
            }
            key = _encode_mapping(name_map)
            score_map[key] = {
                "outcome": {
                    "lost": score_vec[0],
                    "value_diff": score_vec[1],
                    "count_diff": score_vec[2],
                    "mana_diff": score_vec[3],
                    "life_diff": score_vec[4],
                    "poison_diff": score_vec[5],
                }
            }

        if best_score is not None:
            for data in score_map.values():
                sc = cast(dict[str, float | int], data["outcome"])
                score_vec = (
                    int(sc["lost"]),
                    float(sc["value_diff"]),
                    int(sc["count_diff"]),
                    int(sc["mana_diff"]),
                    int(sc["life_diff"]),
                    int(sc["poison_diff"]),
                )
                data["aggregate"] = compute_aggregate_score(score_vec, best_score)

        items.append(
            {
                "prompt": prompt,
                "answer": answer.model_dump(),
                "score": score_map,
            }
        )
        scenario_info = (
            f"Generated scenario {i + 1}/{args.n} with "
            f"{len(attackers)} attackers and {len(blockers)} blockers"
        )
        print(scenario_info)
        for attacker in attackers:
            print(summarize_creature(attacker, include_colors=True))
        for blocker in blockers:
            print(summarize_creature(blocker, include_colors=True))
        for blk_name, atk_name in mapping.items():
            print(f"  {blk_name} -> {atk_name}")

    _dump(Path(args.output), items)


if __name__ == "__main__":
    main()
