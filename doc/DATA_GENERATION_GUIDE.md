# 📊 РУКОВОДСТВО ПО ПРАВИЛЬНОЙ ГЕНЕРАЦИИ ДАННЫХ В TEACHAI

## 🚨 Запрещенные способы загрузки данных

### ❌ НЕ ИСПОЛЬЗУЙТЕ (вызывает FileNotFoundError)
```python
# Загрузка внешних файлов - ЗАПРЕЩЕНО!
data = pd.read_csv('data.csv')           # ❌ FileNotFoundError!
data = pd.read_excel('dataset.xlsx')     # ❌ FileNotFoundError!
data = pd.read_json('data.json')         # ❌ FileNotFoundError!
data = pd.read_sql('SELECT * FROM table') # ❌ ConnectionError!

# Открытие файлов - ЗАПРЕЩЕНО!
with open('data.txt', 'r') as f:         # ❌ FileNotFoundError!
    data = f.read()

# Пути к файлам - ЗАПРЕЩЕНО!
data = np.load('array.npy')              # ❌ FileNotFoundError!
data = pickle.load(open('model.pkl', 'rb')) # ❌ FileNotFoundError!
```

## ✅ Разрешенные способы генерации данных

### 1. **NumPy для генерации случайных данных**
```python
import numpy as np

# Случайные числа
np.random.seed(42)  # Для воспроизводимости
random_numbers = np.random.randn(1000)  # Нормальное распределение
uniform_numbers = np.random.uniform(0, 1, 1000)  # Равномерное распределение
integers = np.random.randint(1, 100, 1000)  # Случайные целые

# Создание массивов
X = np.random.randn(1000, 10)  # 1000 образцов, 10 признаков
y = np.random.randint(0, 2, 1000)  # Бинарные метки классов

# Синтетические зависимости
feature1 = np.random.randn(1000) * 2 + 5
feature2 = np.random.randn(1000) * 1.5 + 3
target = 2 * feature1 + 1.5 * feature2 + np.random.randn(1000) * 0.5
```

### 2. **Sklearn для встроенных датасетов**
```python
from sklearn.datasets import load_iris, make_classification, make_regression

# Встроенные датасеты
iris = load_iris()
X_iris = iris.data
y_iris = iris.target

# Синтетические датасеты
X_class, y_class = make_classification(
    n_samples=1000, 
    n_features=20, 
    n_informative=15,
    n_redundant=5,
    random_state=42
)

X_reg, y_reg = make_regression(
    n_samples=1000, 
    n_features=10, 
    noise=0.1,
    random_state=42
)

# Другие встроенные датасеты
from sklearn.datasets import load_breast_cancer, load_digits, load_wine
cancer = load_breast_cancer()
digits = load_digits()
wine = load_wine()
```

### 3. **Pandas для создания таблиц**
```python
import pandas as pd
import numpy as np

# Создание DataFrame из массивов
np.random.seed(42)
n_samples = 1000

data = pd.DataFrame({
    'feature1': np.random.randn(n_samples) * 2 + 5,
    'feature2': np.random.randn(n_samples) * 1.5 + 3,
    'feature3': np.random.randint(0, 10, n_samples),
    'target': np.random.randint(0, 2, n_samples)
})

# Создание временных рядов
dates = pd.date_range('2023-01-01', periods=1000, freq='D')
time_series = pd.DataFrame({
    'date': dates,
    'value': np.random.randn(1000).cumsum(),
    'trend': np.arange(1000) * 0.1
})

# Создание категориальных данных
categories = ['A', 'B', 'C', 'D']
categorical_data = pd.DataFrame({
    'category': np.random.choice(categories, 1000),
    'value': np.random.randn(1000)
})
```

### 4. **Встроенные возможности Python**
```python
# Списки и словари
numbers = list(range(1, 101))
squares = [x**2 for x in numbers]
even_numbers = [x for x in numbers if x % 2 == 0]

# Словари
student_data = {
    'names': ['Иван', 'Мария', 'Петр', 'Анна'],
    'ages': [20, 22, 21, 23],
    'grades': [4.5, 4.8, 4.2, 4.9]
}

# Строки
text_data = "Это пример текста для анализа. " * 100
words = text_data.split()
word_counts = {word: words.count(word) for word in set(words)}
```

## 🎯 Шаблоны для разных задач

### Классификация
```python
# Генерация данных для классификации
import numpy as np
import pandas as pd
from sklearn.datasets import make_classification

# Способ 1: Синтетические данные
X, y = make_classification(
    n_samples=1000,
    n_features=20,
    n_informative=15,
    n_redundant=5,
    n_classes=3,
    random_state=42
)

# Способ 2: Ручная генерация
np.random.seed(42)
n_samples = 1000
n_features = 10

# Создаем признаки
X = np.random.randn(n_samples, n_features)

# Создаем метки классов на основе признаков
y = np.zeros(n_samples)
y[X[:, 0] + X[:, 1] > 0] = 1
y[X[:, 0] + X[:, 1] > 2] = 2

# Создаем DataFrame
data = pd.DataFrame(X, columns=[f'feature_{i}' for i in range(n_features)])
data['target'] = y
```

