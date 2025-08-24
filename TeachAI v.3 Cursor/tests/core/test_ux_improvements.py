"""
Тест для проверки новых компонентов UX - дашборда и индикаторов загрузки.
Проверяет корректность работы StartupDashboard и LoadingManager.
"""

import sys
import os
import unittest
from unittest.mock import Mock, patch
import json

# Добавляем корневую директорию в путь для импорта
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from startup_dashboard import StartupDashboard
from loading_indicators import LoadingManager, LoadingIndicator, OpenAIAPILoadingIndicator


class TestStartupDashboard(unittest.TestCase):
    """Тесты для StartupDashboard."""
    
    def setUp(self):
        """Настройка тестового окружения."""
        # Создаем мок state_manager
        self.mock_state_manager = Mock()
        
        # Настраиваем мок данные состояния
        self.mock_state = {
            "user": {
                "name": "Тестовый пользователь",
                "total_study_hours": 10,
                "lesson_duration_minutes": 30,
                "communication_style": "friendly"
            },
            "learning": {
                "current_course": "python_basics",
                "current_section": "section1",
                "current_topic": "topic1",
                "current_lesson": "lesson1",
                "completed_lessons": ["section1:topic1:lesson1", "section1:topic1:lesson2"],
                "lesson_scores": {"section1:topic1:lesson1": 85, "section1:topic1:lesson2": 90},
                "lesson_attempts": {"section1:topic1:lesson1": [{"score": 85, "timestamp": "2024-07-13T10:00:00"}], "section1:topic1:lesson2": [{"score": 90, "timestamp": "2024-07-13T11:00:00"}]},
                "lesson_completion_status": {"section1:topic1:lesson1": True, "section1:topic1:lesson2": True},
                "questions_count": {"section1:topic1:lesson1": 3, "section1:topic1:lesson2": 2},
                "average_score": 87.5,
                "total_assessments": 2,
                "total_score": 175,
                "course_progress_percent": 40.0
            },
            "course_plan": {
                "id": "python_basics",
                "title": "Основы Python",
                "description": "Курс по основам программирования на Python",
                "total_duration_minutes": 300,
                "sections": [
                    {
                        "id": "section1",
                        "title": "Введение в Python",
                        "topics": [
                            {
                                "id": "topic1",
                                "title": "Основы синтаксиса",
                                "lessons": [
                                    {"id": "lesson1", "title": "Переменные и типы данных"},
                                    {"id": "lesson2", "title": "Операторы и выражения"}
                                ]
                            }
                        ]
                    }
                ]
            },
            "system": {
                "first_run": False,
                "last_access": "2024-07-13T12:00:00",
                "version": "1.0.0"
            }
        }
        
        # Настраиваем методы мока
        self.mock_state_manager.state = self.mock_state
        self.mock_state_manager.get_learning_progress.return_value = self.mock_state["learning"]
        self.mock_state_manager.is_lesson_completed.return_value = True
        self.mock_state_manager.get_next_lesson.return_value = ("section1", "topic1", "lesson3", {})
        self.mock_state_manager.save_state.return_value = True
        
        # Создаем экземпляр дашборда
        self.dashboard = StartupDashboard(self.mock_state_manager)
    
    def test_dashboard_creation(self):
        """Тест создания дашборда."""
        try:
            dashboard_widget = self.dashboard.show_dashboard()
            self.assertIsNotNone(dashboard_widget)
            print("✅ Дашборд создан успешно")
        except Exception as e:
            self.fail(f"Ошибка при создании дашборда: {str(e)}")
    
    def test_dashboard_data_collection(self):
        """Тест сбора данных для дашборда."""
        try:
            data = self.dashboard._collect_dashboard_data()
            
            # Проверяем наличие основных секций
            self.assertIn("course_info", data)
            self.assertIn("progress_stats", data)
            self.assertIn("time_stats", data)
            self.assertIn("assessment_stats", data)
            
            # Проверяем данные курса
            course_info = data["course_info"]
            self.assertEqual(course_info["title"], "Основы Python")
            
            # Проверяем статистику прогресса
            progress_stats = data["progress_stats"]
            self.assertEqual(progress_stats["completed_lessons_count"], 2)
            self.assertEqual(progress_stats["progress_percent"], 40.0)
            
            # Проверяем статистику тестов
            assessment_stats = data["assessment_stats"]
            self.assertEqual(assessment_stats["average_score"], 87.5)
            self.assertEqual(assessment_stats["passed_tests_count"], 2)
            
            print("✅ Данные дашборда собраны корректно")
        except Exception as e:
            self.fail(f"Ошибка при сборе данных дашборда: {str(e)}")
    
    def test_course_info_extraction(self):
        """Тест извлечения информации о курсе."""
        try:
            course_info = self.dashboard._get_course_info()
            
            self.assertEqual(course_info["title"], "Основы Python")
            self.assertEqual(course_info["description"], "Курс по основам программирования на Python")
            self.assertEqual(course_info["total_duration"], 300)
            
            print("✅ Информация о курсе извлечена корректно")
        except Exception as e:
            self.fail(f"Ошибка при извлечении информации о курсе: {str(e)}")
    
    def test_progress_statistics(self):
        """Тест расчета статистики прогресса."""
        try:
            progress_stats = self.dashboard._get_progress_statistics()
            
            self.assertEqual(progress_stats["completed_lessons_count"], 2)
            self.assertEqual(progress_stats["total_lessons_count"], 2)
            self.assertEqual(progress_stats["progress_percent"], 100.0)  # 2 из 2 уроков завершено
            
            print("✅ Статистика прогресса рассчитана корректно")
        except Exception as e:
            self.fail(f"Ошибка при расчете статистики прогресса: {str(e)}")
    
    def test_assessment_statistics(self):
        """Тест расчета статистики тестов."""
        try:
            assessment_stats = self.dashboard._get_assessment_statistics()
            
            self.assertEqual(assessment_stats["average_score"], 87.5)
            self.assertEqual(assessment_stats["passed_tests_count"], 2)
            self.assertEqual(assessment_stats["total_tests_count"], 2)
            self.assertEqual(assessment_stats["total_attempts_count"], 2)
            
            print("✅ Статистика тестов рассчитана корректно")
        except Exception as e:
            self.fail(f"Ошибка при расчете статистики тестов: {str(e)}")


