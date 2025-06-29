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


class CardDataError(MagicCombatError, ValueError):
    """Raised when card data is missing or unusable."""


class ScenarioGenerationError(MagicCombatError, RuntimeError):
    """Raised when a random scenario cannot be generated."""


class MissingStatisticsError(MagicCombatError, ValueError):
    """Raised when required statistics are not provided."""
