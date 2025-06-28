"""Game state representation for the combat simulator."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List

from . import POISON_LOSS_THRESHOLD
from .creature import CombatCreature
from .rules_text import _describe_abilities
from .utils import check_non_negative


@dataclass
class PlayerState:
    """State for a single player."""

    life: int
    creatures: List[CombatCreature]
    poison: int = 0

    def __post_init__(self) -> None:
        check_non_negative(self.life, "life")
        check_non_negative(self.poison, "poison")

    def __str__(self) -> str:
        """Return a readable summary of the player's state."""
        lines = [f"Life: {self.life}", f"Poison: {self.poison}"]
        if self.creatures:
            lines.append("Creatures:")
            for creature in self.creatures:
                lines.append(f"  - {creature} -- {_describe_abilities(creature)}")
        else:
            lines.append("Creatures: None")
        return "\n".join(lines)


@dataclass
class GameState:
    """Overall game state tracking both players."""

    players: Dict[str, PlayerState] = field(default_factory=dict)

    def __str__(self) -> str:
        """Return a readable summary of all players."""
        lines = []
        for label, state in self.players.items():
            lines.append(f"Player {label}:")
            for line in str(state).splitlines():
                lines.append(f"  {line}")
        return "\n".join(lines)


def has_player_lost(state: GameState, player: str) -> bool:
    """Return ``True`` if ``player`` has lost the game."""
    ps = state.players.get(player)
    if ps is None:
        return False
    return ps.life <= 0 or ps.poison >= POISON_LOSS_THRESHOLD
