"""Gemini API Client with retry logic and streaming support."""

import google.generativeai as genai
from typing import Optional, Generator
import time
import logging

logger = logging.getLogger(__name__)


class GeminiClient:
    """Wrapper around Gemini API with retry and streaming capabilities."""

    def __init__(self, api_key: str, default_model: str = "gemini-2.0-flash-exp"):
        """
        Initialize Gemini client.

        Args:
            api_key: Google Gemini API key
            default_model: Default model to use
        """
        genai.configure(api_key=api_key)
        self.default_model = default_model
        self.max_retries = 3
        self.retry_delay = 5  # seconds
        self.last_token_count = 0

    def list_models(self) -> list[dict]:
        """
        Get list of available Gemini models.

        Returns:
            List of model information dictionaries
        """
        models = []
        for model in genai.list_models():
            if "generateContent" in model.supported_generation_methods:
                models.append({
                    "name": model.name,
                    "display_name": model.display_name,
                    "input_token_limit": model.input_token_limit,
                    "output_token_limit": model.output_token_limit
                })
        return models

    def generate(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_output_tokens: Optional[int] = None
    ) -> str:
        """
        Synchronous content generation with retry logic.

        Args:
            prompt: User prompt/content
            system_instruction: System instruction for the model
            model: Model name (uses default if not specified)
            temperature: Temperature for generation (0.0-1.0)
            max_output_tokens: Maximum tokens in response

        Returns:
            Generated text content

        Raises:
            Exception: If all retries fail
        """
        model_name = model or self.default_model

        generation_config = {
            "temperature": temperature,
        }
        if max_output_tokens:
            generation_config["max_output_tokens"] = max_output_tokens

        model_instance = genai.GenerativeModel(
            model_name=model_name,
            system_instruction=system_instruction,
            generation_config=generation_config
        )

        last_error = None
        for attempt in range(self.max_retries):
            try:
                logger.info(f"Calling Gemini API (attempt {attempt + 1}/{self.max_retries})")
                response = model_instance.generate_content(prompt)

                # Store token count if available
                if hasattr(response, 'usage_metadata'):
                    self.last_token_count = response.usage_metadata.total_token_count

                return response.text

            except Exception as e:
                last_error = e
                logger.warning(f"API call failed (attempt {attempt + 1}): {e}")

                if attempt < self.max_retries - 1:
                    delay = self.retry_delay * (attempt + 1)
                    logger.info(f"Retrying in {delay} seconds...")
                    time.sleep(delay)

        logger.error(f"All retries failed: {last_error}")
        raise last_error

    def generate_stream(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.7
    ) -> Generator[str, None, None]:
        """
        Streaming content generation for UI updates.

        Args:
            prompt: User prompt/content
            system_instruction: System instruction for the model
            model: Model name (uses default if not specified)
            temperature: Temperature for generation

        Yields:
            Text chunks as they are generated
        """
        model_name = model or self.default_model

        model_instance = genai.GenerativeModel(
            model_name=model_name,
            system_instruction=system_instruction,
            generation_config={"temperature": temperature}
        )

        response = model_instance.generate_content(prompt, stream=True)

        for chunk in response:
            if chunk.text:
                yield chunk.text

    def count_tokens(self, text: str, model: Optional[str] = None) -> int:
        """
        Count tokens in text.

        Args:
            text: Text to count tokens for
            model: Model name (uses default if not specified)

        Returns:
            Number of tokens
        """
        model_name = model or self.default_model
        model_instance = genai.GenerativeModel(model_name)
        return model_instance.count_tokens(text).total_tokens
