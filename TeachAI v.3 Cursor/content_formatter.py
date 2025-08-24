"""
Единый обработчик форматирования контента для TeachAI.
Обеспечивает стабильное и правильное отображение учебного материала.
"""

import re
import logging
from typing import Dict, Any, Optional
from pathlib import Path

class ContentFormatter:
    """Единый обработчик форматирования контента."""
    
    def __init__(self):
        """Инициализация форматтера."""
        self.logger = logging.getLogger(__name__)
        
        # CSS стили для красивого отображения
        self.base_css = """
        <style>
        .lesson-content {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 100%;
            margin: 0 auto;
            padding: 20px;
        }
        
        .lesson-content h1, .lesson-content h2, .lesson-content h3, .lesson-content h4 {
            color: #2c3e50;
            margin-top: 25px;
            margin-bottom: 15px;
            font-weight: 600;
        }
        
        .lesson-content h1 { font-size: 2em; border-bottom: 2px solid #3498db; padding-bottom: 10px; }
        .lesson-content h2 { font-size: 1.5em; border-bottom: 1px solid #bdc3c7; padding-bottom: 8px; }
        .lesson-content h3 { font-size: 1.3em; color: #34495e; }
        .lesson-content h4 { font-size: 1.1em; color: #7f8c8d; }
        
        .lesson-content p {
            margin-bottom: 15px;
            text-align: justify;
        }
        
        .lesson-content ul, .lesson-content ol {
            margin-bottom: 15px;
            padding-left: 25px;
        }
        
        .lesson-content li {
            margin-bottom: 8px;
        }
        
        .lesson-content strong, .lesson-content b {
            color: #2c3e50;
            font-weight: 600;
        }
        
        .lesson-content em, .lesson-content i {
            color: #7f8c8d;
            font-style: italic;
        }
        
        .lesson-content code {
            background-color: #f8f9fa;
            padding: 2px 6px;
            border-radius: 4px;
            font-family: 'Courier New', monospace;
            color: #e74c3c;
            font-size: 0.9em;
        }
        
        .lesson-content pre {
            background-color: #2c3e50;
            color: #ecf0f1;
            padding: 15px;
            border-radius: 8px;
            overflow-x: auto;
            margin: 15px 0;
            border-left: 4px solid #3498db;
        }
        
        .lesson-content pre code {
            background-color: transparent;
            color: inherit;
            padding: 0;
            font-size: 0.95em;
            line-height: 1.4;
        }
        
        .lesson-content blockquote {
            border-left: 4px solid #3498db;
            margin: 15px 0;
            padding: 10px 20px;
            background-color: #f8f9fa;
            font-style: italic;
            color: #7f8c8d;
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
            
            # Очищаем контент от лишних элементов
            cleaned_content = self._clean_content(raw_content)
            
            # ИСПРАВЛЕНО: Сначала обрабатываем блоки кода, потом markdown
            # Обрабатываем markdown блоки кода (ПЕРЕД markdown разметкой)
            processed_content = self._process_code_blocks(cleaned_content)
            
            # Обрабатываем markdown разметку (после блоков кода)
            processed_content = self._process_markdown(processed_content)
            
            # Создаем финальный HTML
            final_html = self._create_final_html(processed_content, lesson_title)
            
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
            
            # Убираем лишние markdown метки
            content = re.sub(r'```\w*\n?', '```', content)
            
            return content
            
        except Exception as e:
            self.logger.error(f"Ошибка при очистке контента: {str(e)}")
            return content
    
    def _process_code_blocks(self, content: str) -> str:
        """Обрабатывает блоки кода с использованием плейсхолдеров."""
        try:
            # Находим все блоки кода ```python ... ```
            code_block_pattern = r'```(\w+)?\n(.*?)\n```'
            
            # Сохраняем блоки кода как плейсхолдеры
            code_blocks = []
            
            def save_code_block(match):
                language = match.group(1) or 'python'
                code = match.group(2)
                
                # Форматируем код с правильными отступами
                formatted_code = self._format_code(code, language)
                
                # Создаем HTML для блока кода
                html_block = f'<pre><code class="language-{language}">{formatted_code}</code></pre>'
                
                # Сохраняем блок кода
                code_blocks.append(html_block)
                
                # Возвращаем плейсхолдер
                return f"__CODE_BLOCK_{len(code_blocks)-1}__"
            
            # Заменяем блоки кода на плейсхолдеры
            content = re.sub(code_block_pattern, save_code_block, content, flags=re.DOTALL)
            
            # Обрабатываем inline код (но не внутри блоков кода)
            # Ищем `code` но не внутри уже обработанных блоков
            # Важно: обрабатываем только одиночные `code`, не тройные ```
            inline_code_pattern = r'(?<!`)`([^`]+)`(?!`)'
            content = re.sub(inline_code_pattern, r'<code>\1</code>', content)
            
            # Дополнительно обрабатываем inline код, который мог остаться
            # Ищем одиночные `code` в тексте
            remaining_inline_pattern = r'`([^`\n]+)`'
            content = re.sub(remaining_inline_pattern, r'<code>\1</code>', content)
            
            # Восстанавливаем блоки кода из плейсхолдеров
            for i, code_block in enumerate(code_blocks):
                content = content.replace(f"__CODE_BLOCK_{i}__", code_block)
            
            return content
            
        except Exception as e:
            self.logger.error(f"Ошибка при обработке блоков кода: {str(e)}")
            return content
    
    def _format_code(self, code: str, language: str = 'python') -> str:
        """Форматирует код с правильными отступами."""
        try:
            # Убираем лишние пробелы в начале строк
            lines = code.split('\n')
            cleaned_lines = []
            
            for line in lines:
                # Убираем лишние пробелы в начале
                cleaned_line = line.rstrip()
                if cleaned_line:
                    cleaned_lines.append(cleaned_line)
            
            # Собираем код обратно
            formatted_code = '\n'.join(cleaned_lines)
            
            # Экранируем HTML символы
            formatted_code = formatted_code.replace('<', '&lt;').replace('>', '&gt;')
            
            return formatted_code
            
        except Exception as e:
            self.logger.error(f"Ошибка при форматировании кода: {str(e)}")
            return code
    
    def _process_markdown(self, content: str) -> str:
        """Обрабатывает markdown разметку."""
        try:
            # Заголовки
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
            content = self._process_lists(content)
            
            # Параграфы (но не для элементов списка)
            content = re.sub(r'^\s*([^<].*?)$', r'<p>\1</p>', content, flags=re.MULTILINE)
            
            # Убираем лишние теги параграфов
            content = re.sub(r'<p>\s*</p>', '', content)
            content = re.sub(r'<p>\s*<h([1-6])>', r'<h\1>', content)
            content = re.sub(r'</h([1-6])>\s*</p>', r'</h\1>', content)
            
            # Исправляем структуру списков
            content = re.sub(r'<p>\s*<ul>', r'<ul>', content)
            content = re.sub(r'</ul>\s*</p>', r'</ul>', content)
            
            return content
            
        except Exception as e:
            self.logger.error(f"Ошибка при обработке markdown: {str(e)}")
            return content
    
    def _process_lists(self, content: str) -> str:
        """Обрабатывает списки."""
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