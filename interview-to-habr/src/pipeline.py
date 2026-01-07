"""Pipeline orchestrator for running stages."""

from pathlib import Path
from typing import Optional
import os
import yaml
import logging

from .core.gemini_client import GeminiClient
from .core.prompt_manager import PromptManager
from .core.llm_processor import LLMProcessor
from .core.state_manager import StateManager
from .stages import create_stage, StageResult

logger = logging.getLogger(__name__)


class Pipeline:
    """Pipeline orchestrator for managing project workflow."""

    def __init__(self, config_path: Optional[Path] = None):
        """
        Initialize pipeline.

        Args:
            config_path: Path to config.yaml (uses default if not specified)
        """
        # Load config
        if config_path is None:
            config_path = Path(__file__).parent.parent / "config.yaml"

        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = yaml.safe_load(f)

        # Initialize paths
        self.projects_dir = Path(self.config['paths']['projects_dir'])
        self.prompts_dir = Path(self.config['paths']['prompts_dir'])

        # Current project
        self.project_dir: Optional[Path] = None
        self.state_manager: Optional[StateManager] = None

        # Core components (initialized per project)
        self.gemini_client: Optional[GeminiClient] = None
        self.prompt_manager: Optional[PromptManager] = None
        self.llm_processor: Optional[LLMProcessor] = None

    def create_project(self, project_name: str, input_file: Path, model: Optional[str] = None) -> Path:
        """
        Create new project.

        Args:
            project_name: Project name
            input_file: Input file path
            model: Gemini model to use (uses default if not specified)

        Returns:
            Project directory path

        Raises:
            ValueError: If project already exists
        """
        project_dir = self.projects_dir / project_name

        if project_dir.exists():
            raise ValueError(f"Project already exists: {project_name}")

        # Create project directory
        project_dir.mkdir(parents=True, exist_ok=True)

        # Initialize state
        state_manager = StateManager(project_dir)
        project_config = {
            "model": model or self.config['gemini']['default_model'],
            "temperature": self.config['gemini']['temperature']
        }
        state_manager.create_new(project_name, project_config)

        logger.info(f"Created project: {project_name}")

        # Load project
        self.load_project(project_dir)

        # Run stage 1 (load file)
        self.run_stage(1, input_file=input_file)

        return project_dir

    def load_project(self, project_dir: Path):
        """
        Load existing project.

        Args:
            project_dir: Project directory path

        Raises:
            FileNotFoundError: If project not found
        """
        project_dir = Path(project_dir)

        if not project_dir.exists():
            raise FileNotFoundError(f"Project not found: {project_dir}")

        self.project_dir = project_dir

        # Initialize state manager
        self.state_manager = StateManager(project_dir)
        self.state_manager.load()

        if not self.state_manager.state:
            raise ValueError(f"Invalid project state in {project_dir}")

        # Initialize Gemini client
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable not set")

        model = self.state_manager.state.config.get("model", self.config['gemini']['default_model'])
        self.gemini_client = GeminiClient(api_key, model)

        # Initialize prompt manager
        self.prompt_manager = PromptManager(
            prompts_dir=self.prompts_dir,
            project_dir=project_dir
        )

        # Initialize LLM processor
        self.llm_processor = LLMProcessor(
            gemini_client=self.gemini_client,
            prompt_manager=self.prompt_manager
        )

        logger.info(f"Loaded project: {project_dir}")

    def run_stage(self, stage_num: int, **kwargs) -> StageResult:
        """
        Run specific stage.

        Args:
            stage_num: Stage number (1-10)
            **kwargs: Stage-specific arguments

        Returns:
            StageResult

        Raises:
            ValueError: If project not loaded or stage cannot run
        """
        if not self.project_dir or not self.state_manager:
            raise ValueError("No project loaded")

        # Check if stage can run
        if not self.state_manager.can_run_stage(stage_num):
            last_completed = self.state_manager.get_last_completed_stage()
            raise ValueError(
                f"Cannot run stage {stage_num}. "
                f"Complete stage {last_completed + 1} first."
            )

        # Create stage instance
        stage = create_stage(
            stage_num,
            project_dir=self.project_dir,
            llm_processor=self.llm_processor,
            state_manager=self.state_manager,
            **kwargs
        )

        # Run stage
        logger.info(f"Running stage {stage_num}: {stage.stage_title}")
        result = stage.run()

        if result.success:
            logger.info(f"Stage {stage_num} completed successfully")
        else:
            logger.error(f"Stage {stage_num} failed: {result.error}")

        return result

    def run_all(self, from_stage: int = 1, to_stage: int = 10, **kwargs) -> list[StageResult]:
        """
        Run multiple stages sequentially.

        Args:
            from_stage: Starting stage number
            to_stage: Ending stage number
            **kwargs: Arguments passed to stages

        Returns:
            List of StageResults

        Raises:
            ValueError: If project not loaded
        """
        if not self.project_dir or not self.state_manager:
            raise ValueError("No project loaded")

        results = []

        for stage_num in range(from_stage, to_stage + 1):
            # Check if already completed
            status = self.state_manager.get_stage_status(f"{stage_num}_*")

            # Run stage
            result = self.run_stage(stage_num, **kwargs)
            results.append(result)

            # Stop on error
            if not result.success:
                logger.error(f"Pipeline stopped at stage {stage_num}")
                break

        return results

    def get_project_status(self) -> dict:
        """
        Get current project status.

        Returns:
            Status dictionary

        Raises:
            ValueError: If project not loaded
        """
        if not self.state_manager or not self.state_manager.state:
            raise ValueError("No project loaded")

        state = self.state_manager.state

        return {
            "project_name": state.project_name,
            "current_stage": state.pipeline["current_stage"],
            "total_tokens": state.statistics["total_tokens_used"],
            "total_calls": state.statistics["total_api_calls"],
            "stages": state.pipeline["stages"]
        }

    def list_projects(self) -> list[dict]:
        """
        List all projects.

        Returns:
            List of project info dictionaries
        """
        if not self.projects_dir.exists():
            return []

        projects = []

        for project_path in self.projects_dir.iterdir():
            if not project_path.is_dir():
                continue

            state_file = project_path / "state.json"
            if not state_file.exists():
                continue

            try:
                temp_state = StateManager(project_path)
                temp_state.load()

                if temp_state.state:
                    projects.append({
                        "name": temp_state.state.project_name,
                        "path": str(project_path),
                        "created": temp_state.state.created_at.isoformat(),
                        "updated": temp_state.state.updated_at.isoformat(),
                        "current_stage": temp_state.state.pipeline["current_stage"]
                    })
            except Exception as e:
                logger.warning(f"Failed to load project {project_path}: {e}")
                continue

        return projects
