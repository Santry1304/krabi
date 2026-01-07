"""Universal LLM processor - single point of entry for all LLM interactions."""

from dataclasses import dataclass
from typing import Optional
import logging

from .gemini_client import GeminiClient
from .prompt_manager import PromptManager

logger = logging.getLogger(__name__)


@dataclass
class LLMResult:
    """Result of LLM processing."""
    content: str
    tokens_used: int
    stage: str
    prompt_source: str  # "default" | "custom" | "project"


class LLMProcessor:
    """
    Universal processor for all LLM requests.
    ALL pipeline stages use ONLY this class.
    """

    def __init__(self, gemini_client: GeminiClient, prompt_manager: PromptManager):
        """
        Initialize LLM processor.

        Args:
            gemini_client: Gemini API client
            prompt_manager: Prompt manager (REQUIRED!)
        """
        self.client = gemini_client
        self.prompts = prompt_manager

    def process(
        self,
        stage_name: str,
        user_content: str,
        extra_context: Optional[dict] = None,
        temperature: float = 0.7,
        **kwargs
    ) -> LLMResult:
        """
        Universal processing method.

        Steps:
        1. Load system prompt for stage (with custom prompt support!)
        2. Build full request
        3. Send to Gemini
        4. Return result

        Args:
            stage_name: Stage name for loading prompt
            user_content: Content from user (transcript, text, etc.)
            extra_context: Additional context (plan, previous sections, etc.)
            temperature: Generation temperature
            **kwargs: Additional arguments for Gemini client

        Returns:
            LLMResult with content and metadata

        Raises:
            ValueError: If prompt not found
            Exception: If API call fails
        """
        # Load prompt (automatically checks custom prompts!)
        prompt_info = self.prompts.get_prompt_info(stage_name)

        # Log prompt source
        logger.info(f"Stage {stage_name}: using {prompt_info.source} prompt")

        # Build full prompt with context if provided
        full_prompt = self._build_prompt(user_content, extra_context)

        # Call Gemini API with retry
        response = self.client.generate(
            prompt=full_prompt,
            system_instruction=prompt_info.content,
            temperature=temperature,
            **kwargs
        )

        return LLMResult(
            content=response,
            tokens_used=self.client.last_token_count,
            stage=stage_name,
            prompt_source=prompt_info.source
        )

    def _build_prompt(self, user_content: str, extra_context: Optional[dict]) -> str:
        """
        Build full prompt from user content and context.

        Args:
            user_content: Main content
            extra_context: Additional context dictionary

        Returns:
            Full prompt string
        """
        if not extra_context:
            return user_content

        # If context provided, format it nicely
        parts = []

        # Add context sections
        for key, value in extra_context.items():
            if value:
                parts.append(f"## {key.replace('_', ' ').title()}")
                parts.append(str(value))
                parts.append("")

        # Add main content last
        parts.append("## Main Content")
        parts.append(user_content)

        return "\n".join(parts)

    def process_stream(
        self,
        stage_name: str,
        user_content: str,
        extra_context: Optional[dict] = None,
        temperature: float = 0.7
    ):
        """
        Process with streaming for UI updates.

        Args:
            stage_name: Stage name
            user_content: User content
            extra_context: Additional context
            temperature: Generation temperature

        Yields:
            Text chunks as they are generated
        """
        prompt_info = self.prompts.get_prompt_info(stage_name)
        logger.info(f"Stage {stage_name}: streaming with {prompt_info.source} prompt")

        full_prompt = self._build_prompt(user_content, extra_context)

        for chunk in self.client.generate_stream(
            prompt=full_prompt,
            system_instruction=prompt_info.content,
            temperature=temperature
        ):
            yield chunk
