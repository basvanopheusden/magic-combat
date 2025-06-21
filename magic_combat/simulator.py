"""Core simulation logic for the combat phase."""

from dataclasses import dataclass
from typing import Dict, List, Optional

from .creature import CombatCreature
from .damage import DamageAssignmentStrategy, MostCreaturesKilledStrategy

@dataclass
class CombatResult:
    """Outcome of combat after resolution."""

    damage_to_players: Dict[str, int]
    creatures_destroyed: List[CombatCreature]
    lifegain: Dict[str, int]


class CombatSimulator:
    """High level orchestrator for combat resolution."""

    def __init__(
        self,
        attackers: List[CombatCreature],
        defenders: List[CombatCreature],
        strategy: Optional[DamageAssignmentStrategy] = None,
    ):
        """Store combatants taking part in the current combat phase."""

        self.attackers = attackers
        self.defenders = defenders
        self.all_creatures = attackers + defenders
        self.player_damage: Dict[str, int] = {}
        self.assignment_strategy = strategy or MostCreaturesKilledStrategy()

    def validate_blocking(self):
        """Ensure blocking assignments are legal for this simplified simulator."""
        for blocker in self.defenders:
            if blocker.blocking is not None and blocker.blocking not in self.attackers:
                raise ValueError("Blocker assigned to unknown attacker")

        for attacker in self.attackers:
            for blocker in attacker.blocked_by:
                if blocker.blocking is not attacker:
                    raise ValueError("Inconsistent blocking assignments")

    def apply_precombat_triggers(self):
        """Apply keyword abilities that modify stats before combat damage."""
        # reset any temporary bonuses
        for creature in self.all_creatures:
            creature.reset_temporary_bonuses()

        # group attackers by controller for exalted and training
        attackers_by_controller: Dict[str, List[CombatCreature]] = {}
        for atk in self.attackers:
            attackers_by_controller.setdefault(atk.controller, []).append(atk)

        # Exalted triggers
        for controller, atks in attackers_by_controller.items():
            if len(atks) == 1:
                atk = atks[0]
                exalted_total = atk.exalted_count
                atk.temp_power += exalted_total
                atk.temp_toughness += exalted_total

        # Battle cry
        for atk in self.attackers:
            if atk.battle_cry_count:
                for other in self.attackers:
                    if other is not atk and other.controller == atk.controller:
                        other.temp_power += atk.battle_cry_count

        # Melee
        num_opponents_attacked = 1 if self.attackers else 0
        for atk in self.attackers:
            if atk.melee and num_opponents_attacked:
                atk.temp_power += num_opponents_attacked
                atk.temp_toughness += num_opponents_attacked

        # Training
        for atk in self.attackers:
            if atk.training:
                if any(
                    other.controller == atk.controller
                    and other is not atk
                    and other.effective_power() > atk.effective_power()
                    for other in self.attackers
                ):
                    atk.plus1_counters += 1

        # Bushido, Rampage, and Flanking
        for attacker in self.attackers:
            if attacker.blocked_by:
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

        for blocker in self.defenders:
            if blocker.blocking is not None:
                if blocker.bushido:
                    blocker.temp_power += blocker.bushido
                    blocker.temp_toughness += blocker.bushido

    def resolve_first_strike_damage(self):
        """No first strike logic for vanilla combat."""
        return

    def _assign_damage_from_attacker(self, attacker: CombatCreature) -> None:
        """Deal attacker's damage to its blockers."""
        ordered = self.assignment_strategy.order_blockers(attacker, attacker.blocked_by)
        remaining = attacker.effective_power()
        for blocker in ordered:
            dmg = min(remaining, blocker.effective_toughness())
            blocker.damage_marked += dmg
            remaining -= dmg
            if remaining <= 0:
                break

    def _assign_damage_to_attacker(self, attacker: CombatCreature) -> None:
        """Deal each blocker's combat damage to the attacker."""
        for blocker in attacker.blocked_by:
            attacker.damage_marked += blocker.effective_power()

    def _deal_damage_to_player(self, attacker: CombatCreature) -> None:
        """Deal damage from an unblocked attacker to a defending player."""
        defender = self.defenders[0].controller if self.defenders else "defender"
        self.player_damage[defender] = self.player_damage.get(defender, 0) + attacker.effective_power()

    def resolve_normal_combat_damage(self):
        """Assign and deal damage in the normal damage step for vanilla combat."""
        for attacker in self.attackers:
            if attacker.blocked_by:
                self._assign_damage_from_attacker(attacker)
                self._assign_damage_to_attacker(attacker)
            else:
                self._deal_damage_to_player(attacker)

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
