"""
Модуль для отображения индикаторов загрузки при ожидании ответов от OpenAI API.
Предоставляет различные типы индикаторов для разных операций.
"""

import logging
import time
from typing import Optional, Callable, Any
from IPython.display import display, clear_output, HTML
import ipywidgets as widgets
from threading import Thread, Event

class LoadingIndicator:
    """Базовый класс для индикаторов загрузки."""
    
    def __init__(self):
        """Инициализация индикатора загрузки."""
        self.logger = logging.getLogger(__name__)
        self.is_active = False
        self.widget = None
        self.stop_event = Event()
    
    def show(self, message: str = "Загрузка...") -> widgets.Widget:
        """
        Показывает индикатор загрузки.
        
        Args:
            message: Сообщение для отображения
            
        Returns:
            widgets.Widget: Виджет с индикатором
        """
        try:
            self.is_active = True
            self.stop_event.clear()
            
            # Создаем виджет с анимированным индикатором
            html_content = f"""
            <div style='background: #f8f9fa; padding: 20px; border-radius: 10px; margin: 10px 0; text-align: center; border: 2px solid #ecf0f1;'>
                <div style='display: inline-block; width: 40px; height: 40px; border: 4px solid #ecf0f1; border-top: 4px solid #3498db; border-radius: 50%; animation: spin 1s linear infinite;'></div>
                <p style='margin: 15px 0 0 0; color: #2c3e50; font-size: 1em; font-weight: 500;'>{message}</p>
                <p style='margin: 5px 0 0 0; color: #7f8c8d; font-size: 0.8em;'>Пожалуйста, подождите...</p>
                <style>
                    @keyframes spin {{
                        0% {{ transform: rotate(0deg); }}
                        100% {{ transform: rotate(360deg); }}
                    }}
                </style>
            </div>
            """
            
            self.widget = widgets.HTML(value=html_content)
            self.logger.info(f"Индикатор загрузки показан: {message}")
            return self.widget
            
        except Exception as e:
            self.logger.error(f"Ошибка при показе индикатора загрузки: {str(e)}")
            return self._create_error_widget(str(e))
    
    def hide(self):
        """Скрывает индикатор загрузки."""
        try:
            self.is_active = False
            self.stop_event.set()
            
            if self.widget:
                # Очищаем вывод
                clear_output(wait=True)
                self.logger.info("Индикатор загрузки скрыт")
                
        except Exception as e:
            self.logger.error(f"Ошибка при скрытии индикатора загрузки: {str(e)}")
    
    def _create_error_widget(self, error_message: str) -> widgets.Widget:
        """Создает виджет с сообщением об ошибке."""
        html_content = f"""
        <div style='background: #fee; padding: 15px; border-radius: 10px; margin: 10px 0; border-left: 4px solid #e74c3c;'>
            <h4 style='margin: 0 0 15px 0; color: #c0392b;'>❌ Ошибка индикатора загрузки</h4>
            <p style='margin: 5px 0; font-size: 0.9em; color: #7f8c8d;'>
                {error_message}
            </p>
        </div>
        """
        
        return widgets.HTML(value=html_content)


