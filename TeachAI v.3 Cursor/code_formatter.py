#!/usr/bin/env python3
"""
Модуль для безопасной обработки кода в тексте уроков.
Вынесено в отдельный файл для изоляции от основного функционала.
"""

import re
import logging

class CodeFormatter:
    """Безопасный форматировщик кода для текста уроков."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def format_code_in_text(self, text: str) -> str:
        """
        Безопасно форматирует код в тексте урока.
        
        Args:
            text (str): Исходный текст урока
            
        Returns:
            str: Текст с отформатированным кодом
        """
        try:
            # ИСПРАВЛЕНО: Простая обработка - убираем лишние пробелы в начале кода
            pattern = r"```python\s*(.*?)\s*```"
            
            def replace_code_block(match):
                code_content = match.group(1).strip()
                
                if not code_content:
                    return match.group(0)  # Возвращаем исходный блок
                
                # ИСПРАВЛЕНО: Просто убираем лишние пробелы в начале первой строки
                lines = code_content.split('\n')
                if lines:
                    # Убираем лишние пробелы в начале первой строки
                    first_line = lines[0].lstrip()
                    if first_line:
                        lines[0] = first_line
                
                # Собираем код обратно
                formatted_code = '\n'.join(lines)
                
                # Возвращаем отформатированный код в Markdown блоке
                return f"```python\n{formatted_code}\n```"
            
            # Заменяем все блоки кода
            formatted_text = re.sub(pattern, replace_code_block, text, flags=re.DOTALL)
            
            return formatted_text
            
        except Exception as e:
            self.logger.error(f"Ошибка при форматировании кода: {e}")
            return text  # Возвращаем исходный текст при ошибке

# Создаем глобальный экземпляр
code_formatter = CodeFormatter() 