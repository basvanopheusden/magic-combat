# pylint: disable=missing-function-docstring, missing-module-docstring
from magic_combat import GameState
from magic_combat import PlayerState
from magic_combat.creature import CombatCreature


def test_playerstate_str_summarizes_creatures():
    creature = CombatCreature("Bear", 2, 2, "A")
    creature.plus1_counters = 2
    creature.minus1_counters = 1
    creature.damage_marked = 3
    creature.tapped = True
    ps = PlayerState(life=20, creatures=[creature])
    expected = (
        "Life: 20\n"
        "Poison: 0\n"
        "Creatures:\n"
        "  - Bear (2/2) [+1/+1 x2, -1/-1 x1, 3 dmg, tapped] -- none"
    )
    assert str(ps) == expected


def test_gamestate_str_uses_playerstate():
    creature = CombatCreature("Elf", 1, 1, "A", vigilance=True)
    ps = PlayerState(life=10, creatures=[creature])
    gs = GameState(players={"A": ps})
    text = str(gs)
    assert "Player A:" in text
    assert "- Elf (1/1) -- Vigilance" in text
