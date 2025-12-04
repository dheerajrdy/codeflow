"""Base model client abstraction."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional, Dict, Any


@dataclass
class Message:
    """Chat message."""
    role: str  # "user", "assistant", "system"
    content: str


@dataclass
class ModelResponse:
    """Response from a model."""
    content: str
    raw_response: Optional[Any] = None
    model: Optional[str] = None
    usage: Optional[Dict[str, int]] = None  # token counts, etc.


class ModelClient(ABC):
    """
    Abstract base class for model clients.
    Provides a unified interface for different LLM providers.
    """

    @abstractmethod
    async def chat(
        self,
        messages: List[Message],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> ModelResponse:
        """
        Send a chat completion request to the model.

        Args:
            messages: List of conversation messages
            temperature: Sampling temperature (0.0 to 1.0)
            max_tokens: Maximum tokens to generate

        Returns:
            ModelResponse with the generated text
        """
        pass

    @abstractmethod
    def get_model_name(self) -> str:
        """Return the model name/identifier."""
        pass
