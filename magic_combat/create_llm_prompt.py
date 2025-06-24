"""Helpers for interacting with large language models."""

from typing import Iterable

from magic_combat import GameState, CombatCreature
from scripts.random_combat import summarize_creature

def create_llm_prompt(
    game_state: GameState,
    attackers: Iterable[CombatCreature],
    blockers: Iterable[CombatCreature],
) -> str:
    """Create a prompt instructing a language model to choose blocks.

    Args:
        game_state: The current game state.
        attackers: Creatures attacking this turn.
        blockers: Creatures available to block.

    Returns:
        A formatted prompt for the model.
    """
    attacker_string = '\n'.join(summarize_creature(attacker) for attacker in attackers)
    blocker_string = '\n'.join(summarize_creature(blocker) for blocker in blockers)

    prompt = f"""You are a component of a Magic: The Gathering playing AI.
Your task is to decide the best blocks for the defending player given a set of attackers, a set of candidate blockers, and the current game state.

The current game state is as follows:
{game_state}

The attackers are:
{attacker_string}

The blockers are:
{blocker_string}

Please analyze the combat situation and provide a detailed explanation of the best blocking strategy for the defending player.
The criteria for the best blocking strategy are as follows:
1. Avoid losing the game.
2. Maximize the difference in total creature value destroyed (attacker minus defender).
Value is defined as the sum of the power and toughness of the creatures plus 0.5 times the number of abilities they have.
Skip defender in this calculation (it's worth 0), and count double strike twice (it's worth 1 instead of 0.5).
3. Maximize the difference in number of creatures destroyed.
4. Maximize the total mana value of creatures lost.
5. Minimize life lost.
6. Minimize poison counters gained.
Each criterion should only be considered after the previous one resulted in a tie.

Please provide your analysis followed by **exactly two** markdown sections.
The first section must be called "Block Assignments". Each line in this section
should contain the name of the blocking creature, an arrow ("->"), and the name
of the attacker it blocks. If no blocks can be made, write ``None`` on a single
line below the heading. For example:
#Block Assignments
- Serra Angel -> Grizzly Bears
- Wall of Omens -> Llanowar Elves
Follow this format exactly with no additional commentary or formatting inside
the block assignments section.
Finally, add a markdown section called "Combat Outcome", which contains the life total of both players after combat, any creatures that were destroyed, and any poison counters gained.
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
        raise ValueError("No block assignments found")
    return pairs, invalid
