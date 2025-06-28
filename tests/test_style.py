"""Style guide enforcement tests."""

import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
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
    """Ensure code is formatted with black."""
    run(f"black --check {ROOT}")


def test_isort() -> None:
    """Ensure imports are sorted with isort."""
    run(f"isort --check-only {ROOT}")


def test_flake8() -> None:
    """Run flake8 style checks."""
    run(f"flake8 --ignore=I100,I201,W503,E226 {ROOT}")


def test_pycodestyle() -> None:
    """Run pycodestyle checks."""
    opts = "--max-line-length=88 --ignore=E501,E203,E226,W503"
    run(f"pycodestyle {opts} {ROOT}")


def test_autoflake() -> None:
    """Ensure autoflake finds no issues."""
    run(f"autoflake -c -r {ROOT}")


def test_pylint() -> None:
    """Run pylint analysis."""
    run(f"pylint {ROOT}")


def test_mypy() -> None:
    """Run mypy type checking."""
    run(f"mypy {ROOT}")


def test_pyright() -> None:
    """Run pyright type checking."""
    run("pyright")
