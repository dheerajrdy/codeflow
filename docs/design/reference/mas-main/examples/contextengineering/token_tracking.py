"""
Token tracking middleware and utilities for context engineering demonstration.
"""

import time
from collections.abc import AsyncGenerator
from typing import Any, Dict, List, Optional

from picoagents._middleware import BaseMiddleware, MiddlewareContext
from picoagents.types import Usage


class TokenTrackingMiddleware(BaseMiddleware):
    """
    Middleware that tracks cumulative token usage across agent operations.

    Collects detailed token metrics for visualization and analysis.
    """

    def __init__(self):
        """Initialize token tracking."""
        self.token_history: List[Dict[str, Any]] = []
        self.cumulative_input = 0
        self.cumulative_output = 0
        self.operation_count = 0

    async def process_request(
        self, context: MiddlewareContext
    ) -> AsyncGenerator[MiddlewareContext, None]:
        """Record request timestamp."""
        context.metadata["token_tracking_start"] = time.time()
        yield context

    async def process_response(
        self, context: MiddlewareContext, result: Any
    ) -> AsyncGenerator[Any, None]:
        """Extract and record token usage from response."""
        # Extract token usage if available
        tokens_input = 0
        tokens_output = 0

        if hasattr(result, "usage") and result.usage:
            tokens_input = getattr(result.usage, "tokens_input", 0)
            tokens_output = getattr(result.usage, "tokens_output", 0)

        # Update cumulatives
        self.cumulative_input += tokens_input
        self.cumulative_output += tokens_output
        self.operation_count += 1

        # Record snapshot
        snapshot = {
            "operation": self.operation_count,
            "operation_type": context.operation,
            "agent_name": context.agent_name,
            "tokens_input": tokens_input,
            "tokens_output": tokens_output,
            "total_tokens": tokens_input + tokens_output,
            "cumulative_input": self.cumulative_input,
            "cumulative_output": self.cumulative_output,
            "cumulative_total": self.cumulative_input + self.cumulative_output,
            "timestamp": time.time(),
            "message_count": len(context.agent_context.messages)
            if context.agent_context
            else 0,
        }

        self.token_history.append(snapshot)

        yield result

    async def process_error(
        self, context: MiddlewareContext, error: Exception
    ) -> AsyncGenerator[Any, None]:
        """Handle errors - no token tracking on failures."""
        if False:  # Type checker hint
            yield
        raise error

    def get_summary(self) -> Dict[str, Any]:
        """Get summary statistics."""
        return {
            "total_operations": self.operation_count,
            "cumulative_input_tokens": self.cumulative_input,
            "cumulative_output_tokens": self.cumulative_output,
            "cumulative_total_tokens": self.cumulative_input + self.cumulative_output,
            "average_tokens_per_operation": (
                (self.cumulative_input + self.cumulative_output) / self.operation_count
                if self.operation_count > 0
                else 0
            ),
        }

    def get_history(self) -> List[Dict[str, Any]]:
        """Get complete token history."""
        return self.token_history.copy()

    def reset(self):
        """Reset all tracking."""
        self.token_history.clear()
        self.cumulative_input = 0
        self.cumulative_output = 0
        self.operation_count = 0


def estimate_tokens(text: str) -> int:
    """
    Estimate token count from text.

    Uses simple heuristic: ~4 characters per token.
    For accurate counting, use tiktoken library.
    """
    return len(text) // 4


def estimate_message_tokens(messages: List[Any]) -> int:
    """Estimate total tokens in a list of messages."""
    total = 0
    for msg in messages:
        if hasattr(msg, "content") and msg.content:
            total += estimate_tokens(str(msg.content))
    return total
