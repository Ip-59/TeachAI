"""
Основной модуль системы TeachAI.
Отвечает за инициализацию и координацию всех компонентов системы.
ИСПРАВЛЕНО: правильная логика запуска с проверкой завершенности уроков (проблема #87)
"""

import os
import logging
from pathlib import Path

# Импортируем компоненты системы
from config import ConfigManager
from state_manager import StateManager
from content_generator import ContentGenerator
from assessment import Assessment
from logger import Logger
from interface import UserInterface, InterfaceState

# Импортируем новые компоненты для улучшения UX
from startup_dashboard import StartupDashboard
from loading_indicators import LoadingManager

class TeachAIEngine:
    """Основной класс системы TeachAI, который координирует все компоненты."""
    
    def __init__(self):
        """Инициализация системы TeachAI."""
        # Настраиваем базовый логгер
        self._setup_logging()
        self.logger = logging.getLogger(__name__)
        self.logger.info("Инициализация TeachAI...")
        
        # Инициализируем компоненты
        self.config_manager = None
        self.state_manager = None
        self.system_logger = None
        self.content_generator = None
        self.assessment = None
        self.interface = None
        
        # Инициализируем новые компоненты для улучшения UX
        self.startup_dashboard = None
        self.loading_manager = None
        
        # Флаг готовности системы
        self.is_ready = False
    
    def _setup_logging(self):
        """Настраивает базовый логгер для системы."""
        # Создаем директорию для логов, если она не существует
        Path("logs").mkdir(exist_ok=True)
        
        # Настраиваем формат логов
        log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        logging.basicConfig(
            level=logging.INFO,
            format=log_format,
            handlers=[
                # Явно указываем кодировку UTF-8 для файлового логгера
                logging.FileHandler("logs/teachai.log", mode="a", encoding="utf-8")
                # Убираем StreamHandler для чистого интерфейса
            ]
        )
    
    def initialize(self):
        """
        Инициализирует все компоненты системы.
        
        Returns:
            bool: True если инициализация прошла успешно, иначе False
        """
        try:
            # Если базовая инициализация уже прошла, пропускаем её
            if self.config_manager and self.state_manager:
                self.logger.info("Продолжение инициализации компонентов...")
            else:
                self.logger.info("Инициализация компонентов...")
            
            # Инициализируем конфигурационный менеджер
            self.logger.info("Создание ConfigManager...")
            self.config_manager = ConfigManager()
            
            # Создаем необходимые директории
            self.logger.info("Создание директорий...")
            self.config_manager.ensure_directories()
            
            # Проверяем наличие .env файла и API ключа
            self.logger.info("Проверка .env файла...")
            if not self.config_manager.check_env_file():
                self.logger.error("Файл .env не найден. Создаем образец .env.sample...")
                self.config_manager.create_sample_env()
                print("\n❌ ОШИБКА: Файл .env не найден!")
                print("📁 Создан файл .env.sample с примером конфигурации.")
                print("🔧 Пожалуйста:")
                print("   1. Скопируйте .env.sample в .env")
                print("   2. Добавьте ваш OpenAI API ключ в файл .env")
                print("   3. Перезапустите систему")
                return False
            
            # Загружаем конфигурацию
            self.logger.info("Загрузка конфигурации...")
            if not self.config_manager.load_config():
                self.logger.error("Ошибка при загрузке конфигурации")
                print("\n❌ ОШИБКА: Не удалось загрузить конфигурацию из .env файла!")
                print("🔧 Проверьте правильность формата файла .env")
                return False
            
            # Получаем API ключ
            self.logger.info("Проверка API ключа...")
            api_key = self.config_manager.get_api_key()
            if not api_key:
                self.logger.error("API ключ OpenAI не найден")
                print("\n❌ ОШИБКА: API ключ OpenAI не найден!")
                print("🔧 Пожалуйста:")
                print("   1. Получите API ключ на https://platform.openai.com/api-keys")
                print("   2. Добавьте его в файл .env как: OPENAI_API_KEY=ваш_ключ")
                print("   3. Перезапустите систему")
                return False
            
            # Маскируем ключ для логов (показываем только начало)
            masked_key = api_key[:9] + "..." if len(api_key) > 12 else "***"
            self.logger.info(f"API ключ получен (начинается с: {masked_key})")
            
            # Инициализируем менеджер состояния
            self.logger.info("Создание StateManager...")
            self.state_manager = StateManager()
            
            # Инициализируем логгер системы
            self.logger.info("Создание Logger...")
            self.system_logger = Logger()
            
            # Инициализируем менеджер загрузки
            self.logger.info("Создание LoadingManager...")
            self.loading_manager = LoadingManager()
            
            # Инициализируем генератор контента
            self.logger.info("Создание ContentGenerator...")
            try:
                self.content_generator = ContentGenerator(api_key, self.loading_manager)
            except Exception as e:
                self.logger.error(f"Не удалось инициализировать ContentGenerator: {str(e)}")
                print(f"\n❌ ОШИБКА: Не удалось подключиться к OpenAI API!")
                print(f"🔧 Возможные причины:")
                print(f"   1. Неверный API ключ")
                print(f"   2. Нет доступа к интернету")
                print(f"   3. Проблемы с OpenAI сервисом")
                print(f"   4. Недостаточно средств на аккаунте OpenAI")
                print(f"\n💡 Техническая информация: {str(e)}")
                return False
            
            # Инициализируем модуль оценивания
            self.logger.info("Создание Assessment...")
            self.assessment = Assessment(self.content_generator, self.system_logger)
            
            # Инициализируем интерфейс
            self.logger.info("Создание UserInterface...")
            self.interface = UserInterface(
                self.state_manager,
                self.content_generator,
                self.assessment,
                self.system_logger
            )
            
            # Инициализируем дашборд для улучшения UX
            self.logger.info("Создание StartupDashboard...")
            if not self.startup_dashboard:
                self.startup_dashboard = StartupDashboard(self.state_manager, self.content_generator)
            else:
                # Обновляем компоненты в существующем дашборде
                self.startup_dashboard.state_manager = self.state_manager
                self.startup_dashboard.content_generator = self.content_generator
            
            # Логируем успешную инициализацию
            self.system_logger.log_activity(
                action_type="system_initialized",
                details={"api_key_valid": bool(api_key)}
            )
            
            self.is_ready = True
            self.logger.info("Все компоненты успешно инициализированы")
            print("\n✅ Система TeachAI успешно инициализирована!")
            print("🚀 Все компоненты готовы к работе")
            return True
            
        except Exception as e:
            self.logger.error(f"Критическая ошибка при инициализации системы: {str(e)}")
            print(f"\n❌ КРИТИЧЕСКАЯ ОШИБКА: {str(e)}")
            print("🔧 Обратитесь к администратору системы")
            return False
    
    def start(self):
        """
        ОПТИМИЗИРОВАНО: Запускает систему TeachAI с мгновенным показом дашборда.
        
        Returns:
            UserInterface объект или соответствующий виджет для отображения
        """
        # Проверяем базовую готовность (конфигурация и состояние)
        if not self._check_basic_readiness():
            if not self._initialize_basic_components():
                return None
        
        self.logger.info("Запуск TeachAI...")
        
        # Показываем дашборд сразу, если это не первый запуск
        if self.state_manager and not self.state_manager.is_first_run():
            self.logger.info("Показываем дашборд статистики...")
            if self.startup_dashboard:
                # Создаем дашборд
                dashboard_widget = self.startup_dashboard.show_dashboard()
                
                # ИСПРАВЛЕНО: Настраиваем обработчик кнопки "Продолжить обучение"
                def display_callback(widget):
                    """Функция для отображения нового интерфейса."""
                    from IPython.display import display, clear_output
                    try:
                        # Очищаем вывод перед показом нового интерфейса
                        clear_output(wait=True)
                        
                        # Проверяем, что виджет валидный
                        if widget is not None:
                            display(widget)
                        else:
                            print("❌ Ошибка: не удалось получить интерфейс для отображения")
                    except Exception as e:
                        print(f"❌ Ошибка при отображении интерфейса: {str(e)}")
                        self.logger.error(f"Ошибка в display_callback: {str(e)}")
                
                # Инициализируем полную систему для обработчика кнопки
                if not self.is_ready:
                    self.logger.info("Инициализируем полную систему для обработчика кнопки...")
                    if not self.initialize():
                        self.logger.error("Не удалось инициализировать полную систему")
                        return dashboard_widget
                
                # Настраиваем обработчик кнопки
                self.startup_dashboard.setup_continue_button_handler(self, display_callback)
                
                return dashboard_widget
        
        # Для первого запуска инициализируем все компоненты
        if not self.is_ready:
            if not self.initialize():
                return None
        
        # Логируем запуск системы
        if self.system_logger:
            self.system_logger.log_activity(
                action_type="system_started",
                details={
                    "is_first_run": self.state_manager.is_first_run() if self.state_manager else True
                }
            )
        
        # Первый запуск - показываем настройку профиля
        if self.interface:
            self.interface.current_state = InterfaceState.INITIAL_SETUP
            return self.interface.show_initial_setup()
    
    def _check_basic_readiness(self):
        """
        Проверяет базовую готовность системы (конфигурация и состояние).
        
        Returns:
            bool: True если базовая готовность обеспечена
        """
        try:
            # Проверяем наличие конфигурационного менеджера
            if not self.config_manager:
                self.config_manager = ConfigManager()
            
            # Создаем необходимые директории
            self.config_manager.ensure_directories()
            
            # Проверяем .env файл
            if not self.config_manager.check_env_file():
                return False
            
            # Загружаем конфигурацию
            if not self.config_manager.load_config():
                return False
            
            # Проверяем API ключ
            api_key = self.config_manager.get_api_key()
            if not api_key:
                return False
            
            # Инициализируем менеджер состояния
            if not self.state_manager:
                self.state_manager = StateManager()
            
            # Инициализируем дашборд, если он еще не создан
            if not self.startup_dashboard:
                self.startup_dashboard = StartupDashboard(self.state_manager, None)
            else:
                # Обновляем state_manager в существующем дашборде
                self.startup_dashboard.state_manager = self.state_manager
            
            return True
            
        except Exception as e:
            self.logger.error(f"Ошибка при проверке базовой готовности: {str(e)}")
            return False
    
    def _initialize_basic_components(self):
        """
        Инициализирует только базовые компоненты для показа дашборда.
        
        Returns:
            bool: True если базовая инициализация прошла успешно
        """
        try:
            self.logger.info("Базовая инициализация компонентов...")
            
            # Инициализируем конфигурационный менеджер
            self.config_manager = ConfigManager()
            self.config_manager.ensure_directories()
            
            if not self.config_manager.check_env_file():
                self.config_manager.create_sample_env()
                print("\n❌ ОШИБКА: Файл .env не найден!")
                print("📁 Создан файл .env.sample с примером конфигурации.")
                print("🔧 Пожалуйста:")
                print("   1. Скопируйте .env.sample в .env")
                print("   2. Добавьте ваш OpenAI API ключ в файл .env")
                print("   3. Перезапустите систему")
                return False
            
            if not self.config_manager.load_config():
                print("\n❌ ОШИБКА: Не удалось загрузить конфигурацию из .env файла!")
                return False
            
            api_key = self.config_manager.get_api_key()
            if not api_key:
                print("\n❌ ОШИБКА: API ключ OpenAI не найден!")
                return False
            
            # Инициализируем менеджер состояния
            self.state_manager = StateManager()
            
            # Инициализируем дашборд, если он еще не создан
            if not self.startup_dashboard:
                self.startup_dashboard = StartupDashboard(self.state_manager, None)
            else:
                # Обновляем state_manager в существующем дашборде
                self.startup_dashboard.state_manager = self.state_manager
            
            return True
            
        except Exception as e:
            self.logger.error(f"Ошибка при базовой инициализации: {str(e)}")
            return False
    
    def _check_current_lesson_status(self):
        """
        НОВОЕ: Проверяет статус текущего урока и определяет нужно ли к нему вернуться.
        
        Returns:
            tuple: (section_id, topic_id, lesson_id) если есть незавершенный урок, иначе None
        """
        try:
            # Проверяем наличие state_manager
            if not self.state_manager:
                self.logger.info("StateManager не инициализирован")
                return None
            
            # Получаем информацию о текущем прогрессе
            learning_progress = self.state_manager.get_learning_progress()
            
            current_section = learning_progress.get("current_section")
            current_topic = learning_progress.get("current_topic") 
            current_lesson = learning_progress.get("current_lesson")
            
            # Если нет информации о текущем уроке - возвращаем первый урок из плана
            if not current_section or not current_topic or not current_lesson:
                self.logger.info("Нет информации о текущем уроке - возвращаем первый урок из плана")
                next_section_id, next_topic_id, next_lesson_id, next_lesson_data = self.state_manager.get_next_lesson()
                
                if next_section_id and next_topic_id and next_lesson_id:
                    self.logger.info(f"Найден первый урок: {next_section_id}:{next_topic_id}:{next_lesson_id}")
                    return (next_section_id, next_topic_id, next_lesson_id)
                else:
                    self.logger.info("Не удалось найти первый урок в плане")
                    return None
            
            # Проверяем завершенность текущего урока
            current_lesson_id = f"{current_section}:{current_topic}:{current_lesson}"
            is_completed = self.state_manager.is_lesson_completed(current_lesson_id)
            
            if is_completed:
                self.logger.info(f"Текущий урок {current_lesson_id} завершен")
                
                # Урок завершен - ищем следующий
                next_section_id, next_topic_id, next_lesson_id, next_lesson_data = self.state_manager.get_next_lesson()
                
                if next_section_id and next_topic_id and next_lesson_id:
                    self.logger.info(f"Найден следующий урок: {next_section_id}:{next_topic_id}:{next_lesson_id}")
                    return (next_section_id, next_topic_id, next_lesson_id)
                else:
                    self.logger.info("Все уроки курса завершены")
                    return None
            else:
                self.logger.info(f"Текущий урок {current_lesson_id} НЕ завершен - возвращаемся к нему")
                return (current_section, current_topic, current_lesson)
                
        except Exception as e:
            self.logger.error(f"Ошибка при проверке статуса текущего урока: {str(e)}")
            return None
    
    def shutdown(self):
        """
        Корректно завершает работу системы.
        
        Returns:
            bool: True если завершение прошло успешно, иначе False
        """
        try:
            self.logger.info("Завершение работы TeachAI...")
            
            # Сохраняем текущее состояние
            if self.state_manager:
                self.state_manager.save_state()
            
            # Логируем завершение работы
            if self.system_logger:
                self.system_logger.log_activity(
                    action_type="system_shutdown",
                    details={}
                )
            
            self.logger.info("Система успешно завершила работу")
            return True
            
        except Exception as e:
            self.logger.error(f"Ошибка при завершении работы системы: {str(e)}")
            return False
    
    def handle_error(self, error, context=None):
        """
        Обрабатывает ошибки, возникающие во время работы системы.
        
        Args:
            error (Exception): Объект ошибки
            context (dict, optional): Контекст, в котором произошла ошибка
            
        Returns:
            str: Сообщение об ошибке для пользователя
        """
        try:
            error_message = str(error)
            
            # Логируем ошибку
            self.logger.error(f"Ошибка: {error_message}")
            
            if self.system_logger:
                self.system_logger.log_activity(
                    action_type="system_error",
                    status="error",
                    error=error_message,
                    details=context or {}
                )
            
            # Формируем сообщение об ошибке для пользователя
            user_message = f"К сожалению, произошла ошибка: {error_message}"
            
            if context:
                user_message += f"\nКонтекст: {context}"
            
            user_message += "\n\nПожалуйста, попробуйте еще раз или обратитесь к администратору."
            
            return user_message
            
        except Exception as e:
            # В случае ошибки в обработчике ошибок, возвращаем базовое сообщение
            return f"Произошла критическая ошибка: {str(e)}\nИсходная ошибка: {str(error)}"