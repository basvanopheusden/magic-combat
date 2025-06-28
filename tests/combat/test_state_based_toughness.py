from magic_combat import CombatCreature
from magic_combat import CombatSimulator
from tests.conftest import link_block


def test_flanking_kills_weak_blocker_pre_damage():
    """CR 704.5f: A creature with toughness 0 or less is put into its owner's graveyard."""
    attacker = CombatCreature("Flanker", 1, 1, "A", flanking=1)
    blocker = CombatCreature("Vanilla", 1, 1, "B")
    link_block(attacker, blocker)
    sim = CombatSimulator([attacker], [blocker])
    result = sim.simulate()
    assert blocker in result.creatures_destroyed
    assert attacker not in result.creatures_destroyed


def test_minus_counters_can_cause_precombat_death():
    """CR 704.5f: State-based actions remove creatures with 0 toughness."""
    attacker = CombatCreature("Ogre", 2, 2, "A")
    blocker = CombatCreature("Weakling", 2, 2, "B", _minus1_counters=2)
    link_block(attacker, blocker)
    sim = CombatSimulator([attacker], [blocker])
    result = sim.simulate()
    assert blocker in result.creatures_destroyed
    assert attacker not in result.creatures_destroyed


def test_flanking_does_not_affect_other_flankers():
    """CR 702.25a: Flanking applies only to creatures without flanking."""
    attacker = CombatCreature("Knight1", 1, 1, "A", flanking=1)
    blocker = CombatCreature("Knight2", 1, 1, "B", flanking=1)
    link_block(attacker, blocker)
    sim = CombatSimulator([attacker], [blocker])
    result = sim.simulate()
    assert blocker in result.creatures_destroyed
    assert attacker in result.creatures_destroyed
