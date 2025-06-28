"""Style guide enforcement tests."""

import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STYLE_FILE = ROOT / "style guide.md"


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
    """Run formatters and linters across the project to enforce the style guide."""
    run(f"black --check {ROOT}")
    run(f"isort --check-only --profile black {ROOT}")
    run(f"flake8 {ROOT}")
    run(f"pylint {ROOT}")
    run(f"mypy {ROOT}")
