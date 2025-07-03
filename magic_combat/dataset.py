"""Helpers for creating LLM training datasets."""

from __future__ import annotations

from typing import Dict

from pydantic import BaseModel

from .gamestate import GameState


class ReferenceAnswer(BaseModel):
    """Mapping of blocking creature to attacker."""

    blocks: Dict[str, str]

    model_config = {
        "frozen": True,
    }

    @classmethod
    def from_state(cls, mapping: Dict[str, str], state: GameState) -> "ReferenceAnswer":
        """Validate ``mapping`` against ``state`` and return an instance."""

        attacker_names = {c.name for c in state.players["A"].creatures}
        blocker_names = {c.name for c in state.players["B"].creatures}

        if not set(mapping).issubset(blocker_names):
            raise ValueError("Unknown blocker name in mapping")
        if not set(mapping.values()).issubset(attacker_names):
            raise ValueError("Unknown attacker name in mapping")

        return cls(blocks=dict(mapping))
