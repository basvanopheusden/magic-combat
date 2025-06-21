import pytest

from magic_combat import CombatCreature, CombatSimulator, Color


def test_protection_allows_other_color_block():
    """CR 702.16b: Protection from a color doesn't stop blockers of other colors."""
    attacker = CombatCreature("Paladin", 2, 2, "A", protection_colors={Color.RED})
    blocker = CombatCreature("Bear", 2, 2, "B", colors={Color.GREEN})
    attacker.blocked_by.append(blocker)
    blocker.blocking = attacker
    sim = CombatSimulator([attacker], [blocker])
    sim.validate_blocking()


def test_protection_stops_matching_color():
    """CR 702.16b: A creature can't be blocked by creatures of a color it has protection from."""
    attacker = CombatCreature("Paladin", 2, 2, "A", protection_colors={Color.BLACK})
    blocker = CombatCreature("Shade", 2, 2, "B", colors={Color.BLACK})
    attacker.blocked_by.append(blocker)
    blocker.blocking = attacker
    sim = CombatSimulator([attacker], [blocker])
    with pytest.raises(ValueError):
        sim.validate_blocking()


def test_protection_multiple_colors_blocker_illegal():
    """CR 702.16b: Protection from multiple colors prevents blocking by any of those colors."""
    attacker = CombatCreature(
        "Champion", 3, 3, "A", protection_colors={Color.RED, Color.GREEN}
    )
    blocker = CombatCreature(
        "Hybrid", 2, 2, "B", colors={Color.RED, Color.BLUE}
    )
    attacker.blocked_by.append(blocker)
    blocker.blocking = attacker
    sim = CombatSimulator([attacker], [blocker])
    with pytest.raises(ValueError):
        sim.validate_blocking()


def test_protection_allows_colorless_artifact_block():
    """CR 702.16b: Protection from blue doesn't stop colorless artifact creatures from blocking."""
    attacker = CombatCreature("Mage", 2, 2, "A", protection_colors={Color.BLUE})
    blocker = CombatCreature("Golem", 2, 2, "B", artifact=True)
    attacker.blocked_by.append(blocker)
    blocker.blocking = attacker
    sim = CombatSimulator([attacker], [blocker])
    sim.validate_blocking()


def test_menace_with_protection_one_blocker_illegal():
    """CR 702.110b & 702.16b: Menace requires two blockers, and protection removes illegal blockers."""
    attacker = CombatCreature(
        "Guard", 3, 3, "A", menace=True, protection_colors={Color.GREEN}
    )
    legal = CombatCreature("Knight", 2, 2, "B", colors={Color.WHITE})
    illegal = CombatCreature("Elf", 2, 2, "B", colors={Color.GREEN})
    attacker.blocked_by.extend([legal, illegal])
    legal.blocking = attacker
    illegal.blocking = attacker
    sim = CombatSimulator([attacker], [legal, illegal])
    with pytest.raises(ValueError):
        sim.validate_blocking()


def test_menace_with_protection_two_legal_blockers():
    """CR 702.110b: Two legal blockers satisfy menace when none share a protected color."""
    attacker = CombatCreature(
        "Guard", 3, 3, "A", menace=True, protection_colors={Color.GREEN}
    )
    b1 = CombatCreature("Soldier1", 2, 2, "B", colors={Color.WHITE})
    b2 = CombatCreature("Soldier2", 2, 2, "B", colors={Color.RED})
    attacker.blocked_by.extend([b1, b2])
    b1.blocking = attacker
    b2.blocking = attacker
    sim = CombatSimulator([attacker], [b1, b2])
    sim.validate_blocking()


def test_intimidate_same_color_blocker_illegal_due_to_protection():
    """CR 702.13a & 702.16b: Intimidate allows same-color blockers, but protection from that color still prevents them."""
    attacker = CombatCreature(
        "Sneak", 2, 2, "A", intimidate=True, colors={Color.RED}, protection_colors={Color.RED}
    )
    blocker = CombatCreature("Berserker", 2, 2, "B", colors={Color.RED})
    attacker.blocked_by.append(blocker)
    blocker.blocking = attacker
    sim = CombatSimulator([attacker], [blocker])
    with pytest.raises(ValueError):
        sim.validate_blocking()


def test_intimidate_artifact_blocker_still_legal():
    """CR 702.13a: Artifact creatures may block an intimidate attacker even with protection from its color."""
    attacker = CombatCreature(
        "Sneak", 2, 2, "A", intimidate=True, colors={Color.BLACK}, protection_colors={Color.BLACK}
    )
    blocker = CombatCreature("Golem", 2, 2, "B", artifact=True)
    attacker.blocked_by.append(blocker)
    blocker.blocking = attacker
    sim = CombatSimulator([attacker], [blocker])
    sim.validate_blocking()


def test_has_protection_from_multiple_colors():
    """CR 702.16b: A creature can have protection from more than one color."""
    creature = CombatCreature(
        "Knight", 2, 2, "A", protection_colors={Color.WHITE, Color.BLUE}
    )
    assert creature.has_protection_from(Color.WHITE)
    assert creature.has_protection_from(Color.BLUE)
    assert not creature.has_protection_from(Color.BLACK)


def test_multicolor_blocker_illegal_if_contains_protected_color():
    """CR 702.16b: Any matching color in a multicolored blocker violates protection."""
    attacker = CombatCreature("Hero", 2, 2, "A", protection_colors={Color.GREEN})
    blocker = CombatCreature("Hybrid", 2, 2, "B", colors={Color.GREEN, Color.WHITE})
    attacker.blocked_by.append(blocker)
    blocker.blocking = attacker
    sim = CombatSimulator([attacker], [blocker])
    with pytest.raises(ValueError):
        sim.validate_blocking()


def test_multicolor_blocker_allowed_if_no_protected_colors():
    """CR 702.16b: A blocker with none of the protected colors may block."""
    attacker = CombatCreature("Hero", 2, 2, "A", protection_colors={Color.GREEN})
    blocker = CombatCreature("Hybrid", 2, 2, "B", colors={Color.BLUE, Color.WHITE})
    attacker.blocked_by.append(blocker)
    blocker.blocking = attacker
    sim = CombatSimulator([attacker], [blocker])
    sim.validate_blocking()
