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
