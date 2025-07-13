#!/usr/bin/env python3
"""
Полный тест функциональности контрольных заданий.
Проверяет генерацию, отображение и обработку заданий.
"""

import os
import sys
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

# Добавляем текущую директорию в путь
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import logging
from lesson_interface import LessonInterface
from config import ConfigManager
from control_tasks_generator import ControlTasksGenerator


def test_control_tasks_full():
    """Тестирует полную функциональность контрольных заданий."""

    print("🧪 Полный тест функциональности контрольных заданий")
    print("=" * 70)

    try:
        # Инициализируем компоненты
        config = ConfigManager()
        config.load_config()
        api_key = config.get_api_key()

        if not api_key:
            print("❌ API ключ не найден")
            return False

        from state_manager import StateManager
        from content_generator import ContentGenerator

        state_manager = StateManager()
        content_generator = ContentGenerator(api_key)
        system_logger = logging.getLogger(__name__)

        lesson_interface = LessonInterface(
            state_manager, content_generator, system_logger
        )

        # Создаем кнопки навигации
        lesson_interface._create_enhanced_navigation_buttons(
            "section1", "topic1", "lesson1"
        )

        print("✅ Компоненты инициализированы")

        # Тестируем генератор контрольных заданий
        print("\n🔧 Тестирование генератора контрольных заданий...")

        tasks_generator = ControlTasksGenerator(api_key)

        # Тестовые данные урока
        test_lesson_data = {
            "title": "Операторы сравнения в Python",
            "description": "Изучение операторов сравнения и их использования",
        }

        test_lesson_content = """
        В Python есть несколько операторов сравнения:
        - == (равно)
        - != (не равно)
        - > (больше)
        - < (меньше)
        - >= (больше или равно)
        - <= (меньше или равно)

        Примеры использования:
        x = 5
        y = 10
        print(x < y)  # True
        print(x == y)  # False
        """

        # Генерируем тестовое задание
        task_data = tasks_generator.generate_control_task(
            lesson_data=test_lesson_data,
            lesson_content=test_lesson_content,
            communication_style="friendly",
        )

        print(f"✅ Задание сгенерировано: {task_data.get('title', 'Нет названия')}")
        print(f"   - Описание: {task_data.get('description', 'Нет описания')[:50]}...")
        print(f"   - Код задания: {task_data.get('task_code', 'Нет кода')[:30]}...")
        print(
            f"   - Ожидаемый результат: {task_data.get('expected_output', 'Нет результата')}"
        )

        # Тестируем валидацию выполнения
        print("\n🔍 Тестирование валидации выполнения...")

        test_user_code = "print('Hello, World!')"
        validation_result = tasks_generator.validate_task_execution(
            test_user_code, "Hello, World!"
        )

        print(f"✅ Валидация работает: {validation_result['is_correct']}")

        # Тестируем интерфейс контрольных заданий
        print("\n🖥️ Тестирование интерфейса контрольных заданий...")

        if hasattr(lesson_interface, "control_tasks_interface"):
            print("✅ ControlTasksInterface создан")

            # Проверяем, что интерфейс может создать задание
            try:
                task_interface = (
                    lesson_interface.control_tasks_interface.show_control_task(
                        lesson_data=test_lesson_data, lesson_content=test_lesson_content
                    )
                )
                print("✅ Интерфейс может создать задание")
            except Exception as e:
                print(f"❌ Ошибка при создании интерфейса задания: {str(e)}")
                return False
        else:
            print("❌ ControlTasksInterface не найден")
            return False

        # Тестируем сохранение результатов
        print("\n💾 Тестирование сохранения результатов...")

        try:
            lesson_interface.state_manager.save_control_task_result(
                "test_lesson_1", "Тестовое задание", True
            )
            print("✅ Сохранение результатов работает")
        except Exception as e:
            print(f"❌ Ошибка при сохранении результатов: {str(e)}")
            return False

        print("\n✅ Все компоненты контрольных заданий работают корректно!")
        return True

    except Exception as e:
        print(f"❌ Ошибка при тестировании: {str(e)}")
        return False


if __name__ == "__main__":
    success = test_control_tasks_full()
    if success:
        print("\n🎉 Полный тест пройден успешно!")
    else:
        print("\n💥 Полный тест не пройден!")
