"""Custom exception types for the Magic Combat package."""


class MagicCombatError(Exception):
    """Base class for custom exceptions in this package."""


class UnparsableLLMOutputError(MagicCombatError):
    """Raised when language model output cannot be parsed."""


class IllegalBlockError(MagicCombatError, ValueError):
    """Raised when combat contains illegal blocking assignments."""


class InvalidBlockScenarioError(MagicCombatError):
    """Raised when generated block assignments are invalid or trivial."""


class IterationLimitError(MagicCombatError, RuntimeError):
    """Raised when a search exceeds the configured iteration limit."""
