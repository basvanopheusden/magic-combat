# -*- coding: utf-8 -*-
"""Comprehensive Rules excerpts for keyword abilities."""

from __future__ import annotations

from typing import Iterable
from typing import List
from typing import Set

from .abilities import BOOL_NAMES
from .abilities import INT_NAMES
from .creature import CombatCreature

# Map of keyword ability name to a representative excerpt from the Comprehensive
# Rules. Ideally each entry would contain the full rules text for the ability
# (roughly 10–20 lines), but network access limitations currently prevent
# automatically fetching the official document. The snippets below are therefore
# partial and should be replaced with the precise text from the CR when
# available.

RULES_TEXT: dict[str, str] = {
    "Afflict": """702.130. Afflict

702.130a Afflict is a triggered ability. “Afflict N” means “Whenever this creature becomes blocked, defending player loses N life.”

702.130b If a creature has multiple instances of afflict, each triggers separately.""",
    "Battle cry": """702.91. Battle Cry

702.91a Battle cry is a triggered ability. “Battle cry” means “Whenever this creature attacks, each other attacking creature gets +1/+0 until end of turn.”

702.91b If a creature has multiple instances of battle cry, each triggers separately.""",
    "Battalion": """702.102a Battalion is a triggered ability. Whenever a creature with battalion and at least two other creatures attack, its battalion ability triggers.""",
    "Bushido": """702.45. Bushido

702.45a Bushido is a triggered ability. “Bushido N” means “Whenever this creature blocks or becomes blocked, it gets +N/+N until end of turn.” (See rule 509, “Declare Blockers Step.”)

702.45b If a creature has multiple instances of bushido, each triggers separately.""",
    "Daunt": """702.152a Daunt is an evasion ability. A creature with daunt can't be blocked by creatures with power 2 or less.""",
    "Deathtouch": """702.2. Deathtouch

702.2a Deathtouch is a static ability.

702.2b A creature with toughness greater than 0 that’s been dealt damage by a source with deathtouch since the last time state-based actions were checked is destroyed as a state-based action. See rule 704.

702.2c Any nonzero amount of combat damage assigned to a creature by a source with deathtouch is considered to be lethal damage for the purposes of determining if a proposed combat damage assignment is valid, regardless of that creature’s toughness. See rules 510.1c–d.

702.2d The deathtouch rules function no matter what zone an object with deathtouch deals damage from.

702.2e If an object changes zones before an effect causes it to deal damage, its last known information is used to determine whether it had deathtouch.

702.2f Multiple instances of deathtouch on the same object are redundant.""",
    "Defender": """702.3. Defender

702.3a Defender is a static ability.

702.3b A creature with defender can’t attack.

702.3c Multiple instances of defender on the same creature are redundant.""",
    "Dethrone": """702.105. Dethrone

702.105a Dethrone is a triggered ability. “Dethrone” means “Whenever this creature attacks the player with the most life or tied for most life, put a +1/+1 counter on this creature.”

702.105b If a creature has multiple instances of dethrone, each triggers separately.""",
    "Double strike": """702.4. Double Strike

702.4a Double strike is a static ability that modifies the rules for the combat damage step. (See rule 510, “Combat Damage Step.”)

702.4b If at least one attacking or blocking creature has first strike (see rule 702.7) or double strike as the combat damage step begins, the only creatures that assign combat damage in that step are those with first strike or double strike. After that step, instead of proceeding to the end of combat step, the phase gets a second combat damage step. The only creatures that assign combat damage in that step are the remaining attackers and blockers that had neither first strike nor double strike as the first combat damage step began, as well as the remaining attackers and blockers that currently have double strike. After that step, the phase proceeds to the end of combat step.

702.4c Removing double strike from a creature during the first combat damage step will stop it from assigning combat damage in the second combat damage step.

702.4d Giving double strike to a creature with first strike after it has already dealt combat damage in the first combat damage step will allow the creature to assign combat damage in the second combat damage step.

702.4e Multiple instances of double strike on the same creature are redundant.""",
    "Exalted": """702.83. Exalted

702.83a Exalted is a triggered ability. “Exalted” means “Whenever a creature you control attacks alone, that creature gets +1/+1 until end of turn.”

702.83b A creature “attacks alone” if it’s the only creature declared as an attacker in a given combat phase. See rule 506.5.""",
    "Fear": """702.36. Fear

702.36a Fear is an evasion ability.

702.36b A creature with fear can’t be blocked except by artifact creatures and/or black creatures. (See rule 509, “Declare Blockers Step.”)

702.36c Multiple instances of fear on the same creature are redundant.""",
    "First strike": """702.7. First Strike

702.7a First strike is a static ability that modifies the rules for the combat damage step. (See rule 510, “Combat Damage Step.”)

702.7b If at least one attacking or blocking creature has first strike or double strike (see rule 702.4) as the combat damage step begins, the only creatures that assign combat damage in that step are those with first strike or double strike. After that step, instead of proceeding to the end of combat step, the phase gets a second combat damage step. The only creatures that assign combat damage in that step are the remaining attackers and blockers that had neither first strike nor double strike as the first combat damage step began, as well as the remaining attackers and blockers that currently have double strike. After that step, the phase proceeds to the end of combat step.

702.7c Giving first strike to a creature without it after combat damage has already been dealt in the first combat damage step won’t preclude that creature from assigning combat damage in the second combat damage step. Removing first strike from a creature after it has already dealt combat damage in the first combat damage step won’t allow it to also assign combat damage in the second combat damage step (unless the creature has double strike).

702.7d Multiple instances of first strike on the same creature are redundant.""",
    "Flanking": """702.25. Flanking

702.25a Flanking is a triggered ability that triggers during the declare blockers step. (See rule 509, “Declare Blockers Step.”) “Flanking” means “Whenever this creature becomes blocked by a creature without flanking, the blocking creature gets -1/-1 until end of turn.”

702.25b If a creature has multiple instances of flanking, each triggers separately.""",
    "Flying": """702.9. Flying

702.9a Flying is an evasion ability.

702.9b A creature with flying can’t be blocked except by creatures with flying and/or reach. A creature with flying can block a creature with or without flying. (See rule 509, “Declare Blockers Step,” and rule 702.17, “Reach.”)

702.9c Multiple instances of flying on the same creature are redundant.""",
    "Frenzy": """702.68. Frenzy

702.68a Frenzy is a triggered ability. “Frenzy N” means “Whenever this creature attacks and isn’t blocked, it gets +N/+0 until end of turn.”

702.68b If a creature has multiple instances of frenzy, each triggers separately.""",
    "Horsemanship": """702.31. Horsemanship

702.31a Horsemanship is an evasion ability.

702.31b A creature with horsemanship can’t be blocked by creatures without horsemanship. A creature with horsemanship can block a creature with or without horsemanship. (See rule 509, “Declare Blockers Step.”)

702.31c Multiple instances of horsemanship on the same creature are redundant.""",
    "Indestructible": """702.12. Indestructible

702.12a Indestructible is a static ability.

702.12b A permanent with indestructible can’t be destroyed. Such permanents aren’t destroyed by lethal damage, and they ignore the state-based action that checks for lethal damage (see rule 704.5g).

702.12c Multiple instances of indestructible on the same permanent are redundant.""",
    "Infect": """702.90. Infect

702.90a Infect is a static ability.

702.90b Damage dealt to a player by a source with infect doesn’t cause that player to lose life. Rather, it causes that source’s controller to give the player that many poison counters. See rule 120.3.

702.90c Damage dealt to a creature by a source with infect isn’t marked on that creature. Rather, it causes that source’s controller to put that many -1/-1 counters on that creature. See rule 120.3.

702.90d If an object changes zones before an effect causes it to deal damage, its last known information is used to determine whether it had infect.

702.90e The infect rules function no matter what zone an object with infect deals damage from.

702.90f Multiple instances of infect on the same object are redundant.""",
    "Intimidate": """702.13. Intimidate

702.13a Intimidate is an evasion ability.

702.13b A creature with intimidate can’t be blocked except by artifact creatures and/or creatures that share a color with it. (See rule 509, “Declare Blockers Step.”)

702.13c Multiple instances of intimidate on the same creature are redundant.""",
    "Lifelink": """702.15. Lifelink

702.15a Lifelink is a static ability.

702.15b Damage dealt by a source with lifelink causes that source’s controller, or its owner if it has no controller, to gain that much life (in addition to any other results that damage causes). See rule 120.3.

702.15c If an object changes zones before an effect causes it to deal damage, its last known information is used to determine whether it had lifelink.

702.15d The lifelink rules function no matter what zone an object with lifelink deals damage from.

702.15e If multiple sources with lifelink deal damage at the same time, they cause separate life gain events (see rules 119.9–10).
Example: A player controls Ajani’s Pridemate, which reads “Whenever you gain life, put a +1/+1 counter on this creature,” and two creatures with lifelink. The creatures with lifelink deal combat damage simultaneously. Ajani’s Pridemate’s ability triggers twice.

702.15f Multiple instances of lifelink on the same object are redundant.""",
    "Melee": """702.121. Melee

702.121a Melee is a triggered ability. “Melee” means “Whenever this creature attacks, it gets +1/+1 until end of turn for each opponent you attacked with a creature this combat.”

702.121b If a creature has multiple instances of melee, each triggers separately.""",
    "Menace": """702.111. Menace

702.111a Menace is an evasion ability.

702.111b A creature with menace can’t be blocked except by two or more creatures. (See rule 509, “Declare Blockers Step.”)

702.111c Multiple instances of menace on the same creature are redundant.""",
    "Mentor": """702.134. Mentor

702.134a Mentor is a triggered ability. “Mentor” means “Whenever this creature attacks, put a +1/+1 counter on target attacking creature with power less than this creature’s power.”

702.134b If a creature has multiple instances of mentor, each triggers separately.

702.134c An ability that triggers whenever a creature mentors another creature triggers whenever a mentor ability whose source is the first creature and whose target is the second creature resolves.""",
    "Persist": """702.79. Persist

702.79a Persist is a triggered ability. “Persist” means “When this permanent is put into a graveyard from the battlefield, if it had no -1/-1 counters on it, return it to the battlefield under its owner’s control with a -1/-1 counter on it.”""",
    "Provoke": """702.39. Provoke

702.39a Provoke is a triggered ability. “Provoke” means “Whenever this creature attacks, you may choose to have target creature defending player controls block this creature this combat if able. If you do, untap that creature.”

702.39b If a creature has multiple instances of provoke, each triggers separately.""",
    "Protection": """702.16. Protection

702.16a Protection is a static ability, written “Protection from [quality].” This quality is usually a color (as in “protection from black”) but can be any characteristic value or information. If the quality happens to be a card name, it is treated as such only if the protection ability specifies that the quality is a name. If the quality is a card type, subtype, or supertype, the ability applies to sources that are permanents with that card type, subtype, or supertype and to any sources not on the battlefield that are of that card type, subtype, or supertype. This is an exception to rule 109.2.

702.16b A permanent or player with protection can’t be targeted by spells with the stated quality and can’t be targeted by abilities from a source with the stated quality.

702.16c A permanent or player with protection can’t be enchanted by Auras that have the stated quality. Such Auras attached to the permanent or player with protection will be put into their owners’ graveyards as a state-based action. (See rule 704, “State-Based Actions.”)

702.16d A permanent with protection can’t be equipped by Equipment that have the stated quality or fortified by Fortifications that have the stated quality. Such Equipment or Fortifications become unattached from that permanent as a state-based action, but remain on the battlefield. (See rule 704, “State-Based Actions.”)

702.16e Any damage that would be dealt by sources that have the stated quality to a permanent or player with protection is prevented.

702.16f Attacking creatures with protection can’t be blocked by creatures that have the stated quality.

702.16g “Protection from [quality A] and from [quality B]” is shorthand for “protection from [quality A]” and “protection from [quality B]”; it behaves as two separate protection abilities.

702.16h “Protection from each [characteristic]” is shorthand for “protection from [quality A],” “protection from [quality B],” and so on for each possible quality the listed characteristic could have; it behaves as multiple separate protection abilities.

702.16i “Protection from each [set of characteristics, qualities, or players]” is shorthand for “protection from [A],” “protection from [B],” and so on for each characteristic, quality, or player in the set. It behaves as multiple separate protection abilities.

702.16j “Protection from everything” is a variant of the protection ability. A permanent or player with protection from everything has protection from each object regardless of that object’s characteristic values. Such a permanent or player can’t be targeted by spells or abilities and can’t be enchanted by Auras. Such a permanent can’t be equipped by Equipment, fortified by Fortifications, or blocked by creatures. All damage that would be dealt to such a permanent or player is prevented.

702.16k “Protection from [a player]” is a variant of the protection ability. A permanent or player with protection from a specific player has protection from each object that player controls and protection from each object that player owns not controlled by another player, regardless of that object’s characteristic values. Such a permanent or player can’t be targeted by spells or abilities the specified player controls and can’t be enchanted by Auras that player controls. Such a permanent can’t be equipped by Equipment that player controls, fortified by Fortifications that player controls, or blocked by creatures that player controls. All damage that would be dealt to such a permanent or player by sources controlled by the specified player or owned by that player but not controlled by another player is prevented.

702.16m Multiple instances of protection from the same quality on the same permanent or player are redundant.

702.16n Some Auras both give the enchanted creature protection from a quality and say “this effect doesn’t remove” either that specific Aura or all Auras. This means that the specified Auras aren’t put into their owners’ graveyards as a state-based action. If the creature has other instances of protection from the same quality, those instances affect Auras as normal.

702.16p One Aura (Benevolent Blessing) gives the enchanted creature protection from a quality and says the effect doesn’t remove certain permanents that are “already attached to” that creature. This means that, when the protection effect starts to apply, any objects with the stated quality that are already attached to that creature (including the Aura giving that creature protection) will not be put into their owners’ graveyards as a state-based action. Other permanents with the stated quality can’t become attached to the creature. If the creature has other instances of protection from the same quality, those instances affect attached permanents as normal.""",
    "Rampage": """702.23. Rampage

702.23a Rampage is a triggered ability. “Rampage N” means “Whenever this creature becomes blocked, it gets +N/+N until end of turn for each creature blocking it beyond the first.” (See rule 509, “Declare Blockers Step.”)

702.23b The rampage bonus is calculated only once per combat, when the triggered ability resolves. Adding or removing blockers later in combat won’t change the bonus.

702.23c If a creature has multiple instances of rampage, each triggers separately.""",
    "Reach": """702.17. Reach

702.17a Reach is a static ability.

702.17b A creature with flying can’t be blocked except by creatures with flying and/or reach. (See rule 509, “Declare Blockers Step,” and rule 702.9, “Flying.”)

702.17c Multiple instances of reach on the same creature are redundant.""",
    "Shadow": """702.28. Shadow

702.28a Shadow is an evasion ability.

702.28b A creature with shadow can’t be blocked by creatures without shadow, and a creature without shadow can’t be blocked by creatures with shadow. (See rule 509, “Declare Blockers Step.”)

702.28c Multiple instances of shadow on the same creature are redundant.""",
    "Skulk": """702.118. Skulk

702.118a Skulk is an evasion ability.

702.118b A creature with skulk can’t be blocked by creatures with greater power. (See rule 509, “Declare Blockers Step.”)

702.118c Multiple instances of skulk on the same creature are redundant.""",
    "Toxic": """702.164. Toxic

702.164a Toxic is a static ability. It is written “toxic N,” where N is a number.

702.164b Some rules and effects refer to a creature’s “total toxic value.” A creature’s total toxic value is the sum of all N values of toxic abilities that creature has.
Example: If a creature with toxic 2 gains toxic 1 due to another effect, its total toxic value is 3.

702.164c Combat damage dealt to a player by a creature with toxic causes that creature’s controller to give the player a number of poison counters equal to that creature’s total toxic value, in addition to the damage’s other results. See rule 120.3.""",
    "Training": """702.149. Training

702.149a Training is a triggered ability. “Training” means “Whenever this creature and at least one other creature with power greater than this creature’s power attack, put a +1/+1 counter on this creature.”

702.149b If a creature has multiple instances of training, each triggers separately.

702.149c Some creatures with training have abilities that trigger when they train. “When this creature trains” means “When a resolving training ability puts one or more +1/+1 counters on this creature.”""",
    "Trample": """702.19. Trample

702.19a Trample is a static ability that modifies the rules for assigning an attacking creature’s combat damage. The ability has no effect when a creature with trample is blocking or is dealing noncombat damage. (See rule 510, “Combat Damage Step.”)

702.19b The controller of an attacking creature with trample first assigns damage to the creature(s) blocking it. Once all those blocking creatures are assigned lethal damage, any excess damage is assigned as its controller chooses among those blocking creatures and the player, planeswalker, or battle the creature is attacking. When checking for assigned lethal damage, take into account damage already marked on the creature and damage from other creatures that’s being assigned during the same combat damage step, but not any abilities or effects that might change the amount of damage that’s actually dealt. The attacking creature’s controller need not assign lethal damage to all those blocking creatures but in that case can’t assign any damage to the player or planeswalker it’s attacking.
Example: A 2/2 creature that can block an additional creature blocks two attackers: a 1/1 with no abilities and a 3/3 with trample. The active player could assign 1 damage from the first attacker and 1 damage from the second to the blocking creature, and 2 damage to the defending player from the creature with trample.
Example: A 6/6 green creature with trample is blocked by a 2/2 creature with protection from green. The attacking creature’s controller must assign at least 2 damage to the blocker, even though that damage will be prevented by the blocker’s protection ability. The attacking creature’s controller can divide the rest of the damage as they choose between the blocking creature and the defending player.

702.19c Trample over planeswalkers is a variant of trample that modifies the rules for assigning combat damage to planeswalkers. The controller of a creature with trample over planeswalkers assigns that creature’s combat damage as described in rule 702.19b, with one exception. If that creature is attacking a planeswalker, after lethal damage is assigned to all blocking creatures and damage at least equal to the loyalty of the planeswalker the creature is attacking is assigned to that planeswalker, further excess damage may be assigned as the attacking creature’s controller chooses among those blocking creatures, that planeswalker, and that planeswalker’s controller. When checking for assigned damage equal to a planeswalker’s loyalty, take into account damage from other creatures that’s being assigned during the same combat damage step, but not any abilities or effects that might change the amount of damage that’s actually dealt.
Example: A player controls a planeswalker with three loyalty counters that is being attacked by a 1/1 with no abilities and a 7/7 with trample over planeswalkers. The active player could assign 1 damage from the first attacker and 2 damage from the second to the planeswalker and 5 damage to the defending player from the creature with trample over planeswalkers.

702.19d If an attacking creature with trample or trample over planeswalkers is blocked, but there are no creatures blocking it when damage is assigned, its damage is assigned to the defending player and/or planeswalker as though all blocking creatures have been assigned lethal damage.

702.19e If a creature with trample over planeswalkers is attacking a planeswalker and that planeswalker is removed from combat, the creature’s damage may be assigned to the defending player once all blocking creatures have been dealt lethal damage or, if there are no blocking creatures when damage is assigned, all its damage is assigned to the defending player. This is an exception to rule 506.4c, and it does not cause the creature to be attacking that player.

702.19f If a creature without trample over planeswalkers is attacking a planeswalker, none of its combat damage can be assigned to the defending player, even if that planeswalker has been removed from combat or the damage the attacking creature could assign is greater than the planeswalker’s loyalty.

702.19g Multiple instances of trample on the same creature are redundant. Multiple instances of trample over planeswalkers on the same creature are redundant.""",
    "Undying": """702.93. Undying

702.93a Undying is a triggered ability. “Undying” means “When this permanent is put into a graveyard from the battlefield, if it had no +1/+1 counters on it, return it to the battlefield under its owner’s control with a +1/+1 counter on it.”""",
    "Vigilance": """702.20. Vigilance

702.20a Vigilance is a static ability that modifies the rules for the declare attackers step.

702.20b Attacking doesn’t cause creatures with vigilance to tap. (See rule 508, “Declare Attackers Step.”)

702.20c Multiple instances of vigilance on the same creature are redundant.""",
    "Wither": """702.80. Wither

702.80a Wither is a static ability. Damage dealt to a creature by a source with wither isn’t marked on that creature. Rather, it causes that source’s controller to put that many -1/-1 counters on that creature. See rule 120.3.

702.80b If an object changes zones before an effect causes it to deal damage, its last known information is used to determine whether it had wither.

702.80c The wither rules function no matter what zone an object with wither deals damage from.

702.80d Multiple instances of wither on the same object are redundant.""",
}


