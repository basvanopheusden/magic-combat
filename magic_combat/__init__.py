"""Core package for the Magic Combat simulator."""

from .creature import CombatCreature
from .simulator import CombatResult, CombatSimulator

__all__ = [
    "CombatCreature",
    "CombatResult",
    "CombatSimulator",
]
