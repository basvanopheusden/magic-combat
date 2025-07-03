"""Simple interface for language models."""

from .llm import call_anthropic_model
from .llm import call_openai_model

__all__ = ["call_openai_model", "call_anthropic_model"]