def describe_abilities(creature: CombatCreature) -> str:
    """Return a comma separated string describing the creature's abilities."""

    parts: List[str] = []
    for attr, name in BOOL_NAMES.items():
        if getattr(creature, attr, False):
            parts.append(name)
    for attr, name in INT_NAMES.items():
        val = getattr(creature, attr, 0)
        if val:
            parts.append(f"{name} {val}")
    if creature.protection_colors:
        colors = ", ".join(c.name.capitalize() for c in creature.protection_colors)
        parts.append(f"Protection from {colors}")
    if creature.artifact:
        parts.append("Artifact")
    return ", ".join(parts) if parts else "none"


def get_relevant_rules_text(creatures: Iterable[CombatCreature]) -> str:
    """Return card text and rules for all keywords on ``creatures``."""

    keywords: Set[str] = set()
    lines: List[str] = []

    for creature in creatures:
        for attr, name in BOOL_NAMES.items():
            if getattr(creature, attr, False):
                keywords.add(name)
        for attr, name in INT_NAMES.items():
            if getattr(creature, attr, 0):
                keywords.add(name)
        if creature.protection_colors:
            keywords.add("Protection")

    lines.append("# Relevant Rules")
    for name in sorted(keywords):
        rule = RULES_TEXT.get(name)
        if rule:
            lines.append(f"{name}: {rule}")
    return "\n".join(lines)


__all__ = ["RULES_TEXT", "get_relevant_rules_text"]