class TestLoadingIndicators(unittest.TestCase):
    """Тесты для индикаторов загрузки."""
    
    def setUp(self):
        """Настройка тестового окружения."""
        self.loading_manager = LoadingManager()
        self.basic_indicator = LoadingIndicator()
        self.openai_indicator = OpenAIAPILoadingIndicator()
    
    def test_basic_loading_indicator(self):
        """Тест базового индикатора загрузки."""
        try:
            widget = self.basic_indicator.show("Тестовая загрузка...")
            self.assertIsNotNone(widget)
            
            # Проверяем, что индикатор активен
            self.assertTrue(self.basic_indicator.is_active)
            
            # Скрываем индикатор
            self.basic_indicator.hide()
            self.assertFalse(self.basic_indicator.is_active)
            
            print("✅ Базовый индикатор загрузки работает корректно")
        except Exception as e:
            self.fail(f"Ошибка в базовом индикаторе загрузки: {str(e)}")
    
    def test_openai_loading_indicator(self):
        """Тест индикатора загрузки для OpenAI API."""
        try:
            # Тестируем показ для разных операций
            operations = ["generate_lesson", "generate_test", "generate_examples"]
            
            for operation in operations:
                widget = self.openai_indicator.show_for_operation(operation)
                self.assertIsNotNone(widget)
                self.assertTrue(self.openai_indicator.is_active)
                
                # Скрываем индикатор
                self.openai_indicator.hide()
                self.assertFalse(self.openai_indicator.is_active)
            
            print("✅ Индикатор загрузки OpenAI API работает корректно")
        except Exception as e:
            self.fail(f"Ошибка в индикаторе загрузки OpenAI API: {str(e)}")
    
    def test_loading_manager(self):
        """Тест менеджера загрузки."""
        try:
            # Тестируем показ индикатора
            widget = self.loading_manager.show_loading("default", message="Тестовая загрузка...")
            self.assertIsNotNone(widget)
            
            # Проверяем, что индикатор активен
            for indicator in self.loading_manager.indicators.values():
                if indicator.is_active:
                    break
            else:
                self.fail("Ни один индикатор не активен")
            
            # Скрываем индикатор
            self.loading_manager.hide_loading()
            
            # Проверяем, что все индикаторы неактивны
            for indicator in self.loading_manager.indicators.values():
                self.assertFalse(indicator.is_active)
            
            print("✅ Менеджер загрузки работает корректно")
        except Exception as e:
            self.fail(f"Ошибка в менеджере загрузки: {str(e)}")
    
    def test_loading_manager_different_types(self):
        """Тест менеджера загрузки с разными типами индикаторов."""
        try:
            # Тестируем разные типы индикаторов
            types_and_params = [
                ("default", {"message": "Обычная загрузка..."}),
                ("openai", {"operation": "generate_lesson"}),
                ("lesson", {"lesson_title": "Тестовый урок"})
            ]
            
            for indicator_type, params in types_and_params:
                widget = self.loading_manager.show_loading(indicator_type, **params)
                self.assertIsNotNone(widget)
                
                # Скрываем индикатор
                self.loading_manager.hide_loading()
            
            print("✅ Менеджер загрузки поддерживает разные типы индикаторов")
        except Exception as e:
            self.fail(f"Ошибка при тестировании разных типов индикаторов: {str(e)}")


def run_ux_tests():
    """Запуск всех тестов UX компонентов."""
    print("🧪 Запуск тестов UX компонентов...")
    print("=" * 50)
    
    # Создаем тестовый набор
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Добавляем тесты
    suite.addTests(loader.loadTestsFromTestCase(TestStartupDashboard))
    suite.addTests(loader.loadTestsFromTestCase(TestLoadingIndicators))
    
    # Запускаем тесты
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    print("\n" + "=" * 50)
    if result.wasSuccessful():
        print("🎉 ВСЕ ТЕСТЫ UX КОМПОНЕНТОВ ПРОЙДЕНЫ!")
        print("✅ Дашборд статистики работает корректно")
        print("✅ Индикаторы загрузки работают корректно")
        print("✅ Менеджер загрузки работает корректно")
    else:
        print("❌ НЕКОТОРЫЕ ТЕСТЫ UX КОМПОНЕНТОВ НЕ ПРОЙДЕНЫ")
        print("⚠️ Требуется дополнительная отладка")
    
    return result.wasSuccessful()


if __name__ == "__main__":
    run_ux_tests() 