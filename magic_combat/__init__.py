"""Core package for the Magic Combat simulator."""

from .creature import CombatCreature, Color
from .simulator import CombatResult, CombatSimulator

__all__ = [
    "CombatCreature",
    "Color",
    "CombatResult",
    "CombatSimulator",
]