class OpenAIAPILoadingIndicator(LoadingIndicator):
    """Специализированный индикатор для операций с OpenAI API."""
    
    def __init__(self):
        """Инициализация индикатора для OpenAI API."""
        super().__init__()
        self.operation_messages = {
            "generate_lesson": "🎓 Генерирую урок...",
            "generate_examples": "📝 Создаю примеры...",
            "generate_test": "📋 Формирую тест...",
            "generate_explanation": "💡 Генерирую объяснение...",
            "generate_control_task": "💻 Создаю контрольное задание...",
            "check_relevance": "🔍 Проверяю релевантность...",
            "generate_qa": "❓ Генерирую вопросы и ответы...",
            "default": "🤖 Обрабатываю запрос к OpenAI..."
        }
    
    def show_for_operation(self, operation: str, custom_message: Optional[str] = None) -> widgets.Widget:
        """
        Показывает индикатор для конкретной операции.
        
        Args:
            operation: Тип операции
            custom_message: Пользовательское сообщение
            
        Returns:
            widgets.Widget: Виджет с индикатором
        """
        message = custom_message or self.operation_messages.get(operation, self.operation_messages["default"])
        
        # Добавляем дополнительную информацию для API операций
        enhanced_message = f"{message}\n\n⏱️ Это может занять несколько секунд..."
        
        return self.show(enhanced_message)
    
    def show_with_progress(self, operation: str, progress_callback: Optional[Callable] = None) -> widgets.Widget:
        """
        Показывает индикатор с возможностью обновления прогресса.
        
        Args:
            operation: Тип операции
            progress_callback: Функция обратного вызова для обновления прогресса
            
        Returns:
            widgets.Widget: Виджет с индикатором
        """
        message = self.operation_messages.get(operation, self.operation_messages["default"])
        
        html_content = f"""
        <div style='background: #f8f9fa; padding: 20px; border-radius: 10px; margin: 10px 0; text-align: center; border: 2px solid #ecf0f1;'>
            <div style='display: inline-block; width: 40px; height: 40px; border: 4px solid #ecf0f1; border-top: 4px solid #3498db; border-radius: 50%; animation: spin 1s linear infinite;'></div>
            <p style='margin: 15px 0 0 0; color: #2c3e50; font-size: 1em; font-weight: 500;'>{message}</p>
            <p style='margin: 5px 0 0 0; color: #7f8c8d; font-size: 0.8em;'>⏱️ Ожидание ответа от OpenAI API...</p>
            <div id='progress-container' style='margin: 10px 0;'>
                <div style='background: #ecf0f1; height: 6px; border-radius: 3px; overflow: hidden;'>
                    <div id='progress-bar' style='background: #3498db; height: 100%; width: 0%; transition: width 0.3s ease;'></div>
                </div>
                <p id='progress-text' style='margin: 5px 0; font-size: 0.8em; color: #7f8c8d;'>Подключение к API...</p>
            </div>
            <style>
                @keyframes spin {{
                    0% {{ transform: rotate(0deg); }}
                    100% {{ transform: rotate(360deg); }}
                }}
            </style>
        </div>
        """
        
        self.widget = widgets.HTML(value=html_content)
        self.logger.info(f"Индикатор с прогрессом показан для операции: {operation}")
        return self.widget
    
    def update_progress(self, progress: int, status_message: str = ""):
        """
        Обновляет прогресс индикатора.
        
        Args:
            progress: Процент выполнения (0-100)
            status_message: Сообщение о статусе
        """
        if not self.is_active or not self.widget:
            return
        
        try:
            # Обновляем HTML с новым прогрессом
            current_html = self.widget.value
            
            # Заменяем прогресс-бар
            progress_bar_style = f"width: {progress}%;"
            current_html = current_html.replace(
                'id="progress-bar" style="background: #3498db; height: 100%; width: 0%; transition: width 0.3s ease;"',
                f'id="progress-bar" style="background: #3498db; height: 100%; {progress_bar_style} transition: width 0.3s ease;"'
            )
            
            # Заменяем текст статуса
            if status_message:
                current_html = current_html.replace(
                    'id="progress-text" style="margin: 5px 0; font-size: 0.8em; color: #7f8c8d;">Подключение к API...</p>',
                    f'id="progress-text" style="margin: 5px 0; font-size: 0.8em; color: #7f8c8d;">{status_message}</p>'
                )
            
            self.widget.value = current_html
            
        except Exception as e:
            self.logger.error(f"Ошибка при обновлении прогресса: {str(e)}")


class LessonLoadingIndicator(OpenAIAPILoadingIndicator):
    """Специализированный индикатор для загрузки уроков."""
    
    def __init__(self):
        """Инициализация индикатора для уроков."""
        super().__init__()
        self.lesson_operation_messages = {
            "loading_lesson": "📖 Загружаю урок...",
            "generating_content": "✍️ Генерирую контент урока...",
            "preparing_examples": "📝 Подготавливаю примеры...",
            "creating_test": "📋 Создаю тест для проверки знаний...",
            "finalizing": "✅ Завершаю подготовку урока..."
        }
    
    def show_lesson_loading(self, lesson_title: str = "") -> widgets.Widget:
        """
        Показывает индикатор загрузки урока.
        
        Args:
            lesson_title: Название загружаемого урока
            
        Returns:
            widgets.Widget: Виджет с индикатором
        """
        title_text = f" для урока '{lesson_title}'" if lesson_title else ""
        message = f"📖 Загружаю урок{title_text}..."
        
        html_content = f"""
        <div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 10px; margin: 10px 0; text-align: center;'>
            <div style='display: inline-block; width: 50px; height: 50px; border: 4px solid rgba(255,255,255,0.3); border-top: 4px solid white; border-radius: 50%; animation: spin 1s linear infinite;'></div>
            <h3 style='margin: 15px 0 0 0; color: white;'>{message}</h3>
            <p style='margin: 10px 0 0 0; opacity: 0.9; font-size: 0.9em;'>⏱️ Это может занять несколько секунд...</p>
            <div style='margin: 15px 0 0 0;'>
                <div style='background: rgba(255,255,255,0.2); height: 8px; border-radius: 4px; overflow: hidden;'>
                    <div id='lesson-progress' style='background: white; height: 100%; width: 0%; transition: width 0.5s ease;'></div>
                </div>
                <p id='lesson-status' style='margin: 5px 0 0 0; opacity: 0.8; font-size: 0.8em;'>Подготовка контента...</p>
            </div>
            <style>
                @keyframes spin {{
                    0% {{ transform: rotate(0deg); }}
                    100% {{ transform: rotate(360deg); }}
                }}
            </style>
        </div>
        """
        
        self.widget = widgets.HTML(value=html_content)
        self.logger.info(f"Индикатор загрузки урока показан: {lesson_title}")
        return self.widget
    
    def update_lesson_progress(self, stage: str, progress: int = 0):
        """
        Обновляет прогресс загрузки урока.
        
        Args:
            stage: Этап загрузки
            progress: Процент выполнения
        """
        if not self.is_active or not self.widget:
            return
        
        try:
            stage_messages = {
                "loading_lesson": "Загружаю урок...",
                "generating_content": "Генерирую контент...",
                "preparing_examples": "Подготавливаю примеры...",
                "creating_test": "Создаю тест...",
                "finalizing": "Завершаю подготовку..."
            }
            
            status_message = stage_messages.get(stage, "Обработка...")
            
            # Обновляем HTML
            current_html = self.widget.value
            
            # Обновляем прогресс-бар
            progress_bar_style = f"width: {progress}%;"
            current_html = current_html.replace(
                'id="lesson-progress" style="background: white; height: 100%; width: 0%; transition: width 0.5s ease;"',
                f'id="lesson-progress" style="background: white; height: 100%; {progress_bar_style} transition: width 0.5s ease;"'
            )
            
            # Обновляем статус
            current_html = current_html.replace(
                'id="lesson-status" style="margin: 5px 0 0 0; opacity: 0.8; font-size: 0.8em;">Подготовка контента...</p>',
                f'id="lesson-status" style="margin: 5px 0 0 0; opacity: 0.8; font-size: 0.8em;">{status_message}</p>'
            )
            
            self.widget.value = current_html
            
        except Exception as e:
            self.logger.error(f"Ошибка при обновлении прогресса урока: {str(e)}")


