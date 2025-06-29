class IterationCounter:
    """Track the number of simulated combats and enforce a maximum."""

    def __init__(self, max_iterations: int = int(1e5)) -> None:
        self.max_iterations = max_iterations
        self.count = 0

    def increment(self) -> None:
        """Increment the counter and raise ``RuntimeError`` if the limit is exceeded."""
        self.count += 1
        if self.count > self.max_iterations:
            raise RuntimeError("Maximum combat simulation iterations exceeded")
