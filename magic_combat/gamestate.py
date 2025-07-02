"""Game state representation for the combat simulator."""

from __future__ import annotations

from dataclasses import dataclass
from dataclasses import field
from typing import Optional
from typing import Sequence

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

    def apply_block_assignment(
        self,
        assignment: Sequence[Optional[int]],
        attackers: Sequence[CombatCreature],
        blockers: Sequence[CombatCreature],
        *,
        verbose: bool = False,
    ) -> None:
        """Apply a blocking assignment to the game state.

        Args:
            assignment: Sequence mapping each blocker index to an attacker index
                or ``None`` if the blocker is not assigned.
            attackers: Ordered list of attacking creatures.
            blockers: Ordered list of blocking creatures.
            verbose: If ``True``, print the chosen assignments.
        """

        for blk_idx, choice in enumerate(assignment):
            if verbose:
                print(f"Blocker {blk_idx} assigned to attacker {choice}")
            if choice is not None:
                blk = blockers[blk_idx]
                atk = attackers[choice]
                blk.blocking = atk
                atk.blocked_by.append(blk)
                if verbose:
                    print(
                        f"{blk.name} ({blk.power}/{blk.toughness}) blocks "
                        f"{atk.name} ({atk.power}/{atk.toughness})"
                    )


def has_player_lost(state: GameState, player: str) -> bool:
    """Return ``True`` if ``player`` has lost the game."""
    ps = state.players.get(player)
    if ps is None:
        return False
    return ps.life <= 0 or ps.poison >= POISON_LOSS_THRESHOLD
