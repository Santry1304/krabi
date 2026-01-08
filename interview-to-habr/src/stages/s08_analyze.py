"""Stage 8: Marketing analysis."""

from .base import BaseStage, StageResult


class AnalyzeStage(BaseStage):
    """
    Stage 8: Marketing analysis.

    Analyzes article for derivative marketing materials potential.
    """

    stage_id = 8
    stage_name = "08_marketing_analysis"
    stage_title = "Маркетинговый анализ"

    input_files = ["07_edited.md"]
    output_file = "08_analysis.md"

    def execute(self) -> StageResult:
        """
        Analyze article using LLM.

        Returns:
            StageResult
        """
        # Read final article
        article = self.read_input()

        # Call LLM
        result = self.call_llm(article)

        # Save analysis
        self.save_output(result.content)

        return StageResult(
            success=True,
            output_file=self.output_file,
            tokens_used=result.tokens_used
        )
