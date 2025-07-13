# 🧪 Тесты TeachAI

## 📁 Структура тестов

### `core/` - Основные тесты функциональности
- **`test_qa_fix.py`** - Тестирование системы вопросов и ответов
- **`test_relevance_fix.py`** - Тестирование проверки релевантности вопросов
- **`test_control_tasks_full.py`** - Полное тестирование контрольных заданий

### `cells/` - Тесты образовательных ячеек
- **`test_demo_cells.py`** - Тестирование демонстрационных ячеек
- **`test_interactive_cells.py`** - Тестирование интерактивных ячеек

### `integration/` - Тесты интеграции
- **`test_cell_integration.py`** - Тестирование интеграции ячеек в уроки

## 🚀 Запуск тестов

### Запуск всех тестов:
```bash
python -m pytest tests/
```

### Запуск тестов по категориям:
```bash
# Основные тесты
python -m pytest tests/core/

# Тесты ячеек
python -m pytest tests/cells/

# Тесты интеграции
python -m pytest tests/integration/
```

### Запуск конкретного теста:
```bash
python tests/core/test_qa_fix.py
python tests/cells/test_demo_cells.py
python tests/integration/test_cell_integration.py
```

## 📋 Описание тестов

### Core Tests (Основные)
- **test_qa_fix.py**: Проверяет исправления системы вопросов и ответов
- **test_relevance_fix.py**: Тестирует исправления проверки релевантности
- **test_control_tasks_full.py**: Полное тестирование контрольных заданий

### Cells Tests (Ячейки)
- **test_demo_cells.py**: Тестирует демонстрационные образовательные ячейки
- **test_interactive_cells.py**: Тестирует интерактивные ячейки с выполнением кода

### Integration Tests (Интеграция)
- **test_cell_integration.py**: Тестирует интеграцию ячеек в основной интерфейс

## 🔧 Требования для запуска

1. **Python 3.8+**
2. **Установленные зависимости** из `requirements.txt`
3. **Настроенный API ключ** в `.env` файле
4. **Jupyter Notebook** для тестов ячеек

## 📊 Результаты тестирования

Все тесты должны проходить успешно для подтверждения стабильности системы.

---

**Примечание:** Тесты обновлены после очистки проекта и содержат только актуальные проверки.
