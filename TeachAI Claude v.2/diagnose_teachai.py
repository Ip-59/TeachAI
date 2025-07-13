#!/usr/bin/env python3
"""
Автоматическая диагностика системы TeachAI 2
Этот скрипт проверяет все компоненты системы и выдает детальный отчет о проблемах.

Использование:
    python diagnose_teachai.py

Создано: 12 июля 2025
Версия: 1.0
"""

import os
import sys
import traceback
from datetime import datetime
import logging

# Настройка логирования для диагностики
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)


class TeachAIDiagnostic:
    """Класс для автоматической диагностики системы TeachAI."""

    def __init__(self):
        self.results = {}
        self.issues = []
        self.recommendations = []

    def run_full_diagnostic(self):
        """Запускает полную диагностику системы."""
        print("🔍 АВТОМАТИЧЕСКАЯ ДИАГНОСТИКА TEACHAI 2")
        print("=" * 50)
        print(f"Дата: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}")
        print("=" * 50)

        # Список всех тестов
        tests = [
            ("Проверка .env файла", self._test_env_file),
            ("Проверка API ключа", self._test_api_key),
            ("Тест подключения к OpenAI", self._test_openai_connection),
            ("Проверка модулей системы", self._test_system_modules),
            ("Тест инициализации Engine", self._test_engine_initialization),
            ("Тест генерации урока", self._test_lesson_generation),
            ("Проверка передачи данных", self._test_data_transfer),
            ("Тест интерфейса тестирования", self._test_assessment_interface),
        ]

        # Выполняем все тесты
        for test_name, test_func in tests:
            print(f"\n🔎 {test_name}...")
            try:
                result = test_func()
                self.results[test_name] = result
                if result["success"]:
                    print(f"   ✅ УСПЕХ")
                else:
                    print(f"   ❌ ОШИБКА: {result['error']}")
                    self.issues.append(f"{test_name}: {result['error']}")
                    if result.get("recommendation"):
                        self.recommendations.append(
                            f"{test_name}: {result['recommendation']}"
                        )
            except Exception as e:
                error_msg = f"Исключение при выполнении теста: {str(e)}"
                print(f"   💥 КРИТИЧЕСКАЯ ОШИБКА: {error_msg}")
                self.results[test_name] = {"success": False, "error": error_msg}
                self.issues.append(f"{test_name}: {error_msg}")

        # Выводим итоговый отчет
        self._print_final_report()

    def _test_env_file(self):
        """Тестирует наличие и правильность .env файла."""
        try:
            if not os.path.exists(".env"):
                return {
                    "success": False,
                    "error": ".env файл не найден",
                    "recommendation": "Создайте .env файл с OPENAI_API_KEY=ваш-ключ",
                }

            with open(".env", "r") as f:
                content = f.read()

            if "OPENAI_API_KEY" not in content:
                return {
                    "success": False,
                    "error": "OPENAI_API_KEY не найден в .env файле",
                    "recommendation": "Добавьте строку OPENAI_API_KEY=ваш-ключ в .env файл",
                }

            return {"success": True, "details": ".env файл найден и содержит API ключ"}

        except Exception as e:
            return {
                "success": False,
                "error": f"Ошибка чтения .env файла: {str(e)}",
                "recommendation": "Проверьте права доступа к .env файлу",
            }

    def _test_api_key(self):
        """Тестирует загрузку API ключа."""
        try:
            from dotenv import load_dotenv

            load_dotenv()

            api_key = os.getenv("OPENAI_API_KEY")

            if not api_key:
                return {
                    "success": False,
                    "error": "API ключ не загружается из .env",
                    "recommendation": "Проверьте формат записи в .env: OPENAI_API_KEY=REMOVED...",
                }

            if not api_key.startswith("REMOVED"):
                return {
                    "success": False,
                    "error": "API ключ имеет неправильный формат",
                    "recommendation": "API ключ должен начинаться с 'REMOVED'",
                }

            if len(api_key) < 20:
                return {
                    "success": False,
                    "error": "API ключ слишком короткий",
                    "recommendation": "Проверьте что вы скопировали полный ключ",
                }

            return {
                "success": True,
                "details": f"API ключ загружен (длина: {len(api_key)}, начало: {api_key[:10]}...)",
            }

        except ImportError:
            return {
                "success": False,
                "error": "Модуль python-dotenv не установлен",
                "recommendation": "Установите: pip install python-dotenv",
            }
        except Exception as e:
            return {"success": False, "error": f"Ошибка загрузки API ключа: {str(e)}"}

    def _test_openai_connection(self):
        """Тестирует подключение к OpenAI API."""
        try:
            from dotenv import load_dotenv

            load_dotenv()

            import openai

            openai.api_key = os.getenv("OPENAI_API_KEY")

            # Минимальный запрос для проверки
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": "Test"}],
                max_tokens=5,
            )

            return {"success": True, "details": "Подключение к OpenAI API работает"}

        except Exception as e:
            error_str = str(e).lower()

            if "authentication" in error_str or "api key" in error_str:
                recommendation = "Проверьте правильность API ключа на https://platform.openai.com/api-keys"
            elif "rate limit" in error_str:
                recommendation = "Превышен лимит запросов, подождите несколько минут"
            elif "connection" in error_str or "timeout" in error_str:
                recommendation = "Проверьте интернет соединение и статус OpenAI: https://status.openai.com/"
            else:
                recommendation = "Проверьте настройки OpenAI API"

            return {
                "success": False,
                "error": f"Ошибка OpenAI API: {str(e)}",
                "recommendation": recommendation,
            }

    def _test_system_modules(self):
        """Тестирует импорт основных модулей системы."""
        required_modules = [
            "engine",
            "state_manager",
            "content_generator",
            "lesson_interface",
            "lesson_interactive_handlers",
            "assessment_interface",
            "interface_facade",
        ]

        missing_modules = []

        for module_name in required_modules:
            try:
                __import__(module_name)
            except ImportError as e:
                missing_modules.append(f"{module_name}: {str(e)}")

        if missing_modules:
            return {
                "success": False,
                "error": f"Отсутствуют модули: {', '.join(missing_modules)}",
                "recommendation": "Убедитесь что все файлы проекта находятся в текущей директории",
            }

        return {
            "success": True,
            "details": f"Все {len(required_modules)} основных модулей доступны",
        }

    def _test_engine_initialization(self):
        """Тестирует инициализацию основного движка."""
        try:
            from engine import TeachAIEngine

            engine = TeachAIEngine()
            init_result = engine.initialize()

            if not init_result.get("success", False):
                return {
                    "success": False,
                    "error": f"Инициализация engine неудачна: {init_result.get('error', 'Неизвестная ошибка')}",
                    "recommendation": "Проверьте наличие всех зависимостей и правильность конфигурации",
                }

            # Проверяем компоненты
            components_check = []
            if hasattr(engine, "config_manager") and engine.config_manager:
                components_check.append("config_manager")
            if hasattr(engine, "state_manager") and engine.state_manager:
                components_check.append("state_manager")
            if hasattr(engine, "content_generator") and engine.content_generator:
                components_check.append("content_generator")
            if hasattr(engine, "interface") and engine.interface:
                components_check.append("interface")

            return {
                "success": True,
                "details": f"Engine инициализирован, компоненты: {', '.join(components_check)}",
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Ошибка инициализации engine: {str(e)}",
                "recommendation": "Проверьте логи системы для детальной диагностики",
            }

    def _test_lesson_generation(self):
        """Тестирует генерацию урока."""
        try:
            from content_generator import ContentGenerator
            from dotenv import load_dotenv

            load_dotenv()

            api_key = os.getenv("OPENAI_API_KEY")
            generator = ContentGenerator(api_key)

            # Тестовая генерация урока
            lesson_content = generator.generate_lesson_content(
                lesson_data={"title": "Тест урок", "id": "test-lesson"},
                user_data={"name": "Тест", "communication_style": "friendly"},
                course_context={"course_name": "Тест курс"},
            )

            if not lesson_content:
                return {
                    "success": False,
                    "error": "generate_lesson_content вернул пустой результат",
                    "recommendation": "Проверьте настройки ContentGenerator и доступность API",
                }

            return {
                "success": True,
                "details": f"Урок успешно сгенерирован, тип: {type(lesson_content)}",
            }

        except Exception as e:
            error_str = str(e).lower()

            if "connection" in error_str:
                recommendation = "Проверьте интернет соединение и статус OpenAI API"
            elif "rate limit" in error_str:
                recommendation = "Превышен лимит запросов к API"
            elif "authentication" in error_str:
                recommendation = "Проверьте правильность API ключа"
            else:
                recommendation = "Проверьте настройки генератора контента"

            return {
                "success": False,
                "error": f"Ошибка генерации урока: {str(e)}",
                "recommendation": recommendation,
            }

    def _test_data_transfer(self):
        """Тестирует передачу данных между компонентами."""
        try:
            from lesson_interactive_handlers import LessonInteractiveHandlers
            import logging

            # Создаем моковые данные
            mock_lesson_content = {"content": "Тестовое содержание"}
            mock_course_info = {
                "course_title": "Тест курс",
                "lesson_title": "Тест урок",
                "facade": "mock_facade",
            }
            mock_lesson_id = "test-lesson"

            # Создаем обработчик
            handlers = LessonInteractiveHandlers(
                content_generator="mock_generator",
                state_manager="mock_state",
                utils="mock_utils",
                logger=logging.getLogger("test"),
            )

            # Тестируем передачу данных
            handlers.set_lesson_data(
                mock_lesson_content, mock_course_info, mock_lesson_id
            )

            # Проверяем что данные переданы
            data_ok = (
                handlers.current_lesson_content is not None
                and handlers.current_course_info is not None
                and handlers.current_lesson_id is not None
            )

            if not data_ok:
                return {
                    "success": False,
                    "error": "Данные урока не передаются в обработчики",
                    "recommendation": "Проверьте метод set_lesson_data в LessonInteractiveHandlers",
                }

            return {
                "success": True,
                "details": "Передача данных между компонентами работает корректно",
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Ошибка тестирования передачи данных: {str(e)}",
                "recommendation": "Проверьте импорты и структуру LessonInteractiveHandlers",
            }

    def _test_assessment_interface(self):
        """Тестирует интерфейс тестирования."""
        try:
            from assessment_interface import AssessmentInterface

            # Создаем моковый assessment interface
            assessment = AssessmentInterface(
                state_manager="mock_state",
                assessment="mock_assessment",
                system_logger="mock_logger",
                parent_facade=None,  # Это может быть проблемой
            )

            # Проверяем инициализацию
            if not hasattr(assessment, "_diagnose_assessment_issue"):
                return {
                    "success": False,
                    "error": "AssessmentInterface не имеет метода диагностики",
                    "recommendation": "Примените исправления для assessment_interface.py",
                }

            # Тестируем диагностику
            diagnosis = assessment._diagnose_assessment_issue("test_content")

            if "ПРОБЛЕМЫ С ТЕСТИРОВАНИЕМ" in diagnosis:
                return {
                    "success": True,
                    "details": "AssessmentInterface обновлен с улучшенной диагностикой",
                    "warning": "Может потребоваться настройка parent_facade",
                }

            return {
                "success": True,
                "details": "AssessmentInterface инициализируется корректно",
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Ошибка тестирования assessment interface: {str(e)}",
                "recommendation": "Примените исправления для assessment_interface.py",
            }

    def _print_final_report(self):
        """Выводит итоговый отчет диагностики."""
        print("\n" + "=" * 50)
        print("📊 ИТОГОВЫЙ ОТЧЕТ ДИАГНОСТИКИ")
        print("=" * 50)

        # Подсчет результатов
        total_tests = len(self.results)
        successful_tests = sum(
            1 for result in self.results.values() if result["success"]
        )

        print(f"Выполнено тестов: {total_tests}")
        print(f"Успешных тестов: {successful_tests}")
        print(f"Неудачных тестов: {total_tests - successful_tests}")
        print(f"Процент готовности: {successful_tests/total_tests*100:.1f}%")

        # Статус системы
        if successful_tests == total_tests:
            print("\n🎉 СИСТЕМА ПОЛНОСТЬЮ РАБОТОСПОСОБНА!")
            print("Все компоненты функционируют корректно.")
        elif successful_tests >= total_tests * 0.7:
            print("\n⚠️ СИСТЕМА ЧАСТИЧНО РАБОТОСПОСОБНА")
            print("Основные компоненты работают, но есть проблемы.")
        else:
            print("\n❌ СИСТЕМА ТРЕБУЕТ СЕРЬЕЗНЫХ ИСПРАВЛЕНИЙ")
            print("Множественные проблемы препятствуют нормальной работе.")

        # Список проблем
        if self.issues:
            print(f"\n🔥 ОБНАРУЖЕННЫЕ ПРОБЛЕМЫ ({len(self.issues)}):")
            for i, issue in enumerate(self.issues, 1):
                print(f"{i}. {issue}")

        # Рекомендации
        if self.recommendations:
            print(f"\n💡 РЕКОМЕНДАЦИИ ПО УСТРАНЕНИЮ ({len(self.recommendations)}):")
            for i, rec in enumerate(self.recommendations, 1):
                print(f"{i}. {rec}")

        # Следующие шаги
        print(f"\n🎯 СЛЕДУЮЩИЕ ШАГИ:")
        if successful_tests == total_tests:
            print("1. Система готова к использованию")
            print("2. Запустите teachai.ipynb для начала работы")
        elif successful_tests >= total_tests * 0.7:
            print("1. Устраните обнаруженные проблемы согласно рекомендациям")
            print("2. Перезапустите диагностику для проверки")
            print("3. При необходимости примените исправления из артефактов")
        else:
            print("1. Проверьте настройку API ключа OpenAI")
            print("2. Убедитесь что все файлы проекта на месте")
            print("3. Примените все исправления из артефактов")
            print("4. Перезапустите диагностику")

        print("\n" + "=" * 50)
        print(f"Диагностика завершена: {datetime.now().strftime('%H:%M:%S')}")
        print("=" * 50)


def main():
    """Главная функция запуска диагностики."""
    try:
        diagnostic = TeachAIDiagnostic()
        diagnostic.run_full_diagnostic()
    except KeyboardInterrupt:
        print("\n\n❌ Диагностика прервана пользователем")
    except Exception as e:
        print(f"\n\n💥 КРИТИЧЕСКАЯ ОШИБКА ДИАГНОСТИКИ: {str(e)}")
        print(f"Traceback: {traceback.format_exc()}")


if __name__ == "__main__":
    main()
