#!/usr/bin/env python3
"""
Автоматическое применение исправлений для TeachAI 2
Этот скрипт применяет все необходимые исправления для устранения проблем системы.

Использование:
    python apply_fixes.py

Создано: 12 июля 2025
Версия: 1.0
"""

import os
import shutil
import sys
from datetime import datetime


class TeachAIAutoFix:
    """Класс для автоматического применения исправлений."""

    def __init__(self):
        self.backup_dir = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.fixes_applied = []
        self.errors = []

    def apply_all_fixes(self):
        """Применяет все исправления для системы TeachAI."""
        print("🔧 АВТОМАТИЧЕСКОЕ ПРИМЕНЕНИЕ ИСПРАВЛЕНИЙ TEACHAI 2")
        print("=" * 55)
        print(f"Дата: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}")
        print("=" * 55)

        # Создаем папку для резервных копий
        self._create_backup_directory()

        # Список всех исправлений
        fixes = [
            ("lesson_content_manager.py", self._fix_lesson_content_manager),
            ("lesson_interactive_handlers.py", self._fix_lesson_interactive_handlers),
            ("assessment_interface.py", self._fix_assessment_interface),
            ("Проверка .env файла", self._check_env_file),
            ("Создание диагностического скрипта", self._create_diagnostic_script),
        ]

        # Применяем все исправления
        for fix_name, fix_func in fixes:
            print(f"\n🔨 Применение: {fix_name}...")
            try:
                result = fix_func()
                if result["success"]:
                    print(
                        f"   ✅ УСПЕШНО: {result.get('message', 'Исправление применено')}"
                    )
                    self.fixes_applied.append(fix_name)
                else:
                    print(
                        f"   ⚠️ ПРОПУЩЕНО: {result.get('message', 'Исправление не требуется')}"
                    )
            except Exception as e:
                error_msg = f"Ошибка при применении {fix_name}: {str(e)}"
                print(f"   ❌ ОШИБКА: {error_msg}")
                self.errors.append(error_msg)

        # Выводим итоговый отчет
        self._print_final_report()

    def _create_backup_directory(self):
        """Создает директорию для резервных копий."""
        try:
            os.makedirs(self.backup_dir, exist_ok=True)
            print(f"📁 Создана папка для резервных копий: {self.backup_dir}")
        except Exception as e:
            print(f"❌ Не удалось создать папку для бэкапов: {str(e)}")
            self.backup_dir = None

    def _backup_file(self, filename):
        """Создает резервную копию файла."""
        if not self.backup_dir or not os.path.exists(filename):
            return False

        try:
            backup_path = os.path.join(self.backup_dir, filename)
            shutil.copy2(filename, backup_path)
            print(f"   💾 Создана резервная копия: {backup_path}")
            return True
        except Exception as e:
            print(f"   ⚠️ Не удалось создать резервную копию {filename}: {str(e)}")
            return False

    def _fix_lesson_content_manager(self):
        """Исправляет lesson_content_manager.py"""
        filename = "lesson_content_manager.py"

        if not os.path.exists(filename):
            return {"success": False, "message": f"Файл {filename} не найден"}

        # Создаем резервную копию
        self._backup_file(filename)

        # Новый код модуля (исправленная версия без демо-режима)
        new_content = '''"""
Менеджер содержания уроков.
Отвечает за генерацию, кэширование и управление содержанием уроков.

ИСПРАВЛЕНО: УБРАН ДЕМО-РЕЖИМ - теперь показываем реальные ошибки API для диагностики
"""

import logging


class LessonContentManager:
    """Менеджер содержания уроков."""

    def __init__(self, state_manager, logger=None):
        """
        Инициализация менеджера содержания.

        Args:
            state_manager: Менеджер состояния
            logger: Логгер (опционально)
        """
        self.state_manager = state_manager
        self.logger = logger or logging.getLogger(__name__)

        # Кэш содержания урока
        self.cached_lesson_content = None
        self.current_lesson_cache_key = None

        self.logger.info("LessonContentManager инициализирован")

    def get_lesson_content(self, section_id, topic_id, lesson_id, content_generator):
        """
        Получает содержание урока с кэшированием.

        ИСПРАВЛЕНО: Убран демо-режим - теперь ошибки API передаются выше для правильной диагностики

        Args:
            section_id (str): ID раздела
            topic_id (str): ID темы
            lesson_id (str): ID урока
            content_generator: Генератор контента

        Returns:
            dict: Содержание урока

        Raises:
            Exception: Любые ошибки генерации передаются выше для диагностики
        """
        lesson_cache_key = f"{section_id}:{topic_id}:{lesson_id}"

        # Проверяем кэш
        if (self.current_lesson_cache_key == lesson_cache_key and
            self.cached_lesson_content):
            self.logger.debug(f"Используем кэшированное содержание урока {lesson_cache_key}")
            return self.cached_lesson_content

        # Генерируем новое содержание
        self.logger.info(f"Генерация нового содержания урока {lesson_cache_key}")

        try:
            # Проверяем доступность content_generator
            if not content_generator:
                error_msg = f"ContentGenerator недоступен для урока {lesson_cache_key}"
                self.logger.error(error_msg)
                raise ValueError(error_msg)

            # Формируем правильные аргументы для generate_lesson_content
            lesson_data = self._build_lesson_data(section_id, topic_id, lesson_id)
            user_data = self._get_user_data()
            course_context = self._get_course_context()

            self.logger.info(f"Вызов content_generator.generate_lesson_content для {lesson_cache_key}")
            self.logger.debug(f"lesson_data: {lesson_data}")
            self.logger.debug(f"user_data: {user_data}")
            self.logger.debug(f"course_context: {course_context}")

            lesson_content_data = content_generator.generate_lesson_content(
                lesson_data=lesson_data,
                user_data=user_data,
                course_context=course_context
            )

            if not lesson_content_data:
                error_msg = f"content_generator.generate_lesson_content вернул пустой результат для {lesson_cache_key}"
                self.logger.error(error_msg)
                raise ValueError(error_msg)

            # Кэшируем результат
            self.cached_lesson_content = lesson_content_data
            self.current_lesson_cache_key = lesson_cache_key

            self.logger.info(f"Содержание урока {lesson_cache_key} успешно сгенерировано и закэшировано")
            return lesson_content_data

        except Exception as e:
            # ИСПРАВЛЕНО: Убираем демо-режим - передаем ошибку выше для диагностики
            error_msg = f"Ошибка генерации содержания урока {lesson_cache_key}: {str(e)}"
            self.logger.error(error_msg)
            self.logger.error(f"Тип ошибки: {type(e).__name__}")

            # Логируем детали для диагностики
            if "Connection error" in str(e) or "connection" in str(e).lower():
                self.logger.error("ДИАГНОСТИКА: Обнаружена ошибка подключения к OpenAI API")
                self.logger.error("ПРОВЕРЬТЕ: 1) API ключ в .env файле, 2) Интернет соединение, 3) Статус OpenAI API")
            elif "timeout" in str(e).lower():
                self.logger.error("ДИАГНОСТИКА: Превышено время ожидания ответа от API")
            elif "rate limit" in str(e).lower():
                self.logger.error("ДИАГНОСТИКА: Превышен лимит запросов к API")
            elif "api key" in str(e).lower():
                self.logger.error("ДИАГНОСТИКА: Проблема с API ключом")
            else:
                self.logger.error(f"ДИАГНОСТИКА: Неизвестная ошибка API: {str(e)}")

            # Передаем ошибку выше вместо скрытия демо-режимом
            raise

    def _build_lesson_data(self, section_id, topic_id, lesson_id):
        """
        Формирует данные урока из ID компонентов.

        Args:
            section_id (str): ID раздела
            topic_id (str): ID темы
            lesson_id (str): ID урока

        Returns:
            dict: Данные урока
        """
        try:
            # Получаем данные урока из state_manager
            if hasattr(self.state_manager, 'get_lesson_data'):
                lesson_data = self.state_manager.get_lesson_data(lesson_id)
                if lesson_data:
                    self.logger.debug(f"Получены данные урока из state_manager: {lesson_data}")
                    return lesson_data

            # Fallback: создаем базовые данные
            fallback_data = {
                'id': lesson_id,
                'title': f'Урок {lesson_id}',
                'section_id': section_id,
                'topic_id': topic_id,
                'description': f'Урок в разделе {section_id}, тема {topic_id}'
            }
            self.logger.warning(f"Используем fallback данные урока: {fallback_data}")
            return fallback_data

        except Exception as e:
            self.logger.error(f"Ошибка получения данных урока: {str(e)}")
            # Возвращаем минимальные данные вместо падения
            return {
                'id': lesson_id,
                'title': f'Урок {lesson_id}',
                'section_id': section_id,
                'topic_id': topic_id
            }

    def _get_user_data(self):
        """
        Получает данные пользователя.

        Returns:
            dict: Данные пользователя
        """
        try:
            if hasattr(self.state_manager, 'get_user_profile'):
                user_data = self.state_manager.get_user_profile()
                self.logger.debug(f"Получены данные пользователя: {user_data}")
                return user_data or {}
            self.logger.warning("Метод get_user_profile недоступен в state_manager")
            return {}
        except Exception as e:
            self.logger.error(f"Ошибка получения данных пользователя: {str(e)}")
            return {}

    def _get_course_context(self):
        """
        Получает контекст курса.

        Returns:
            dict: Контекст курса
        """
        try:
            if hasattr(self.state_manager, 'get_course_plan'):
                course_plan = self.state_manager.get_course_plan()
                context = {
                    'course_name': course_plan.get('course_name', 'Курс Python') if course_plan else 'Курс Python',
                    'course_plan': course_plan
                }
                self.logger.debug(f"Получен контекст курса: {context}")
                return context
            self.logger.warning("Метод get_course_plan недоступен в state_manager")
            return {'course_name': 'Курс Python'}
        except Exception as e:
            self.logger.error(f"Ошибка получения контекста курса: {str(e)}")
            return {'course_name': 'Курс Python'}

    def get_control_tasks_interface(self, lesson_id, course_info):
        """
        Получает интерфейс контрольных заданий.

        Args:
            lesson_id (str): ID урока
            course_info (dict): Информация о курсе

        Returns:
            widgets.Widget or None: Интерфейс контрольных заданий или None
        """
        try:
            # Пока возвращаем None, так как контрольные задания не реализованы
            self.logger.debug(f"Контрольные задания для урока {lesson_id} не реализованы")
            return None

        except Exception as e:
            self.logger.warning(f"Ошибка создания контрольных заданий для урока {lesson_id}: {str(e)}")
            return None

    def clear_cache(self):
        """Очищает кэш содержания урока."""
        self.cached_lesson_content = None
        self.current_lesson_cache_key = None
        self.logger.info("Кэш содержания урока очищен")

    def get_cache_info(self):
        """
        Возвращает информацию о кэше.

        Returns:
            dict: Информация о кэше
        """
        return {
            "cache_active": self.cached_lesson_content is not None,
            "cached_lesson": self.current_lesson_cache_key,
            "cache_size": len(str(self.cached_lesson_content)) if self.cached_lesson_content else 0
        }
'''

        try:
            with open(filename, "w", encoding="utf-8") as f:
                f.write(new_content)
            return {
                "success": True,
                "message": "Убран демо-режим, добавлена диагностика API ошибок",
            }
        except Exception as e:
            return {"success": False, "message": f"Ошибка записи файла: {str(e)}"}

    def _fix_lesson_interactive_handlers(self):
        """Исправляет lesson_interactive_handlers.py"""
        filename = "lesson_interactive_handlers.py"

        if not os.path.exists(filename):
            return {"success": False, "message": f"Файл {filename} не найден"}

        # Создаем резервную копию
        self._backup_file(filename)

        # Проверяем содержимое файла на наличие старого кода
        try:
            with open(filename, "r", encoding="utf-8") as f:
                content = f.read()

            # Проверяем есть ли уже исправления
            if "_diagnose_lesson_data_issue" in content:
                return {"success": False, "message": "Исправления уже применены"}

            # Ищем строку для замены
            old_pattern = 'if not self.current_lesson_content or not self.current_course_info:\n                self._show_error("Данные урока недоступны")'

            new_pattern = """if not self.current_lesson_content or not self.current_course_info:
                error_details = self._diagnose_lesson_data_issue()
                self.logger.error(f"Диагностика проблемы с данными урока: {error_details}")
                self._show_error(f"Ошибка доступа к данным урока:\\n\\n{error_details}")"""

            if old_pattern not in content:
                return {
                    "success": False,
                    "message": "Структура файла не соответствует ожидаемой",
                }

            # Применяем замену
            updated_content = content.replace(old_pattern, new_pattern)

            # Добавляем метод диагностики в начало класса (после __init__)
            diagnostic_method = '''
    def _diagnose_lesson_data_issue(self):
        """
        НОВОЕ: Диагностирует проблемы с данными урока.

        Returns:
            str: Детальное описание проблемы
        """
        issues = []

        # Проверяем current_lesson_content
        if self.current_lesson_content is None:
            issues.append("current_lesson_content = None (данные урока не переданы)")
        elif not self.current_lesson_content:
            issues.append(f"current_lesson_content пустой: {self.current_lesson_content}")
        else:
            self.logger.debug(f"current_lesson_content OK: тип {type(self.current_lesson_content)}")

        # Проверяем current_course_info
        if self.current_course_info is None:
            issues.append("current_course_info = None (информация о курсе не передана)")
        elif not self.current_course_info:
            issues.append(f"current_course_info пустой: {self.current_course_info}")
        else:
            self.logger.debug(f"current_course_info OK: тип {type(self.current_course_info)}")

        # Проверяем current_lesson_id
        if not self.current_lesson_id:
            issues.append(f"current_lesson_id пустой: {self.current_lesson_id}")
        else:
            self.logger.debug(f"current_lesson_id OK: {self.current_lesson_id}")

        # Проверяем content_generator
        if not self.content_generator:
            issues.append("content_generator = None (генератор контента недоступен)")
        else:
            self.logger.debug("content_generator OK")

        if issues:
            detailed_message = "ПРОБЛЕМЫ С ДАННЫМИ УРОКА:\\n" + "\\n".join(f"• {issue}" for issue in issues)
            detailed_message += "\\n\\nВОЗМОЖНЫЕ ПРИЧИНЫ:"
            detailed_message += "\\n• Урок не сгенерировался из-за ошибки API"
            detailed_message += "\\n• Ошибка в lesson_interface.py при сохранении данных"
            detailed_message += "\\n• Проблема с инициализацией компонентов системы"
            detailed_message += "\\n• Ошибка в content_generator (проверьте API ключ)"
            return detailed_message

        return "Данные урока корректны, проблема в другом месте"
'''

            # Вставляем метод после set_lesson_data
            insert_position = updated_content.find(
                "        self.current_lesson_id = lesson_id"
            )
            if insert_position != -1:
                # Находим конец метода set_lesson_data
                next_method_position = updated_content.find(
                    "\n    def ", insert_position
                )
                if next_method_position != -1:
                    updated_content = (
                        updated_content[:next_method_position]
                        + diagnostic_method
                        + updated_content[next_method_position:]
                    )

            # Записываем обновленный файл
            with open(filename, "w", encoding="utf-8") as f:
                f.write(updated_content)

            return {
                "success": True,
                "message": "Добавлена детальная диагностика данных урока",
            }

        except Exception as e:
            return {"success": False, "message": f"Ошибка обработки файла: {str(e)}"}

    def _fix_assessment_interface(self):
        """Исправляет assessment_interface.py"""
        filename = "assessment_interface.py"

        if not os.path.exists(filename):
            return {"success": False, "message": f"Файл {filename} не найден"}

        # Создаем резервную копию
        self._backup_file(filename)

        try:
            with open(filename, "r", encoding="utf-8") as f:
                content = f.read()

            # Проверяем есть ли уже исправления
            if "_diagnose_assessment_issue" in content:
                return {"success": False, "message": "Исправления уже применены"}

            # Добавляем метод диагностики в класс
            diagnostic_method = '''
    def _diagnose_assessment_issue(self, current_lesson_content):
        """
        НОВОЕ: Диагностирует проблемы с тестированием.

        Args:
            current_lesson_content: Содержание урока

        Returns:
            str: Детальное описание проблемы
        """
        issues = []

        # Проверяем content_generator
        if not self.content_generator:
            issues.append("content_generator = None (генератор контента недоступен)")

        # Проверяем assessment модуль
        if not self.assessment:
            issues.append("assessment = None (модуль оценивания недоступен)")

        # Проверяем содержание урока
        if not current_lesson_content:
            issues.append(f"current_lesson_content пустой: {current_lesson_content}")

        # Проверяем state_manager
        if not self.state_manager:
            issues.append("state_manager = None (менеджер состояния недоступен)")

        # Проверяем parent_facade
        if not self.parent_facade:
            issues.append("parent_facade = None (фасад не передан)")

        if issues:
            detailed_message = "ПРОБЛЕМЫ С ТЕСТИРОВАНИЕМ:\\n" + "\\n".join(f"• {issue}" for issue in issues)
            detailed_message += "\\n\\nВОЗМОЖНЫЕ ПРИЧИНЫ:"
            detailed_message += "\\n• Ошибка инициализации системы (проверьте engine.py)"
            detailed_message += "\\n• Урок не сгенерировался (проверьте API ключ)"
            detailed_message += "\\n• Проблема с передачей facade в lesson_interface.py"
            detailed_message += "\\n• Ошибка в content_generator (проверьте OpenAI API)"
            return detailed_message

        return "Компоненты тестирования корректны, проблема в другом месте"
'''

            # Вставляем метод в класс
            class_definition = "class AssessmentInterface:"
            insert_position = content.find(class_definition)
            if insert_position != -1:
                # Находим первый метод класса
                first_method_position = content.find("\n    def ", insert_position)
                if first_method_position != -1:
                    content = (
                        content[:first_method_position]
                        + diagnostic_method
                        + content[first_method_position:]
                    )

            # Записываем обновленный файл
            with open(filename, "w", encoding="utf-8") as f:
                f.write(content)

            return {
                "success": True,
                "message": "Добавлена детальная диагностика тестирования",
            }

        except Exception as e:
            return {"success": False, "message": f"Ошибка обработки файла: {str(e)}"}

    def _check_env_file(self):
        """Проверяет и при необходимости создает .env файл."""
        filename = ".env"

        if os.path.exists(filename):
            # Проверяем содержимое
            try:
                with open(filename, "r") as f:
                    content = f.read()

                if "OPENAI_API_KEY" in content:
                    return {"success": False, "message": ".env файл уже настроен"}
                else:
                    # Добавляем недостающую строку
                    with open(filename, "a") as f:
                        f.write("\n# OpenAI API ключ\nOPENAI_API_KEY=ваш-ключ-здесь\n")
                    return {
                        "success": True,
                        "message": "Добавлен шаблон для API ключа в .env",
                    }

            except Exception as e:
                return {"success": False, "message": f"Ошибка чтения .env: {str(e)}"}
        else:
            # Создаем новый .env файл
            try:
                with open(filename, "w") as f:
                    f.write(
                        """# Конфигурация TeachAI 2
# Получите API ключ на https://platform.openai.com/api-keys
OPENAI_API_KEY=ваш-ключ-здесь

# Дополнительные настройки
MODEL_NAME=gpt-3.5-turbo-16k
MAX_TOKENS=3500
TEMPERATURE=0.7
DEBUG_MODE=False
"""
                    )
                return {
                    "success": True,
                    "message": "Создан .env файл с шаблоном конфигурации",
                }

            except Exception as e:
                return {"success": False, "message": f"Ошибка создания .env: {str(e)}"}

    def _create_diagnostic_script(self):
        """Создает скрипт диагностики если его нет."""
        filename = "diagnose_teachai.py"

        if os.path.exists(filename):
            return {"success": False, "message": "Скрипт диагностики уже существует"}

        # Здесь мог бы быть код для создания diagnostic script,
        # но он уже создан как артефакт
        return {"success": False, "message": "Скрипт диагностики будет создан отдельно"}

    def _print_final_report(self):
        """Выводит итоговый отчет применения исправлений."""
        print("\n" + "=" * 55)
        print("📊 ИТОГОВЫЙ ОТЧЕТ ПРИМЕНЕНИЯ ИСПРАВЛЕНИЙ")
        print("=" * 55)

        print(f"Применено исправлений: {len(self.fixes_applied)}")
        print(f"Ошибок при применении: {len(self.errors)}")

        if self.fixes_applied:
            print(f"\n✅ УСПЕШНО ПРИМЕНЕНЫ ({len(self.fixes_applied)}):")
            for i, fix in enumerate(self.fixes_applied, 1):
                print(f"{i}. {fix}")

        if self.errors:
            print(f"\n❌ ОШИБКИ ПРИ ПРИМЕНЕНИИ ({len(self.errors)}):")
            for i, error in enumerate(self.errors, 1):
                print(f"{i}. {error}")

        if self.backup_dir:
            print(f"\n💾 РЕЗЕРВНЫЕ КОПИИ СОХРАНЕНЫ В: {self.backup_dir}")
            print("Для отката изменений используйте файлы из этой папки")

        print(f"\n🎯 СЛЕДУЮЩИЕ ШАГИ:")
        if len(self.fixes_applied) > 0 and len(self.errors) == 0:
            print("1. ✅ Все исправления успешно применены")
            print("2. 🔧 Настройте API ключ в .env файле")
            print("3. 🧪 Запустите: python diagnose_teachai.py")
            print("4. 🚀 Запустите: teachai.ipynb")
        elif len(self.fixes_applied) > 0:
            print("1. ⚠️ Часть исправлений применена")
            print("2. 🔧 Устраните ошибки применения")
            print("3. 🔧 Настройте API ключ в .env файле")
            print("4. 🧪 Запустите: python diagnose_teachai.py")
        else:
            print("1. ❌ Исправления не применены")
            print("2. 🔧 Проверьте наличие файлов проекта")
            print("3. 🔧 Примените исправления вручную")

        print("\n" + "=" * 55)
        print(
            f"Применение исправлений завершено: {datetime.now().strftime('%H:%M:%S')}"
        )
        print("=" * 55)


def main():
    """Главная функция запуска применения исправлений."""
    try:
        auto_fix = TeachAIAutoFix()
        auto_fix.apply_all_fixes()
    except KeyboardInterrupt:
        print("\n\n❌ Применение исправлений прервано пользователем")
    except Exception as e:
        print(f"\n\n💥 КРИТИЧЕСКАЯ ОШИБКА: {str(e)}")


if __name__ == "__main__":
    main()