class LoadingManager:
    """Менеджер для управления индикаторами загрузки."""
    
    def __init__(self):
        """Инициализация менеджера загрузки."""
        self.logger = logging.getLogger(__name__)
        self.current_indicator = None
        self.indicators = {
            "default": LoadingIndicator(),
            "openai": OpenAIAPILoadingIndicator(),
            "lesson": LessonLoadingIndicator()
        }
    
    def show_loading(self, indicator_type: str = "default", **kwargs) -> widgets.Widget:
        """
        Показывает индикатор загрузки.
        
        Args:
            indicator_type: Тип индикатора
            **kwargs: Дополнительные параметры
            
        Returns:
            widgets.Widget: Виджет с индикатором
        """
        try:
            indicator = self.indicators.get(indicator_type, self.indicators["default"])
            
            if indicator_type == "openai" and "operation" in kwargs:
                self.current_indicator = indicator.show_for_operation(kwargs["operation"])
            elif indicator_type == "lesson":
                lesson_title = kwargs.get("lesson_title", "")
                self.current_indicator = indicator.show_lesson_loading(lesson_title)
            else:
                message = kwargs.get("message", "Загрузка...")
                self.current_indicator = indicator.show(message)
            
            self.logger.info(f"Индикатор загрузки показан: {indicator_type}")
            return self.current_indicator
            
        except Exception as e:
            self.logger.error(f"Ошибка при показе индикатора загрузки: {str(e)}")
            return self._create_error_widget(str(e))
    
    def hide_loading(self):
        """Скрывает текущий индикатор загрузки."""
        try:
            if self.current_indicator:
                # Находим активный индикатор и скрываем его
                for indicator in self.indicators.values():
                    if indicator.is_active:
                        indicator.hide()
                        break
                
                self.current_indicator = None
                self.logger.info("Индикатор загрузки скрыт")
                
        except Exception as e:
            self.logger.error(f"Ошибка при скрытии индикатора загрузки: {str(e)}")
    
    def update_progress(self, progress: int, status_message: str = ""):
        """
        Обновляет прогресс текущего индикатора.
        
        Args:
            progress: Процент выполнения
            status_message: Сообщение о статусе
        """
        try:
            # Находим активный индикатор и обновляем его
            for indicator in self.indicators.values():
                if indicator.is_active and hasattr(indicator, 'update_progress'):
                    indicator.update_progress(progress, status_message)
                    break
                    
        except Exception as e:
            self.logger.error(f"Ошибка при обновлении прогресса: {str(e)}")
    
    def _create_error_widget(self, error_message: str) -> widgets.Widget:
        """Создает виджет с сообщением об ошибке."""
        html_content = f"""
        <div style='background: #fee; padding: 15px; border-radius: 10px; margin: 10px 0; border-left: 4px solid #e74c3c;'>
            <h4 style='margin: 0 0 15px 0; color: #c0392b;'>❌ Ошибка индикатора загрузки</h4>
            <p style='margin: 5px 0; font-size: 0.9em; color: #7f8c8d;'>
                {error_message}
            </p>
        </div>
        """
        
        return widgets.HTML(value=html_content) 