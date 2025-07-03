"""Game state representation for the combat simulator."""

from __future__ import annotations

from dataclasses import dataclass
from dataclasses import field
from typing import Any

from magic_combat.constants import POISON_LOSS_THRESHOLD

from .creature import CombatCreature
from .text_utils import summarize_creature
from .utils import check_non_negative


@dataclass
class PlayerState:
    """State for a single player."""

    life: int
    creatures: list[CombatCreature]
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
                lines.append(f"  - {summarize_creature(creature)}")
        else:
            lines.append("Creatures: None")
        return "\n".join(lines)


@dataclass
class GameState:
    """Overall game state tracking both players."""

    players: dict[str, PlayerState] = field(default_factory=dict[str, PlayerState])

    def __str__(self) -> str:
        """Return a readable summary of all players."""
        lines: list[str] = []
        for label, state in self.players.items():
            lines.append(f"Player {label}:")
            for line in str(state).splitlines():
                lines.append(f"  {line}")
        return "\n".join(lines)

    def to_dict(self) -> dict[str, dict[str, int]]:
        """Return life totals and poison counters for this state."""
        life = {p: ps.life for p, ps in self.players.items()}
        poison = {p: ps.poison for p, ps in self.players.items()}
        return {"life": life, "poison": poison}

    @classmethod
    def from_dict(
        cls,
        data: dict[str, Any],
        attackers: list[CombatCreature],
        blockers: list[CombatCreature],
    ) -> "GameState":
        """Create a ``GameState`` from raw ``data`` and creature lists."""
        return cls(
            players={
                "A": PlayerState(
                    life=int(data["life"]["A"]),
                    poison=int(data["poison"]["A"]),
                    creatures=attackers,
                ),
                "B": PlayerState(
                    life=int(data["life"]["B"]),
                    poison=int(data["poison"]["B"]),
                    creatures=blockers,
                ),
            }
        )


def has_player_lost(state: GameState, player: str) -> bool:
    """Return ``True`` if ``player`` has lost the game."""
    ps = state.players.get(player)
    if ps is None:
        return False
    return ps.life <= 0 or ps.poison >= POISON_LOSS_THRESHOLD
