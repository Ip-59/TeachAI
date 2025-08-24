"""
Финальная версия ContentFormatter с правильной архитектурой
"""

import re
import logging
from typing import Dict, Any, Optional, List, Tuple
from pathlib import Path

class ContentFormatterFinal:
    """Финальная версия обработчика форматирования контента."""
    
    def __init__(self):
        """Инициализация форматтера."""
        self.logger = logging.getLogger(__name__)
        
        # CSS стили для красивого отображения
        self.base_css = """
        <style>
        .lesson-content {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif !important;
            line-height: 1.6 !important;
            color: #000000 !important;  /* ЧИСТО ЧЕРНЫЙ для максимального контраста */
            max-width: 100% !important;
            margin: 0 auto !important;
            padding: 20px !important;
            font-weight: 900 !important;  /* МАКСИМАЛЬНАЯ жирность основного текста */
        }
        
        .lesson-content h1, .lesson-content h2, .lesson-content h3, .lesson-content h4 {
            color: #000000 !important;  /* Заголовки максимально темные */
            margin-top: 25px !important;
            margin-bottom: 15px !important;
            font-weight: 900 !important;  /* МАКСИМАЛЬНАЯ жирность */
        }
        
        .lesson-content h1 { 
            font-size: 2em !important; 
            border-bottom: 2px solid #000000 !important; 
            padding-bottom: 10px !important; 
            color: #000000 !important; 
            font-weight: 900 !important;
        }
        .lesson-content h2 { 
            font-size: 1.5em !important; 
            border-bottom: 1px solid #000000 !important; 
            padding-bottom: 8px !important; 
            color: #000000 !important; 
            font-weight: 900 !important;
        }
        .lesson-content h3 { 
            font-size: 1.3em !important; 
            color: #000000 !important; 
            font-weight: 900 !important;
        }
        .lesson-content h4 { 
            font-size: 1.1em !important; 
            color: #000000 !important; 
            font-weight: 900 !important;
        }
        
        .lesson-content p {
            margin-bottom: 15px !important;
            text-align: justify !important;
            color: #000000 !important;  /* Максимально темный текст */
            font-weight: 900 !important;  /* Максимальная жирность */
        }
        
        .lesson-content ul, .lesson-content ol {
            margin-bottom: 15px !important;
            padding-left: 25px !important;
        }
        
        .lesson-content li {
            margin-bottom: 8px !important;
            color: #000000 !important;  /* Максимально темный текст */
            font-weight: 900 !important;  /* Максимальная жирность */
        }
        
        .lesson-content strong, .lesson-content b {
            color: #000000 !important;  /* Жирный текст максимально темный */
            font-weight: 900 !important;  /* МАКСИМАЛЬНАЯ жирность */
        }
        
        .lesson-content em, .lesson-content i {
            color: #000000 !important;  /* Курсив тоже максимально темный */
            font-style: italic !important;
            font-weight: 900 !important;  /* Максимальная жирность */
        }
        
        .lesson-content code {
            background-color: #000000 !important;  /* ЧИСТО ЧЕРНЫЙ ФОН для максимального контраста */
            color: #ffffff !important;  /* БЕЛЫЙ ТЕКСТ на черном фоне */
            padding: 3px 8px;
            border-radius: 4px;
            font-family: 'Courier New', monospace;
            font-size: 0.9em;
            font-weight: 900 !important;  /* Максимальная жирность */
            text-shadow: 0 0 2px rgba(255,255,255,0.8) !important;  /* Белая тень для лучшей видимости */
            border: 2px solid #333333;  /* Темная рамка */
        }
        
        .lesson-content pre {
            background-color: #000000 !important;  /* ЧИСТО ЧЕРНЫЙ фон для максимального контраста */
            color: #ffffff !important;  /* БЕЛЫЙ текст на черном фоне */
            padding: 15px !important;
            border-radius: 8px !important;
            overflow-x: auto !important;
            margin: 15px 0 !important;
            border: 3px solid #ffffff !important;  /* БЕЛАЯ рамка для максимального контраста */
        }
        
        .lesson-content pre code {
            background-color: transparent !important;
            color: #ffffff !important;  /* БЕЛЫЙ текст */
            padding: 0 !important;
            font-size: 1.2em !important;  /* Увеличенный размер для лучшей читаемости */
            line-height: 1.6 !important;  /* Увеличенный межстрочный интервал */
            font-weight: 900 !important;  /* МАКСИМАЛЬНАЯ жирность */
            text-shadow: 0 0 5px rgba(0,0,0,1), 0 0 8px rgba(0,0,0,1), 0 0 12px rgba(0,0,0,1) !important;  /* Усиленная черная тень */
        }
        
        /* Стили для комментариев в коде - максимальная контрастность */
        .lesson-content pre code .comment,
        .lesson-content pre code .hljs-comment {
            color: #ffff00 !important;  /* ЯРКО-ЖЕЛТЫЙ для максимального контраста */
            font-weight: 900 !important;  /* Максимальная жирность */
            text-shadow: 0 0 3px rgba(0,0,0,1), 0 0 5px rgba(0,0,0,1) !important;  /* Усиленная черная тень */
        }
        
        /* Стили для строк с комментариями (начинающихся с #) */
        .lesson-content pre code:has(.comment),
        .lesson-content pre code:has(.hljs-comment) {
            color: #ffff00 !important;  /* ЯРКО-ЖЕЛТЫЙ для комментариев */
        }
        
        .lesson-content blockquote {
            border-left: 4px solid #000000 !important;  /* Черная рамка */
            margin: 15px 0 !important;
            padding: 10px 20px !important;
            background-color: #ffffff !important;  /* Белый фон */
            font-style: italic !important;
            color: #000000 !important;  /* Черный текст */
            font-weight: 900 !important;  /* Максимальная жирность */
            border: 2px solid #000000 !important;  /* Черная рамка */
        }
        
        /* ДОПОЛНИТЕЛЬНЫЕ СТИЛИ ДЛЯ МАКСИМАЛЬНОГО КОНТРАСТА */
        .lesson-content * {
            color: #000000 !important;  /* ВСЕ элементы максимально темные */
        }
        
        .lesson-content pre * {
            color: #ffffff !important;  /* ВСЕ элементы в блоках кода - белые */
        }
        
        .lesson-content code * {
            color: #ffffff !important;  /* ВСЕ элементы в inline коде - белые */
        }
        
        /* Принудительное применение стилей */
        .lesson-content, .lesson-content * {
            text-shadow: 0 0 1px rgba(0,0,0,0.5) !important;  /* Легкая тень для всех элементов */
        }
        
        .lesson-content table {
            border-collapse: collapse;
            width: 100%;
            margin: 15px 0;
        }
        
        .lesson-content th, .lesson-content td {
            border: 1px solid #bdc3c7;
            padding: 8px 12px;
            text-align: left;
        }
        
        .lesson-content th {
            background-color: #3498db;
            color: white;
            font-weight: 600;
        }
        
        .lesson-content tr:nth-child(even) {
            background-color: #f8f9fa;
        }
        
        .lesson-content .highlight {
            background-color: #fff3cd;
            padding: 10px;
            border-radius: 5px;
            border-left: 4px solid #ffc107;
            margin: 15px 0;
        }
        
        .lesson-content .warning {
            background-color: #f8d7da;
            padding: 10px;
            border-radius: 5px;
            border-left: 4px solid #dc3545;
            margin: 15px 0;
        }
        
        .lesson-content .info {
            background-color: #d1ecf1;
            padding: 10px;
            border-radius: 5px;
            border-left: 4px solid #17a2b8;
            margin: 15px 0;
        }
        </style>
        """
    
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
            
            # Шаг 2: Обрабатываем markdown разметку
            processed_content = self._process_markdown_simple(content_with_placeholders)
            
            # Шаг 3: Восстанавливаем блоки кода
            final_content = self._restore_code_blocks(processed_content, code_blocks)
            
            # Шаг 4: Очищаем финальный контент от лишних параграфов вокруг блоков кода
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
                
                # Возвращаем плейсхолдер
                placeholder = f"__CODE_BLOCK_{len(code_blocks)-1}__"
                return placeholder
            
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
            # Восстанавливаем блоки кода из плейсхолдеров
            for i, code_block in enumerate(code_blocks):
                placeholder = f"__CODE_BLOCK_{i}__"
                content = content.replace(placeholder, code_block)
            
            # Логируем для отладки
            self.logger.debug(f"Восстановлено {len(code_blocks)} блоков кода")
            
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