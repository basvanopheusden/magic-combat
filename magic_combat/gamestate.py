from __future__ import annotations

"""Game state representation for the combat simulator."""

from dataclasses import dataclass, field
from typing import Dict, List

from .utils import check_non_negative

from .creature import CombatCreature


@dataclass
class PlayerState:
    """State for a single player."""

    life: int
    creatures: List[CombatCreature]
    poison: int = 0

    def __post_init__(self) -> None:
        check_non_negative(self.life, "life")
        check_non_negative(self.poison, "poison")


@dataclass
class GameState:
    """Overall game state tracking both players."""

    players: Dict[str, PlayerState] = field(default_factory=dict)


def has_player_lost(state: GameState, player: str) -> bool:
    """Return ``True`` if ``player`` has lost the game."""
    ps = state.players.get(player)
    if ps is None:
        return False
    return ps.life <= 0 or ps.poison >= 10
