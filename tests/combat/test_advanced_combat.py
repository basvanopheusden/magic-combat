from magic_combat import CombatCreature
from magic_combat import CombatSimulator
from tests.conftest import link_block


def test_double_strike_first_and_normal_damage():
    """CR 702.4b: A creature with double strike deals damage during both first-strike and regular damage steps."""
    attacker = CombatCreature("Duelist", 2, 2, "A", double_strike=True)
    blocker = CombatCreature("Bear", 2, 2, "B")
    link_block(attacker, blocker)
    sim = CombatSimulator([attacker], [blocker])
    result = sim.simulate()
    assert blocker in result.creatures_destroyed
    assert attacker not in result.creatures_destroyed


def test_lifelink_grants_life_when_dealing_damage():
    """CR 702.15a: Damage dealt by a creature with lifelink also causes its controller to gain that much life."""
    attacker = CombatCreature("Cleric", 2, 2, "A", lifelink=True)
    blocker = CombatCreature("Guard", 2, 2, "B")
    link_block(attacker, blocker)
    sim = CombatSimulator([attacker], [blocker])
    result = sim.simulate()
    assert result.lifegain["A"] == 2
    assert attacker in result.creatures_destroyed
    assert blocker in result.creatures_destroyed


def test_lifelink_unblocked_attacker_gain_life_from_player_damage():
    """CR 702.15a: Lifelink applies to combat damage dealt to a player."""
    attacker = CombatCreature("Vampire", 3, 3, "A", lifelink=True)
    defender = CombatCreature("Dummy", 0, 1, "B")
    sim = CombatSimulator([attacker], [defender])
    result = sim.simulate()
    assert result.damage_to_players["B"] == 3
    assert result.lifegain["A"] == 3
