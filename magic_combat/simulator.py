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
        self.lifegain: Dict[str, int] = {}
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

        for attacker in self.attackers:
            if attacker.unblockable and attacker.blocked_by:
                raise ValueError("Unblockable creature was blocked")

            if attacker.menace and 0 < len(attacker.blocked_by) < 2:
                raise ValueError("Menace creature blocked by fewer than two")

            for blocker in attacker.blocked_by:
                if attacker.flying and not (blocker.flying or blocker.reach):
                    raise ValueError("Non-flying/reach blocker blocking flyer")

                if attacker.shadow and not blocker.shadow:
                    raise ValueError("Non-shadow creature blocking shadow")

                if attacker.horsemanship and not blocker.horsemanship:
                    raise ValueError("Non-horsemanship creature blocking")

                if attacker.skulk and blocker.effective_power() > attacker.effective_power():
                    raise ValueError("Skulk prevents block by higher power")

                if attacker.fear and not (blocker.artifact or "black" in blocker.colors):
                    raise ValueError("Fear creature blocked illegally")

                if attacker.protection_colors & blocker.colors:
                    raise ValueError("Attacker has protection from blocker's color")

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
        """Handle the first strike combat damage step."""
        for attacker in self.attackers:
            if attacker.blocked_by:
                if attacker.first_strike or attacker.double_strike:
                    self._assign_damage_from_attacker(attacker)
                for blocker in attacker.blocked_by:
                    if blocker.first_strike or blocker.double_strike:
                        attacker.damage_marked += blocker.effective_power()
                        if blocker.lifelink:
                            self.lifegain[blocker.controller] = (
                                self.lifegain.get(blocker.controller, 0)
                                + blocker.effective_power()
                            )
            else:
                if attacker.first_strike or attacker.double_strike:
                    self._deal_damage_to_player(attacker)

    def _assign_damage_from_attacker(
        self, attacker: CombatCreature, blockers: Optional[List[CombatCreature]] = None
    ) -> None:
        """Deal attacker's damage to its blockers."""
        blockers = blockers if blockers is not None else attacker.blocked_by
        ordered = self.assignment_strategy.order_blockers(attacker, blockers)
        remaining = attacker.effective_power()
        for blocker in ordered:
            lethal = 1 if attacker.deathtouch else blocker.effective_toughness()
            dmg = min(remaining, lethal)
            blocker.damage_marked += dmg
            if attacker.deathtouch and dmg > 0:
                blocker.damaged_by_deathtouch = True
            if attacker.lifelink:
                self.lifegain[attacker.controller] = (
                    self.lifegain.get(attacker.controller, 0) + dmg
                )
            remaining -= dmg
            if remaining <= 0:
                break

    def _assign_damage_to_attacker(
        self, attacker: CombatCreature, blockers: Optional[List[CombatCreature]] = None
    ) -> None:
        """Deal each blocker's combat damage to the attacker."""
        blockers = blockers if blockers is not None else attacker.blocked_by
        for blocker in blockers:
            dmg = blocker.effective_power()
            attacker.damage_marked += dmg
            if blocker.deathtouch and dmg > 0:
                attacker.damaged_by_deathtouch = True
            if blocker.lifelink:
                self.lifegain[blocker.controller] = (
                    self.lifegain.get(blocker.controller, 0) + dmg
                )

    def _deal_damage_to_player(self, attacker: CombatCreature) -> None:
        """Deal damage from an unblocked attacker to a defending player."""
        defender = self.defenders[0].controller if self.defenders else "defender"
        dmg = attacker.effective_power()
        self.player_damage[defender] = self.player_damage.get(defender, 0) + dmg
        if attacker.lifelink:
            self.lifegain[attacker.controller] = (
                self.lifegain.get(attacker.controller, 0) + dmg
            )

    def resolve_normal_combat_damage(self):
        """Assign and deal damage in the normal damage step."""
        for attacker in self.attackers:
            if attacker in self.dead_creatures:
                continue
            blockers_alive = [b for b in attacker.blocked_by if b not in self.dead_creatures]
            if blockers_alive:
                if not attacker.first_strike or attacker.double_strike:
                    self._assign_damage_from_attacker(attacker, blockers_alive)
                eligible_blockers = [
                    b for b in blockers_alive if not b.first_strike or b.double_strike
                ]
                if eligible_blockers:
                    self._assign_damage_to_attacker(attacker, eligible_blockers)
            else:
                if not attacker.first_strike or attacker.double_strike:
                    self._deal_damage_to_player(attacker)

    def check_lethal_damage(self):
        """Evaluate which creatures die after damage."""
        self.dead_creatures = [c for c in self.all_creatures if c.is_destroyed_by_damage()]

    def apply_lifelink_and_combat_lifegain(self):
        """Placeholder for additional combat-related lifegain."""
        # lifegain has been accumulated during damage assignment

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
