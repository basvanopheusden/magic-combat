from magic_combat import (
    CombatCreature,
    CombatSimulator,
    GameState,
    PlayerState,
    DEFAULT_STARTING_LIFE,
)
from tests.conftest import link_block


def test_indestructible_attacker_survives_block():
    """CR 702.12b: Indestructible permanents aren't destroyed by lethal damage."""
    attacker = CombatCreature("Hero", 2, 2, "A", indestructible=True)
    blocker = CombatCreature("Ogre", 3, 3, "B")
    link_block(attacker, blocker)
    sim = CombatSimulator([attacker], [blocker])
    result = sim.simulate()
    assert attacker not in result.creatures_destroyed
    assert blocker not in result.creatures_destroyed


def test_double_strike_indestructible_attacker_survives():
    """CR 702.4b & 702.12b: Double strike doesn't destroy an indestructible creature even after lethal damage."""
    attacker = CombatCreature(
        "Champion", 2, 2, "A", indestructible=True, double_strike=True
    )
    blocker = CombatCreature("Guard", 3, 3, "B")
    link_block(attacker, blocker)
    sim = CombatSimulator([attacker], [blocker])
    result = sim.simulate()
    assert attacker not in result.creatures_destroyed
    assert blocker in result.creatures_destroyed


def test_trample_vs_indestructible_blocker():
    """CR 702.12b & 702.19b: Trample must still assign lethal damage to an indestructible blocker."""
    attacker = CombatCreature("Beast", 5, 5, "A", trample=True)
    blocker = CombatCreature("Guardian", 2, 2, "B", indestructible=True)
    link_block(attacker, blocker)
    sim = CombatSimulator([attacker], [blocker])
    result = sim.simulate()
    assert result.damage_to_players["B"] == 3
    assert blocker not in result.creatures_destroyed


def test_wither_damage_kills_indestructible():
    """CR 702.90a & 702.12b: Wither counters can cause an indestructible creature to die."""
    attacker = CombatCreature("Corrosive Blade", 2, 2, "A", wither=True)
    blocker = CombatCreature("Steel Guardian", 2, 2, "B", indestructible=True)
    link_block(attacker, blocker)
    sim = CombatSimulator([attacker], [blocker])
    result = sim.simulate()
    assert blocker in result.creatures_destroyed
    assert blocker.minus1_counters == 2


def test_double_strike_wither_kills_indestructible():
    """CR 702.4b & 702.90a & 702.12b: Double strike with wither can destroy an indestructible creature in the first-strike step."""
    attacker = CombatCreature(
        "Acid Duelist", 1, 1, "A", double_strike=True, wither=True
    )
    blocker = CombatCreature("Iron Guardian", 1, 1, "B", indestructible=True)
    link_block(attacker, blocker)
    sim = CombatSimulator([attacker], [blocker])
    result = sim.simulate()
    assert blocker in result.creatures_destroyed
    assert attacker not in result.creatures_destroyed
    assert blocker.minus1_counters == 1


def test_persist_indestructible_dies_no_return_with_counters():
    """CR 702.12b & 702.77a: Persist doesn't return a creature that dies with a -1/-1 counter."""
    attacker = CombatCreature("Corrosive", 2, 2, "A", wither=True)
    blocker = CombatCreature(
        "Everlasting", 2, 2, "B", indestructible=True, persist=True
    )
    link_block(attacker, blocker)
    sim = CombatSimulator([attacker], [blocker])
    result = sim.simulate()
    assert blocker in result.creatures_destroyed
    assert blocker.minus1_counters == 2


def test_undying_indestructible_returns_with_counter():
    """CR 702.12b & 702.92a: An indestructible creature with undying returns with a +1/+1 counter if it dies without one."""
    attacker = CombatCreature("Corrosive", 1, 1, "A", wither=True)
    blocker = CombatCreature("Phoenix", 1, 1, "B", indestructible=True, undying=True)
    link_block(attacker, blocker)
    sim = CombatSimulator([attacker], [blocker])
    result = sim.simulate()
    assert blocker not in result.creatures_destroyed
    assert blocker.plus1_counters == 1
    assert blocker.minus1_counters == 0


def test_indestructible_lifelink_gains_life():
    """CR 702.15a & 702.12b: Lifelink causes life gain even if the creature is indestructible."""
    attacker = CombatCreature("Angel", 2, 2, "A", indestructible=True, lifelink=True)
    blocker = CombatCreature("Bear", 2, 2, "B")
    link_block(attacker, blocker)
    state = GameState(
        players={
            "A": PlayerState(life=10, creatures=[attacker]),
            "B": PlayerState(life=DEFAULT_STARTING_LIFE, creatures=[blocker]),
        }
    )
    sim = CombatSimulator([attacker], [blocker], game_state=state)
    result = sim.simulate()
    assert result.lifegain["A"] == 2
    assert attacker not in result.creatures_destroyed
    assert state.players["A"].life == 12


def test_trample_wither_vs_indestructible_blocker():
    """CR 702.19b, 702.90a & 702.12b: Trample with wither assigns lethal counters before excess damage."""
    attacker = CombatCreature("Toxic Beast", 3, 3, "A", trample=True, wither=True)
    blocker = CombatCreature("Steel Wall", 2, 2, "B", indestructible=True)
    link_block(attacker, blocker)
    sim = CombatSimulator([attacker], [blocker])
    result = sim.simulate()
    assert blocker in result.creatures_destroyed
    assert result.damage_to_players["B"] == 1
    assert blocker.minus1_counters == 2


def test_indestructible_attacker_multiple_blockers():
    """CR 702.12b: Even lethal damage from multiple blockers won't destroy an indestructible creature."""
    attacker = CombatCreature("Titan", 4, 4, "A", indestructible=True)
    b1 = CombatCreature("Soldier1", 2, 2, "B")
    b2 = CombatCreature("Soldier2", 2, 2, "B")
    link_block(attacker, b1, b2)
    sim = CombatSimulator([attacker], [b1, b2])
    result = sim.simulate()
    assert attacker not in result.creatures_destroyed
    assert b1 in result.creatures_destroyed
    assert b2 in result.creatures_destroyed
