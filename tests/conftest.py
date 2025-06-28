import sys
from pathlib import Path

# Ensure the package is importable when running tests from any location
sys.path.append(str(Path(__file__).resolve().parents[1]))


def link_block(attacker, *blockers):
    """Connect an attacker with one or more blockers."""
    attacker.blocked_by.extend(blockers)
    for b in blockers:
        b.blocking = attacker
