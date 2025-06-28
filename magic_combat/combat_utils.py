from __future__ import annotations

from typing import Dict
from typing import Optional

from .creature import CombatCreature
from .gamestate import GameState
from .utils import ensure_player_state

__all__ = ["damage_creature", "damage_player"]


def damage_creature(
    creature: CombatCreature, amount: int, source: CombatCreature
) -> None:
    """Apply combat damage to ``creature``.

    CR 702.90a states that wither damage is dealt in the form of -1/-1 counters,
    while CR 702.90b extends this to infect. Deathtouch (CR 702.2b) marks the
    damaged creature for destruction if any damage is dealt.
    """
    if source.wither or source.infect:
        creature.minus1_counters += amount
    else:
        creature.damage_marked += amount
    if source.deathtouch and amount > 0:
        creature.damaged_by_deathtouch = True


def damage_player(
    player: str,
    amount: int,
    source: CombatCreature,
    *,
    damage_to_players: Dict[str, int],
    poison_counters: Dict[str, int],
    game_state: Optional[GameState] = None,
) -> None:
    """Deal combat damage from ``source`` to ``player``.

    Per CR 702.90b, damage from a source with infect gives that player poison
    counters instead of causing life loss. Toxic adds additional poison counters
    after damage is dealt.
    """
    if source.infect:
        poison_counters[player] = poison_counters.get(player, 0) + amount
        if game_state is not None:
            ps = ensure_player_state(game_state, player)
            ps.poison += amount
    else:
        damage_to_players[player] = damage_to_players.get(player, 0) + amount
        if game_state is not None:
            ps = ensure_player_state(game_state, player)
            ps.life -= amount
    if source.toxic:
        poison_counters[player] = poison_counters.get(player, 0) + source.toxic
        if game_state is not None:
            ps = ensure_player_state(game_state, player)
            ps.poison += source.toxic
