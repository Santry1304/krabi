"""Stage 1: Load and normalize input file."""

from pathlib import Path
from .base import BaseStage, StageResult
from ..core.file_handlers import FileHandlerFactory, normalize_text
import shutil


class LoadStage(BaseStage):
    """
    Stage 1: Load input file.

    Loads TXT, DOCX, or MD file and normalizes it.
    Does NOT use LLM.
    """

    stage_id = 1
    stage_name = "01_load"
    stage_title = "Загрузка файла"

    output_file = "01_loaded.md"

    requires_llm = False  # No LLM needed!

    def __init__(self, project_dir: Path, llm_processor, state_manager, input_file: Path):
        """
        Initialize load stage.

        Args:
            project_dir: Project directory
            llm_processor: LLM processor (not used)
            state_manager: State manager
            input_file: Input file path
        """
        super().__init__(project_dir, llm_processor, state_manager)
        self.input_file = Path(input_file)

    def execute(self) -> StageResult:
        """
        Load and normalize input file.

        Returns:
            StageResult
        """
        # Copy original file to project
        original_dest = self.project_dir / "input" / f"original{self.input_file.suffix}"
        shutil.copy2(self.input_file, original_dest)

        # Read file using appropriate handler
        content = FileHandlerFactory.read_file(self.input_file)

        # Normalize text
        content = normalize_text(content)

        # Save as markdown
        self.save_output(content)

        # Update state input info
        self.state.state.input = {
            "original_file": str(self.input_file.name),
            "original_size": len(content),
            "format": self.input_file.suffix
        }
        self.state.save()

        return StageResult(
            success=True,
            output_file=self.output_file,
            tokens_used=0,
            metadata={"characters": len(content)}
        )
