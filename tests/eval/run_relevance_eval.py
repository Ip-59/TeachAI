#!/usr/bin/env python
"""
Скрипт оценки точности проверки релевантности вопросов.

Прогоняет 50 тестовых вопросов через НАСТОЯЩУЮ функцию проверки релевантности
приложения и выводит метрики точности.

НЕ попадает в обычный прогон pytest (имя без test_).
"""
import json
import sys
from pathlib import Path
from collections import defaultdict
import tempfile
import shutil

# Добавляем корень проекта в path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from content_generator import ContentGenerator


def load_questions():
    """Загружает вопросы из relevance_questions.json."""
    questions_file = Path(__file__).parent / "relevance_questions.json"
    with open(questions_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data


def create_lesson_context(course_data, lesson_id, lesson_title):
    """Создаёт контекст урока для проверки релевантности."""
    return {
        "course_title": course_data["title"],
        "course_plan": {
            "title": course_data["title"],
            "description": course_data["description"],
        },
        "section_title": "Основы языка",
        "topic_title": "Тема урока",
        "lesson_title": lesson_title,
        "section_id": "section-1",
        "topic_id": "topic-1",
        "lesson_id": lesson_id,
    }


def create_lesson_data(lesson_id, lesson_title):
    """Создаёт метаданные урока."""
    keywords_map = {
        "lesson-install": ["установка", "pip", "python"],
        "lesson-constructs": ["переменные", "циклы", "условия", "for", "if"],
        "lesson-jupyter": ["jupyter", "notebook", "ячейки"],
        "lesson-numpy": ["numpy", "массивы", "array"],
        "lesson-pandas": ["pandas", "dataframe", "series"],
        "lesson-comparison": ["numpy", "pandas", "сравнение"],
        "lesson-missing": ["NaN", "пропуски", "fillna"],
        "lesson-filtering": ["фильтрация", "выборка", "условия"],
        "lesson-groupby": ["groupby", "агрегация", "группировка"],
        "lesson-matplotlib": ["matplotlib", "графики", "plot"],
        "lesson-plot-types": ["scatter", "line", "bar", "hist"],
        "lesson-plot-customize": ["заголовок", "легенда", "оси"],
        "lesson-project": ["проект", "тема"],
        "lesson-collect": ["данные", "датасет", "источники"],
    }
    return {
        "title": lesson_title,
        "description": f"Урок о {lesson_title.lower()}",
        "keywords": keywords_map.get(lesson_id, []),
    }


def get_lesson_content(lesson_id):
    """Возвращает минимальный контент урока (заглушка для контекста)."""
    content_map = {
        "lesson-install": "<h2>Установка Python и необходимых библиотек</h2><p>Установка Python, pip, pandas, numpy, matplotlib.</p>",
        "lesson-constructs": "<h2>Основные конструкции языка Python</h2><p>Переменные, типы данных, циклы for и while, условия if/else, функции.</p>",
        "lesson-jupyter": "<h2>Работа с Jupyter Notebook</h2><p>Создание ячеек, выполнение кода, markdown, магические команды.</p>",
        "lesson-numpy": "<h2>NumPy: Основы работы с массивами</h2><p>Создание массивов numpy, индексация, срезы, операции.</p>",
        "lesson-pandas": "<h2>Pandas: Работа с датафреймами</h2><p>DataFrame, Series, чтение CSV, основные операции с данными.</p>",
        "lesson-comparison": "<h2>Сравнение NumPy и Pandas</h2><p>Когда использовать массивы NumPy, а когда DataFrame Pandas.</p>",
        "lesson-missing": "<h2>Обработка пропущенных значений</h2><p>Поиск NaN, fillna, dropna, стратегии заполнения пропусков.</p>",
        "lesson-filtering": "<h2>Фильтрация и выборка данных</h2><p>Выборка строк по условию, loc, iloc, булевы индексы.</p>",
        "lesson-groupby": "<h2>Группировка и агрегация данных</h2><p>groupby, agg, transform, применение функций к группам.</p>",
        "lesson-matplotlib": "<h2>Введение в Matplotlib</h2><p>Создание графиков, plt.plot, figure и axes.</p>",
        "lesson-plot-types": "<h2>Построение различных типов графиков</h2><p>Line, scatter, bar, histogram, pie charts.</p>",
        "lesson-plot-customize": "<h2>Настройка графиков</h2><p>Заголовки, легенда, оси, цвета, стили.</p>",
        "lesson-project": "<h2>Определение темы проекта</h2><p>Выбор интересной темы для анализа данных.</p>",
        "lesson-collect": "<h2>Сбор данных из открытых источников</h2><p>Kaggle, data.gov, API, веб-скрейпинг.</p>",
    }
    return content_map.get(lesson_id, "<p>Урок</p>")


def run_evaluation():
    """Основная функция оценки."""
    print("=" * 80)
    print("ОЦЕНКА ТОЧНОСТИ ПРОВЕРКИ РЕЛЕВАНТНОСТИ")
    print("=" * 80)
    print()
    
    # Загружаем вопросы
    data = load_questions()
    course_data = data["course"]
    questions = data["questions"]
    
    print(f"Курс: {course_data['title']}")
    print(f"Вопросов: {len(questions)}")
    print()
    
    # Принудительно устанавливаем direct route (OpenAI) для этого процесса
    import os
    os.environ["OPENAI_API_ROUTE"] = "direct"
    
    # Загружаем ключ API из .env (как делает приложение)
    from dotenv import load_dotenv
    env_path = PROJECT_ROOT / ".env"
    if env_path.exists():
        load_dotenv(env_path)
    
    api_key = os.getenv("OPENAI_API_KEY")
    print(f"Маршрут LLM: {os.getenv('OPENAI_API_ROUTE')}")
    
    if not api_key:
        print("ОШИБКА: OPENAI_API_KEY не найден в .env")
        sys.exit(1)
    
    # Создаём генератор контента (как в приложении)
    generator = ContentGenerator(api_key)
    
    # Результаты
    results = []
    correct = 0
    total = 0
    api_calls = 0
    
    # Матрица ошибок: [ожидаемый][полученный]
    confusion = defaultdict(lambda: defaultdict(int))
    
    print("Прогон вопросов через реальную проверку релевантности...")
    print("-" * 80)
    
    for i, q in enumerate(questions, 1):
        question_text = q["question"]
        expected_scope = q["expected_scope"]
        lesson_id = q["lesson_id"]
        lesson_title = q["lesson_title"]
        
        # Контекст урока
        course_context = create_lesson_context(course_data, lesson_id, lesson_title)
        lesson_data = create_lesson_data(lesson_id, lesson_title)
        lesson_content = get_lesson_content(lesson_id)
        
        # Реальный вызов проверки релевантности (как в приложении)
        try:
            result = generator.check_question_relevance(
                user_question=question_text,
                lesson_content=lesson_content,
                lesson_data=lesson_data,
                course_context=course_context,
                lesson_raw_content=lesson_content,
            )
            api_calls += 1
            
            actual_scope = result.get("scope", "unknown")
            reason = result.get("reason", "")
            
            # Проверяем правильность
            is_correct = (actual_scope == expected_scope)
            if is_correct:
                correct += 1
            
            total += 1
            confusion[expected_scope][actual_scope] += 1
            
            results.append({
                "id": q["id"],
                "question": question_text,
                "lesson": lesson_title,
                "expected": expected_scope,
                "actual": actual_scope,
                "correct": is_correct,
                "reason": reason,
                "rationale": q["rationale"],
            })
            
            # Прогресс
            status = "✓" if is_correct else "✗"
            print(f"{status} {i:2d}. {question_text[:60]:60s} | exp={expected_scope:7s} act={actual_scope:7s}")
            
        except Exception as e:
            print(f"✗ {i:2d}. ОШИБКА: {e}")
            results.append({
                "id": q["id"],
                "question": question_text,
                "expected": expected_scope,
                "actual": "error",
                "correct": False,
                "reason": str(e),
                "rationale": q["rationale"],
            })
            total += 1
    
    print()
    print("=" * 80)
    print("РЕЗУЛЬТАТЫ")
    print("=" * 80)
    print()
    
    # Точность
    accuracy = (correct / total * 100) if total > 0 else 0
    print(f"Общая точность: {correct}/{total} = {accuracy:.1f}%")
    print(f"API запросов: {api_calls}")
    print()
    
    # Матрица ошибок
    print("МАТРИЦА ОШИБОК (строки=ожидаемый, столбцы=фактический):")
    print()
    scopes = ["lesson", "course", "outside"]
    
    # Заголовок
    print(f"{'':12s} | {'lesson':>8s} {'course':>8s} {'outside':>8s} | {'ИТОГО':>8s}")
    print("-" * 56)
    
    # Строки
    for expected in scopes:
        counts = [confusion[expected][actual] for actual in scopes]
        row_total = sum(counts)
        counts_str = " ".join(f"{c:8d}" for c in counts)
        print(f"{expected:12s} | {counts_str} | {row_total:8d}")
    
    print()
    
    # Точность по классам
    print("ТОЧНОСТЬ ПО КЛАССАМ:")
    for scope in scopes:
        true_positive = confusion[scope][scope]
        total_expected = sum(confusion[scope].values())
        acc = (true_positive / total_expected * 100) if total_expected > 0 else 0
        print(f"  {scope:8s}: {true_positive}/{total_expected} = {acc:.1f}%")
    print()
    
    # Ложные отказы (ожидалось lesson/course, получено outside)
    false_rejections = [r for r in results if r["expected"] in ["lesson", "course"] and r["actual"] == "outside"]
    
    if false_rejections:
        print("ЛОЖНЫЕ ОТКАЗЫ (ожидалось lesson/course, получено outside):")
        print("-" * 80)
        for r in false_rejections:
            print(f"ID {r['id']:2d} [{r['expected']:7s}→outside]: {r['question']}")
            print(f"    Урок: {r.get('lesson', 'N/A')}")
            print(f"    Reason: {r['reason']}")
            print(f"    Обоснование: {r['rationale']}")
            print()
    else:
        print("ЛОЖНЫЕ ОТКАЗЫ: нет")
        print()
    
    # Ложные пропуски (ожидалось outside, получено lesson/course)
    false_acceptances = [r for r in results if r["expected"] == "outside" and r["actual"] in ["lesson", "course"]]
    
    if false_acceptances:
        print("ЛОЖНЫЕ ПРОПУСКИ (ожидалось outside, получено lesson/course):")
        print("-" * 80)
        for r in false_acceptances:
            print(f"ID {r['id']:2d} [outside→{r['actual']:7s}]: {r['question']}")
            print(f"    Урок: {r.get('lesson', 'N/A')}")
            print(f"    Reason: {r['reason']}")
            print(f"    Обоснование: {r['rationale']}")
            print()
    else:
        print("ЛОЖНЫЕ ПРОПУСКИ: нет")
        print()
    
    # Путаница lesson↔course
    lesson_course_confusion = [r for r in results 
                              if (r["expected"] == "lesson" and r["actual"] == "course") or 
                                 (r["expected"] == "course" and r["actual"] == "lesson")]
    
    if lesson_course_confusion:
        print("ПУТАНИЦА lesson↔course:")
        print("-" * 80)
        for r in lesson_course_confusion:
            print(f"ID {r['id']:2d} [{r['expected']:7s}→{r['actual']:7s}]: {r['question']}")
            print(f"    Урок: {r.get('lesson', 'N/A')}")
            print(f"    Reason: {r['reason']}")
            print(f"    Обоснование: {r['rationale']}")
            print()
    
    print("=" * 80)
    print(f"Всего API запросов: {api_calls} (лимит: 150)")
    print("=" * 80)


if __name__ == "__main__":
    run_evaluation()
