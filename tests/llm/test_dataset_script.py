import json
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

from magic_combat.creature import CombatCreature
from magic_combat.dataset import ReferenceAnswer
from magic_combat.gamestate import GameState
from magic_combat.gamestate import PlayerState
from scripts import create_dataset

DATA_PATH = Path(__file__).resolve().parents[1] / "data" / "example_test_cards.json"


def test_reference_answer_validation() -> None:
    atk = CombatCreature("Att", 2, 2, "A")
    blk = CombatCreature("Blk", 1, 3, "B")
    state = GameState(
        players={"A": PlayerState(20, [atk]), "B": PlayerState(20, [blk])}
    )
    mapping = {blk.name: atk.name}
    ans = ReferenceAnswer.from_state(mapping, state)
    assert ans.blocks == mapping
    with pytest.raises(ValueError):
        ReferenceAnswer.from_state({"Foo": atk.name}, state)
    with pytest.raises(ValueError):
        ReferenceAnswer.from_state({blk.name: "Bar"}, state)


def test_create_dataset_script(tmp_path: Path) -> None:
    out = tmp_path / "data.jsonl"
    with patch.object(
        sys,
        "argv",
        [
            "create_dataset.py",
            "-n",
            "1",
            "--cards",
            str(DATA_PATH),
            "--output",
            str(out),
            "--seed",
            "123",
        ],
    ):
        create_dataset.main()
    lines = out.read_text().splitlines()
    assert len(lines) == 1
    entry = json.loads(lines[0])
    assert isinstance(entry.get("prompt"), str)
    ReferenceAnswer.model_validate(entry.get("answer"))
