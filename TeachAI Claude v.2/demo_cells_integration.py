"""
Модуль интеграции демонстрационных ячеек Jupiter Notebook в уроки.
Отвечает за преобразование сгенерированных примеров кода в интерактивные демо-ячейки.
НОВОЕ: Парсинг примеров кода из HTML и создание DemoCellWidget
НОВОЕ: Замена статических примеров на интерактивные исполняемые ячейки
"""

import re
import logging
from typing import List, Dict, Tuple, Optional
import ipywidgets as widgets
from IPython.display import display
import html

# Импортируем модули Jupiter notebook ячеек
try:
    from demo_cell_widget import DemoCellWidget, create_demo_cell
except ImportError:
    logging.error("Не удалось импортировать модули Jupiter notebook ячеек")

    # Создаем заглушки для случая отсутствия модулей
    class DemoCellWidget:
        def __init__(self, *args, **kwargs):
            pass

    def create_demo_cell(*args, **kwargs):
        return widgets.HTML("<p>Демо-ячейки недоступны</p>")


class DemoCellsIntegration:
    """Интеграция демонстрационных ячеек в интерфейс уроков."""

    def __init__(self):
        """Инициализация интегратора демо-ячеек."""
        self.logger = logging.getLogger(__name__)
        self.logger.info("DemoCellsIntegration инициализирован")

        # Счетчик для уникальных ID ячеек
        self._cell_counter = 0

    def integrate_demo_cells_in_lesson(
        self, lesson_content: str, lesson_id: str = None
    ) -> str:
        """
        ОСНОВНОЙ МЕТОД: Интегрирует демо-ячейки в содержимое урока.

        Args:
            lesson_content (str): HTML содержимое урока
            lesson_id (str, optional): ID урока для уникальности ячеек

        Returns:
            str: Содержимое урока с интегрированными демо-ячейками
        """
        try:
            self.logger.info(f"Начинаем интеграцию демо-ячеек для урока {lesson_id}")

            # Парсим примеры кода из HTML
            code_examples = self._parse_code_examples(lesson_content)

            if not code_examples:
                self.logger.info("Примеры кода для демо-ячеек не найдены")
                return lesson_content

            self.logger.info(
                f"Найдено {len(code_examples)} примеров кода для демо-ячеек"
            )

            # Создаем интерактивные демо-ячейки
            integrated_content = self._replace_with_demo_cells(
                lesson_content, code_examples, lesson_id
            )

            self.logger.info("Интеграция демо-ячеек завершена успешно")
            return integrated_content

        except Exception as e:
            self.logger.error(f"Ошибка при интеграции демо-ячеек: {str(e)}")
            # В случае ошибки возвращаем оригинальное содержимое
            return lesson_content

    def _parse_code_examples(self, html_content: str) -> List[Dict[str, str]]:
        """
        Парсит примеры Python кода из HTML содержимого.

        Args:
            html_content (str): HTML содержимое с примерами

        Returns:
            List[Dict]: Список словарей с информацией о примерах кода
        """
        try:
            examples = []

            # Паттерн для поиска блоков кода в <pre><code>
            code_pattern = r"<pre><code[^>]*>(.*?)</code></pre>"
            code_matches = re.findall(
                code_pattern, html_content, re.DOTALL | re.IGNORECASE
            )

            for i, code_match in enumerate(code_matches):
                # Декодируем HTML сущности
                clean_code = html.unescape(code_match.strip())

                # Проверяем, что это Python код
                if self._is_python_code(clean_code):
                    # Ищем заголовок перед блоком кода
                    title = self._extract_code_title(html_content, code_match, i)

                    # Извлекаем описание после блока кода
                    description = self._extract_code_description(
                        html_content, code_match
                    )

                    example_info = {
                        "code": clean_code,
                        "title": title,
                        "description": description,
                        "original_html": f"<pre><code>{code_match}</code></pre>",
                        "index": i,
                    }

                    examples.append(example_info)
                    self.logger.debug(f"Найден Python пример #{i}: {title[:50]}...")

            return examples

        except Exception as e:
            self.logger.error(f"Ошибка при парсинге примеров кода: {str(e)}")
            return []

    def _is_python_code(self, code: str) -> bool:
        """
        Определяет, является ли код Python кодом.

        Args:
            code (str): Код для проверки

        Returns:
            bool: True если это Python код
        """
        python_indicators = [
            "def ",
            "import ",
            "from ",
            "print(",
            "if __name__",
            "class ",
            "for ",
            "while ",
            "if ",
            "elif ",
            "else:",
            "# ",
            "return ",
            "try:",
            "except:",
            "with ",
            "lambda",
            "True",
            "False",
            "None",
            "__init__",
            "self.",
        ]

        # Исключаем не-Python код
        non_python_indicators = [
            "<html>",
            "<head>",
            "<body>",
            "<div>",
            "<script>",
            "function(",
            "var ",
            "document.",
            "console.log",
            "<?php",
            "<?xml",
            "public class",
            "#include",
            "using namespace",
        ]

        code_lower = code.lower()

        # Проверяем на не-Python код
        if any(indicator in code_lower for indicator in non_python_indicators):
            return False

        # Проверяем на Python индикаторы
        return any(indicator in code for indicator in python_indicators)

    def _extract_code_title(
        self, html_content: str, code_match: str, index: int
    ) -> str:
        """
        Извлекает заголовок для примера кода.

        Args:
            html_content (str): Полное HTML содержимое
            code_match (str): Найденный код
            index (int): Индекс примера

        Returns:
            str: Заголовок для примера
        """
        try:
            # Ищем заголовки перед блоком кода
            code_position = html_content.find(code_match)
            if code_position > 0:
                # Берем текст перед кодом
                before_code = html_content[:code_position]

                # Ищем последний заголовок h3, h4, или строку с "пример"
                header_patterns = [
                    r"<h3[^>]*>(.*?)</h3>",
                    r"<h4[^>]*>(.*?)</h4>",
                    r"<p[^>]*><strong>(.*?пример.*?)</strong></p>",
                    r"<strong>(.*?пример.*?)</strong>",
                ]

                for pattern in header_patterns:
                    matches = re.findall(
                        pattern, before_code, re.IGNORECASE | re.DOTALL
                    )
                    if matches:
                        # Берем последний найденный заголовок
                        title = html.unescape(matches[-1].strip())
                        # Удаляем HTML теги
                        title = re.sub(r"<[^>]+>", "", title)
                        if title and len(title) < 100:
                            return title

            # Если заголовок не найден, генерируем базовый
            return f"Пример Python кода #{index + 1}"

        except Exception as e:
            self.logger.error(f"Ошибка при извлечении заголовка: {str(e)}")
            return f"Пример кода #{index + 1}"

    def _extract_code_description(self, html_content: str, code_match: str) -> str:
        """
        Извлекает описание для примера кода.

        Args:
            html_content (str): Полное HTML содержимое
            code_match (str): Найденный код

        Returns:
            str: Описание примера
        """
        try:
            # Ищем текст после блока кода
            code_html = f"<pre><code>{code_match}</code></pre>"
            code_position = html_content.find(code_html)

            if code_position >= 0:
                after_code = html_content[code_position + len(code_html) :]

                # Ищем первый абзац после кода
                paragraph_match = re.search(r"<p[^>]*>(.*?)</p>", after_code, re.DOTALL)
                if paragraph_match:
                    description = html.unescape(paragraph_match.group(1).strip())
                    # Удаляем HTML теги
                    description = re.sub(r"<[^>]+>", "", description)
                    if description and len(description) < 300:
                        return description

            return "Интерактивный пример Python кода"

        except Exception as e:
            self.logger.error(f"Ошибка при извлечении описания: {str(e)}")
            return "Пример кода для изучения"

    def _replace_with_demo_cells(
        self, html_content: str, code_examples: List[Dict], lesson_id: str = None
    ) -> str:
        """
        Заменяет статические примеры кода на интерактивные демо-ячейки.

        Args:
            html_content (str): Исходное HTML содержимое
            code_examples (List[Dict]): Примеры кода для замены
            lesson_id (str): ID урока

        Returns:
            str: HTML с интегрированными демо-ячейками
        """
        try:
            modified_content = html_content

            # Обрабатываем примеры в обратном порядке (чтобы не сбить позиции)
            for example in reversed(code_examples):
                demo_cell_html = self._create_demo_cell_html(example, lesson_id)

                # Заменяем оригинальный блок кода на демо-ячейку
                modified_content = modified_content.replace(
                    example["original_html"],
                    demo_cell_html,
                    1,  # Заменяем только первое вхождение
                )

                self.logger.debug(
                    f"Заменен пример кода на демо-ячейку: {example['title']}"
                )

            return modified_content

        except Exception as e:
            self.logger.error(f"Ошибка при замене на демо-ячейки: {str(e)}")
            return html_content

    def _create_demo_cell_html(self, example: Dict, lesson_id: str = None) -> str:
        """
        Создает HTML представление демо-ячейки.

        Args:
            example (Dict): Информация о примере кода
            lesson_id (str): ID урока

        Returns:
            str: HTML код демо-ячейки
        """
        try:
            # Генерируем уникальный ID для ячейки
            self._cell_counter += 1
            cell_id = f"demo_cell_{lesson_id or 'lesson'}_{self._cell_counter}"

            # Создаем демо-ячейку (пока как HTML, позже можно будет создавать виджет)
            demo_cell_html = f"""
            <div class="demo-cell-container" style="
                border: 2px solid #007bff;
                border-radius: 8px;
                margin: 15px 0;
                background-color: #f8f9ff;
                overflow: hidden;
            ">
                <div class="demo-cell-header" style="
                    background-color: #007bff;
                    color: white;
                    padding: 8px 12px;
                    font-weight: bold;
                    font-size: 14px;
                ">
                    🐍 {example['title']} <span style="float: right;">▶️ Выполнить</span>
                </div>

                <div class="demo-cell-code" style="
                    background-color: #f8f9fa;
                    border-bottom: 1px solid #dee2e6;
                ">
                    <pre style="
                        margin: 0;
                        padding: 12px;
                        font-family: 'Courier New', monospace;
                        font-size: 13px;
                        line-height: 1.4;
                        color: #212529;
                        overflow-x: auto;
                    "><code>{html.escape(example['code'])}</code></pre>
                </div>

                <div class="demo-cell-output" style="
                    padding: 12px;
                    background-color: #ffffff;
                    border-top: 1px solid #dee2e6;
                    min-height: 40px;
                    font-family: 'Courier New', monospace;
                    font-size: 13px;
                    color: #666;
                ">
                    <em>Нажмите "▶️ Выполнить" чтобы увидеть результат</em>
                </div>

                <div class="demo-cell-description" style="
                    padding: 8px 12px;
                    background-color: #e7f3ff;
                    font-size: 13px;
                    color: #495057;
                    border-top: 1px solid #b3d9ff;
                ">
                    💡 {example['description']}
                </div>
            </div>

            <script>
            // Здесь будет JavaScript для выполнения кода (будет добавлен позже)
            console.log('Demo cell created: {cell_id}');
            </script>
            """

            return demo_cell_html

        except Exception as e:
            self.logger.error(f"Ошибка при создании HTML демо-ячейки: {str(e)}")
            # Возвращаем оригинальный код в случае ошибки
            return f'<pre><code>{html.escape(example["code"])}</code></pre>'

    def create_interactive_demo_cells(
        self, code_examples: List[Dict], lesson_id: str = None
    ) -> List[widgets.Widget]:
        """
        АЛЬТЕРНАТИВНЫЙ МЕТОД: Создает список интерактивных демо-ячеек как виджетов.

        Args:
            code_examples (List[Dict]): Примеры кода
            lesson_id (str): ID урока

        Returns:
            List[widgets.Widget]: Список демо-ячеек как виджетов
        """
        try:
            demo_widgets = []

            for i, example in enumerate(code_examples):
                cell_id = f"demo_{lesson_id or 'lesson'}_{i}"

                try:
                    # Создаем демо-ячейку через модуль Jupiter notebook
                    demo_cell = create_demo_cell(
                        code=example["code"],
                        title=example["title"],
                        description=example["description"],
                        cell_id=cell_id,
                    )

                    demo_widgets.append(demo_cell)
                    self.logger.debug(
                        f"Создана интерактивная демо-ячейка: {example['title']}"
                    )

                except Exception as cell_error:
                    self.logger.error(
                        f"Ошибка создания демо-ячейки {i}: {str(cell_error)}"
                    )
                    # Создаем fallback виджет
                    fallback_widget = self._create_fallback_demo_widget(example)
                    demo_widgets.append(fallback_widget)

            self.logger.info(f"Создано {len(demo_widgets)} интерактивных демо-ячеек")
            return demo_widgets

        except Exception as e:
            self.logger.error(f"Ошибка при создании интерактивных демо-ячеек: {str(e)}")
            return []

    def _create_fallback_demo_widget(self, example: Dict) -> widgets.Widget:
        """
        Создает fallback виджет в случае ошибки создания демо-ячейки.

        Args:
            example (Dict): Информация о примере

        Returns:
            widgets.Widget: Fallback виджет
        """
        fallback_html = f"""
        <div style="border: 1px solid #ddd; border-radius: 4px; padding: 10px; margin: 10px 0;">
            <h4>📝 {example['title']}</h4>
            <pre style="background: #f5f5f5; padding: 8px; border-radius: 4px;">
                <code>{html.escape(example['code'])}</code>
            </pre>
            <p><em>{example['description']}</em></p>
        </div>
        """

        return widgets.HTML(value=fallback_html)

    def get_integration_stats(self) -> Dict[str, int]:
        """
        Возвращает статистику интеграции демо-ячеек.

        Returns:
            Dict[str, int]: Статистика
        """
        return {"total_cells_created": self._cell_counter, "integration_version": 1}
