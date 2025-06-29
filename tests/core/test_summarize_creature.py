from magic_combat.creature import CombatCreature
from magic_combat.text_utils import summarize_creature


def test_summarize_creature_includes_mana_cost():
    creature = CombatCreature("Wizard", 2, 3, "A", mana_cost="{1}{U}")
    summary = summarize_creature(creature)
    assert "{1}{U}" in summary
