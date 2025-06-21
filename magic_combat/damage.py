"""Damage assignment ordering strategies."""

from typing import List

from .creature import CombatCreature


class DamageAssignmentStrategy:
    """Base strategy for ordering blockers when assigning combat damage."""

    def order_blockers(
        self, attacker: CombatCreature, blockers: List[CombatCreature]
    ) -> List[CombatCreature]:
        """Return blockers in the order the attacker will assign damage."""
        return list(blockers)


class MostCreaturesKilledStrategy(DamageAssignmentStrategy):
    """Order blockers so the attacker tries to kill as many as possible."""

    def order_blockers(
        self, attacker: CombatCreature, blockers: List[CombatCreature]
    ) -> List[CombatCreature]:
        # Sort by effective toughness ascending so the attacker deals damage to
        # the most fragile creatures first.
        return sorted(blockers, key=lambda c: c.effective_toughness())
