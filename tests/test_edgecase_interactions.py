import pytest
from magic_combat import CombatCreature, CombatSimulator


def test_skulk_prevents_stronger_blocker():
    """CR 702.121a: A creature with skulk can't be blocked by creatures with greater power."""
    attacker = CombatCreature("Sneak", 1, 1, "A", skulk=True)
    blocker = CombatCreature("Giant", 3, 3, "B")
    attacker.blocked_by.append(blocker)
    blocker.blocking = attacker
    sim = CombatSimulator([attacker], [blocker])
    with pytest.raises(ValueError):
        sim.validate_blocking()


def test_skulk_bushido_with_weaker_blocker():
    """CR 702.46a: Bushido grants +N/+N when the creature becomes blocked."""
    attacker = CombatCreature("Sneaky Samurai", 1, 1, "A", skulk=True, bushido=1)
    blocker = CombatCreature("Peasant", 0, 2, "B")
    attacker.blocked_by.append(blocker)
    blocker.blocking = attacker
    sim = CombatSimulator([attacker], [blocker])
    result = sim.simulate()
    assert blocker in result.creatures_destroyed
    assert attacker not in result.creatures_destroyed


def test_flying_horsemanship_not_flying_only_block():
    """CR 702.30b: Horsemanship restricts blocking to creatures with horsemanship."""
    attacker = CombatCreature("Sky Rider", 2, 2, "A", flying=True, horsemanship=True)
    blocker = CombatCreature("Falcon", 1, 1, "B", flying=True)
    attacker.blocked_by.append(blocker)
    blocker.blocking = attacker
    sim = CombatSimulator([attacker], [blocker])
    with pytest.raises(ValueError):
        sim.validate_blocking()


def test_flying_horsemanship_not_horsemanship_only_block():
    """CR 702.9b and 702.30b: A blocker needs both flying (or reach) and horsemanship."""
    attacker = CombatCreature("Sky Rider", 2, 2, "A", flying=True, horsemanship=True)
    blocker = CombatCreature("Horseman", 1, 1, "B", horsemanship=True)
    attacker.blocked_by.append(blocker)
    blocker.blocking = attacker
    sim = CombatSimulator([attacker], [blocker])
    with pytest.raises(ValueError):
        sim.validate_blocking()


def test_flying_horsemanship_proper_blocker_allowed():
    """CR 702.30b: A creature with both abilities may block one with both."""
    attacker = CombatCreature("Sky Rider", 2, 2, "A", flying=True, horsemanship=True)
    blocker = CombatCreature("Pegasus Knight", 1, 3, "B", flying=True, horsemanship=True)
    attacker.blocked_by.append(blocker)
    blocker.blocking = attacker
    sim = CombatSimulator([attacker], [blocker])
    # Should not raise
    sim.validate_blocking()
    result = sim.simulate()
    assert result.creatures_destroyed == []
