"""Stage 9: Select materials."""

from .base import BaseStage, StageResult


# Material types definition
MATERIAL_TYPES = {
    "tg_vk_post": {
        "id": "tg_vk_post",
        "name": "Пост для Telegram/VK",
        "description": "Короткий пост для социальных сетей с ключевым инсайтом",
        "prompt_file": "materials/tg_vk_post",
        "output_file": "tg_vk_post.md"
    },
    "email_announce": {
        "id": "email_announce",
        "name": "Анонс для рассылки",
        "description": "Email-анонс статьи для подписчиков",
        "prompt_file": "materials/email_announce",
        "output_file": "email_announce.md"
    },
    "press_release": {
        "id": "press_release",
        "name": "Пресс-релиз",
        "description": "Официальный пресс-релиз о публикации",
        "prompt_file": "materials/press_release",
        "output_file": "press_release.md"
    },
    "cards": {
        "id": "cards",
        "name": "Карточки для соцсетей",
        "description": "Серия карточек с ключевыми тезисами и цифрами",
        "prompt_file": "materials/cards",
        "output_file": "cards.md"
    },
    "business_media": {
        "id": "business_media",
        "name": "Статья для делового СМИ",
        "description": "Адаптация для РБК, Коммерсант и подобных изданий",
        "prompt_file": "materials/business_media",
        "output_file": "business_media.md"
    }
}


class SelectStage(BaseStage):
    """
    Stage 9: Select materials to generate.

    Interactive selection - does NOT use LLM.
    Updates state with selected materials.
    """

    stage_id = 9
    stage_name = "09_select"
    stage_title = "Выбор материалов"

    input_files = ["08_analysis.md"]

    requires_llm = False  # No LLM needed!

    def __init__(self, project_dir, llm_processor, state_manager, selected_materials: list[str] = None):
        """
        Initialize select stage.

        Args:
            project_dir: Project directory
            llm_processor: LLM processor (not used)
            state_manager: State manager
            selected_materials: List of selected material IDs (if None, selects all)
        """
        super().__init__(project_dir, llm_processor, state_manager)
        self.selected_materials = selected_materials

    def execute(self) -> StageResult:
        """
        Select materials to generate.

        Returns:
            StageResult
        """
        # If no selection provided, select all materials
        if self.selected_materials is None:
            self.selected_materials = list(MATERIAL_TYPES.keys())

        # Validate selections
        invalid = [m for m in self.selected_materials if m not in MATERIAL_TYPES]
        if invalid:
            return StageResult(
                success=False,
                error=f"Invalid material types: {', '.join(invalid)}"
            )

        # Update state
        self.state.state.materials["selected"] = self.selected_materials
        self.state.save()

        return StageResult(
            success=True,
            tokens_used=0,
            metadata={"selected_count": len(self.selected_materials)}
        )

    @staticmethod
    def get_material_types() -> dict:
        """
        Get available material types.

        Returns:
            Dictionary of material types
        """
        return MATERIAL_TYPES
