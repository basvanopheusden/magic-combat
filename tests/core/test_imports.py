from magic_combat import CombatCreature, CombatResult, CombatSimulator


def test_imports():
    creature = CombatCreature(name="Goblin", power=1, toughness=1, controller="player")
    simulator = CombatSimulator([creature], [creature])
    assert isinstance(simulator.attackers[0], CombatCreature)
    assert simulator.all_creatures == [creature, creature]


def test_combat_result_dataclass():
    result = CombatResult(damage_to_players={"player": 0}, creatures_destroyed=[], lifegain={})
    assert result.damage_to_players["player"] == 0

