"""Utility helpers used across the combat simulator."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover - for type checking only
    from .creature import CombatCreature

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


def ensure_player_state(state, player: str):
    """Return existing :class:`PlayerState` for ``player`` or create one."""
    if state is None:
        raise ValueError("state cannot be None")

    # Import inside the function to avoid circular imports at module load time.
    from . import DEFAULT_STARTING_LIFE
    from .gamestate import PlayerState

    return state.players.setdefault(
        player, PlayerState(life=DEFAULT_STARTING_LIFE, creatures=[], poison=0)
    )


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
    color_letters = {"W", "U", "B", "R", "G"}
    processed_positions = set()
    i = 0
    while i < len(mana_cost):
        if mana_cost[i] == "{":
            j = i + 1
            brace_count = 1
            while j < len(mana_cost) and brace_count > 0:
                if mana_cost[j] == "{":
                    brace_count += 1
                elif mana_cost[j] == "}":
                    brace_count -= 1
                j += 1

            if brace_count == 0 and i not in processed_positions:
                symbol_content = mana_cost[i + 1 : j - 1]
                for pos in range(i, j):
                    processed_positions.add(pos)
                if "{" not in symbol_content and "}" not in symbol_content and symbol_content != "":
                    if symbol_content.isdigit():
                        total_value += int(symbol_content)
                    elif symbol_content in color_letters:
                        total_value += 1
                    elif symbol_content == "C":
                        total_value += 1
                    elif symbol_content == "X":
                        total_value += x_value
                    elif "/" in symbol_content and symbol_content.count("/") == 1:
                        parts = symbol_content.split("/")
                        if len(parts) == 2:
                            if parts[0] in color_letters and parts[1] in color_letters and parts[0] != parts[1]:
                                total_value += 1
                            elif parts[0] in color_letters and parts[1] == "P":
                                total_value += 1
        i += 1

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
