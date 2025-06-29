class IterationCounter:
    """Track the number of simulated combats and enforce a maximum."""

    def __init__(self, max_iterations: int = int(1e5)) -> None:
        self.max_iterations = max_iterations
        self.count = 0

    def increment(self) -> None:
        """Increment the counter and raise ``IterationLimitError`` if exceeded."""
        self.count += 1
        if self.count > self.max_iterations:
            from .exceptions import IterationLimitError

            raise IterationLimitError("Maximum combat simulation iterations exceeded")
