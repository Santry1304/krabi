"""Stage 6: Merge sections."""

from .base import BaseStage, StageResult


class MergeStage(BaseStage):
    """
    Stage 6: Merge sections into one article.

    Simple concatenation - does NOT use LLM.
    """

    stage_id = 6
    stage_name = "06_merge"
    stage_title = "Сведение секций"

    output_file = "06_merged.md"

    requires_llm = False  # No LLM needed!

    def execute(self) -> StageResult:
        """
        Merge all sections into one article.

        Returns:
            StageResult
        """
        # Load plan for titles
        plan = self.read_json("04_plan.json")

        # Read all section files
        sections_dir = self.stages_dir / "05_sections"
        section_files = sorted(sections_dir.glob("*.md"))

        if len(section_files) != len(plan["sections"]):
            return StageResult(
                success=False,
                error=f"Section count mismatch: {len(section_files)} files, {len(plan['sections'])} in plan"
            )

        # Build article
        parts = []

        # Title
        parts.append(f"# {plan['title']}\n")

        # Subtitle
        if plan.get("subtitle"):
            parts.append(f"*{plan['subtitle']}*\n")

        # Sections
        for i, (section_file, section_data) in enumerate(zip(section_files, plan["sections"])):
            section_text = section_file.read_text(encoding='utf-8')
            parts.append(f"\n## {section_data['title']}\n")
            parts.append(section_text)

        # Merge
        merged = "\n".join(parts)

        # Save
        self.save_output(merged)

        return StageResult(
            success=True,
            output_file=self.output_file,
            tokens_used=0,
            metadata={"sections_merged": len(section_files)}
        )
