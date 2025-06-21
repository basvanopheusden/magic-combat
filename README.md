# Magic Combat

This project contains a very early skeleton for a small combat simulator inspired
by trading card games such as *Magic: The Gathering*.

At this stage only the module layout and a couple of stub classes exist. The
actual combat logic is intentionally left unimplemented and will be developed in
future iterations.

## Repository layout

```
magic_combat/       Core package containing combat code
magic_combat/creature.py     Basic ``CombatCreature`` dataclass
magic_combat/simulator.py    ``CombatSimulator`` and ``CombatResult`` stubs
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

The current tests simply verify that the package can be imported and that the
stubs are callable.
