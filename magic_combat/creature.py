from dataclasses import dataclass

@dataclass
class CombatCreature:
    """Simplified representation of a creature during combat."""

    name: str
    power: int
    toughness: int
    first_strike: bool = False
    double_strike: bool = False

    def __str__(self) -> str:
        return f"{self.name} ({self.power}/{self.toughness})"
