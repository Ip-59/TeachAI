# Диагностическая проверка модулей системы
print("🔍 ДИАГНОСТИКА ПРОБЛЕМЫ ИНИЦИАЛИЗАЦИИ ИНТЕРФЕЙСОВ")
print("=" * 60)

# Проверяем импорт базовых модулей
try:
    print("1. Проверка импорта базовых модулей...")
    import logging
    from interface_utils import InterfaceState
    import ipywidgets as widgets

    print("✅ Базовые модули импортированы успешно")
except Exception as e:
    print(f"❌ Ошибка импорта базовых модулей: {e}")
    exit()

# Проверяем импорт lesson_interface
try:
    print("\n2. Проверка импорта lesson_interface...")
    from lesson_interface import LessonInterface

    print("✅ LessonInterface импортирован успешно")
except Exception as e:
    print(f"❌ Ошибка импорта LessonInterface: {e}")
    print("📋 Детали ошибки:")
    import traceback

    traceback.print_exc()

# Проверяем импорт assessment_interface
try:
    print("\n3. Проверка импорта assessment_interface...")
    from assessment_interface import AssessmentInterface

    print("✅ AssessmentInterface импортирован успешно")
except Exception as e:
    print(f"❌ Ошибка импорта AssessmentInterface: {e}")
    print("📋 Детали ошибки:")
    import traceback

    traceback.print_exc()

# Проверяем инициализацию interface_facade
try:
    print("\n4. Проверка создания InterfaceFacade...")
    from interface_facade import InterfaceFacade

    # Создаем заглушки для параметров
    class MockStateManager:
        pass

    class MockContentGenerator:
        pass

    class MockAssessment:
        pass

    class MockSystemLogger:
        def log_lesson(self, **kwargs):
            pass

    state_manager = MockStateManager()
    content_generator = MockContentGenerator()
    assessment = MockAssessment()
    system_logger = MockSystemLogger()

    # Пытаемся создать фасад
    facade = InterfaceFacade(
        state_manager, content_generator, assessment, system_logger
    )

    print(f"✅ InterfaceFacade создан: {type(facade)}")
    print(
        f"📊 lesson_interface: {type(facade.lesson_interface) if facade.lesson_interface else 'None'}"
    )
    print(
        f"📊 assessment_interface: {type(facade.assessment_interface) if facade.assessment_interface else 'None'}"
    )

except Exception as e:
    print(f"❌ Ошибка создания InterfaceFacade: {e}")
    print("📋 Детали ошибки:")
    import traceback

    traceback.print_exc()

print("\n" + "=" * 60)
print("🔍 ДИАГНОСТИКА ЗАВЕРШЕНА")
print("\nЕсли видите ошибки выше, то проблема в соответствующем модуле.")
print("Наиболее вероятно - синтаксическая ошибка в assessment_interface.py")
