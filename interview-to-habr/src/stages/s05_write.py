"""Stage 5: Write article sections."""

import json
from .base import BaseStage, StageResult


class WriteStage(BaseStage):
    """
    Stage 5: Write article sections.

    Writes each section sequentially, passing ALL previous sections as context.
    """

    stage_id = 5
    stage_name = "05_write_section"
    stage_title = "Написание секций"

    input_files = ["03_corrected.md", "04_plan.json"]
    output_file = "05_sections/"

    def execute(self) -> StageResult:
        """
        Write all sections using LLM.

        Returns:
            StageResult
        """
        # Load data
        transcript = self.read_input("03_corrected.md")
        plan = self.read_json("04_plan.json")

        sections = plan["sections"]
        total = len(sections)
        written_sections: list[str] = []
        total_tokens = 0

        # Create sections directory
        sections_dir = self.stages_dir / "05_sections"
        sections_dir.mkdir(parents=True, exist_ok=True)

        for i, section in enumerate(sections):
            # Update progress
            self.update_progress(i + 1, total)

            # Build prompt for this section
            content = self._build_section_prompt(
                section=section,
                section_num=i + 1,
                total=total,
                transcript=transcript,
                plan=plan,
                previous_sections=written_sections  # ALL previous sections!
            )

            # Call LLM
            result = self.call_llm(content)

            # Save section
            section_file = f"{i+1:02d}_{self._slugify(section['title'])}.md"
            self.save_output(result.content, f"05_sections/{section_file}")

            # Add to context for next sections
            written_sections.append(result.content)
            total_tokens += result.tokens_used

        return StageResult(
            success=True,
            output_file=self.output_file,
            tokens_used=total_tokens,
            metadata={"sections_count": total}
        )

    def _build_section_prompt(
        self,
        section: dict,
        section_num: int,
        total: int,
        transcript: str,
        plan: dict,
        previous_sections: list[str]
    ) -> str:
        """
        Build prompt for writing a section.

        Args:
            section: Section data from plan
            section_num: Section number
            total: Total sections
            transcript: Full transcript
            plan: Full article plan
            previous_sections: List of ALL previously written sections

        Returns:
            Formatted prompt
        """
        # Format previous sections
        if previous_sections:
            prev_text = "\n\n---\n\n".join([
                f"## Секция {i+1}\n{text}"
                for i, text in enumerate(previous_sections)
            ])
        else:
            prev_text = "(Это первая секция статьи)"

        # Format key points
        key_points_text = "\n".join([f"- {point}" for point in section.get("key_points", [])])

        # Build full prompt
        return f"""## Полный план статьи

```json
{json.dumps(plan, ensure_ascii=False, indent=2)}
```

## Полная транскрипция интервью

{transcript}

## Уже написанные секции статьи

{prev_text}

## Текущая задача

Напиши секцию {section_num} из {total}: "{section['title']}"

### Ключевые тезисы для раскрытия в этой секции:

{key_points_text}

## Требования

- Используй релевантные цитаты и факты из транскрипции
- Обеспечь плавный переход от предыдущей секции (если она есть)
- Сохраняй единый стиль повествования
- НЕ повторяй то, что уже было сказано в предыдущих секциях
- Пиши только текст секции, без заголовка (заголовок уже есть в плане)
"""
