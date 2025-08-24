# 🔧 РУКОВОДСТВО ПО РЕШЕНИЮ ПРОБЛЕМ С ПРИМЕРАМИ КОДА

## 🎯 Основные проблемы и их решения

### 1. ❌ IndentationError: unexpected indent

**Проблема:** Лишние отступы в коде вызывают ошибку выполнения.

**Решение:** ✅ **ИСПРАВЛЕНО** - TeachAI теперь автоматически очищает отступы.

**Пример:**
```python
# ДО исправления (вызывало ошибку):
        import numpy as np
        X = np.array([[1], [2], [3]])

# ПОСЛЕ исправления (работает корректно):
import numpy as np
X = np.array([[1], [2], [3]])
```

### 2. ❌ ModuleNotFoundError: No module named 'sklearn'

**Проблема:** Отсутствуют необходимые библиотеки.

**Решение:** Запустите скрипт установки зависимостей:
```bash
python install_dependencies.py
```

**Или установите вручную:**
```bash
pip install scikit-learn pandas numpy matplotlib
```

### 3. ❌ NameError: name 'train_test_split' is not defined

**Проблема:** Функция используется без импорта.

**Решение:** Добавьте необходимые импорты в начало кода:
```python
# Правильные импорты для sklearn:
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.datasets import make_classification
import numpy as np
```

## 🚀 Как избежать проблем

### ✅ Правильная структура примера

```python
# 1. Комментарий с инструкцией по установке (если нужны внешние библиотеки)
# Для работы примера установите: pip install scikit-learn pandas numpy matplotlib

# 2. Все необходимые импорты
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
import numpy as np

# 3. Основной код без лишних отступов
X, y = make_classification(n_samples=1000, n_features=20, random_state=42)
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)

# 4. Обработка ошибок
try:
    model = RandomForestClassifier()
    model.fit(X_train, y_train)
    print("Модель обучена!")
except Exception as e:
    print(f"Ошибка: {e}")
```

### ❌ Что НЕ делать

```python
# НЕ используйте функции без импорта:
X_train, X_test, y_train, y_test = train_test_split(X, y)  # NameError!

# НЕ добавляйте лишние отступы:
        import numpy as np  # IndentationError!

# НЕ используйте HTML теги в коде:
<html><body><script>...</script></body></html>  # Не Python!
```

## 🛠️ Инструменты для диагностики

### 1. Скрипт установки зависимостей
```bash
python install_dependencies.py
```
- Проверяет установленные пакеты
- Автоматически устанавливает недостающие
- Показывает статус установки

### 2. Тестирование примера
```bash
python your_example.py
```
- Проверяет синтаксис
- Выявляет ошибки импорта
- Тестирует выполнение

### 3. Проверка версий
```python
import sklearn
import pandas
import numpy
print(f"sklearn: {sklearn.__version__}")
print(f"pandas: {pandas.__version__}")
print(f"numpy: {numpy.__version__}")
```

## 📚 Примеры правильного кода

### Простой пример (только Python)
```python
# Работа со списками и словарями
numbers = [1, 2, 3, 4, 5]
squares = [x**2 for x in numbers]
print(f"Числа: {numbers}")
print(f"Квадраты: {squares}")

student = {"name": "Иван", "age": 20}
student["subjects"] = ["Математика", "Физика"]
print(f"Студент: {student}")
```

### Пример с sklearn (с правильными импортами)
```python
# Для работы примера установите: pip install scikit-learn numpy

from sklearn.datasets import make_classification
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
import numpy as np

# Создание данных
X, y = make_classification(n_samples=100, n_features=10, random_state=42)

# Разделение данных
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)

# Обучение модели
model = RandomForestClassifier(n_estimators=50, random_state=42)
model.fit(X_train, y_train)

# Оценка
accuracy = model.score(X_test, y_test)
print(f"Точность: {accuracy:.4f}")
```

## 🔍 Диагностика ошибок

### Частые ошибки и их причины

| Ошибка | Причина | Решение |
|--------|---------|---------|
| `IndentationError` | Лишние отступы | ✅ Автоматически исправляется |
| `ModuleNotFoundError` | Библиотека не установлена | `pip install package_name` |
| `NameError` | Функция не импортирована | Добавить `from module import function` |
| `SyntaxError` | Неправильный синтаксис | Проверить код на ошибки |
| `AttributeError` | Неправильный атрибут | Проверить документацию API |

### Логи ошибок TeachAI

Проверьте файлы в директории `logs/`:
```bash
# Последние ошибки
tail -f logs/teachai.log

# Ошибки генерации примеров
grep "examples" logs/teachai.log
```

## 📞 Получение помощи

### 1. Проверьте документацию
- `EXAMPLES_INDENTATION_FIX_SUMMARY.md` - отчет об исправлениях
- `PROJECT_STATUS.md` - текущий статус проекта

### 2. Запустите диагностику
```bash
# Проверка зависимостей
python install_dependencies.py

# Тестирование простого примера
python simple_python_example.py
```

### 3. Создайте минимальный пример
```python
# Начните с простого кода
print("Hello, World!")

# Постепенно добавляйте функциональность
import numpy as np
arr = np.array([1, 2, 3])
print(arr)
```

## 🎉 Результат

После применения всех исправлений:
- ✅ **Отступы автоматически очищаются**
- ✅ **Примеры генерируются с правильными импортами**
- ✅ **Система предлагает инструкции по установке**
- ✅ **Код выполняется без ошибок**

TeachAI теперь создает качественные, исполняемые примеры кода! 🐍✨ 