# Interview-to-Habr Pipeline

Автоматизированное преобразование транскрипций экспертных интервью в готовые статьи для Хабра и производные маркетинговые материалы с использованием Google Gemini API.

## Возможности

- **10-этапный пайплайн обработки**: от загрузки файла до генерации маркетинговых материалов
- **Поддержка множества форматов**: TXT, DOCX, Markdown
- **Унифицированная LLM-архитектура**: единая точка взаимодействия с Gemini API
- **Трёхуровневая система промптов**: default → custom → project
- **Сохранение состояния**: возможность продолжить с любого этапа
- **CLI интерфейс**: полное управление через командную строку

## Установка

### Требования

- Python 3.11+
- Google Gemini API ключ

### Установка зависимостей

```bash
cd interview-to-habr
pip install -r requirements.txt
```

### Настройка API ключа

```bash
export GEMINI_API_KEY="your-api-key-here"
```

## Быстрый старт

### 1. Диагностика системы

Проверьте, что все настроено корректно:

```bash
python main.py diagnose
```

### 2. Создание проекта

```bash
python main.py new interview.docx --name my_interview
```

### 3. Обработка

```bash
python main.py process ./projects/my_interview
```

### 4. Просмотр результатов

Готовая статья будет в `./projects/my_interview/output/final_article.md`

## Этапы пайплайна

| № | Этап | Описание | LLM |
|---|------|----------|-----|
| 1 | **Load** | Загрузка и нормализация файла | Нет |
| 2 | **Format** | Форматирование транскрипции | Да |
| 3 | **Compare** | Сравнение с оригиналом и коррекция | Да |
| 4 | **Plan** | Создание плана статьи | Да |
| 5 | **Write** | Написание секций (цикл) | Да |
| 6 | **Merge** | Сведение секций | Нет |
| 7 | **Edit** | Литературная правка | Да |
| 8 | **Analyze** | Маркетинговый анализ | Да |
| 9 | **Select** | Выбор материалов | Нет |
| 10 | **Generate** | Генерация материалов | Да |

## CLI Команды

### Проекты

```bash
# Список всех проектов
python main.py projects

# Создать новый проект
python main.py new <файл> [--name <имя>] [--model <модель>]

# Обработать проект
python main.py process <проект> [--from-stage N] [--to-stage M]

# Запустить один этап
python main.py stage <проект> <номер_этапа>
```

### Информация

```bash
# Диагностика системы
python main.py diagnose

# Список доступных моделей
python main.py models
```

## Кастомные промпты

### Трёхуровневая система

Промпты загружаются с приоритетом:
1. **Project** (`./projects/{name}/prompts/02_format.md`) - высший приоритет
2. **Custom** (`./prompts/02_format.md`) - средний приоритет
3. **Default** (встроенные в код) - низший приоритет

### Создание кастомного промпта

1. Создайте файл в `./prompts/`:

```bash
mkdir -p prompts
cat > prompts/02_format.md << 'EOF'
# Мой кастомный промпт для форматирования

Ты — редактор. Форматируй транскрипцию так:
- Используй формат: **Спикер:** текст
- Разбивай на короткие абзацы
...
EOF
```

2. При следующем запуске этот промпт будет использован автоматически!

### Промпты проекта

Для специфичных настроек конкретного проекта:

```bash
mkdir -p projects/my_project/prompts
cp prompts/02_format.md projects/my_project/prompts/
# Отредактируйте файл под нужды проекта
```

## Маркетинговые материалы

На этапе 9 можно выбрать материалы для генерации:

- `tg_vk_post` - Пост для Telegram/VK
- `email_announce` - Анонс для рассылки
- `press_release` - Пресс-релиз
- `cards` - Карточки для соцсетей
- `business_media` - Статья для делового СМИ

```bash
python main.py process ./projects/my_project \
  --from-stage 9 \
  --materials tg_vk_post \
  --materials email_announce
```

## Архитектура

### Унифицированная LLM-обработка

**Все** взаимодействия с Gemini API идут через **один** универсальный класс:

```python
# src/core/llm_processor.py
class LLMProcessor:
    """Единственная точка взаимодействия с LLM"""

    def process(self, stage_name: str, user_content: str, **kwargs):
        # Автоматически загружает промпт (с учётом кастомных!)
        prompt_info = self.prompts.get_prompt_info(stage_name)

        # Вызывает Gemini API
        response = self.client.generate(...)

        return LLMResult(content=response, ...)
```

### Минималистичные этапы

Каждый этап — это всего ~20-50 строк кода:

```python
# src/stages/s02_format.py
class FormatStage(BaseStage):
    stage_id = 2
    stage_name = "02_format"
    input_files = ["01_loaded.md"]
    output_file = "02_formatted.md"

    def execute(self) -> StageResult:
        text = self.read_input()
        result = self.call_llm(text)  # Промпт загрузится автоматически!
        self.save_output(result.content)
        return StageResult(success=True, tokens_used=result.tokens_used)
```

Вся общая логика в `BaseStage`:
- Чтение/запись файлов
- Вызов LLM
- Обновление состояния
- Обработка ошибок

## Структура проекта

```
projects/my_interview/
├── state.json                 # Состояние проекта
├── prompts/                   # Промпты проекта (опционально)
├── input/
│   └── original.docx         # Оригинальный файл
├── stages/
│   ├── 01_loaded.md
│   ├── 02_formatted.md
│   ├── 03_corrected.md
│   ├── 04_plan.json
│   ├── 05_sections/
│   │   ├── 01_intro.md
│   │   └── ...
│   ├── 06_merged.md
│   ├── 07_edited.md
│   └── 08_analysis.md
└── output/
    ├── final_article.md       # Готовая статья
    └── materials/
        ├── tg_vk_post.md
        └── ...
```

## Конфигурация

Редактируйте `config.yaml`:

```yaml
gemini:
  default_model: "gemini-2.0-flash-exp"
  temperature: 0.7
  max_retries: 3
  retry_delay: 5

paths:
  projects_dir: "./projects"
  prompts_dir: "./prompts"
```

## Примеры использования

### Полный пайплайн

```bash
# Создать проект
python main.py new interview.docx --name security_interview

# Запустить все этапы
python main.py process ./projects/security_interview

# Результат: ./projects/security_interview/output/final_article.md
```

### Повторный запуск этапа

Если на этапе 5 была ошибка:

```bash
# Исправьте промпт или данные
vim prompts/05_write_section.md

# Запустите заново с этапа 5
python main.py process ./projects/security_interview --from-stage 5
```

### Только генерация материалов

```bash
# Выбрать и сгенерировать материалы
python main.py process ./projects/security_interview \
  --from-stage 9 \
  --materials tg_vk_post \
  --materials cards
```

## Разработка

### Добавление нового промпта

1. Добавьте в `src/core/prompt_manager.py`:

```python
DEFAULT_PROMPTS = {
    # ...
    "materials/my_new_material": """Текст промпта...""",
}
```

2. Добавьте в `src/stages/s09_select.py`:

```python
MATERIAL_TYPES = {
    "my_new_material": {
        "id": "my_new_material",
        "name": "Мой новый материал",
        "description": "Описание",
        "prompt_file": "materials/my_new_material",
        "output_file": "my_new_material.md"
    }
}
```

## Устранение проблем

### API ключ не найден

```bash
export GEMINI_API_KEY="your-key"
python main.py diagnose
```

### Ошибка при чтении DOCX

```bash
pip install --upgrade python-docx
```

### Слишком большой файл

Разбейте интервью на части и обработайте отдельно.

## Лицензия

MIT

## Автор

Created with Claude Code
