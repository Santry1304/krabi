"""Stage 2: Format transcript."""

from .base import BaseStage, StageResult


class FormatStage(BaseStage):
    """
    Stage 2: Format raw transcript.

    Structures raw transcription with speaker separation and paragraphs.
    """

    stage_id = 2
    stage_name = "02_format"
    stage_title = "Форматирование"

    input_files = ["01_loaded.md"]
    output_file = "02_formatted.md"

    def execute(self) -> StageResult:
        """
        Format transcript using LLM.

        Returns:
            StageResult
        """
        # Read input
        raw_text = self.read_input()

        # Call LLM (prompt loads automatically!)
        result = self.call_llm(raw_text)

        # Save output
        self.save_output(result.content)

        return StageResult(
            success=True,
            output_file=self.output_file,
            tokens_used=result.tokens_used
        )
