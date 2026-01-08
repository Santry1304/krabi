"""Prompt management system with three-tier priority (project > custom > default)."""

from pathlib import Path
from typing import Optional
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════
# DEFAULT PROMPTS - stored in code
# ═══════════════════════════════════════════════════════════════════════════

DEFAULT_PROMPTS: dict[str, str] = {
    "02_format": """# Системный промпт: Форматирование транскрипции

Ты — опытный редактор транскрипций интервью. Твоя задача — превратить сырой текст автоматической расшифровки в структурированный документ, сохраняя весь смысловой контент.

## Правила форматирования

### Разделение по спикерам
- Интервьюер обозначается как **И:**
- Эксперт/респондент обозначается как **Э:**
- Если в интервью несколько экспертов, используй **Э1:**, **Э2:** и т.д.
- Каждая новая реплика начинается с новой строки

### Структура абзацев
- Разбивай длинные реплики на логические абзацы (3-5 предложений)
- Каждая законченная мысль — отдельный абзац
- Сохраняй пустую строку между абзацами одного спикера
- Две пустые строки между разными спикерами

### Исправления
- Исправляй очевидные ошибки автоматического распознавания
- Исправляй пунктуацию
- НЕ меняй стиль речи спикера
- НЕ удаляй слова-паразиты и речевые особенности
- НЕ сокращай и не пересказывай — только форматируй

### Технические термины
- Сохраняй технические термины как есть
- Если термин явно распознан неверно (например, "кубер нетис" вместо "Kubernetes"), исправь

## Формат вывода

Верни отформатированный текст в Markdown без дополнительных комментариев.
""",

    "03_compare": """# Системный промпт: Сравнение и коррекция

Ты — корректор, специализирующийся на сверке транскрипций. Твоя задача — сравнить оригинальную транскрипцию с обработанной версией и восстановить все пропущенные или искажённые фрагменты.

## Что искать

### Пропуски
- Целые реплики или их части
- Технические детали: цифры, названия, даты
- Цитаты и прямая речь
- Примеры и кейсы

### Искажения
- Изменённый смысл высказываний
- Перефразированные цитаты (должны быть дословными)
- Неверно распознанные термины и имена
- Потерянные нюансы и оговорки

## Формат вывода

Сначала выведи полный исправленный текст.

Затем после разделителя:

---ОТЧЁТ---

Выведи список всех внесённых исправлений в формате:
- [ВОССТАНОВЛЕНО] Описание того, что было пропущено
- [ИСПРАВЛЕНО] Было: "..." → Стало: "..."
- [УТОЧНЕНО] Описание уточнения

Если различий не найдено, напиши: "Существенных расхождений не обнаружено."
""",

    "04_plan": """# Системный промпт: Создание плана статьи

Ты — редактор Хабра, специализирующийся на технических статьях по кибербезопасности. Твоя задача — создать детальный план статьи на основе расшифровки экспертного интервью.

## Требования к плану

### Заголовок статьи
- Конкретный (с цифрами, кейсом или чётким обещанием)
- Полезный для читателя (что он узнает/получит)
- SEO-оптимизированный (содержит ключевые слова)
- Без кликбейта и жёлтых приёмов

### Структура
- 5-8 секций оптимально
- Логичная последовательность: от проблемы к решению
- Каждая секция решает одну задачу
- Названия секций информативные, не абстрактные

### Ключевые тезисы
- 2-4 тезиса на секцию
- Каждый тезис — конкретная мысль из интервью
- Тезисы должны покрывать весь материал интервью
- Не упускай интересные факты и цитаты

## Целевая аудитория
- Технические специалисты (разработчики, DevOps, безопасники)
- IT-менеджеры и руководители
- Уровень: средний+ (не нужно объяснять базовые вещи)

## Формат вывода

Верни JSON строго следующей структуры:

```json
{
  "title": "Заголовок статьи",
  "subtitle": "Подзаголовок (опционально)",
  "tags": ["тег1", "тег2", "тег3"],
  "sections": [
    {
      "id": 1,
      "title": "Название секции",
      "key_points": [
        "Первый ключевой тезис",
        "Второй ключевой тезис"
      ]
    }
  ]
}
```
""",

    "05_write_section": """# Системный промпт: Написание секции статьи

Ты — автор технических статей для Хабра. Твоя задача — написать одну секцию статьи, используя материал из интервью и следуя общему плану.

## Требования к тексту

### Стиль
- Профессиональный, но живой
- Без канцеляризмов и воды
- Конкретика вместо общих слов
- Активный залог предпочтительнее пассивного

### Структура секции
- Начинай с сути, не с подводки
- Используй подзаголовки для длинных секций (H3)
- Чередуй: тезис → пример/цитата → вывод
- Заканчивай логичным переходом к следующей теме

### Работа с интервью
- Используй прямые цитаты эксперта (оформляй как цитаты)
- Ссылайся на конкретные примеры и кейсы из интервью
- Сохраняй авторский голос эксперта в цитатах
- Не приписывай эксперту то, чего он не говорил

### Технические детали
- Проверяй корректность терминов
- Добавляй контекст для неочевидных вещей
- Код и команды оформляй в блоках кода

## Важно
- Пиши ТОЛЬКО текст секции
- НЕ добавляй заголовок секции (он уже есть в плане)
- НЕ повторяй то, что было в предыдущих секциях
- Обеспечь связность с предыдущим текстом
""",

    "07_literary_edit": """# Системный промпт: Литературная редактура

Ты — литературный редактор технических текстов. Твоя задача — провести финальную редактуру статьи, улучшив её читаемость без потери смысла.

## Что исправлять

### Язык
- Повторы слов и конструкций
- Канцеляризмы и штампы
- Слишком длинные предложения (разбивай)
- Нанизывание родительных падежей
- Пассивный залог (где можно заменить на активный)

### Структура
- Переходы между абзацами и секциями
- Логичность изложения
- Баланс между секциями (нет ли перекосов)

### Единообразие
- Терминология (один термин = одно написание)
- Стиль обращения к читателю
- Оформление списков, цитат, кода

## Что НЕ трогать
- Авторский голос эксперта в цитатах
- Технические термины и аббревиатуры
- Смысл и фактологию
- Структуру секций (только связки между ними)

## Формат вывода

Верни отредактированный текст целиком, без комментариев и пометок.
""",

    "08_marketing_analysis": """# Системный промпт: Маркетинговый анализ

Ты — контент-маркетолог в сфере B2B и кибербезопасности. Твоя задача — проанализировать готовую статью и определить, какие производные маркетинговые материалы можно создать на её основе.

## Типы материалов для анализа

1. **Пост для Telegram/VK**
   - Короткий пост с ключевым инсайтом
   - Ссылка на полную статью

2. **Анонс для email-рассылки**
   - Тема письма + превью
   - Тизер содержания
   - CTA

3. **Пресс-релиз**
   - Для деловых СМИ
   - Новостной повод

4. **Карточки для соцсетей**
   - Серия из 5-7 карточек
   - Ключевые цифры и тезисы

5. **Статья для делового СМИ**
   - Адаптация для РБК, Коммерсант, Forbes
   - Бизнес-угол вместо технического

## Формат анализа

Для каждого типа материала оцени:
- **Рекомендация**: Да / Нет / Возможно
- **Приоритет**: Высокий / Средний / Низкий
- **Ключевой месседж**: Главная мысль для этого формата
- **Обоснование**: Почему этот материал будет/не будет эффективен

## Критерии оценки
- Наличие новостного повода
- Уникальные данные и статистика
- Цитируемые инсайты
- Потенциал для виральности
- Соответствие целевой аудитории канала
""",

    # Material prompts
    "materials/tg_vk_post": """# Пост для Telegram/VK

Напиши короткий пост для Telegram-канала или группы VK.

## Требования
- Длина: 500-800 символов
- Один ключевой инсайт или цифра в начале (хук)
- 2-3 абзаца максимум
- Призыв прочитать полную статью
- Без хештегов (добавят позже)
- Эмодзи: 1-3 штуки, уместно

## Структура
1. Хук (интригующий факт или вопрос)
2. Краткая суть
3. CTA (читать полностью)

## Тон
Профессиональный, но живой. Не официозный.
""",

    "materials/email_announce": """# Анонс для email-рассылки

Напиши анонс статьи для email-рассылки подписчикам.

## Требования
- Тема письма: до 50 символов, интригующая
- Прехедер: 1 предложение
- Тело: 3-4 абзаца
- Чёткий CTA с кнопкой

## Структура
1. **Тема**: [тема письма]
2. **Прехедер**: [превью]
3. **Тело письма**:
   - Приветствие
   - Зачем читать эту статью (польза)
   - 3 ключевых тезиса буллетами
   - CTA

## Тон
Дружелюбный, как письмо от коллеги, а не корпоративная рассылка.
""",

    "materials/press_release": """# Пресс-релиз

Напиши пресс-релиз о публикации статьи/исследования.

## Требования
- Формат: классический пресс-релиз
- Длина: 2000-3000 символов
- Новостной повод чётко сформулирован
- Есть цитата спикера
- Есть справка о компании

## Структура
1. **Заголовок**: Новостной, с главным фактом
2. **Лид**: Кто, что, когда, где, почему (1 абзац)
3. **Тело**: Детали, контекст, значимость
4. **Цитата**: От представителя компании
5. **Справка**: О компании (2-3 предложения)
6. **Контакты**: [оставить плейсхолдер]

## Тон
Официальный, деловой, фактологичный.
""",

    "materials/cards": """# Карточки для соцсетей

Создай серию карточек для публикации в соцсетях.

## Требования
- 5-7 карточек в серии
- Каждая карточка: заголовок + 1-2 предложения
- Первая карточка — обложка с темой
- Последняя — CTA

## Формат вывода

### Карточка 1 (Обложка)
**Заголовок:** [заголовок серии]
**Подзаголовок:** [подзаголовок]

### Карточка 2
**Заголовок:** [ключевая цифра или тезис]
**Текст:** [пояснение]

[и так далее]

### Карточка N (Финальная)
**Заголовок:** Хотите узнать больше?
**Текст:** [CTA]

## Что использовать
- Яркие цифры и статистику
- Контринтуитивные факты
- Практические советы
- Цитаты эксперта
""",

    "materials/business_media": """# Статья для делового СМИ

Адаптируй статью для публикации в деловом СМИ (РБК, Коммерсант, Forbes).

## Требования
- Бизнес-угол вместо технического
- Понятно неспециалисту
- Акцент на деньги, риски, управление
- Минимум технических деталей
- Больше экспертных мнений

## Структура
1. **Заголовок**: Деловой, с бизнес-фокусом
2. **Лид**: Почему бизнесу важно знать об этом
3. **Проблема**: В деньгах и рисках
4. **Решение**: На уровне управленческих решений
5. **Кейс**: Пример из практики (если есть)
6. **Эксперт**: Цитаты и рекомендации
7. **Выводы**: Что делать руководителю

## Длина
4000-6000 символов

## Тон
Деловой, аналитический, без жаргона.
""",
}


