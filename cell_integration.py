"""
Адаптер для интеграции системы образовательных ячеек с основной системой TeachAI.
Служит мостом между уроками и ячейками, не нарушая существующую архитектуру.
"""

import re
import logging
from typing import List, Dict, Any, Optional, Tuple
from IPython.display import display
import ipywidgets as widgets

# ZAP-08/D9: модуля demo_cell_widget в репозитории нет — мёртвый импорт убран.
# Раньше ImportError из-за него держал CELLS_AVAILABLE=False; сохраняем False,
# чтобы не включать давно не гонявшийся UI integrate_cells / create_demo_cell.
# Примеры выполняются через examples_display._create_fallback_code_widget + sandbox.
CELLS_AVAILABLE = False

try:
    # Оставлено для прямого использования interactive-ячеек вне adapter.demo-пути.
    from interactive_cell_widget import create_interactive_cell  # noqa: F401
    from result_checker import check_result  # noqa: F401
except ImportError:
    create_interactive_cell = None  # type: ignore
    check_result = None  # type: ignore


class CellIntegrationAdapter:
    """
    Адаптер для интеграции образовательных ячеек с системой уроков.
    Обеспечивает безопасную интеграцию без нарушения существующей архитектуры.
    """

    def __init__(self):
        """Инициализация адаптера."""
        self.logger = logging.getLogger(__name__)
        self.cells_available = CELLS_AVAILABLE

        if not self.cells_available:
            self.logger.warning("Система образовательных ячеек недоступна")

    def extract_code_blocks(self, lesson_content: str) -> List[Dict[str, Any]]:
        """
        Извлекает блоки кода из содержания урока.

        Args:
            lesson_content: Содержание урока

        Returns:
            Список словарей с информацией о блоках кода
        """
        if not self.cells_available:
            return []

        # ИСПРАВЛЕНО: Декодируем HTML-кодировку в содержании урока
        decoded_content = (
            lesson_content.replace("&lt;", "<")
            .replace("&gt;", ">")
            .replace("&amp;", "&")
            .replace("&quot;", '"')
            .replace("&#x27;", "'")
        )

        code_blocks = []

        # Паттерны для поиска кода
        patterns = [
            # Блоки кода в markdown
            r"```python\s*\n(.*?)\n```",
            r"```\s*\n(.*?)\n```",
            # Инлайн код
            r"`([^`]+)`",
            # Простые блоки кода
            r"^\s*(print\(.*\)|import\s+.*|from\s+.*|def\s+.*|class\s+.*|.*=.*)$",
        ]

        lines = decoded_content.split("\n")
        current_block = []
        in_code_block = False

        for i, line in enumerate(lines):
            # Проверяем начало блока кода
            if "```" in line and not in_code_block:
                in_code_block = True
                current_block = []
                continue

            # Проверяем конец блока кода
            if "```" in line and in_code_block:
                in_code_block = False
                if current_block:
                    code_blocks.append(
                        {
                            "type": "demo",
                            "code": "\n".join(current_block),
                            "line_start": i - len(current_block),
                            "line_end": i,
                        }
                    )
                current_block = []
                continue

            # Собираем код в блоке
            if in_code_block:
                current_block.append(line)
                continue

            # Проверяем отдельные строки кода
            for pattern in patterns[2:]:  # Пропускаем markdown блоки
                if re.match(pattern, line.strip()):
                    code_blocks.append(
                        {
                            "type": "demo",
                            "code": line.strip(),
                            "line_start": i,
                            "line_end": i,
                        }
                    )
                    break

        self.logger.info(f"Найдено {len(code_blocks)} блоков кода в уроке")
        return code_blocks

    def is_python_code(self, code: str) -> bool:
        """
        Простая эвристика для фильтрации только Python-кода.
        Возвращает True, если код похож на Python, иначе False.
        """
        # ИСПРАВЛЕНО: Декодируем HTML-кодировку в коде
        decoded_code = (
            code.replace("&lt;", "<")
            .replace("&gt;", ">")
            .replace("&amp;", "&")
            .replace("&quot;", '"')
            .replace("&#x27;", "'")
        )
        
        code = decoded_code.strip()
        if not code:
            return False
        # Явно HTML
        if code.startswith("<") or code.lower().startswith("html"):
            return False
        # Часто встречающиеся HTML-теги
        html_tags = [
            "<div",
            "<span",
            "<p",
            "<a",
            "<img",
            "<table",
            "<tr",
            "<td",
            "<body",
            "<head",
            "<script",
            "<style",
        ]
        if any(code.lower().startswith(tag) for tag in html_tags):
            return False
        # Явные признаки не-Python
        if "class=" in code or "id=" in code or "content-container" in code:
            return False
        # Простейшая эвристика: есть ключевые слова Python
        python_keywords = [
            "def ",
            "import ",
            "print(",
            "for ",
            "while ",
            "if ",
            "return ",
            "class ",
            "=",
            "in ",
            "range(",
            "from ",
        ]
        if any(kw in code for kw in python_keywords):
            return True
        # Если много строк и нет ни одного ключевого слова — тоже не Python
        if "\n" in code:
            return False
        return False

    def create_demo_cells(
        self, code_blocks: List[Dict[str, Any]]
    ) -> List[widgets.Widget]:
        """
        Демо-ячейки через отсутствующий demo_cell_widget больше не создаём (ZAP-08).
        examples_display использует fallback-виджет с code_sandbox.
        """
        return []

    def generate_interactive_tasks(
        self, lesson_content: str, lesson_title: str
    ) -> List[widgets.Widget]:
        """
        Генерирует интерактивные задания на основе содержания урока.

        Args:
            lesson_content: Содержание урока
            lesson_title: Название урока

        Returns:
            Список виджетов интерактивных заданий
        """
        if not self.cells_available:
            return []

        # Простые задания на основе контента урока
        tasks = []

        # Задание 1: Если есть print, просим создать свой
        if "print(" in lesson_content:
            tasks.append(
                {
                    "description": 'Создайте программу, которая выводит "Привет, мир!"',
                    "expected_result": "Привет, мир!",
                    "check_type": "output",
                    "initial_code": '# Напишите код для вывода "Привет, мир!"\n',
                    "title": "Задание 1: Вывод текста",
                }
            )

        # Задание 2: Если есть переменные, просим создать свою
        if "=" in lesson_content and "print(" in lesson_content:
            tasks.append(
                {
                    "description": "Создайте переменную name со своим именем и выведите её",
                    "expected_result": None,  # Будет проверяться наличие переменной
                    "check_type": "function",
                    "initial_code": '# Создайте переменную name и выведите её\nname = "Ваше имя"\n',
                    "title": "Задание 2: Работа с переменными",
                }
            )

        # Создаем ячейки для заданий
        interactive_cells = []
        for i, task in enumerate(tasks):
            try:
                cell = create_interactive_cell(
                    task_description=task["description"],
                    expected_result=task["expected_result"],
                    check_type=task["check_type"],
                    initial_code=task["initial_code"],
                    title=task["title"],
                    cell_id=f"{lesson_title.lower().replace(' ', '_')}_task_{i+1}",
                )
                interactive_cells.append(cell)
                self.logger.info(f"Создано интерактивное задание {i+1}")
            except Exception as e:
                self.logger.error(f"Ошибка создания интерактивного задания {i+1}: {e}")

        return interactive_cells

    def create_cells_container(
        self, demo_cells: List[widgets.Widget], interactive_cells: List[widgets.Widget]
    ) -> Optional[widgets.VBox]:
        """
        Создает контейнер для отображения ячеек.

        Args:
            demo_cells: Список демонстрационных ячеек
            interactive_cells: Список интерактивных ячеек

        Returns:
            Контейнер с ячейками или None, если ячейки недоступны
        """
        if not self.cells_available:
            return None

        if not demo_cells and not interactive_cells:
            return None

        # Создаем заголовки секций
        children = []

        if demo_cells:
            demo_header = widgets.HTML(
                value="<h3>📝 Примеры кода</h3>",
                layout=widgets.Layout(margin="10px 0 5px 0"),
            )
            children.append(demo_header)
            children.extend(demo_cells)

        if interactive_cells:
            if demo_cells:
                # Добавляем разделитель
                separator = widgets.HTML(
                    value="<hr style='margin: 20px 0; border: 1px solid #ddd;'>",
                    layout=widgets.Layout(margin="10px 0"),
                )
                children.append(separator)

            interactive_header = widgets.HTML(
                value="<h3>🎯 Практические задания</h3>",
                layout=widgets.Layout(margin="10px 0 5px 0"),
            )
            children.append(interactive_header)
            children.extend(interactive_cells)

        # Создаем контейнер
        container = widgets.VBox(
            children=children,
            layout=widgets.Layout(
                border="1px solid #e0e0e0",
                border_radius="8px",
                padding="15px",
                margin="10px 0",
                background_color="#fafafa",
            ),
        )

        return container

    def integrate_cells_into_lesson(
        self, lesson_content: str, lesson_title: str
    ) -> Optional[widgets.VBox]:
        """
        Интегрирует ячейки в урок.

        Args:
            lesson_content: Содержание урока
            lesson_title: Название урока

        Returns:
            Контейнер с ячейками или None
        """
        if not self.cells_available:
            self.logger.info("Система ячеек недоступна, пропускаем интеграцию")
            return None

        try:
            # Извлекаем блоки кода
            code_blocks = self.extract_code_blocks(lesson_content)

            # Создаем демонстрационные ячейки
            demo_cells = self.create_demo_cells(code_blocks)

            # Генерируем интерактивные задания
            interactive_cells = self.generate_interactive_tasks(
                lesson_content, lesson_title
            )

            # Создаем контейнер
            cells_container = self.create_cells_container(demo_cells, interactive_cells)

            if cells_container:
                self.logger.info(
                    f"Успешно интегрированы ячейки в урок '{lesson_title}'"
                )

            return cells_container

        except Exception as e:
            self.logger.error(f"Ошибка интеграции ячеек в урок '{lesson_title}': {e}")
            return None

    def is_available(self) -> bool:
        """Проверяет доступность системы ячеек."""
        return self.cells_available


# Глобальный экземпляр адаптера
cell_adapter = CellIntegrationAdapter()
