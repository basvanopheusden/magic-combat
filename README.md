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
magic_combat/parsing.py      Parsing helpers for card data
magic_combat/random_creature.py Utilities for sampling creatures
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

Alternatively, a small helper script ``scripts/download_cards.py`` can be run
from the repository root to perform the download:

```bash
python scripts/download_cards.py data/cards.json
```

## Random creature generation

Once you have downloaded card data, you can build statistics for the real
creature distribution and sample new creatures from it:

```python
from magic_combat import load_cards, compute_card_statistics, generate_random_creature

cards = load_cards("data/cards.json")
stats = compute_card_statistics(cards)
creature = generate_random_creature(stats)
print(creature)
```
