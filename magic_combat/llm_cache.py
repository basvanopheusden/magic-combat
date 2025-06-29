import json
from pathlib import Path
from typing import Optional
from typing import cast


class LLMCache:
    """Simple JSONL cache for LLM responses."""

    def __init__(self, path: str) -> None:
        self.path = Path(path)
        self.entries: list[dict[str, object]] = []
        if self.path.exists():
            with self.path.open(encoding="utf8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        self.entries.append(json.loads(line))

    def get(
        self, prompt: str, model: str, seed: int, temperature: float
    ) -> Optional[str]:
        for entry in self.entries:
            if (
                entry.get("prompt") == prompt
                and entry.get("model") == model
                and entry.get("seed") == seed
                and entry.get("temperature") == temperature
            ):
                return cast(Optional[str], entry.get("response"))
        return None

    def add(
        self,
        prompt: str,
        model: str,
        seed: int,
        temperature: float,
        response: str,
    ) -> None:
        entry: dict[str, object] = {
            "prompt": prompt,
            "model": model,
            "seed": seed,
            "temperature": temperature,
            "response": response,
        }
        self.entries.append(entry)
        with self.path.open("a", encoding="utf8") as f:
            f.write(json.dumps(entry) + "\n")


class MockLLMCache(LLMCache):
    """In-memory cache for testing purposes."""

    def __init__(self) -> None:
        self.entries: list[dict[str, object]] = []
        self.path = None  # type: ignore[assignment]

    def add(
        self,
        prompt: str,
        model: str,
        seed: int,
        temperature: float,
        response: str,
    ) -> None:
        entry: dict[str, object] = {
            "prompt": prompt,
            "model": model,
            "seed": seed,
            "temperature": temperature,
            "response": response,
        }
        self.entries.append(entry)
        # No file operations for mock cache
