from magic_combat import CombatCreature
from magic_combat.combat_utils import damage_creature, damage_player


def test_damage_creature_wither_and_deathtouch():
    """CR 702.90a & 702.2b: Wither damage uses -1/-1 counters and deathtouch makes it lethal."""
    source = CombatCreature("Assassin", 1, 1, "A", wither=True, deathtouch=True)
    target = CombatCreature("Giant", 5, 5, "B")
    damage_creature(target, 1, source)
    assert target.minus1_counters == 1
    assert target.damage_marked == 0
    assert target.damaged_by_deathtouch


def test_damage_player_infect():
    """CR 702.90b: Damage from a source with infect gives poison counters instead of life loss."""
    source = CombatCreature("Infecter", 2, 2, "A", infect=True)
    damage: dict[str, int] = {}
    poison: dict[str, int] = {}
    damage_player(
        "B",
        2,
        source,
        damage_to_players=damage,
        poison_counters=poison,
        game_state=None,
    )
    assert damage.get("B", 0) == 0
    assert poison.get("B", 0) == 2
