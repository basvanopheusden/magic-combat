"""Helpers for interacting with large language models."""

from typing import Iterable

from magic_combat.creature import CombatCreature
from magic_combat.gamestate import GameState
from magic_combat.rules_text import get_relevant_rules_text
from magic_combat.text_utils import summarize_creature


def create_llm_prompt(game_state: GameState) -> str:
    """Create a prompt instructing a language model to choose blocks.

    Args:
        game_state: The current game state with players ``A`` and ``B``.

    Returns:
        A formatted prompt for the model.
    """
    attackers = list(game_state.players["A"].creatures)
    blockers = list(game_state.players["B"].creatures)
    all_creatures = attackers + blockers
    include_colors = any(
        c.fear or c.intimidate or c.protection_colors for c in all_creatures
    )
    attacker_string = "\n".join(
        summarize_creature(attacker, include_colors=include_colors)
        for attacker in attackers
    )
    blocker_string = "\n".join(
        summarize_creature(blocker, include_colors=include_colors)
        for blocker in blockers
    )
    rules_text = get_relevant_rules_text(all_creatures)

    prompt = f"""You are a component of a Magic: The Gathering playing AI.
Your task is to decide the best blocks for the defending player
given a set of attackers, a set of candidate blockers, and the current
game state.

The current game state is as follows:
{game_state}

The attackers are:
{attacker_string}

The blockers are:
{blocker_string}

{rules_text}

Please analyze the combat situation and provide a detailed explanation
of the best blocking strategy for the defending player.
The criteria for the best blocking strategy are as follows:
1. Avoid losing the game.
2. Maximize the difference in total creature value destroyed (attacker minus
   defender). See ``##Creature value calculation`` below for how value is
   computed.
3. Maximize the difference in number of creatures destroyed.
4. Maximize the total mana value of creatures lost.
5. Minimize life lost.
6. Minimize poison counters gained.
Each criterion should only be considered after the previous one resulted in a tie.

##Creature value calculation
Creature value is the sum of effective power, effective toughness and half the
number of keyword abilities.
Count double strike twice so it contributes 1 full point. Subtract 0.5 if the
creature has defender.
Persist and undying creatures are special cases:
- A persist creature with a -1/-1 counter loses the persist ability's value.
- An undying creature with a +1/+1 counter loses the undying ability but keeps
  the +1/+1 counter.
Plus and minus counters modify power and toughness before calculating value and
cannot reduce a stat below 0.
Examples:
- A 2/2 Goblin with first strike has value 4.5.
- A 1/4 creature with defender has value 4.5 - 0.5 = 4.0.
- A 2/2 double strike creature has value 6.0.
- A 3/3 persist creature with one -1/-1 counter has value 4.0.
- A 3/3 undying creature with a +1/+1 counter has value 8.0.

Please provide your analysis in **exactly three** markdown sections.
The first section must be called "Analysis" and should contain a detailed explanation
of the scenario, relevant factors in your decision-making, and the rationale
for your blocking choices. Make sure to touch on any relevant abilities of the
creatures involved, such as flying, trample, or protection.
The second section must be called "Block Assignments". Each line in this section
should contain the name of the blocking creature, an arrow ("->"), and the name
of the attacker it blocks. If no blocks can be made, write ``None`` on a single
line below the heading. For example:
#Block Assignments
- Serra Angel -> Grizzly Bears
- Wall of Omens -> Llanowar Elves
Follow this format exactly with no additional commentary or formatting inside
the block assignments section.
Finally, add a markdown section called "Combat Outcome", which contains
the life total of both players after combat, any creatures that were
destroyed, and any poison counters gained.
Do so in a format like this:
#Combat Outcome
Player 1 Life: 20
Player 2 Life: 15
Player 1 Poison Counters: 0
Player 2 Poison Counters: 1
Player 2 Creatures Destroyed: None
Player 1 Creatures Destroyed: Grizzly Bears
"""
    return prompt.strip()


def parse_block_assignments(
    text: str,
    blockers: Iterable[CombatCreature] | Iterable[str],
    attackers: Iterable[CombatCreature] | Iterable[str],
) -> tuple[dict[str, str], bool]:
    """Parse a markdown list of ``blocker -> attacker`` pairs.

    Parameters
    ----------
    text:
        Response text from the language model.
    blockers:
        Blockers available for the defending player or just their names.
    attackers:
        Attackers declared this combat or just their names.

    Returns
    -------
    tuple[dict[str, str], bool]
        ``dict`` mapping blocker name to attacker name and a boolean flag
        indicating whether any illegal names or duplicate assignments were
        encountered in the text.
    """
    blocker_names = {b.name if isinstance(b, CombatCreature) else b for b in blockers}
    attacker_names = {a.name if isinstance(a, CombatCreature) else a for a in attackers}

    pairs: dict[str, str] = {}
    seen_assignment = False
    invalid = False
    for line in text.splitlines():
        clean = line.strip().lower()
        if "->" not in line and clean not in {"none", "no blocks"}:
            continue
        if clean in {"none", "no blocks"}:
            seen_assignment = True
            continue
        line = line.lstrip("*-• ").strip()
        before, _, after = line.partition("->")
        b = before.strip()
        a = after.strip()
        seen_assignment = True
        if b in blocker_names and a in attacker_names and b not in pairs:
            pairs[b] = a
        else:
            invalid = True
    if not seen_assignment:
        from magic_combat.exceptions import UnparsableLLMOutputError

        raise UnparsableLLMOutputError("No block assignments found")
    return pairs, invalid
