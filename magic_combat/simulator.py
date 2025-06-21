"""Core simulation logic for the combat phase."""

from dataclasses import dataclass
from typing import Dict, List

from .creature import CombatCreature

@dataclass
class CombatResult:
    """Outcome of combat after resolution."""

    damage_to_players: Dict[str, int]
    creatures_destroyed: List[CombatCreature]
    lifegain: Dict[str, int]


class CombatSimulator:
    """High level orchestrator for combat resolution."""

    def __init__(self, attackers: List[CombatCreature], defenders: List[CombatCreature]):
        """Store combatants taking part in the current combat phase."""

        self.attackers = attackers
        self.defenders = defenders
        self.all_creatures = attackers + defenders
        self.player_damage: Dict[str, int] = {}

    def validate_blocking(self):
        """Ensure blocking assignments are legal for this simplified simulator."""
        for attacker in self.attackers:
            if len(attacker.blocked_by) > 1:
                # TODO: allow double blocking in the future
                raise ValueError("Multiple blockers are not supported yet")

        for blocker in self.defenders:
            if blocker.blocking is not None and blocker.blocking not in self.attackers:
                raise ValueError("Blocker assigned to unknown attacker")

    def apply_precombat_triggers(self):
        """Placeholder for future precombat trigger logic."""
        return

    def resolve_first_strike_damage(self):
        """No first strike logic for vanilla combat."""
        return

    def resolve_normal_combat_damage(self):
        """Assign and deal damage in the normal damage step for vanilla combat."""
        for attacker in self.attackers:
            if attacker.blocked_by:
                blocker = attacker.blocked_by[0]
                blocker.damage_marked += attacker.effective_power()
                attacker.damage_marked += blocker.effective_power()
            else:
                defender = self.defenders[0].controller if self.defenders else "defender"
                self.player_damage[defender] = self.player_damage.get(defender, 0) + attacker.effective_power()

    def check_lethal_damage(self):
        """Evaluate which creatures die after damage."""
        self.dead_creatures = [c for c in self.all_creatures if c.is_destroyed_by_damage()]

    def apply_lifelink_and_combat_lifegain(self):
        """No lifelink implementation for vanilla combat."""
        self.lifegain = {}

    def finalize(self) -> CombatResult:
        """Return the outcome of combat."""
        return CombatResult(
            damage_to_players=self.player_damage,
            creatures_destroyed=self.dead_creatures,
            lifegain=self.lifegain,
        )

    def simulate(self) -> CombatResult:
        """Run a full combat phase resolution and return the result."""
        self.dead_creatures: List[CombatCreature] = []
        self.validate_blocking()
        self.apply_precombat_triggers()

        # First strike step
        any_first_strike = any(c.first_strike or c.double_strike for c in self.all_creatures)
        if any_first_strike:
            self.resolve_first_strike_damage()
            self.check_lethal_damage()

        self.resolve_normal_combat_damage()
        self.check_lethal_damage()
        self.apply_lifelink_and_combat_lifegain()

        return self.finalize()
