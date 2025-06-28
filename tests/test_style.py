"""Style guide enforcement tests."""

import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CODE_DIRS = "magic_combat scripts tests"
STYLE_FILE = ROOT / "style_guide.md"


def run(cmd: str) -> None:
    """Run a shell command and assert it succeeds."""
    result = subprocess.run(
        cmd, shell=True, capture_output=True, text=True, check=False
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_style_guide_exists() -> None:
    """Ensure the style guide document is present."""
    assert STYLE_FILE.exists(), "style_guide.md is missing"


def test_black() -> None:
    """Run ``black`` in check mode."""
    run(f"black --check {CODE_DIRS}")


def test_isort() -> None:
    """Ensure imports are properly sorted with ``isort``."""
    run(f"isort --profile black --check-only {CODE_DIRS}")


def test_flake8() -> None:
    """Run ``flake8`` for style compliance."""
    run(f"flake8 {CODE_DIRS}")


def test_pycodestyle() -> None:
    """Run ``pycodestyle`` for additional PEP 8 checks."""
    run(
        f"pycodestyle --max-line-length=2000 --ignore=E203,W503,E226 --exclude=comprehensive_rules.py {CODE_DIRS}"
    )


def test_autoflake() -> None:
    """Ensure ``autoflake`` finds no issues."""
    run(f"autoflake --check --recursive {CODE_DIRS}")


def test_pylint() -> None:
    """Run ``pylint`` on the code base."""
    run(f"pylint {CODE_DIRS}")


def test_mypy() -> None:
    """Run ``mypy`` for static type checking."""
    run(f"mypy {CODE_DIRS}")


def test_pyright() -> None:
    """Run ``pyright`` for additional type checking."""
    run(f"pyright {CODE_DIRS}")