### Регрессия
```python
# Генерация данных для регрессии
import numpy as np
import pandas as pd

np.random.seed(42)
n_samples = 1000

# Создаем признаки
feature1 = np.random.randn(n_samples) * 2 + 5
feature2 = np.random.randn(n_samples) * 1.5 + 3
feature3 = np.random.uniform(0, 10, n_samples)

# Создаем целевую переменную с линейной зависимостью
target = 2 * feature1 + 1.5 * feature2 - 0.8 * feature3 + np.random.randn(n_samples) * 0.5

# Создаем DataFrame
data = pd.DataFrame({
    'feature1': feature1,
    'feature2': feature2,
    'feature3': feature3,
    'target': target
})
```

### Кластеризация
```python
# Генерация данных для кластеризации
import numpy as np
import pandas as pd
from sklearn.datasets import make_blobs

# Способ 1: Встроенный датасет
X, y_true = make_blobs(
    n_samples=1000,
    centers=4,
    cluster_std=1.0,
    random_state=42
)

# Способ 2: Ручная генерация
np.random.seed(42)
n_samples = 1000

# Создаем центры кластеров
centers = np.array([
    [0, 0],
    [5, 5],
    [0, 5],
    [5, 0]
])

# Создаем данные вокруг центров
X = []
y_true = []

for i, center in enumerate(centers):
    cluster_points = np.random.randn(n_samples // 4, 2) * 0.5 + center
    X.extend(cluster_points)
    y_true.extend([i] * (n_samples // 4))

X = np.array(X)
y_true = np.array(y_true)

# Создаем DataFrame
data = pd.DataFrame(X, columns=['x', 'y'])
data['cluster'] = y_true
```

## 🚀 Лучшие практики

### 1. **Всегда используйте seed для воспроизводимости**
```python
import numpy as np
np.random.seed(42)  # Фиксируем случайность
```

### 2. **Создавайте реалистичные зависимости**
```python
# ✅ Хорошо - реалистичная зависимость
feature1 = np.random.randn(1000) * 2 + 5
feature2 = np.random.randn(1000) * 1.5 + 3
target = 2 * feature1 + 1.5 * feature2 + np.random.randn(1000) * 0.5

# ❌ Плохо - случайная зависимость
feature1 = np.random.randn(1000)
feature2 = np.random.randn(1000)
target = np.random.randn(1000)  # Нет связи с признаками
```

### 3. **Добавляйте комментарии к генерации данных**
```python
# Генерируем синтетические данные для демонстрации
# 1000 образцов, 10 признаков, 3 класса
np.random.seed(42)
X, y = make_classification(
    n_samples=1000,
    n_features=10,
    n_informative=8,
    n_redundant=2,
    n_classes=3,
    random_state=42
)
```

### 4. **Проверяйте качество сгенерированных данных**
```python
# Проверяем размеры
print(f"Размеры данных: X={X.shape}, y={y.shape}")

# Проверяем распределение классов
unique, counts = np.unique(y, return_counts=True)
print("Распределение классов:")
for class_idx, count in zip(unique, counts):
    print(f"  Класс {class_idx}: {count} образцов")

# Проверяем статистику признаков
print(f"Статистика признаков:")
print(f"  Среднее: {X.mean(axis=0)}")
print(f"  Стандартное отклонение: {X.std(axis=0)}")
```

## 📋 Чек-лист для проверки

Перед созданием примера убедитесь, что:

- [ ] НЕ используется `pd.read_csv()`, `pd.read_excel()`, `open()`
- [ ] НЕ используются пути к внешним файлам
- [ ] Данные генерируются с помощью numpy.random или sklearn.datasets
- [ ] Используется `np.random.seed()` для воспроизводимости
- [ ] Создаются реалистичные зависимости между признаками
- [ ] Добавлены комментарии к генерации данных
- [ ] Проверяется качество сгенерированных данных

## 🎉 Результат

Следуя этому руководству, вы избежите:
- ❌ `FileNotFoundError: No such file or directory: 'data.csv'`
- ❌ `FileNotFoundError: No such file or directory: 'dataset.xlsx'`
- ❌ `ConnectionError` при попытке подключения к базе данных

И получите:
- ✅ Самодостаточные примеры без внешних зависимостей
- ✅ Воспроизводимые результаты
- ✅ Реалистичные данные для демонстрации
- ✅ Легкость тестирования и отладки

**Правильная генерация данных - залог успешного выполнения примеров!** 🐍✨ 