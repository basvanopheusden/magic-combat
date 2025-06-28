"""Style guide enforcement tests."""

import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STYLE_FILE = ROOT / "style guide.md"
THIS_FILE = Path(__file__)


def run(cmd: str) -> None:
    """Run a shell command and assert it succeeds."""
    result = subprocess.run(
        cmd, shell=True, capture_output=True, text=True, check=False
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_style_guide_exists() -> None:
    """Ensure the style guide document is present."""
    assert STYLE_FILE.exists(), "style guide.md is missing"


def test_style_check() -> None:
    """Run formatters and linters on this file to enforce the style guide."""
    run(f"black --check {THIS_FILE}")
    run(f"isort --check-only {THIS_FILE}")
    run(f"q {THIS_FILE}")
    run(f"pylint -E {THIS_FILE}")
    run(f"mypy {THIS_FILE}")
