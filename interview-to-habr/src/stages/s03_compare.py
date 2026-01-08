"""Stage 3: Compare and correct transcript."""

from .base import BaseStage, StageResult


class CompareStage(BaseStage):
    """
    Stage 3: Compare with original and correct.

    Compares formatted version with original to restore missing parts.
    """

    stage_id = 3
    stage_name = "03_compare"
    stage_title = "Сравнение и коррекция"

    input_files = ["01_loaded.md", "02_formatted.md"]
    output_file = "03_corrected.md"

    def execute(self) -> StageResult:
        """
        Compare and correct transcript using LLM.

        Returns:
            StageResult
        """
        # Read both files
        original = self.read_input("01_loaded.md")
        formatted = self.read_input("02_formatted.md")

        # Build content for LLM
        content = f"""## Оригинальная транскрипция
{original}

## Обработанная версия
{formatted}
"""

        # Call LLM
        result = self.call_llm(content)

        # Extract text part (before report)
        if "---ОТЧЁТ---" in result.content:
            text_part = result.content.split("---ОТЧЁТ---")[0].strip()
        else:
            text_part = result.content

        # Save corrected text
        self.save_output(text_part)

        # Optionally save full output with report
        self.save_output(result.content, "03_corrected_with_report.md")

        return StageResult(
            success=True,
            output_file=self.output_file,
            tokens_used=result.tokens_used
        )
