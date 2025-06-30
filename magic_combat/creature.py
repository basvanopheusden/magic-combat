"""Data model for creatures used during combat simulation."""

from dataclasses import dataclass
from dataclasses import field
from enum import Enum
from typing import Optional

from .utils import check_non_negative
from .utils import check_positive

# Keyword sets used for estimating combat value of a creature
_POSITIVE_KEYWORDS = [
    "flying",
    "reach",
    "menace",
    "fear",
    "shadow",
    "horsemanship",
    "skulk",
    "unblockable",
    "vigilance",
    "daunt",
    "first_strike",
    "double_strike",
    "deathtouch",
    "trample",
    "lifelink",
    "wither",
    "infect",
    "indestructible",
    "melee",
    "training",
    "battalion",
    "dethrone",
    "intimidate",
    "undying",
    "persist",
]
_STACKABLE_KEYWORDS = [
    "bushido",
    "flanking",
    "rampage",
    "exalted_count",
    "battle_cry_count",
    "frenzy",
    "afflict",
]


class Color(Enum):
    """Enumeration of Magic: The Gathering's five colors."""

    WHITE = "white"
    BLUE = "blue"
    BLACK = "black"
    RED = "red"
    GREEN = "green"


@dataclass
class CombatCreature:
    """Comprehensive combat creature model with common keyword abilities."""

    name: str
    power: int
    toughness: int
    controller: str
    mana_cost: str = ""
    oracle_text: str = ""
    colors: set[Color] = field(default_factory=set[Color])
    artifact: bool = False

    # --- Combat Keywords ---
    flying: bool = False
    reach: bool = False
    menace: bool = False
    fear: bool = False
    shadow: bool = False
    horsemanship: bool = False
    skulk: bool = False
    unblockable: bool = False
    daunt: bool = False
    vigilance: bool = False

    first_strike: bool = False
    double_strike: bool = False
    deathtouch: bool = False
    trample: bool = False
    lifelink: bool = False
    wither: bool = False
    infect: bool = False
    toxic: int = 0
    indestructible: bool = False
    damaged_by_deathtouch: bool = False

    # --- Stackable Keyword Abilities ---
    bushido: int = 0
    flanking: int = 0
    rampage: int = 0
    exalted_count: int = 0
    battle_cry_count: int = 0
    melee: bool = False
    training: bool = False
    mentor: bool = False
    frenzy: int = 0
    battalion: bool = False
    dethrone: bool = False
    undying: bool = False
    persist: bool = False
    intimidate: bool = False
    defender: bool = False
    afflict: int = 0
    provoke: bool = False

    # --- Special Protections ---
    protection_colors: set[Color] = field(default_factory=set[Color])

    # --- State ---
    tapped: bool = False
    attacking: bool = False
    blocking: Optional["CombatCreature"] = None
    blocked_by: list["CombatCreature"] = field(default_factory=list["CombatCreature"])
    damage_marked: int = 0

    # --- Counters ---
    _plus1_counters: int = field(default=0, repr=False)
    _minus1_counters: int = field(default=0, repr=False)

    # --- Temporary stat modifiers (until end of turn) ---
    temp_power: int = field(default=0, repr=False)
    temp_toughness: int = field(default=0, repr=False)

    # Allow use as dictionary keys by object identity
    __hash__ = object.__hash__

    def __post_init__(self) -> None:
        check_non_negative(self.power, "power")
        check_positive(self.toughness, "toughness")
        check_non_negative(self._plus1_counters, "plus1 counters")
        check_non_negative(self._minus1_counters, "minus1 counters")
        check_non_negative(self.damage_marked, "damage_marked")
        check_non_negative(self.frenzy, "frenzy")
        check_non_negative(self.toxic, "toxic")
        check_non_negative(self.afflict, "afflict")

    def has_protection_from(self, color: Color) -> bool:
        """Return ``True`` if this creature is protected from the color."""
        return color in self.protection_colors

    def effective_power(self) -> int:
        """Base power, counters, and temporary modifiers."""
        return max(
            0,
            self.power + self.plus1_counters - self.minus1_counters + self.temp_power,
        )

    def effective_toughness(self) -> int:
        """Base toughness, counters, and temporary modifiers."""
        return max(
            0,
            self.toughness
            + self.plus1_counters
            - self.minus1_counters
            + self.temp_toughness,
        )

    def is_destroyed_by_damage(self) -> bool:
        """Check if damage received is lethal, including deathtouch."""
        if self.indestructible:
            return False
        return (
            self.damage_marked >= self.effective_toughness()
            or self.damaged_by_deathtouch
        )

    def __str__(self) -> str:
        return f"{self.name} ({self.power}/{self.toughness})"

    def __repr__(self) -> str:
        cls = self.__class__.__name__
        return (
            f"{cls}(name={self.name!r}, power={self.power}, "
            f"toughness={self.toughness}, controller={self.controller!r})"
        )

    @property
    def mana_value(self) -> int:
        """Return the numeric mana value calculated from ``mana_cost``."""
        from .utils import calculate_mana_value

        return calculate_mana_value(self.mana_cost, 0)

    # --- Counter properties with validation ---
    @property
    def plus1_counters(self) -> int:
        """Number of +1/+1 counters on the creature."""
        return self._plus1_counters

    @plus1_counters.setter
    def plus1_counters(self, value: int) -> None:
        """Validate and set the +1/+1 counter total."""
        check_non_negative(value, "plus1 counters")
        self._plus1_counters = value

    @property
    def minus1_counters(self) -> int:
        """Number of -1/-1 counters on the creature."""
        return self._minus1_counters

    @minus1_counters.setter
    def minus1_counters(self, value: int) -> None:
        """Validate and set the -1/-1 counter total."""
        check_non_negative(value, "minus1 counters")
        self._minus1_counters = value

    def apply_counter_annihilation(self) -> None:
        """Remove matched +1/+1 and -1/-1 counters.

        CR 704.5q specifies that if a permanent has both a +1/+1 counter and
        a -1/-1 counter on it, a +1/+1 counter and a -1/-1 counter are removed
        from it until it has no counters of one of those kinds."""
        cancel = min(self.plus1_counters, self.minus1_counters)
        if cancel:
            self._plus1_counters -= cancel
            self._minus1_counters -= cancel

    def reset_temporary_bonuses(self) -> None:
        """Clear temporary power and toughness modifiers."""
        self.temp_power = 0
        self.temp_toughness = 0

    def value(self) -> float:
        """Heuristic combat value for tie-breaking.

        The value is computed as the sum of the creature's effective power and
        toughness plus half the number of keyword abilities it has. Double strike is
        counted twice. Creatures with the ``defender`` ability incur a ``-0.5``
        penalty. If a creature with persist has a -1/-1 counter it loses ``0.5`` and
        a creature with undying that has a +1/+1 counter loses ``2.5``.
        """

        positive = sum(1 for attr in _POSITIVE_KEYWORDS if getattr(self, attr, False))
        if self.double_strike:
            # Count double strike twice so it contributes 1 point instead of 0.5.
            positive += 1
        positive += sum(getattr(self, attr, 0) for attr in _STACKABLE_KEYWORDS)

        value = self.effective_power() + self.effective_toughness() + positive / 2
        if self.persist and self.minus1_counters:
            value -= 0.5
        if self.undying and self.plus1_counters:
            value -= 2.5
        if self.defender:
            value -= 0.5
        return value
