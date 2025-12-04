"""Google Gemini model client implementation."""

import os
from typing import List, Optional

from dotenv import load_dotenv

try:
    import google.generativeai as genai
    GOOGLE_AI_AVAILABLE = True
except ImportError:
    GOOGLE_AI_AVAILABLE = False

from .base import ModelClient, Message, ModelResponse


class GoogleGeminiClient(ModelClient):
    """
    Model client for Google's Gemini models via the generativeai SDK.

    Requires GOOGLE_API_KEY environment variable to be set.
    """

    def __init__(
        self,
        model_name: str = "gemini-2.0-flash-exp",
        api_key: Optional[str] = None,
        default_temperature: float = 0.7,
        default_max_tokens: int = 2048,
    ):
        """
        Initialize Google Gemini client.

        Args:
            model_name: Gemini model to use (e.g., "gemini-2.0-flash-exp", "gemini-1.5-pro")
            api_key: Google API key (defaults to GOOGLE_API_KEY env var)
            default_temperature: Default temperature for generation
            default_max_tokens: Default max tokens for generation
        """
        if not GOOGLE_AI_AVAILABLE:
            raise ImportError(
                "google-generativeai package not installed. "
                "Install with: pip install google-generativeai"
            )

        self.model_name = model_name
        self.default_temperature = default_temperature
        self.default_max_tokens = default_max_tokens

        # Configure API key
        # Load from .env if present so local runs Just Work.
        load_dotenv()
        api_key = api_key or os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError(
                "Google API key required. Set GOOGLE_API_KEY environment variable "
                "or pass api_key parameter."
            )

        genai.configure(api_key=api_key)

        # Configure safety settings to allow code generation
        # (code diffs can sometimes trigger safety filters)
        from google.generativeai.types import HarmCategory, HarmBlockThreshold

        safety_settings = {
            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
        }

        self.model = genai.GenerativeModel(
            model_name,
            safety_settings=safety_settings,
        )

    async def chat(
        self,
        messages: List[Message],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> ModelResponse:
        """
        Send chat completion request to Gemini.

        Args:
            messages: List of conversation messages
            temperature: Sampling temperature (overrides default)
            max_tokens: Maximum tokens (overrides default)

        Returns:
            ModelResponse with generated text
        """
        # Use defaults if not specified
        temperature = temperature if temperature is not None else self.default_temperature
        max_tokens = max_tokens if max_tokens is not None else self.default_max_tokens

        # Convert messages to Gemini format
        # Gemini doesn't have a direct chat API, so we concatenate messages
        prompt = self._format_messages(messages)

        # Configure generation
        generation_config = genai.GenerationConfig(
            temperature=temperature,
            max_output_tokens=max_tokens,
        )

        # Generate response
        response = await self.model.generate_content_async(
            prompt,
            generation_config=generation_config,
        )

        # Extract response text with better error handling for blocked responses
        try:
            content = response.text
        except (ValueError, AttributeError) as e:
            # Handle blocked responses (safety filters, etc.)
            if hasattr(response, 'candidates') and response.candidates:
                candidate = response.candidates[0]
                finish_reason = getattr(candidate, 'finish_reason', 'UNKNOWN')
                safety_ratings = getattr(candidate, 'safety_ratings', [])

                error_msg = f"Response blocked by model (finish_reason={finish_reason})"
                if safety_ratings:
                    ratings_str = ", ".join([f"{r.category.name}:{r.probability.name}" for r in safety_ratings])
                    error_msg += f"\nSafety ratings: {ratings_str}"

                raise ValueError(error_msg) from e
            raise ValueError(f"Failed to get response text: {e}") from e

        # Build usage info if available
        usage = None
        if hasattr(response, 'usage_metadata'):
            usage = {
                'prompt_tokens': getattr(response.usage_metadata, 'prompt_token_count', 0),
                'completion_tokens': getattr(response.usage_metadata, 'candidates_token_count', 0),
                'total_tokens': getattr(response.usage_metadata, 'total_token_count', 0),
            }

        return ModelResponse(
            content=content,
            raw_response=response,
            model=self.model_name,
            usage=usage,
        )

    def _format_messages(self, messages: List[Message]) -> str:
        """
        Format messages for Gemini.

        For now, we concatenate messages with role prefixes.
        Future: Use Gemini's chat API when available.
        """
        formatted_parts = []

        for msg in messages:
            if msg.role == "system":
                formatted_parts.append(f"System: {msg.content}")
            elif msg.role == "user":
                formatted_parts.append(f"User: {msg.content}")
            elif msg.role == "assistant":
                formatted_parts.append(f"Assistant: {msg.content}")
            else:
                formatted_parts.append(msg.content)

        return "\n\n".join(formatted_parts)

    def get_model_name(self) -> str:
        """Return the Gemini model name."""
        return self.model_name
