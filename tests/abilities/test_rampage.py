from magic_combat import CombatCreature, CombatSimulator


def test_rampage_unblocked_no_bonus():
    """CR 702.23a: Rampage only triggers when blocked by multiple creatures."""
    atk = CombatCreature("Beast", 3, 3, "A", rampage=2)
    defender = CombatCreature("Dummy", 0, 1, "B")
    sim = CombatSimulator([atk], [defender])
    result = sim.simulate()
    assert result.damage_to_players["B"] == 3
