"""Utility helpers used across the combat simulator."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .creature import CombatCreature
    from .gamestate import GameState, PlayerState


def check_non_negative(value: int, name: str) -> None:
    """Validate that ``value`` is not negative.

    Parameters
    ----------
    value:
        The integer value to validate.
    name:
        Human readable name of the value being validated.

    Raises
    ------
    ValueError
        If ``value`` is less than zero.
    """
    if value < 0:
        raise ValueError(f"{name} cannot be negative")


def check_positive(value: int, name: str) -> None:
    """Validate that ``value`` is strictly positive."""
    if value <= 0:
        raise ValueError(f"{name} must be positive")


def ensure_player_state(state: "GameState", player: str) -> "PlayerState":
    """Return existing :class:`PlayerState` for ``player`` or create one."""
    if state is None:
        raise ValueError("state cannot be None")

    # Import inside the function to avoid circular imports at module load time.
    from . import DEFAULT_STARTING_LIFE
    from .gamestate import PlayerState

    return state.players.setdefault(
        player, PlayerState(life=DEFAULT_STARTING_LIFE, creatures=[], poison=0)
    )


def _evaluate_mana_symbol(symbol: str, x_value: int) -> int:
    """Return the mana value contributed by a single symbol."""

    color_letters = {"W", "U", "B", "R", "G"}

    if symbol.isdigit():
        return int(symbol)
    if symbol in color_letters or symbol == "C":
        return 1
    if symbol == "X":
        return x_value
    if "/" in symbol and symbol.count("/") == 1:
        left, right = symbol.split("/")
        if left in color_letters and right in color_letters and left != right:
            return 1
        if left in color_letters and right == "P":
            return 1
    return 0


def calculate_mana_value(mana_cost: str, x_value: int) -> int:
    """
    Calculate the converted mana value (a.k.a. mana value) of a Magic: The
    Gathering card from a string written in curly-brace notation.

    Inputs
    ------
    mana_cost : str
        A string that may contain plain text and/or mana symbols. A mana symbol
        is **only** recognised when it is enclosed by exactly one opening "{" and
        one closing "}" (i.e. the substring between the braces does **not**
        contain another "{" or "}"). The content between the braces is
        case-sensitive and is considered valid iff it matches one of the
        patterns below:

            • Unsigned decimal integer            -> contributes its numeric value
              e.g. "{0}", "{1}", "{15}"

            • Single colour letter (W,U,B,R,G)    -> contributes 1
              e.g. "{W}"

            • "C" (colourless)                    -> contributes 1
              e.g. "{C}"

            • Hybrid: "<A>/<B>" where A and B are colour letters
              -> contributes 1                     e.g. "{W/U}", "{B/R}"

            • Phyrexian: "<A>/P" where A is a colour letter
              -> contributes 1                     e.g. "{G/P}"

            • "X"                                 -> contributes `x_value`

        Any other symbol (wrong case, unknown letters, nested braces such as
        "{{2}}", unmatched braces, etc.) is **ignored** and contributes 0.
        Characters that are not part of a recognised symbol—including whitespace
        or text outside of braces—are likewise ignored.

    x_value : int
        The integer value substituted for every "{X}" symbol. May be positive,
        zero or negative.

    Outputs
    -------
    int
        The sum of the contributions of all recognised symbols. The result can
        be negative if `x_value` is negative and at least one "{X}" symbol is
        present.

    Raises
    ------
    This function intentionally raises no exceptions; all malformed or unknown
    symbols are ignored rather than causing an error.

    Assumptions
    -----------
    • A valid mana symbol is delimited by a single pair of braces with no
      nested braces.
    • When parsing symbols, each "{" is matched with the next available "}" to
      form a potential symbol; overlapping interpretations are not considered.
    • Evaluation is strictly case-sensitive; lowercase letters never form a
      valid symbol.
    • Whitespace and non-symbol text have no effect on the computed mana
      value.
    """

    total_value = 0
    pattern = r"\{[^{}]+\}"
    for match in re.finditer(pattern, mana_cost):
        start = match.start()
        if mana_cost.rfind("{", 0, start) > mana_cost.rfind("}", 0, start):
            continue  # inside nested braces
        symbol = match.group()[1:-1]
        total_value += _evaluate_mana_symbol(symbol, x_value)

    return total_value


def _can_block(attacker: "CombatCreature", blocker: "CombatCreature") -> bool:
    """Return ``True`` if ``blocker`` can legally block ``attacker``."""

    # Import locally to avoid circular dependencies at module import time.
    from .creature import Color

    if attacker.unblockable:
        return False
    if attacker.flying and not (blocker.flying or blocker.reach):
        return False
    if attacker.shadow and not blocker.shadow:
        return False
    if attacker.horsemanship and not blocker.horsemanship:
        return False
    if attacker.skulk and blocker.effective_power() > attacker.effective_power():
        return False
    if attacker.daunt and blocker.effective_power() <= 2:
        return False
    if attacker.fear and not (blocker.artifact or Color.BLACK in blocker.colors):
        return False
    if attacker.intimidate and not (
        blocker.artifact or (attacker.colors & blocker.colors)
    ):
        return False
    if attacker.protection_colors & blocker.colors:
        return False
    return True


def apply_attacker_blocking_bonuses(attacker: "CombatCreature") -> None:
    """Apply bushido, rampage and flanking from ``attacker`` to blockers."""

    if not attacker.blocked_by:
        return

    if attacker.bushido:
        attacker.temp_power += attacker.bushido
        attacker.temp_toughness += attacker.bushido

    if attacker.rampage:
        extra = max(0, len(attacker.blocked_by) - 1)
        attacker.temp_power += attacker.rampage * extra
        attacker.temp_toughness += attacker.rampage * extra

    if attacker.flanking:
        for blocker in attacker.blocked_by:
            if blocker.flanking == 0:
                blocker.temp_power -= attacker.flanking
                blocker.temp_toughness -= attacker.flanking


def apply_blocker_bushido(blocker: "CombatCreature") -> None:
    """Grant bushido bonuses to ``blocker`` if it's blocking."""

    if blocker.blocking is not None and blocker.bushido:
        blocker.temp_power += blocker.bushido
        blocker.temp_toughness += blocker.bushido
