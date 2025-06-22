import json
from magic_combat import create_random_combat, DEFAULT_STARTING_LIFE


def test_create_random_combat_initial_life(tmp_path):
    """CR 103.1a: Each player begins the game with 20 life."""
    sample = [
        {"name": "Alpha", "mana_cost": "{1}", "power": "1", "toughness": "1", "oracle_text": "", "keywords": []},
        {"name": "Bravo", "mana_cost": "{2}", "power": "2", "toughness": "2", "oracle_text": "Flying", "keywords": ["Flying"]},
        {"name": "Charlie", "mana_cost": "{3}", "power": "3", "toughness": "3", "oracle_text": "First strike", "keywords": ["First strike"]},
    ]
    path = tmp_path / "cards.json"
    path.write_text(json.dumps(sample))

    atk, blk, state = create_random_combat(2, 1, card_path=str(path))
    assert len(atk) == 2
    assert len(blk) == 1
    assert state.players["A"].life == DEFAULT_STARTING_LIFE
    assert state.players["B"].life == DEFAULT_STARTING_LIFE
