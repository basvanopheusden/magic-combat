"""Core simulation logic for the combat phase."""

from dataclasses import dataclass
from dataclasses import field
from typing import Dict
from typing import List
from typing import Optional
from typing import Tuple

from .combat_utils import damage_creature
from .combat_utils import damage_player
from .creature import CombatCreature
from .damage import optimal_damage_order
from .exceptions import IllegalBlockError
from .gamestate import GameState
from .gamestate import has_player_lost
from .utils import can_block
from .utils import ensure_player_state


@dataclass
class CombatResult:
    """Outcome of combat after resolution."""

    damage_to_players: Dict[str, int]
    creatures_destroyed: List[CombatCreature]
    lifegain: Dict[str, int]
    poison_counters: Dict[str, int] = field(default_factory=dict[str, int])
    players_lost: List[str] = field(default_factory=list[str])

    def __repr__(self) -> str:
        cls = self.__class__.__name__
        destroyed = [c.name for c in self.creatures_destroyed]
        return (
            f"{cls}(damage_to_players={self.damage_to_players}, "
            f"creatures_destroyed={destroyed}, lifegain={self.lifegain}, "
            f"poison_counters={self.poison_counters}, players_lost={self.players_lost})"
        )

    def __str__(self) -> str:
        """Return a readable multi-line summary of the result."""
        parts: List[str] = []
        if self.damage_to_players:
            dmg = ", ".join(f"{p} {d}" for p, d in self.damage_to_players.items())
            parts.append(f"Damage to players: {dmg}")
        if self.poison_counters:
            poison = ", ".join(f"{p} +{c}" for p, c in self.poison_counters.items())
            parts.append(f"Poison counters: {poison}")
        if self.lifegain:
            gain = ", ".join(f"{p} +{g}" for p, g in self.lifegain.items())
            parts.append(f"Life gain: {gain}")
        if self.creatures_destroyed:
            dead = ", ".join(c.name for c in self.creatures_destroyed)
            parts.append(f"Creatures destroyed: {dead}")
        if self.players_lost:
            parts.append("Players lost: " + ", ".join(self.players_lost))
        return "\n".join(parts) if parts else "No changes"

    def score(
        self,
        attacker_player: str,
        defender: str,
        *,
        include_value: bool = True,
        include_count: bool = True,
        include_mana: bool = True,
        include_life: bool = True,
        include_poison: bool = True,
        include_loss: bool = True,
    ) -> tuple[int, float, int, int, int, int]:
        """Return a scoring tuple from the defender's perspective.

        The tuple elements are ordered so that smaller values represent better
        outcomes for the defending player:

        1. ``lost`` -- ``1`` if the defender lost the game, else ``0``.
        2. ``val_diff`` -- difference in total creature value destroyed
           (defender minus attacker).
        3. ``cnt_diff`` -- difference in number of creatures destroyed
           (defender minus attacker).
        4. ``mana_component`` -- difference in mana value lost
           (defender minus attacker).
        5. ``life_component`` -- difference in net life change including
           lifelink (defender minus attacker).
        6. ``poison_component`` -- difference in poison counters gained
           (defender minus attacker).
        """

        lost = 1 if defender in self.players_lost else 0
        if not include_loss:
            lost = 0

        att_val = sum(
            c.value()
            for c in self.creatures_destroyed
            if c.controller == attacker_player
        )
        def_val = sum(
            c.value() for c in self.creatures_destroyed if c.controller == defender
        )
        val_diff = def_val - att_val if include_value else 0

        att_cnt = sum(
            1 for c in self.creatures_destroyed if c.controller == attacker_player
        )
        def_cnt = sum(1 for c in self.creatures_destroyed if c.controller == defender)
        cnt_diff = def_cnt - att_cnt if include_count else 0

        att_mana = sum(
            c.mana_value
            for c in self.creatures_destroyed
            if c.controller == attacker_player
        )
        def_mana = sum(
            c.mana_value for c in self.creatures_destroyed if c.controller == defender
        )
        mana_component = def_mana - att_mana if include_mana else 0

        dmg_def = self.damage_to_players.get(defender, 0)
        dmg_att = self.damage_to_players.get(attacker_player, 0)
        gain_def = self.lifegain.get(defender, 0)
        gain_att = self.lifegain.get(attacker_player, 0)
        life_component = (
            (dmg_def - dmg_att) + (gain_att - gain_def) if include_life else 0
        )
        poison_def = self.poison_counters.get(defender, 0)
        poison_att = self.poison_counters.get(attacker_player, 0)
        poison_component = poison_def - poison_att if include_poison else 0

        return (
            lost,
            val_diff,
            cnt_diff,
            mana_component,
            life_component,
            poison_component,
        )


