"""
Модуль для генерации списка ключевых понятий из материалов уроков.
Отвечает за извлечение важных терминов и концепций для детального изучения.
"""

import json
import re
from content_utils import BaseContentGenerator


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

    def extract_key_concepts(self, lesson_content, lesson_data):
        """
        Извлекает ключевые понятия из содержания урока.

        Args:
            lesson_content (str): Содержание урока
            lesson_data (dict): Метаданные урока

        Returns:
            list: Список ключевых понятий с описаниями

        Raises:
            Exception: Если не удалось извлечь понятия
        """
        try:
            # Получаем базовую информацию об уроке
            lesson_title = lesson_data.get("title", "Урок")
            lesson_description = lesson_data.get("description", "Нет описания")
            lesson_keywords = lesson_data.get("keywords", [])

            # Очищаем HTML теги для анализа
            clean_content = self._clean_html_for_analysis(lesson_content)

            # Ограничиваем длину для запроса
            content_for_analysis = (
                clean_content[:3000] if len(clean_content) > 3000 else clean_content
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
                messages=messages, temperature=0.7, max_tokens=2500
            )

            # Сохраняем отладочную информацию
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

            # Применяем стилизацию
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
        """
        Очищает HTML теги и CSS стили для анализа содержания.

        Args:
            content (str): Содержание с HTML

        Returns:
            str: Очищенное содержание
        """
        # Убираем CSS стили полностью
        content = re.sub(r'<style[^>]*>.*?</style>', '', content, flags=re.DOTALL)
        
        # Убираем HTML теги, но сохраняем их содержимое
        content = re.sub(r'<[^>]+>', ' ', content)
        
        # Убираем HTML сущности
        content = re.sub(r'&[a-zA-Z]+;', ' ', content)
        content = re.sub(r'&#\d+;', ' ', content)
        
        # Убираем лишние пробелы и переносы строк
        content = re.sub(r'\s+', ' ', content)
        
        # Убираем пробелы в начале и конце
        content = content.strip()
        
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
        Проанализируй следующий урок и извлеки из него 5-8 ключевых понятий или терминов, которые студент может захотеть изучить более подробно:

        Название урока: {lesson_title}
        Описание урока: {lesson_description}
        Ключевые слова: {keywords_str}

        СОДЕРЖАНИЕ УРОКА (АНАЛИЗИРУЙ ТОЛЬКО ЭТОТ ТЕКСТ):
        {content}

        🚨 КРИТИЧЕСКИ ВАЖНЫЕ ТРЕБОВАНИЯ:
        1. ВЫБИРАЙ ТОЛЬКО те понятия, которые ДЕЙСТВИТЕЛЬНО УПОМИНАЮТСЯ в содержании урока выше
        2. НЕ ПРИДУМЫВАЙ понятия, которых нет в тексте
        3. Понятия должны быть достаточно важными и сложными для детального изучения
        4. Избегай слишком общих или слишком простых терминов
        5. Для каждого понятия дай краткое описание (1-2 предложения)
        6. Понятия должны быть на русском языке
        7. НЕ ИСПОЛЬЗУЙ CSS стили, HTML теги или технические термины веб-разработки
        8. ФОКУСИРУЙСЯ НА СОДЕРЖАНИИ УРОКА, а не на технических деталях

        ПРИМЕР ПРАВИЛЬНОГО АНАЛИЗА:
        - Если в уроке говорится о "машинном обучении" → это понятие подходит
        - Если в уроке говорится о "алгоритмах" → это понятие подходит  
        - Если в уроке НЕТ упоминания "шрифтов" → это понятие НЕ подходит
        - Если в уроке НЕТ упоминания "CSS" → это понятие НЕ подходит

        Верни результат в формате JSON:
        {{
            "concepts": [
                {{
                    "name": "Название понятия",
                    "brief_description": "Краткое описание понятия в 1-2 предложениях"
                }},
                ...
            ]
        }}

        ПЕРЕД ОТВЕТОМ ПРОВЕРЬ: все ли понятия действительно встречаются в тексте урока выше?
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
        Дай подробное и глубокое объяснение следующего понятия:

        Понятие: {concept_name}
        Краткое описание: {concept_description}

        КОНТЕКСТ ИЗ УРОКА (ОСНОВА ДЛЯ ОБЪЯСНЕНИЯ):
        {content}

        Стиль общения: {style_description}

        🚨 КРИТИЧЕСКИ ВАЖНЫЕ ТРЕБОВАНИЯ:
        1. Начни с четкого определения понятия
        2. Объясни, почему это понятие важно в данном контексте урока
        3. Приведи конкретные примеры использования ИЗ СОДЕРЖАНИЯ УРОКА
        4. Расскажи о связи с другими понятиями ИЗ УРОКА
        5. Добавь практические советы по применению
        6. Укажи возможные сложности или частые ошибки
        7. Используй четкую структуру с заголовками
        8. НЕ ПРИДУМЫВАЙ информацию, которой нет в уроке
        9. ФОКУСИРУЙСЯ на материале урока, а не на общих знаниях

        Объяснение должно быть:
        - Подробным и информативным (в 2-3 раза больше краткого описания)
        - Легким для понимания
        - Практически полезным
        - Хорошо структурированным
        - СВЯЗАННЫМ С КОНКРЕТНЫМ УРОКОМ

        Используй HTML-форматирование для улучшения читаемости.
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
            line-height: 1.05;
            border: 2px solid #333;
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
