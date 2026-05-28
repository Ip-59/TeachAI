"""
Финальная версия ContentFormatter с правильной архитектурой
"""

import re
import logging
from typing import Dict, Any, Optional, List, Tuple
from pathlib import Path

from content_renderer import enhance_content, render_markdown_to_html

_CODE_PLACEHOLDER_TAG = "TEACHAI_CODE_BLOCK"


def code_block_placeholder(index: int) -> str:
    """HTML-комментарий — markdown его не ломает (в отличие от __PLACEHOLDER__)."""
    return f"<!--{_CODE_PLACEHOLDER_TAG}_{index}-->"


def content_has_unresolved_code_placeholders(content: str) -> bool:
    """True, если в HTML остались заглушки вместо блоков кода."""
    if not content:
        return False
    if "<pre>" in content and "CODE_BLOCK_" not in content:
        return False
    return bool(
        re.search(
            rf"(?:<!--{_CODE_PLACEHOLDER_TAG}_\d+-->|<strong>CODE_BLOCK_\d+</strong>|__CODE_BLOCK_\d+__)",
            content,
            re.IGNORECASE,
        )
    )

class ContentFormatterFinal:
    """Финальная версия обработчика форматирования контента."""
    
    def __init__(self):
        """Инициализация форматтера."""
        self.logger = logging.getLogger(__name__)
        
        # Стили урока задаются в content_renderer.get_display_css() при показе
        self.base_css = ""
    
    def format_lesson_content(self, raw_content: str, lesson_title: str = "") -> str:
        """
        Форматирует контент урока для правильного отображения.
        
        Args:
            raw_content (str): Сырой контент от OpenAI
            lesson_title (str): Название урока
            
        Returns:
            str: Отформатированный HTML контент
        """
        try:
            self.logger.info(f"Форматирование контента урока: {lesson_title}")
            
            # Очищаем контент
            cleaned_content = self._clean_content(raw_content)
            
            # Шаг 1: Извлекаем блоки кода и создаем плейсхолдеры
            content_with_placeholders, code_blocks = self._extract_code_blocks(cleaned_content)
            
            # Шаг 2: Markdown → HTML (таблицы, списки, заголовки)
            processed_content = render_markdown_to_html(content_with_placeholders)
            
            # Шаг 3: Восстанавливаем блоки кода
            final_content = self._restore_code_blocks(processed_content, code_blocks)
            
            # Шаг 4: LaTeX и таблицы, которые LLM мог вставить после markdown
            final_content = enhance_content(final_content)
            
            # Шаг 5: Очищаем финальный контент от лишних параграфов вокруг блоков кода
            final_content = self._clean_final_content(final_content)
            
            # Создаем финальный HTML
            final_html = self._create_final_html(final_content, lesson_title)
            
            self.logger.info("Контент успешно отформатирован")
            return final_html
            
        except Exception as e:
            self.logger.error(f"Ошибка при форматировании контента: {str(e)}")
            return self._create_error_html(raw_content, str(e))
    
    def _clean_content(self, content: str) -> str:
        """Очищает контент от лишних элементов."""
        try:
            # Убираем лишние пробелы и переносы
            content = re.sub(r'\n\s*\n\s*\n', '\n\n', content)
            content = content.strip()
            
            # Убираем лишние HTML теги если они есть
            content = re.sub(r'<div[^>]*>|</div>', '', content)
            content = re.sub(r'<p[^>]*>|</p>', '', content)
            
            return content
            
        except Exception as e:
            self.logger.error(f"Ошибка при очистке контента: {str(e)}")
            return content
    
    def _extract_code_blocks(self, content: str) -> Tuple[str, List[str]]:
        """Извлекает блоки кода и заменяет их плейсхолдерами."""
        try:
            code_blocks = []
            code_block_pattern = r'```(\w+)?\n(.*?)\n```'
            
            def save_code_block(match):
                language = match.group(1) or 'python'
                code = match.group(2)
                
                # Форматируем код
                formatted_code = self._format_code(code, language)
                
                # Создаем HTML для блока кода
                html_block = f'<pre><code class="language-{language}">{formatted_code}</code></pre>'
                
                # Сохраняем блок кода
                code_blocks.append(html_block)
                
                # Возвращаем плейсхолдер (HTML-комментарий — безопасен для markdown)
                return code_block_placeholder(len(code_blocks) - 1)
            
            # Заменяем блоки кода на плейсхолдеры
            content_with_placeholders = re.sub(code_block_pattern, save_code_block, content, flags=re.DOTALL)
            
            return content_with_placeholders, code_blocks
            
        except Exception as e:
            self.logger.error(f"Ошибка при извлечении блоков кода: {str(e)}")
            return content, []
    
    def _format_code(self, code: str, language: str = 'python') -> str:
        """Форматирует код с правильными отступами и подсветкой комментариев."""
        try:
            # Убираем лишние пробелы в начале строк
            lines = code.split('\n')
            formatted_lines = []
            
            for line in lines:
                # Убираем лишние пробелы в начале
                cleaned_line = line.rstrip()
                if cleaned_line:
                    # Проверяем, является ли строка комментарием
                    if cleaned_line.strip().startswith('#'):
                        # Сначала экранируем HTML символы в комментарии
                        escaped_line = cleaned_line.replace('<', '&lt;').replace('>', '&gt;')
                        # Потом добавляем класс для комментария
                        formatted_line = f'<span class="comment">{escaped_line}</span>'
                    else:
                        # Для обычных строк кода экранируем HTML символы
                        formatted_line = cleaned_line.replace('<', '&lt;').replace('>', '&gt;')
                    formatted_lines.append(formatted_line)
            
            # Собираем код обратно
            formatted_code = '\n'.join(formatted_lines)
            
            return formatted_code
            
        except Exception as e:
            self.logger.error(f"Ошибка при форматировании кода: {str(e)}")
            return code
    
    def _process_markdown_simple(self, content: str) -> str:
        """Простая обработка markdown разметки."""
        try:
            # ЗАЩИТА ПЛЕЙСХОЛДЕРОВ: Используем уникальные маркеры без подчеркиваний
            placeholder_map = {}
            placeholder_pattern = r'__CODE_BLOCK_(\d+)__'
            
            def protect_placeholder(match):
                placeholder = match.group(0)
                placeholder_id = match.group(1)
                # Используем HTML-подобный маркер, который точно не будет обработан markdown
                protected_marker = f"<placeholder-code-block-{placeholder_id}/>"
                placeholder_map[protected_marker] = placeholder
                return protected_marker
            
            # Защищаем плейсхолдеры от markdown обработки
            content = re.sub(placeholder_pattern, protect_placeholder, content)
            
            # Заголовки
            content = re.sub(r'^#### (.*?)$', r'<h4>\1</h4>', content, flags=re.MULTILINE)
            content = re.sub(r'^### (.*?)$', r'<h3>\1</h3>', content, flags=re.MULTILINE)
            content = re.sub(r'^## (.*?)$', r'<h2>\1</h2>', content, flags=re.MULTILINE)
            content = re.sub(r'^# (.*?)$', r'<h1>\1</h1>', content, flags=re.MULTILINE)
            
            # Жирный текст
            content = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', content)
            content = re.sub(r'__(.*?)__', r'<strong>\1</strong>', content)
            
            # Курсив
            content = re.sub(r'\*(.*?)\*', r'<em>\1</em>', content)
            content = re.sub(r'_(.*?)_', r'<em>\1</em>', content)
            
            # Обрабатываем списки
            content = self._process_lists_simple(content)
            
            # Параграфы (но не для плейсхолдеров)
            content = re.sub(r'^\s*([^<].*?)$', r'<p>\1</p>', content, flags=re.MULTILINE)
            
            # Убираем параграфы вокруг плейсхолдеров
            content = re.sub(r'<p>\s*__CODE_BLOCK_\d+__\s*</p>', lambda m: m.group(0).replace('<p>', '').replace('</p>', ''), content)
            
            # Убираем параграфы вокруг блоков кода
            content = re.sub(r'<p>\s*<pre><code[^>]*>.*?</code></pre>\s*</p>', lambda m: m.group(0).replace('<p>', '').replace('</p>', ''), content, flags=re.DOTALL)
            
            # Убираем лишние теги параграфов
            content = re.sub(r'<p>\s*</p>', '', content)
            content = re.sub(r'<p>\s*<h([1-6])>', r'<h\1>', content)
            content = re.sub(r'</h([1-6])>\s*</p>', r'</h\1>', content)
            
            # Исправляем структуру списков
            content = re.sub(r'<p>\s*<ul>', r'<ul>', content)
            content = re.sub(r'</ul>\s*</p>', r'</ul>', content)
            
            # ВОССТАНОВЛЕНИЕ ПЛЕЙСХОЛДЕРОВ: Возвращаем оригинальные плейсхолдеры
            for protected_marker, original_placeholder in placeholder_map.items():
                content = content.replace(protected_marker, original_placeholder)
            
            return content
            
        except Exception as e:
            self.logger.error(f"Ошибка при обработке markdown: {str(e)}")
            return content
    
    def _process_lists_simple(self, content: str) -> str:
        """Простая обработка списков."""
        try:
            # Находим блоки списков
            lines = content.split('\n')
            result_lines = []
            in_list = False
            
            for line in lines:
                if re.match(r'^\s*[\*\-]\s+', line):
                    if not in_list:
                        result_lines.append('<ul>')
                        in_list = True
                    # Убираем маркер списка и добавляем как li
                    list_item = re.sub(r'^\s*[\*\-]\s+', '', line)
                    result_lines.append(f'<li>{list_item}</li>')
                else:
                    if in_list:
                        result_lines.append('</ul>')
                        in_list = False
                    result_lines.append(line)
            
            if in_list:
                result_lines.append('</ul>')
            
            return '\n'.join(result_lines)
            
        except Exception as e:
            self.logger.error(f"Ошибка при обработке списков: {str(e)}")
            return content
    
    def _restore_code_blocks(self, content: str, code_blocks: List[str]) -> str:
        """Восстанавливает блоки кода из плейсхолдеров."""
        try:
            for i, code_block in enumerate(code_blocks):
                placeholders = (
                    code_block_placeholder(i),
                    f"__CODE_BLOCK_{i}__",
                )
                for placeholder in placeholders:
                    content = content.replace(placeholder, code_block)

                # Старый баг: markdown превращал __CODE_BLOCK_N__ в <strong>CODE_BLOCK_N</strong>
                content = re.sub(
                    rf"<p>\s*<strong>CODE_BLOCK_{i}</strong>\s*</p>",
                    code_block,
                    content,
                    flags=re.IGNORECASE,
                )
                content = re.sub(
                    rf"<strong>CODE_BLOCK_{i}</strong>",
                    code_block,
                    content,
                    flags=re.IGNORECASE,
                )

            self.logger.debug("Восстановлено %s блоков кода", len(code_blocks))
            return content
            
        except Exception as e:
            self.logger.error(f"Ошибка при восстановлении блоков кода: {str(e)}")
            return content
    
    def _clean_final_content(self, content: str) -> str:
        """Очищает финальный контент от лишних параграфов вокруг блоков кода."""
        try:
            # Убираем параграфы вокруг блоков кода
            content = re.sub(r'<p>\s*<pre><code[^>]*>.*?</code></pre>\s*</p>', 
                           lambda m: m.group(0).replace('<p>', '').replace('</p>', ''), 
                           content, flags=re.DOTALL)
            
            # Убираем лишние пустые параграфы
            content = re.sub(r'<p>\s*</p>', '', content)
            
            return content
            
        except Exception as e:
            self.logger.error(f"Ошибка при очистке финального контента: {str(e)}")
            return content
    
    def _create_final_html(self, content: str, lesson_title: str) -> str:
        """Создает финальный HTML."""
        try:
            html = f"""
            <div class="lesson-content">
                {self.base_css}
                {content}
            </div>
            """
            return html
            
        except Exception as e:
            self.logger.error(f"Ошибка при создании HTML: {str(e)}")
            return f"<div class='lesson-content'>{content}</div>"
    
    def _create_error_html(self, original_content: str, error_message: str) -> str:
        """Создает HTML с ошибкой."""
        return f"""
        <div class="lesson-content">
            {self.base_css}
            <div class="warning">
                <h3>Ошибка форматирования</h3>
                <p>Произошла ошибка при форматировании контента: {error_message}</p>
                <p>Оригинальный контент:</p>
                <pre>{original_content}</pre>
            </div>
        </div>
        """ 