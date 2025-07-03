"""Game state representation for the combat simulator."""

from __future__ import annotations

from dataclasses import dataclass
from dataclasses import field

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

    def reset_block_assignments(self) -> None:
        """Clear ``blocked_by`` and ``blocking`` fields on all combatants."""

        for attacker in self.players["A"].creatures:
            attacker.blocked_by.clear()
        for blocker in self.players["B"].creatures:
            blocker.blocking = None


def has_player_lost(state: GameState, player: str) -> bool:
    """Return ``True`` if ``player`` has lost the game."""
    ps = state.players.get(player)
    if ps is None:
        return False
    return ps.life <= 0 or ps.poison >= POISON_LOSS_THRESHOLD
