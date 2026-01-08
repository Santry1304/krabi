"""Stage 7: Literary editing."""

from .base import BaseStage, StageResult


class EditStage(BaseStage):
    """
    Stage 7: Literary editing.

    Final editing pass to improve readability and style.
    """

    stage_id = 7
    stage_name = "07_literary_edit"
    stage_title = "Литературная правка"

    input_files = ["06_merged.md"]
    output_file = "07_edited.md"

    def execute(self) -> StageResult:
        """
        Edit article using LLM.

        Returns:
            StageResult
        """
        # Read merged article
        article = self.read_input()

        # Call LLM
        result = self.call_llm(article)

        # Save edited article
        self.save_output(result.content)

        # Also copy to output as final article
        output_path = self.output_dir / "final_article.md"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(result.content, encoding='utf-8')

        return StageResult(
            success=True,
            output_file=self.output_file,
            tokens_used=result.tokens_used
        )
