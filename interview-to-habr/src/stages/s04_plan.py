"""Stage 4: Create article plan."""

import json
from .base import BaseStage, StageResult


class PlanStage(BaseStage):
    """
    Stage 4: Create article plan.

    Creates structured plan with sections and key points.
    """

    stage_id = 4
    stage_name = "04_plan"
    stage_title = "План статьи"

    input_files = ["03_corrected.md"]
    output_file = "04_plan.json"

    def execute(self) -> StageResult:
        """
        Create article plan using LLM.

        Returns:
            StageResult
        """
        # Read corrected transcript
        transcript = self.read_input()

        # Call LLM
        result = self.call_llm(transcript)

        # Parse JSON from response
        plan = self._extract_json(result.content)

        # Validate plan structure
        if not self._validate_plan(plan):
            return StageResult(
                success=False,
                error="Invalid plan structure returned by LLM"
            )

        # Save plan as JSON
        self.save_json(plan)

        # Also save as readable markdown
        self._save_plan_markdown(plan)

        return StageResult(
            success=True,
            output_file=self.output_file,
            tokens_used=result.tokens_used,
            metadata={"sections_count": len(plan.get("sections", []))}
        )

    def _extract_json(self, text: str) -> dict:
        """
        Extract JSON from LLM response.

        Args:
            text: Response text

        Returns:
            Parsed JSON

        Raises:
            ValueError: If JSON not found or invalid
        """
        # Try to find JSON in response (may be wrapped in markdown code block)
        import re

        # Try to extract from code block
        json_match = re.search(r'```(?:json)?\s*\n?(.*?)\n?```', text, re.DOTALL)
        if json_match:
            json_text = json_match.group(1)
        else:
            # Try to find JSON object directly
            json_match = re.search(r'\{.*\}', text, re.DOTALL)
            if json_match:
                json_text = json_match.group(0)
            else:
                # Use entire text
                json_text = text

        return json.loads(json_text)

    def _validate_plan(self, plan: dict) -> bool:
        """
        Validate plan structure.

        Args:
            plan: Plan dictionary

        Returns:
            True if valid
        """
        required_fields = ["title", "sections"]

        for field in required_fields:
            if field not in plan:
                return False

        # Validate sections
        if not isinstance(plan["sections"], list) or len(plan["sections"]) == 0:
            return False

        for section in plan["sections"]:
            if "title" not in section or "key_points" not in section:
                return False

        return True

    def _save_plan_markdown(self, plan: dict):
        """
        Save plan as readable markdown.

        Args:
            plan: Plan dictionary
        """
        lines = [f"# {plan['title']}\n"]

        if plan.get("subtitle"):
            lines.append(f"*{plan['subtitle']}*\n")

        if plan.get("tags"):
            lines.append(f"**Теги:** {', '.join(plan['tags'])}\n")

        lines.append("\n## Структура статьи\n")

        for i, section in enumerate(plan["sections"], 1):
            lines.append(f"\n### {i}. {section['title']}\n")

            if section.get("key_points"):
                lines.append("\n**Ключевые тезисы:**\n")
                for point in section["key_points"]:
                    lines.append(f"- {point}\n")

        content = "\n".join(lines)
        self.save_output(content, "04_plan_readable.md")
