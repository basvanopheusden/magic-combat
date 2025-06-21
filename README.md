# Magic Combat

This project provides a small combat simulator inspired by trading card games
such as *Magic: The Gathering*.

The ``magic_combat`` package now includes fully implemented modules such as
``CombatCreature`` and ``CombatSimulator`` which handle blocking validation,
damage assignment, keyword abilities and more.

## Repository layout

```
magic_combat/                Core package containing combat code
magic_combat/creature.py     ``CombatCreature`` data model
magic_combat/damage.py       Damage assignment strategies
magic_combat/simulator.py    ``CombatSimulator`` and ``CombatResult`` classes
magic_combat/utils.py        Small utility helpers used internally
```

## Development

1. Install the requirements

```bash
pip install -r requirements.txt
```

2. Run the test suite

```bash
pytest
```

The test suite exercises many combat interactions to ensure the rules are
implemented correctly.

## Usage

```python
from magic_combat import CombatCreature, CombatSimulator

attacker = CombatCreature("Knight", 2, 2, "A")
blocker = CombatCreature("Goblin", 1, 1, "B")
attacker.blocked_by.append(blocker)
blocker.blocking = attacker

sim = CombatSimulator([attacker], [blocker])
result = sim.simulate()
print(result.creatures_destroyed)
```

## Downloading sample card data

The :func:`fetch_french_vanilla_cards` utility searches Scryfall for
"French vanilla" creatures. These are creature cards whose rules text
contains only keyword abilities recognized by ``CombatCreature``. The
resulting data can be stored locally using :func:`save_cards` and later
loaded with :func:`load_cards`.

```python
from magic_combat import fetch_french_vanilla_cards, save_cards

cards = fetch_french_vanilla_cards()
save_cards(cards, "data/cards.json")
```

For convenience you can also run ``fetch_cards.py`` from the repository
root to download the card data directly:

```bash
python fetch_cards.py data/cards.json
```
