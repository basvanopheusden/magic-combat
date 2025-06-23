import asyncio
from typing import List

from magic_combat import CombatResult, GameState, CombatCreature
from scripts.random_combat import summarize_creature
import openai

def create_llm_prompt(game_state: GameState, attackers: list[CombatCreature], blockers: list[CombatCreature]) -> str:
    """
    Create a prompt for an LLM to analyze combat results and game state.

    Args:
        combat_result (CombatResult): The result of the combat.
        game_state (GameState): The current state of the game.

    Returns:
        str: A formatted prompt for the LLM.
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

Please provide your analysis and the recommended blocking assignments in a markdown format. 
Each line should start with a bullet point, the name of the blocking creature, an arrow ("->"), and the name of the attacker it blocks.

Also include the outcome of the combat, using the bullet points:
- Life total of both players after combat
- Creatures destroyed by each player
- Poison counters on each player"""
    return prompt.strip()
