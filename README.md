# Magic Combat
from llms.llm import call_anthropic_model
from magic_combat import CombatCreature
from magic_combat import CombatSimulator
from magic_combat import compute_card_statistics
from magic_combat import fetch_french_vanilla_cards
from magic_combat import generate_random_creature
from magic_combat import load_cards
from magic_combat import save_cards

This project provides a small combat simulator inspired by trading card games
such as *Magic: The Gathering*.

The ``magic_combat`` package now includes fully implemented modules such as
``CombatCreature`` and ``CombatSimulator`` which handle blocking validation,
damage assignment, keyword abilities and more.

This project requires **Python 3.12**.

## Installation

Install the package from the repository root using ``pip``:

```bash
pip install .
```

## Repository layout

```
magic_combat/                Core package containing combat code
magic_combat/creature.py     ``CombatCreature`` data model
magic_combat/damage.py       Damage assignment strategies
magic_combat/simulator.py    ``CombatSimulator`` and ``CombatResult`` classes
magic_combat/utils.py        Small utility helpers used internally
magic_combat/combat_utils.py Damage helpers for creatures and players
magic_combat/parsing.py      Parsing helpers for card data
magic_combat/random_creature.py Utilities for sampling creatures
magic_combat/blocking_ai.py  Blocking heuristics and search
magic_combat/block_utils.py  Utilities for evaluating block assignments
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

cards = fetch_french_vanilla_cards()  # optional ``timeout`` parameter
save_cards(cards, "data/cards.json")

# By default each request will wait up to 10 seconds; adjust ``timeout`` if
# you need a different value.
```

Alternatively, a small helper script ``scripts/download_cards.py`` can be run
from the repository root to perform the download.  It accepts an optional
``--timeout`` argument matching :func:`fetch_french_vanilla_cards`:

```bash
python scripts/download_cards.py data/cards.json
# python scripts/download_cards.py --timeout 5 data/cards.json
```

## Random creature generation

Once you have downloaded card data, you can build statistics for the real
creature distribution and sample new creatures from it:

```python

cards = load_cards("data/cards.json")
stats = compute_card_statistics(cards)
creature = generate_random_creature(stats)
print(creature)
```

## Utility functions

The :mod:`magic_combat.utils` module provides helpers for applying combat
bonuses programmatically. ``apply_attacker_blocking_bonuses`` grants bushido,
rampage and flanking bonuses to an attacker, while ``apply_blocker_bushido``
handles bushido on a blocker. ``magic_combat.combat_utils`` exposes
``damage_creature`` and ``damage_player`` for applying damage outside of the
``CombatSimulator`` class. The :mod:`magic_combat.rules_text` module also
provides ``describe_abilities`` for generating a comma-separated list of a
creature's keyword abilities.

## Using the OpenAI scripts

The ``scripts`` directory includes tools that rely on the OpenAI API.  These
require the ``openai`` package, which is installed when running ``pip install
-r requirements.txt``.  Before using these scripts you must set the
``OPENAI_API_KEY`` environment variable so that the client can authenticate.

``scripts/evaluate_random_combat_scenarios.py`` contacts the model to
evaluate blocking assignments for randomly generated combat scenarios.  A
typical invocation looks like this:

```bash
OPENAI_API_KEY=<your-key> \
    python scripts/evaluate_random_combat_scenarios.py -n 3 \
    --cards data/cards.json
```

The script will generate scenarios, send them to the model and print the
results to the console.

## Using Anthropic models

Support for Anthropic's Claude models is also provided.  Before using these
functions you must install the ``anthropic`` package (already included in
``requirements.txt``) and set the ``ANTHROPIC_API_KEY`` environment variable.
The :func:`llms.llm.call_anthropic_model` helper mirrors
``call_openai_model`` but queries the Anthropic API instead.  Example:

```bash
ANTHROPIC_API_KEY=<your-key> python - <<'EOF'
print(asyncio.run(call_anthropic_model(["Hello"], model="claude-3-sonnet-20240229")))
EOF
```
