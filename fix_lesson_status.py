#!/usr/bin/env python3
"""
Скрипт для исправления статуса первого урока.
Убирает первый урок из completed_lessons, так как он не завершен.
"""

from state_manager import StateManager

def fix_first_lesson_status():
    """Исправляет статус первого урока."""
    try:
        # Инициализируем StateManager
        sm = StateManager()
        
        # ID первого урока
        lesson_id = 'section-1:topic-1:lesson-1'
        
        # Получаем доступ к learning секции
        learning = sm.state['learning']
        completed_lessons = learning.get('completed_lessons', [])
        
        print(f"До исправления: {completed_lessons}")
        
        # Убираем первый урок из completed_lessons
        if lesson_id in completed_lessons:
            learning['completed_lessons'] = [l for l in completed_lessons if l != lesson_id]
            print(f"После исправления: {learning['completed_lessons']}")
            
            # Сохраняем состояние
            sm.save_state()
            print("✅ Состояние сохранено")
            
            # Проверяем, что исправление сработало
            is_completed = sm.is_lesson_completed(lesson_id)
            print(f"Урок {lesson_id} завершен: {is_completed}")
            
        else:
            print(f"Урок {lesson_id} не найден в completed_lessons")
            
    except Exception as e:
        print(f"❌ Ошибка при исправлении: {str(e)}")

if __name__ == "__main__":
    fix_first_lesson_status()