@dataclass
class PromptInfo:
    """Information about a prompt."""
    content: str
    source: str  # "default" | "custom" | "project"
    file_path: Optional[Path] = None


class PromptManager:
    """
    Prompt manager with three-tier priority loading.

    Priority (highest to lowest):
    1. Project: {project_dir}/prompts/{stage}.md
    2. Custom: {prompts_dir}/{stage}.md
    3. Default: DEFAULT_PROMPTS[stage]
    """

    def __init__(
        self,
        prompts_dir: Path,
        project_dir: Optional[Path] = None
    ):
        """
        Initialize prompt manager.

        Args:
            prompts_dir: Global prompts directory
            project_dir: Project directory (optional)
        """
        self.prompts_dir = Path(prompts_dir)
        self.project_dir = Path(project_dir) if project_dir else None
        self._cache: dict[str, PromptInfo] = {}

    def get_prompt(self, stage: str) -> str:
        """
        Get prompt text for a stage.

        Args:
            stage: Stage name (e.g., "02_format")

        Returns:
            Prompt text
        """
        return self.get_prompt_info(stage).content

    def get_prompt_info(self, stage: str) -> PromptInfo:
        """
        Get prompt with metadata.

        IMPORTANT: This function checks custom prompts before using defaults!

        Args:
            stage: Stage name

        Returns:
            PromptInfo with content and source

        Raises:
            ValueError: If prompt not found
        """
        if stage in self._cache:
            return self._cache[stage]

        # STEP 1: Check project prompt
        if self.project_dir:
            project_path = self.project_dir / "prompts" / f"{stage}.md"
            if project_path.exists():
                logger.info(f"Loading project prompt for {stage}")
                content = project_path.read_text(encoding='utf-8')
                info = PromptInfo(content=content, source="project", file_path=project_path)
                self._cache[stage] = info
                return info

        # STEP 2: Check global custom prompt
        custom_path = self.prompts_dir / f"{stage}.md"
        if custom_path.exists():
            logger.info(f"Loading custom prompt for {stage}")
            content = custom_path.read_text(encoding='utf-8')
            info = PromptInfo(content=content, source="custom", file_path=custom_path)
            self._cache[stage] = info
            return info

        # STEP 3: Use default prompt
        if stage in DEFAULT_PROMPTS:
            logger.info(f"Using default prompt for {stage}")
            info = PromptInfo(content=DEFAULT_PROMPTS[stage], source="default")
            self._cache[stage] = info
            return info

        raise ValueError(f"Prompt for stage '{stage}' not found!")

    def get_source(self, stage: str) -> str:
        """
        Get prompt source.

        Args:
            stage: Stage name

        Returns:
            Source type: 'default', 'custom', or 'project'
        """
        return self.get_prompt_info(stage).source

    def save_prompt(
        self,
        stage: str,
        content: str,
        to_project: bool = False
    ) -> Path:
        """
        Save custom prompt.

        Args:
            stage: Stage name
            content: Prompt text
            to_project: True to save in project folder, False for global

        Returns:
            Path to saved file
        """
        if to_project and self.project_dir:
            target_dir = self.project_dir / "prompts"
        else:
            target_dir = self.prompts_dir

        target_dir.mkdir(parents=True, exist_ok=True)
        target_path = target_dir / f"{stage}.md"
        target_path.write_text(content, encoding='utf-8')

        # Clear cache for this stage
        self._cache.pop(stage, None)

        logger.info(f"Saved prompt for {stage} to {target_path}")
        return target_path

    def reset_to_default(self, stage: str) -> bool:
        """
        Reset prompt to default (delete custom files).

        Args:
            stage: Stage name

        Returns:
            True if files were deleted
        """
        deleted = False

        # Delete project prompt
        if self.project_dir:
            project_path = self.project_dir / "prompts" / f"{stage}.md"
            if project_path.exists():
                project_path.unlink()
                logger.info(f"Deleted project prompt for {stage}")
                deleted = True

        # Delete global custom prompt
        custom_path = self.prompts_dir / f"{stage}.md"
        if custom_path.exists():
            custom_path.unlink()
            logger.info(f"Deleted custom prompt for {stage}")
            deleted = True

        # Clear cache
        self._cache.pop(stage, None)

        return deleted

    def get_default_prompt(self, stage: str) -> str:
        """
        Get default prompt (ignoring custom files).

        Args:
            stage: Stage name

        Returns:
            Default prompt text
        """
        return DEFAULT_PROMPTS.get(stage, "")

    def list_all_stages(self) -> list[dict]:
        """
        List all stages with prompt information.

        Returns:
            List of stage info dictionaries
        """
        stages = []
        for stage_key in DEFAULT_PROMPTS.keys():
            info = self.get_prompt_info(stage_key)
            stages.append({
                "stage": stage_key,
                "source": info.source,
                "file_path": str(info.file_path) if info.file_path else None,
                "has_custom": info.source != "default"
            })
        return stages

    def set_project_dir(self, project_dir: Optional[Path]):
        """
        Set project directory (when opening a project).

        Args:
            project_dir: Project directory path
        """
        self.project_dir = Path(project_dir) if project_dir else None
        self._cache.clear()  # Clear cache when changing project
        logger.info(f"Set project directory to {self.project_dir}")

    def clear_cache(self):
        """Clear prompt cache."""
        self._cache.clear()
        logger.info("Cleared prompt cache")
