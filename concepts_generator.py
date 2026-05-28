"""
Модуль для генерации списка ключевых понятий из материалов уроков.
Отвечает за извлечение важных терминов и концепций для детального изучения.
"""

import json
import re
from content_utils import BaseContentGenerator
from content_renderer import enhance_content, get_display_css


class ConceptsGenerator(BaseContentGenerator):
    """Генератор ключевых понятий для уроков."""

    def __init__(self, api_key):
        """
        Инициализация генератора понятий.

        Args:
            api_key (str): API ключ OpenAI
        """
        super().__init__(api_key)
        self.logger.info("ConceptsGenerator инициализирован")

    def extract_key_concepts(self, lesson_content, lesson_data, course_context=None):
        """
        Извлекает ключевые понятия из содержания урока.

        Args:
            lesson_content (str): Содержание урока (может включать breadcrumb-
                заголовки курса/раздела/темы в начале — они будут срезаны).
            lesson_data (dict): Метаданные урока (title, description, keywords).
            course_context (dict, optional): Контекст курса
                (course_title, section_title, topic_title) для удаления
                breadcrumb-заголовков из текста. Без него анализ может
                захватить «Машинное обучение» и подобные понятия из шапки,
                не относящиеся к телу конкретного урока.

        Returns:
            list: Список ключевых понятий с описаниями.

        Raises:
            Exception: Если не удалось извлечь понятия.
        """
        try:
            lesson_title = lesson_data.get("title", "Урок")
            lesson_description = lesson_data.get("description", "Нет описания")
            lesson_keywords = lesson_data.get("keywords", [])

            # Срезаем breadcrumb-шапку до выглаживания HTML, по самим тегам
            # (общий хелпер из BaseContentGenerator).
            content_without_header = self.strip_lesson_breadcrumb(
                lesson_content, course_context
            )

            # Удаляем <style>/<script>/комментарии до снятия тегов,
            # чтобы CSS не утекал в анализ как «материал урока».
            clean_content = self.clean_lesson_html_for_analysis(content_without_header)

            # 8000 символов — достаточно для типичного урока целиком;
            # 3000 было слишком мало и часто содержало только введение.
            content_for_analysis = (
                clean_content[:8000] if len(clean_content) > 8000 else clean_content
            )

            prompt = self._build_concepts_prompt(
                lesson_title, lesson_description, lesson_keywords, content_for_analysis
            )

            messages = [
                {
                    "role": "system",
                    "content": "Ты - эксперт по образованию, который анализирует учебные материалы и выделяет ключевые понятия для глубокого изучения.",
                },
                {"role": "user", "content": prompt},
            ]

            response_content = self.make_api_request(
                messages=messages,
                temperature=0.3,  # Низкая температура для точного анализа
                max_tokens=2000,
                response_format={"type": "json_object"},
            )

            # Сохраняем отладочную информацию
            self.save_debug_response(
                "key_concepts",
                prompt,
                response_content,
                {
                    "lesson_title": lesson_title,
                    "lesson_description": lesson_description,
                    "keywords": lesson_keywords,
                },
            )

            concepts_data = json.loads(response_content)
            concepts = self._extract_concepts_from_response(concepts_data)

            if not concepts or len(concepts) == 0:
                raise Exception("API вернул пустой список понятий")

            # Дополнительная проверка качества понятий
            self.logger.info(f"Проверяем качество {len(concepts)} сгенерированных понятий...")
            
            # Проверяем, что понятия не содержат технических терминов веб-разработки
            invalid_concepts = []
            for concept in concepts:
                concept_name = concept.get("name", "").lower()
                if any(tech_term in concept_name for tech_term in ["css", "html", "шрифт", "выравнивание", "стиль", "разметка"]):
                    invalid_concepts.append(concept_name)
            
            if invalid_concepts:
                self.logger.warning(f"Обнаружены подозрительные понятия: {invalid_concepts}")
                # Если все понятия подозрительные, генерируем заново с более строгим промптом
                if len(invalid_concepts) == len(concepts):
                    self.logger.warning("Все понятия подозрительные, генерируем заново...")
                    # Добавляем дополнительное предупреждение в промпт
                    enhanced_prompt = prompt + "\n\n🚨 ВНИМАНИЕ: В предыдущем ответе были понятия, не связанные с содержанием урока. Строго анализируй только текст урока!"
                    messages[1]["content"] = enhanced_prompt
                    
                    response_content = self.make_api_request(
                        messages=messages,
                        temperature=0.1,  # Еще более низкая температура
                        max_tokens=2000,
                        response_format={"type": "json_object"},
                    )
                    
                    concepts_data = json.loads(response_content)
                    concepts = self._extract_concepts_from_response(concepts_data)
                    
                    if not concepts or len(concepts) == 0:
                        raise Exception("API вернул пустой список понятий после повторной попытки")

            self.logger.info(f"Успешно извлечено {len(concepts)} ключевых понятий")
            return concepts

        except Exception as e:
            self.logger.error(
                f"Критическая ошибка при извлечении ключевых понятий: {str(e)}"
            )
            raise Exception(f"Не удалось извлечь ключевые понятия: {str(e)}")

    def explain_concept(self, concept, lesson_content, communication_style="friendly"):
        """
        Генерирует детальное объяснение выбранного понятия.

        Args:
            concept (dict): Данные о понятии (name, brief_description)
            lesson_content (str): Содержание урока для контекста
            communication_style (str): Стиль общения

        Returns:
            str: Подробное объяснение понятия

        Raises:
            Exception: Если не удалось сгенерировать объяснение
        """
        try:
            concept_name = concept.get("name", "Понятие")
            concept_description = concept.get("brief_description", "Нет описания")

            # Очищаем и ограничиваем содержание урока
            clean_content = self._clean_html_for_analysis(lesson_content)
            content_for_context = (
                clean_content[:2000] if len(clean_content) > 2000 else clean_content
            )

            prompt = self._build_concept_explanation_prompt(
                concept_name,
                concept_description,
                content_for_context,
                communication_style,
            )

            messages = [
                {
                    "role": "system",
                    "content": "Ты - опытный преподаватель, который дает подробные и понятные объяснения сложных понятий.",
                },
                {"role": "user", "content": prompt},
            ]

            explanation = self.make_api_request(
                messages=messages, temperature=0.5, max_tokens=4000
            )

            self.save_debug_response(
                "concept_explanation",
                prompt,
                explanation,
                {
                    "concept_name": concept_name,
                    "concept_description": concept_description,
                    "communication_style": communication_style,
                },
            )

            # Снимаем возможные markdown-обёртки ```html ... ``` и лишний общий
            # отступ внутри <pre><code> (LLM часто вкладывает блок кода в <li>
            # и выдаёт код с лишними 8-12 пробелами слева у каждой строки).
            explanation = self.clean_markdown_code_blocks(explanation)
            explanation = enhance_content(explanation)

            styled_explanation = self._style_concept_explanation(
                explanation, concept_name, communication_style
            )

            self.logger.info(
                f"Успешно сгенерировано объяснение понятия '{concept_name}'"
            )
            return styled_explanation

        except Exception as e:
            self.logger.error(f"Критическая ошибка при объяснении понятия: {str(e)}")
            raise Exception(f"Не удалось сгенерировать объяснение понятия: {str(e)}")

    def _clean_html_for_analysis(self, content):
        """Совместимая обёртка над общим хелпером BaseContentGenerator.

        Логика: режутся <style>/<script>/комментарии, снимаются теги
        и HTML-сущности, схлопываются пробелы.
        """
        content = self.clean_lesson_html_for_analysis(content)
        
        # Убираем CSS-подобные конструкции, которые могли остаться
        content = re.sub(r'[a-zA-Z-]+\s*:\s*[^;]+;', '', content)
        content = re.sub(r'[a-zA-Z-]+\s*:\s*[^;]+', '', content)
        
        # Финальная очистка пробелов
        content = re.sub(r'\s+', ' ', content).strip()
        
        return content

    def _build_concepts_prompt(
        self, lesson_title, lesson_description, lesson_keywords, content
    ):
        """
        Создает промпт для извлечения ключевых понятий.

        Args:
            lesson_title (str): Название урока
            lesson_description (str): Описание урока
            lesson_keywords (list): Ключевые слова урока
            content (str): Содержание урока

        Returns:
            str: Промпт для API
        """
        keywords_str = (
            ", ".join(lesson_keywords)
            if isinstance(lesson_keywords, list)
            else str(lesson_keywords)
        )

        return f"""
Проанализируй ТЕКСТ КОНКРЕТНОГО УРОКА ниже и извлеки из него 5–8 ключевых
понятий, которые студент мог бы захотеть изучить ПОДРОБНЕЕ ИМЕННО ПО ЭТОМУ
УРОКУ.

МЕТАДАННЫЕ УРОКА (только для ориентира, понятия отсюда не бери):
- Название урока: {lesson_title}
- Описание урока: {lesson_description}
- Ключевые слова: {keywords_str}

ТЕКСТ УРОКА (единственный источник понятий):
{content}

🚨 КРИТИЧЕСКИ ВАЖНЫЕ ТРЕБОВАНИЯ:
1. Понятия должны быть из ТЕЛА УРОКА, а не из общего контекста курса.
   Если в тексте упоминается название курса или дисциплины
   (например, «машинное обучение», «анализ данных»), НЕ включай это
   как ключевое понятие урока — это название уровня выше, не материал
   конкретного урока.
2. Понятия должны быть достаточно конкретными для детального изучения:
   термин, синтаксическая конструкция, структура данных, типичный паттерн.
3. Избегай слишком общих формулировок («Библиотеки Python», «Программирование»).
4. Не выдумывай понятия, которых нет в тексте.
5. Для каждого понятия дай краткое описание в 1–2 предложениях.
6. Понятия и описания — на русском языке.
7. Не используй CSS/HTML-термины или термины веб-разработки, если
   урок не про веб-разработку.

ПРИМЕРЫ:
- Урок про основы Python с разделом «Переменные, Типы данных, Списки, Условия и циклы»
  → подходят: Переменные, Типы данных (int/float/str/bool), Списки,
    Условия (if/else), Циклы (for/while), Логические значения.
  → НЕ подходят: Машинное обучение (это название курса),
    Библиотеки Python (если в этом уроке нет ни одной библиотеки в теле).

Верни результат строго в формате JSON:
{{
    "concepts": [
        {{
            "name": "Название понятия",
            "brief_description": "Краткое описание в 1-2 предложениях"
        }},
        ...
    ]
}}

ПЕРЕД ОТВЕТОМ ПРОВЕРЬ:
- Каждое понятие реально РАЗБИРАЕТСЯ в теле урока (а не упомянуто вскользь
  и не является названием курса/раздела).
"""

    def _build_concept_explanation_prompt(
        self, concept_name, concept_description, content, communication_style
    ):
        """
        Создает промпт для детального объяснения понятия.

        Args:
            concept_name (str): Название понятия
            concept_description (str): Краткое описание понятия
            content (str): Содержание урока для контекста
            communication_style (str): Стиль общения

        Returns:
            str: Промпт для API
        """
        from content_utils import ContentUtils

        style_description = ContentUtils.COMMUNICATION_STYLES.get(
            communication_style, ContentUtils.COMMUNICATION_STYLES["friendly"]
        )

        return f"""
Дай ДЕЙСТВИТЕЛЬНО ПОДРОБНОЕ объяснение следующего понятия.
Не одно-два предложения, а полноценный учебный материал
объёмом 400–800 слов с примерами кода.

Понятие: {concept_name}
Краткое описание (только отправная точка, его НЕДОСТАТОЧНО): {concept_description}

КОНТЕКСТ ИЗ УРОКА (опора, но можно дополнять стандартными знаниями
по теме, если в уроке тема раскрыта неполно):
{content}

Стиль общения: {style_description}

ОБЯЗАТЕЛЬНАЯ СТРУКТУРА ответа (используй HTML-разметку: <h4>, <p>,
<ul>/<li>, <pre><code>):

1. <h4>Определение</h4>
   2-3 предложения, чёткое определение без воды.

2. <h4>Из чего состоит / какие бывают</h4>
   Если это структура данных — какие типы элементов внутри допустимы
   (для списков/кортежей: любые объекты Python — числа, строки,
   другие списки, словари, объекты классов; смешанные типы; вложенность).
   Если это процесс/алгоритм — этапы. Если это парадигма — компоненты.

3. <h4>Синтаксис и создание</h4>
   Минимум один блок <pre><code> с РАБОЧИМ Python-кодом, показывающим,
   как создать/использовать. Несколько вариантов создания, если применимо
   (литерал, конструктор, comprehension и т.п.).

4. <h4>Основные операции и методы</h4>
   Список 3–6 наиболее важных операций или методов с короткими примерами
   (индексация, срезы, append/pop/insert для списков; неизменяемость и
   распаковка для кортежей; и т.п. — выбирай релевантное для понятия).
   Каждая операция — отдельная строка кода в <pre><code>.

5. <h4>Чем отличается от похожего</h4>
   Если есть близкое понятие (списки↔кортежи, list↔tuple↔set↔dict,
   функция↔метод, переменная↔константа и т.д.) — таблица или список
   ключевых отличий: изменяемость, производительность, типичное применение.
   Если нет близкого понятия — пропусти раздел.

6. <h4>Когда применять</h4>
   2-4 реалистичных сценария использования (желательно — в контексте
   машинного обучения / анализа данных / Python-разработки).

7. <h4>Частые ошибки</h4>
   2-3 типичные ошибки начинающих и как их избегать. Где уместно —
   короткие примеры некорректного и корректного кода в <pre><code>.

ТРЕБОВАНИЯ К КАЧЕСТВУ:
- НЕ ограничивайся повторением краткого описания — это считается провалом.
- Минимум 2 блока <pre><code> с рабочим Python-кодом.
- Никаких "В этом разделе мы рассмотрим...", "Сейчас разберёмся..." —
  сразу по существу.
- Если в уроке есть конкретные примеры по этому понятию — обязательно
  упомяни и разверни их.
- Не выдумывай несуществующие методы/синтаксис. Только реальный Python.

🚨 ФОРМАТ ВЫВОДА:
- Верни ТОЛЬКО чистый HTML, без markdown-обёрток.
- НЕ оборачивай ответ в ```html ... ```, ``` ... ```, '''html ... ''' или ~~~.
- Внутри <pre><code> код пиши БЕЗ лишнего общего отступа слева:
  первая строка кода — БЕЗ ведущих пробелов, дальше Python-отступ 4 пробела
  только для вложенных конструкций (тело for/while/if/def/class).
  Не сдвигай весь блок вправо, даже если <pre><code> находится внутри <li>.
"""

    def _extract_concepts_from_response(self, concepts_data):
        """
        Извлекает понятия из ответа API.

        Args:
            concepts_data (dict): Ответ API в формате JSON

        Returns:
            list: Список понятий
        """
        # Проверяем, есть ли в ответе ключ "concepts"
        if "concepts" in concepts_data:
            return concepts_data["concepts"]
        elif isinstance(concepts_data, list):
            # Если API вернул сразу список понятий
            return concepts_data
        else:
            # Проверяем, содержит ли ответ другие ключи, которые могут быть списком понятий
            for key, value in concepts_data.items():
                if isinstance(value, list) and len(value) > 0:
                    return value
            raise Exception("API вернул некорректный формат понятий")

    def _style_concept_explanation(
        self, explanation, concept_name, communication_style
    ):
        """
        Применяет стилизацию к объяснению понятия.

        Args:
            explanation (str): Исходное объяснение
            concept_name (str): Название понятия
            communication_style (str): Стиль общения

        Returns:
            str: Стилизованное объяснение
        """
        # Получаем префикс в зависимости от стиля общения
        prefix = self._get_concept_prefix(concept_name, communication_style)

        # Применяем CSS стили
        styled_explanation = f"""
        {get_display_css()}
        <style>
        .concept-explanation {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            font-size: 16px;
            line-height: 1.4;
            padding: 20px;
            background: linear-gradient(135deg, #fff3e0 0%, #ffe0b2 100%);
            border-radius: 10px;
            margin: 15px 0;
            border-left: 4px solid #ff9800;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        .concept-explanation h1, .concept-explanation h2, .concept-explanation h3, .concept-explanation h4 {{
            color: #e65100;
            margin-top: 15px;
            margin-bottom: 8px;
            line-height: 1.2;
            border-bottom: 2px solid #ff9800;
            padding-bottom: 4px;
        }}
        .concept-explanation h1 {{ font-size: 20px; }}
        .concept-explanation h2 {{ font-size: 18px; }}
        .concept-explanation h3 {{ font-size: 17px; }}
        .concept-explanation h4 {{ font-size: 16px; }}
        .concept-explanation p {{
            margin-bottom: 8px;
            line-height: 1.3;
            text-align: justify;
        }}
        .concept-explanation ul, .concept-explanation ol {{
            margin-bottom: 10px;
            padding-left: 25px;
            line-height: 1.3;
        }}
        .concept-explanation li {{
            margin-bottom: 4px;
        }}
        .concept-explanation code {{
            background-color: #1a1a1a;
            color: #00ff41;
            padding: 2px 6px;
            border-radius: 4px;
            font-family: 'Courier New', monospace;
            font-size: 14px;
            font-weight: 600;
            border: 1px solid #333;
        }}
        .concept-explanation pre {{
            background-color: #1a1a1a;
            color: #00ff41;
            padding: 12px;
            border-radius: 8px;
            overflow-x: auto;
            margin: 10px 0;
            font-family: 'Courier New', monospace;
            font-size: 14px;
            line-height: 1.5;
            border: 2px solid #333;
            white-space: pre;
        }}
        .concept-explanation pre code {{
            background: none;
            color: inherit;
            padding: 0;
            font-size: inherit;
        }}
        .concept-explanation .concept-highlight {{
            background-color: #fff8e1;
            padding: 10px;
            border-radius: 6px;
            border-left: 3px solid #ffc107;
            margin: 10px 0;
        }}
        .concept-explanation strong {{
            color: #e65100;
            font-weight: 600;
        }}
        .concept-explanation em {{
            color: #ff6f00;
            font-style: italic;
        }}
        </style>
        <div class="concept-explanation">
            {prefix}{explanation}
        </div>
        """

        return styled_explanation

    def _get_concept_prefix(self, concept_name, communication_style):
        """
        Возвращает префикс для объяснения понятия в зависимости от стиля общения.

        Args:
            concept_name (str): Название понятия
            communication_style (str): Стиль общения

        Returns:
            str: HTML префикс
        """
        if communication_style == "formal":
            return f"<p style='font-size: 16px; line-height: 1.4;'>Подробное академическое объяснение понятия <strong>{concept_name}</strong>:</p>"
        elif communication_style == "casual":
            return f"<p style='font-size: 16px; line-height: 1.4;'>Давайте разберемся с понятием <strong>{concept_name}</strong> подробнее! 🤓</p>"
        elif communication_style == "brief":
            return f"<p style='font-size: 16px; line-height: 1.4;'>Понятие <strong>{concept_name}</strong>:</p>"
        else:  # friendly по умолчанию
            return f"<p style='font-size: 16px; line-height: 1.4;'>Отлично! Давайте подробно изучим понятие <strong>{concept_name}</strong>:</p>"
