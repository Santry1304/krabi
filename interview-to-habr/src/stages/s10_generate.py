"""Stage 10: Generate marketing materials."""

from .base import BaseStage, StageResult
from .s09_select import MATERIAL_TYPES


class GenerateStage(BaseStage):
    """
    Stage 10: Generate marketing materials.

    Generates selected marketing materials based on article.
    """

    stage_id = 10
    stage_name = "10_generate"
    stage_title = "Генерация материалов"

    input_files = ["07_edited.md", "08_analysis.md"]
    output_file = "output/materials/"

    def execute(self) -> StageResult:
        """
        Generate all selected materials using LLM.

        Returns:
            StageResult
        """
        # Load article and analysis
        article = self.read_input("07_edited.md")
        analysis = self.read_input("08_analysis.md")

        # Get selected materials from state
        selected = self.state.state.materials.get("selected", [])

        if not selected:
            return StageResult(
                success=False,
                error="No materials selected"
            )

        total_tokens = 0
        materials_dir = self.output_dir / "materials"
        materials_dir.mkdir(parents=True, exist_ok=True)

        # Generate each material
        for i, material_id in enumerate(selected):
            self.update_progress(i + 1, len(selected))

            material_info = MATERIAL_TYPES[material_id]

            # Build content
            content = f"""## Исходная статья

{article}

## Результаты маркетингового анализа

{analysis}
"""

            # Call LLM with material-specific prompt
            # Temporarily override stage_name to load correct prompt
            original_stage_name = self.stage_name
            self.stage_name = material_info["prompt_file"]

            result = self.call_llm(content)

            # Restore stage name
            self.stage_name = original_stage_name

            # Save material
            output_file = materials_dir / material_info["output_file"]
            output_file.write_text(result.content, encoding='utf-8')

            # Update state
            self.state.add_generated_material(
                material_id,
                str(output_file.relative_to(self.project_dir))
            )

            total_tokens += result.tokens_used

        return StageResult(
            success=True,
            output_file=self.output_file,
            tokens_used=total_tokens,
            metadata={"materials_generated": len(selected)}
        )
