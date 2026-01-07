"""Base stage class with all common logic."""

from abc import ABC, abstractmethod
from pathlib import Path
from dataclasses import dataclass
from typing import Optional, TYPE_CHECKING
import json
import logging

if TYPE_CHECKING:
    from ..core.llm_processor import LLMProcessor, LLMResult
    from ..core.state_manager import StateManager

logger = logging.getLogger(__name__)


@dataclass
class StageResult:
    """Result of stage execution."""
    success: bool
    output_file: Optional[str] = None
    tokens_used: int = 0
    error: Optional[str] = None
    metadata: Optional[dict] = None


class BaseStage(ABC):
    """
    Base class for ALL pipeline stages.

    Contains ALL common logic:
    - Reading/writing files
    - LLM interaction via LLMProcessor
    - State updates
    - Error handling
    - Logging
    """

    # ═══════════════════════════════════════════════════════════════════
    # CONFIGURATION - override in subclasses
    # ═══════════════════════════════════════════════════════════════════

    stage_id: int = 0                    # Stage number (1-10)
    stage_name: str = ""                 # Name for prompt: "02_format"
    stage_title: str = ""                # Title for UI: "Форматирование"

    input_files: list[str] = []          # Input files
    output_file: str = ""                # Output file

    requires_llm: bool = True            # Does this stage need LLM?

    # ═══════════════════════════════════════════════════════════════════
    # INITIALIZATION
    # ═══════════════════════════════════════════════════════════════════

    def __init__(
        self,
        project_dir: Path,
        llm_processor: 'LLMProcessor',
        state_manager: 'StateManager'
    ):
        """
        Initialize stage.

        Args:
            project_dir: Project directory
            llm_processor: LLM processor instance
            state_manager: State manager instance
        """
        self.project_dir = Path(project_dir)
        self.llm = llm_processor
        self.state = state_manager
        self.stages_dir = project_dir / "stages"
        self.output_dir = project_dir / "output"

    # ═══════════════════════════════════════════════════════════════════
    # PUBLIC INTERFACE
    # ═══════════════════════════════════════════════════════════════════

    def run(self) -> StageResult:
        """
        Run stage with full error handling.

        This method is NOT overridden in subclasses!
        It implements common flow for all stages.

        Returns:
            StageResult
        """
        try:
            logger.info(f"Starting stage {self.stage_id}: {self.stage_title}")

            # 1. Mark as in progress
            self.state.update_stage(self.stage_key, "in_progress")

            # 2. Execute stage-specific logic
            result = self.execute()

            # 3. Save result
            if result.success:
                self.state.update_stage(
                    self.stage_key,
                    "completed",
                    output_file=result.output_file,
                    tokens_used=result.tokens_used
                )

                # Update statistics
                if result.tokens_used > 0:
                    self.state.update_statistics(
                        total_tokens_used=result.tokens_used,
                        total_api_calls=1
                    )

                logger.info(f"Stage {self.stage_id} completed successfully")

            return result

        except Exception as e:
            logger.error(f"Stage {self.stage_id} failed: {e}", exc_info=True)

            # Mark as error
            error_result = StageResult(success=False, error=str(e))
            self.state.update_stage(self.stage_key, "error", error_message=str(e))

            return error_result

    @abstractmethod
    def execute(self) -> StageResult:
        """
        Stage-specific logic.

        MUST be overridden in each subclass.
        Should return StageResult.

        Returns:
            StageResult
        """
        pass

    # ═══════════════════════════════════════════════════════════════════
    # HELPER METHODS - used by subclasses
    # ═══════════════════════════════════════════════════════════════════

    @property
    def stage_key(self) -> str:
        """
        Get stage key for state.json.

        Returns:
            Stage key (e.g., "2_format")
        """
        # Extract name from stage_name (e.g., "02_format" -> "format")
        if "_" in self.stage_name:
            name = self.stage_name.split("_", 1)[1]
        else:
            name = self.stage_name
        return f"{self.stage_id}_{name}"

    def read_input(self, filename: Optional[str] = None) -> str:
        """
        Read input file.

        Args:
            filename: File name (uses first input_file if not specified)

        Returns:
            File content

        Raises:
            ValueError: If no input file specified
            FileNotFoundError: If file not found
        """
        if filename is None:
            if not self.input_files:
                raise ValueError("No input file specified")
            filename = self.input_files[0]

        path = self.stages_dir / filename
        if not path.exists():
            raise FileNotFoundError(f"Input file not found: {path}")

        logger.info(f"Reading input: {path}")
        return path.read_text(encoding='utf-8')

    def read_json(self, filename: str) -> dict:
        """
        Read JSON file.

        Args:
            filename: JSON file name

        Returns:
            Parsed JSON data

        Raises:
            FileNotFoundError: If file not found
            json.JSONDecodeError: If invalid JSON
        """
        path = self.stages_dir / filename
        if not path.exists():
            raise FileNotFoundError(f"JSON file not found: {path}")

        logger.info(f"Reading JSON: {path}")
        return json.loads(path.read_text(encoding='utf-8'))

    def save_output(self, content: str, filename: Optional[str] = None) -> Path:
        """
        Save output file.

        Args:
            content: Content to save
            filename: File name (uses self.output_file if not specified)

        Returns:
            Path to saved file
        """
        if filename is None:
            filename = self.output_file

        path = self.stages_dir / filename
        path.parent.mkdir(parents=True, exist_ok=True)

        path.write_text(content, encoding='utf-8')
        logger.info(f"Saved output: {path}")
        return path

    def save_json(self, data: dict, filename: Optional[str] = None) -> Path:
        """
        Save JSON file.

        Args:
            data: Data to save
            filename: File name (uses self.output_file if not specified)

        Returns:
            Path to saved file
        """
        if filename is None:
            filename = self.output_file

        path = self.stages_dir / filename
        path.parent.mkdir(parents=True, exist_ok=True)

        path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding='utf-8'
        )
        logger.info(f"Saved JSON: {path}")
        return path

    def call_llm(
        self,
        content: str,
        extra_context: Optional[dict] = None,
        **kwargs
    ) -> 'LLMResult':
        """
        Call LLM via unified processor.

        Prompt is loaded automatically by self.stage_name!

        Args:
            content: Main content for LLM
            extra_context: Additional context dictionary
            **kwargs: Additional arguments for LLM

        Returns:
            LLMResult

        Raises:
            Exception: If LLM call fails
        """
        logger.info(f"Calling LLM for stage {self.stage_name}")
        return self.llm.process(
            stage_name=self.stage_name,
            user_content=content,
            extra_context=extra_context,
            **kwargs
        )

    def _slugify(self, text: str, max_length: int = 30) -> str:
        """
        Convert text to filename-safe slug.

        Args:
            text: Text to slugify
            max_length: Maximum length

        Returns:
            Slugified text
        """
        import re

        # Convert to lowercase
        slug = text.lower()

        # Replace spaces with underscores
        slug = slug.replace(" ", "_")

        # Remove non-alphanumeric characters (except underscore and dash)
        slug = re.sub(r'[^a-z0-9_-]', '', slug)

        # Limit length
        slug = slug[:max_length]

        return slug

    def update_progress(self, current: int, total: int):
        """
        Update stage progress.

        Args:
            current: Current item
            total: Total items
        """
        self.state.update_stage(
            self.stage_key,
            "in_progress",
            progress={"current": current, "total": total}
        )
        logger.info(f"Progress: {current}/{total}")