class CombatSimulator:
    """High level orchestrator for combat resolution."""

    def __init__(
        self,
        attackers: List[CombatCreature],
        defenders: List[CombatCreature],
        damage_order_map: Optional[
            Dict[CombatCreature, Tuple[CombatCreature, ...]]
        ] = None,
        game_state: Optional["GameState"] = None,
        provoke_map: Optional[Dict[CombatCreature, CombatCreature]] = None,
        mentor_map: Optional[Dict[CombatCreature, CombatCreature]] = None,
    ):
        """Store combatants taking part in the current combat phase."""

        self.attackers = attackers
        self.defenders = defenders
        self.all_creatures = attackers + defenders
        self.player_damage: Dict[str, int] = dict[str, int]()
        self.poison_counters: Dict[str, int] = dict[str, int]()
        self.lifegain: Dict[str, int] = dict[str, int]()
        self._lifegain_applied: Dict[str, int] = dict[str, int]()
        self.damage_order_map: Dict[CombatCreature, Tuple[CombatCreature, ...]] = (
            damage_order_map or {}
        )
        self.game_state = game_state
        self.provoke_map: Dict[CombatCreature, CombatCreature] = (
            provoke_map or dict[CombatCreature, CombatCreature]()
        )
        self.mentor_map: Dict[CombatCreature, CombatCreature] = (
            mentor_map or dict[CombatCreature, CombatCreature]()
        )
        self.players_lost: List[str] = list[str]()
        self.dead_creatures: List[CombatCreature] = list[CombatCreature]()

        for attacker in attackers:
            if attacker.defender:
                raise IllegalBlockError("Defender creatures can't attack")

    def _get_defending_player(self) -> str:
        """Return the name of the defending player."""
        return self.defenders[0].controller if self.defenders else "defender"

    def tap_attackers(self) -> None:
        """Mark attackers as attacking and tap those without vigilance."""
        for attacker in self.attackers:
            attacker.attacking = True
            if not attacker.vigilance:
                attacker.tapped = True

    def _check_players_lost(self) -> None:
        """Record any players who have lost the game."""
        if self.game_state is not None:
            for player in self.game_state.players:
                if (
                    has_player_lost(self.game_state, player)
                    and player not in self.players_lost
                ):
                    self.players_lost.append(player)

    def _check_block_assignments(self) -> None:
        """Validate basic blocker assignments and duplicates."""
        for blocker in self.defenders:
            if blocker.blocking is not None and blocker.blocking not in self.attackers:
                raise IllegalBlockError("Blocker assigned to unknown attacker")

        for attacker in self.attackers:
            for blocker in attacker.blocked_by:
                if blocker.blocking is not attacker:
                    raise IllegalBlockError("Inconsistent blocking assignments")

        for attacker in self.attackers:
            seen_ids: set[int] = set()
            for blocker in attacker.blocked_by:
                bid = id(blocker)
                if bid in seen_ids:
                    raise IllegalBlockError("Blocker listed multiple times")
                seen_ids.add(bid)

    def _check_unblockable(self) -> None:
        """Ensure unblockable creatures haven't been blocked."""
        for attacker in self.attackers:
            if attacker.unblockable and attacker.blocked_by:
                raise IllegalBlockError("Unblockable creature was blocked")

    def _check_menace(self) -> None:
        """Validate menace blocking requirements."""
        for attacker in self.attackers:
            if attacker.menace and 0 < len(attacker.blocked_by) < 2:
                raise IllegalBlockError("Menace creature blocked by fewer than two")

    def _check_evasion(self) -> None:
        """Check evasion abilities like flying, shadow, and skulk."""
        from .utils import can_block

        for attacker in self.attackers:
            for blocker in attacker.blocked_by:
                if not can_block(attacker, blocker):
                    raise IllegalBlockError(
                        "Illegal block according to keyword abilities"
                    )

    def _check_provoke(self) -> None:
        """Verify provoke targets are blocking as required."""
        for attacker, target in self.provoke_map.items():
            if attacker not in self.attackers:
                raise IllegalBlockError("Provoke attacker not in combat")
            if target not in self.defenders:
                raise IllegalBlockError("Provoke target not defending creature")
            if not can_block(attacker, target) or target.tapped:
                continue
            if attacker.menace:
                eligible = [
                    b
                    for b in self.defenders
                    if b is not target and not b.tapped and can_block(attacker, b)
                ]
                if not eligible:
                    continue
            if target.blocking is not attacker:
                raise IllegalBlockError("Provoke target failed to block")

    def _check_tapped_blockers(self) -> None:
        """Ensure no tapped creatures are declared as blockers."""

        for blocker in self.defenders:
            if blocker.blocking is not None and blocker.tapped:
                raise IllegalBlockError("Tapped creature can't block")

    def _check_mentor(self) -> None:
        """Validate mentor targets before applying counters."""
        for mentor, target in self.mentor_map.items():
            if mentor not in self.attackers:
                raise IllegalBlockError("Mentor creature not attacking")
            if not mentor.mentor:
                raise IllegalBlockError("Mentor map key lacks mentor ability")
            if target not in self.attackers:
                raise IllegalBlockError("Mentor target not attacking")
            if target.effective_power() >= mentor.effective_power():
                raise IllegalBlockError("Mentor target not lower power")

    def validate_blocking(self):
        """Ensure blocking assignments are legal for this simplified simulator."""
        self._check_block_assignments()
        self._check_unblockable()
        self._check_menace()
        self._check_evasion()
        self._check_tapped_blockers()
        self._check_provoke()

    def apply_precombat_triggers(self):
        """Apply keyword abilities that modify stats before combat damage.

        This method resets temporary stat bonuses and then delegates to
        specialized helpers for each ability. The helpers implement effects
        such as exalted (CR 702.90), battle cry (CR 702.92), melee
        (CR 702.111) and others that grant bonuses or counters before damage
        is assigned.
        """
        attackers_by_controller: Dict[str, List[CombatCreature]] = {}
        for atk in self.attackers:
            attackers_by_controller.setdefault(atk.controller, []).append(atk)

        self._check_mentor()
        self._reset_temporary_bonuses()
        self._handle_exalted(attackers_by_controller)
        self._handle_mentor()
        self._handle_battle_cry()
        self._handle_melee()
        self._handle_training()
        self._handle_battalion(attackers_by_controller)
        self._handle_dethrone()
        self._handle_frenzy_afflict()
        self._handle_bushido_rampage_flanking()

    def _reset_temporary_bonuses(self) -> None:
        """Clear any temporary power/toughness modifiers on creatures."""
        for creature in self.all_creatures:
            creature.reset_temporary_bonuses()

    def _handle_exalted(
        self, attackers_by_controller: Dict[str, List[CombatCreature]]
    ) -> None:
        """Apply exalted triggers (CR 702.90)."""
        for _controller, atks in attackers_by_controller.items():
            if len(atks) == 1:
                atk = atks[0]
                exalted_total = atk.exalted_count
                atk.temp_power += exalted_total
                atk.temp_toughness += exalted_total

    def _handle_battle_cry(self) -> None:
        """Apply battle cry bonuses (CR 702.92)."""
        for atk in self.attackers:
            if atk.battle_cry_count:
                for other in self.attackers:
                    if other is not atk and other.controller == atk.controller:
                        other.temp_power += atk.battle_cry_count

    def _handle_melee(self) -> None:
        """Apply melee bonuses (CR 702.111)."""
        num_opponents_attacked = 1 if self.attackers else 0
        for atk in self.attackers:
            if atk.melee and num_opponents_attacked:
                atk.temp_power += num_opponents_attacked
                atk.temp_toughness += num_opponents_attacked

    def _handle_training(self) -> None:
        """Add +1/+1 counters for training (CR 702.138)."""
        for atk in self.attackers:
            if atk.training:
                if any(
                    other.controller == atk.controller
                    and other is not atk
                    and other.effective_power() > atk.effective_power()
                    for other in self.attackers
                ):
                    atk.plus1_counters += 1

    def _handle_mentor(self) -> None:
        """Apply mentor counters (CR 702.121)."""
        for mentor, target in self.mentor_map.items():
            if (
                mentor in self.attackers
                and target in self.attackers
                and target.effective_power() < mentor.effective_power()
            ):
                target.plus1_counters += 1

    def _handle_battalion(
        self, attackers_by_controller: Dict[str, List[CombatCreature]]
    ) -> None:
        """Apply battalion bonuses (CR 702.101)."""
        for _controller, atks in attackers_by_controller.items():
            if len(atks) >= 3:
                for atk in atks:
                    if atk.battalion:
                        atk.temp_power += 1
                        atk.temp_toughness += 1

    def _handle_dethrone(self) -> None:
        """Grant counters for dethrone (CR 702.103)."""
        if self.game_state is None:
            return
        max_life = max(ps.life for ps in self.game_state.players.values())
        defender = self._get_defending_player()
        defender_life = ensure_player_state(self.game_state, defender).life
        for atk in self.attackers:
            if atk.dethrone and defender_life >= max_life:
                atk.plus1_counters += 1

    def _handle_frenzy_afflict(self) -> None:
        """Resolve frenzy and afflict abilities (CR 702.35 & 702.131)."""
        for atk in self.attackers:
            if atk.frenzy and not atk.blocked_by:
                atk.temp_power += atk.frenzy
            if atk.afflict and atk.blocked_by:
                defender = self._get_defending_player()
                self.player_damage[defender] = (
                    self.player_damage.get(defender, 0) + atk.afflict
                )
                if self.game_state is not None:
                    ps = ensure_player_state(self.game_state, defender)
                    ps.life -= atk.afflict

    def _handle_bushido_rampage_flanking(self) -> None:
        """Apply bushido, rampage, and flanking bonuses."""
        from .utils import apply_attacker_blocking_bonuses
        from .utils import apply_blocker_bushido

        for attacker in self.attackers:
            apply_attacker_blocking_bonuses(attacker)

        for blocker in self.defenders:
            apply_blocker_bushido(blocker)

    def _apply_damage_to_creature(
        self, target: "CombatCreature | str", amount: int, source: CombatCreature
    ) -> None:
        """Apply ``amount`` of damage from ``source`` to ``target``."""
        if isinstance(target, CombatCreature):
            damage_creature(target, amount, source)
        else:
            damage_player(
                target,
                amount,
                source,
                damage_to_players=self.player_damage,
                poison_counters=self.poison_counters,
                game_state=self.game_state,
            )
        if source.lifelink:
            self.lifegain[source.controller] = (
                self.lifegain.get(source.controller, 0) + amount
            )

    def resolve_first_strike_damage(self):
        """Handle the first strike combat damage step."""
        # Capture blockers' power before any damage is assigned so damage is
        # simultaneous even when wither or infect would reduce it.
        first_strike_power: dict[CombatCreature, int] = {}
        for attacker in self.attackers:
            for blocker in attacker.blocked_by:
                if blocker.first_strike or blocker.double_strike:
                    first_strike_power[blocker] = blocker.effective_power()

        for attacker in self.attackers:
            if attacker.blocked_by:
                if attacker.first_strike or attacker.double_strike:
                    self._assign_damage_from_attacker(attacker)
                for blocker in attacker.blocked_by:
                    if blocker.first_strike or blocker.double_strike:
                        dmg: int = first_strike_power[blocker]
                        self._apply_damage_to_creature(attacker, dmg, blocker)
            else:
                if attacker.first_strike or attacker.double_strike:
                    self._deal_damage_to_player(attacker)

    def _assign_damage_from_attacker(
        self, attacker: CombatCreature, blockers: Optional[List[CombatCreature]] = None
    ) -> None:
        """Deal attacker's damage to its blockers and excess to the player."""
        blockers = blockers if blockers is not None else attacker.blocked_by
        ordered = list(
            self.damage_order_map.get(attacker, tuple())
        ) or optimal_damage_order(attacker, blockers)
        remaining = attacker.effective_power()
        for blocker in ordered:
            lethal = 1 if attacker.deathtouch else blocker.effective_toughness()
            dmg: int = min(remaining, lethal)
            self._apply_damage_to_creature(blocker, dmg, attacker)
            remaining -= dmg
            if remaining <= 0:
                break
        if remaining > 0 and attacker.trample:
            self._deal_damage_to_player(attacker, remaining)

    def _assign_damage_to_attacker(
        self, attacker: CombatCreature, blockers: Optional[List[CombatCreature]] = None
    ) -> None:
        """Deal each blocker's combat damage to the attacker."""
        blockers = blockers if blockers is not None else attacker.blocked_by
        for blocker in blockers:
            dmg: int = blocker.effective_power()
            self._apply_damage_to_creature(attacker, dmg, blocker)

    def _deal_damage_to_player(
        self, attacker: CombatCreature, dmg: Optional[int] = None
    ) -> None:
        """Deal combat damage from ``attacker`` to a defending player."""
        defender = self._get_defending_player()
        dmg = attacker.effective_power() if dmg is None else int(dmg)
        self._apply_damage_to_creature(defender, dmg, attacker)

    def _revive_creature(
        self,
        creature: CombatCreature,
        *,
        plus1: bool = False,
        minus1: bool = False,
    ) -> None:
        """Return ``creature`` to the battlefield with specified counters."""

        creature.damage_marked = 0
        creature.damaged_by_deathtouch = False
        creature.reset_temporary_bonuses()
        creature.tapped = False
        creature.attacking = False

        if creature.blocking is not None:
            attacker = creature.blocking
            if creature in attacker.blocked_by:
                attacker.blocked_by.remove(creature)
            creature.blocking = None

        for atk in self.attackers:
            if creature in atk.blocked_by:
                atk.blocked_by.remove(creature)

        creature.blocked_by.clear()

        if creature in self.attackers:
            self.attackers.remove(creature)
        if creature in self.defenders:
            self.defenders.remove(creature)

        creature.plus1_counters = 1 if plus1 else 0
        creature.minus1_counters = 1 if minus1 else 0

    def resolve_normal_combat_damage(self):
        """Assign and deal damage in the normal damage step."""
        # Record blocker power before any damage so lifelink isn't reduced by
        # simultaneous wither/infect damage.
        normal_power: dict[CombatCreature, int] = {}
        for attacker in self.attackers:
            for blocker in attacker.blocked_by:
                if blocker not in self.dead_creatures and (
                    not blocker.first_strike or blocker.double_strike
                ):
                    normal_power[blocker] = blocker.effective_power()

        for attacker in self.attackers:
            if attacker in self.dead_creatures:
                continue
            blockers_alive = [
                b for b in attacker.blocked_by if b not in self.dead_creatures
            ]
            if blockers_alive:
                if not attacker.first_strike or attacker.double_strike:
                    self._assign_damage_from_attacker(attacker, blockers_alive)
                eligible_blockers = [
                    b for b in blockers_alive if not b.first_strike or b.double_strike
                ]
                if eligible_blockers:
                    for blocker in eligible_blockers:
                        dmg = normal_power[blocker]
                        self._apply_damage_to_creature(attacker, dmg, blocker)
            else:
                if not attacker.first_strike or attacker.double_strike:
                    if not attacker.blocked_by:
                        self._deal_damage_to_player(attacker)
                    elif attacker.trample:
                        self._deal_damage_to_player(attacker)

    def check_lethal_damage(self):
        """Evaluate which creatures die after damage or state-based effects."""
        for creature in self.all_creatures:
            creature.apply_counter_annihilation()
        destroyed_by_damage = [
            c for c in self.all_creatures if c.is_destroyed_by_damage()
        ]
        zero_toughness = [c for c in self.all_creatures if c.effective_toughness() <= 0]
        self.dead_creatures = destroyed_by_damage
        for creature in zero_toughness:
            if creature not in self.dead_creatures:
                self.dead_creatures.append(creature)

        for creature in list(self.dead_creatures):
            if creature.undying and creature.plus1_counters == 0:
                self._revive_creature(creature, plus1=True)
                if creature in self.dead_creatures:
                    self.dead_creatures.remove(creature)
            elif creature.persist and creature.minus1_counters == 0:
                self._revive_creature(creature, minus1=True)
                if creature in self.dead_creatures:
                    self.dead_creatures.remove(creature)

    def apply_lifelink_and_combat_lifegain(self):
        """Apply lifelink life gain to the game state, if any."""
        if self.game_state is not None:
            for player, gain in self.lifegain.items():
                already = self._lifegain_applied.get(player, 0)
                diff = gain - already
                if diff:
                    ps = ensure_player_state(self.game_state, player)
                    ps.life += diff
                    self._lifegain_applied[player] = gain
        # lifegain remains tracked for CombatResult

    def finalize(self) -> CombatResult:
        """Return the outcome of combat."""
        return CombatResult(
            damage_to_players=self.player_damage,
            poison_counters=self.poison_counters,
            creatures_destroyed=self.dead_creatures,
            lifegain=self.lifegain,
            players_lost=self.players_lost,
        )

    def simulate(self) -> CombatResult:
        """Run a full combat phase resolution and return the result."""
        self.dead_creatures = []
        self.tap_attackers()
        self.validate_blocking()
        self.apply_precombat_triggers()
        self.check_lethal_damage()
        self._check_players_lost()

        # First strike step
        any_first_strike = any(
            c.first_strike or c.double_strike for c in self.all_creatures
        )
        if any_first_strike:
            self.resolve_first_strike_damage()
            self.apply_lifelink_and_combat_lifegain()
            self.check_lethal_damage()
            self._check_players_lost()

        self.resolve_normal_combat_damage()
        self.apply_lifelink_and_combat_lifegain()
        self.check_lethal_damage()
        self._check_players_lost()

        return self.finalize()
