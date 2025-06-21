"""Data model for creatures used during combat simulation."""

from dataclasses import dataclass, field
from typing import Set, List, Optional

Color = str  # e.g., "white", "blue", "black", "red", "green"


@dataclass
class CombatCreature:
    """Comprehensive combat creature model with common keyword abilities."""

    name: str
    power: int
    toughness: int
    controller: str

    # --- Combat Keywords ---
    flying: bool = False
    reach: bool = False
    menace: bool = False
    shadow: bool = False
    horsemanship: bool = False
    skulk: bool = False
    unblockable: bool = False
    vigilance: bool = False

    first_strike: bool = False
    double_strike: bool = False
    deathtouch: bool = False
    trample: bool = False
    lifelink: bool = False
    wither: bool = False
    infect: bool = False
    indestructible: bool = False

    # --- Stackable Keyword Abilities ---
    bushido: int = 0
    flanking: int = 0
    rampage: int = 0
    exalted_count: int = 0
    battle_cry_count: int = 0
    melee: bool = False
    training: bool = False

    # --- Special Protections ---
    protection_colors: Set[Color] = field(default_factory=set)

    # --- State ---
    tapped: bool = False
    attacking: bool = False
    blocking: Optional["CombatCreature"] = None
    blocked_by: List["CombatCreature"] = field(default_factory=list)
    damage_marked: int = 0

    # --- Counters ---
    _plus1_counters: int = field(default=0, repr=False)
    _minus1_counters: int = field(default=0, repr=False)

    def __post_init__(self) -> None:
        if self.power < 0:
            raise ValueError("power cannot be negative")
        if self.toughness <= 0:
            raise ValueError("toughness must be positive")
        if self._plus1_counters < 0 or self._minus1_counters < 0:
            raise ValueError("counters cannot be negative")
        if self.damage_marked < 0:
            raise ValueError("damage_marked cannot be negative")

    def has_protection_from(self, color: Color) -> bool:
        return color in self.protection_colors

    def effective_power(self) -> int:
        """Base power + +1/+1 counters - -1/-1 counters"""
        return max(0, self.power + self.plus1_counters - self.minus1_counters)

    def effective_toughness(self) -> int:
        return max(0, self.toughness + self.plus1_counters - self.minus1_counters)

    def is_destroyed_by_damage(self) -> bool:
        """Check if marked damage is lethal, accounting for indestructibility"""
        return not self.indestructible and self.damage_marked >= self.effective_toughness()

    def __str__(self) -> str:
        return f"{self.name} ({self.power}/{self.toughness})"

    # --- Counter properties with validation ---
    @property
    def plus1_counters(self) -> int:
        return self._plus1_counters

    @plus1_counters.setter
    def plus1_counters(self, value: int) -> None:
        if value < 0:
            raise ValueError("plus1 counters cannot be negative")
        self._plus1_counters = value

    @property
    def minus1_counters(self) -> int:
        return self._minus1_counters

    @minus1_counters.setter
    def minus1_counters(self, value: int) -> None:
        if value < 0:
            raise ValueError("minus1 counters cannot be negative")
        self._minus1_counters = value
