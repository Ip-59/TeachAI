# 🔧 РУКОВОДСТВО ПО ПРАВИЛЬНЫМ ИМПОРТАМ SKLEARN

## 🚨 Частые ошибки импорта

### ❌ Неправильно (вызывает NameError)
```python
# ОШИБКА: 'datasets' не определен
from sklearn.model_selection import train_test_split
iris = datasets.load_iris()  # NameError!

# ОШИБКА: 'RandomForestClassifier' не импортирован
X_train, X_test, y_train, y_test = train_test_split(X, y)
model = RandomForestClassifier()  # NameError!
```

### ✅ Правильно (работает корректно)
```python
# Правильные импорты
from sklearn.datasets import load_iris
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score
import numpy as np

# Теперь все работает
iris = load_iris()
X_train, X_test, y_train, y_test = train_test_split(X, y)
model = RandomForestClassifier()
```

## 📚 Основные импорты sklearn

### 1. **Датасеты (Datasets)**
```python
# Встроенные датасеты
from sklearn.datasets import load_iris
from sklearn.datasets import load_breast_cancer
from sklearn.datasets import load_digits
from sklearn.datasets import load_wine

# Синтетические датасеты
from sklearn.datasets import make_classification
from sklearn.datasets import make_regression
from sklearn.datasets import make_blobs
from sklearn.datasets import make_moons

# Использование
iris = load_iris()
X, y = make_classification(n_samples=1000, n_features=20)
```

### 2. **Модели (Models)**
```python
# Классификация
from sklearn.ensemble import RandomForestClassifier
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC
from sklearn.neighbors import KNeighborsClassifier

# Регрессия
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.svm import SVR

# Кластеризация
from sklearn.cluster import KMeans
from sklearn.cluster import DBSCAN
```

### 3. **Разделение данных (Data Splitting)**
```python
from sklearn.model_selection import train_test_split
from sklearn.model_selection import cross_val_score
from sklearn.model_selection import GridSearchCV
from sklearn.model_selection import StratifiedKFold

# Использование
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)
```

### 4. **Метрики (Metrics)**
```python
# Классификация
from sklearn.metrics import accuracy_score
from sklearn.metrics import precision_score
from sklearn.metrics import recall_score
from sklearn.metrics import f1_score
from sklearn.metrics import classification_report
from sklearn.metrics import confusion_matrix

# Регрессия
from sklearn.metrics import mean_squared_error
from sklearn.metrics import r2_score
from sklearn.metrics import mean_absolute_error

# Использование
accuracy = accuracy_score(y_test, predictions)
print(classification_report(y_test, predictions))
```

### 5. **Предобработка данных (Preprocessing)**
```python
from sklearn.preprocessing import StandardScaler
from sklearn.preprocessing import MinMaxScaler
from sklearn.preprocessing import LabelEncoder
from sklearn.preprocessing import OneHotEncoder

# Использование
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)
```

## 🎯 Шаблоны для разных задач

### Классификация с Random Forest
```python
# Импорты
from sklearn.datasets import load_iris
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report
import numpy as np

# Загрузка данных
iris = load_iris()
X = iris.data
y = iris.target

# Разделение данных
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

# Обучение модели
model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X_train, y_train)

# Предсказание и оценка
predictions = model.predict(X_test)
accuracy = accuracy_score(y_test, predictions)
print(f"Точность: {accuracy:.4f}")
```

### Регрессия с Linear Regression
```python
# Импорты
from sklearn.datasets import make_regression
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score, mean_squared_error
import numpy as np

# Генерация данных
X, y = make_regression(n_samples=1000, n_features=10, random_state=42)

# Разделение данных
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

# Обучение модели
model = LinearRegression()
model.fit(X_train, y_train)

# Предсказание и оценка
predictions = model.predict(X_test)
r2 = r2_score(y_test, predictions)
mse = mean_squared_error(y_test, predictions)
print(f"R²: {r2:.4f}, MSE: {mse:.4f}")
```

### Кластеризация с K-Means
```python
# Импорты
from sklearn.datasets import make_blobs
from sklearn.cluster import KMeans
import numpy as np

# Генерация данных
X, y_true = make_blobs(n_samples=300, centers=4, random_state=42)

# Кластеризация
kmeans = KMeans(n_clusters=4, random_state=42)
y_pred = kmeans.fit_predict(X)

# Результаты
print(f"Центры кластеров: {kmeans.cluster_centers_}")
print(f"Метка инерции: {kmeans.inertia_:.2f}")
```

## 🚀 Лучшие практики

### 1. **Всегда импортируйте в начале файла**
```python
# ✅ Хорошо
from sklearn.datasets import load_iris
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier

# Загрузка данных
iris = load_iris()
```

### 2. **Используйте полные пути импорта**
```python
# ✅ Хорошо
from sklearn.datasets import load_iris

# ❌ Плохо
from sklearn import datasets
iris = datasets.load_iris()  # Может вызвать путаницу
```

### 3. **Группируйте импорты по категориям**
```python
# Стандартная библиотека Python
import numpy as np
import pandas as pd

# Библиотеки машинного обучения
from sklearn.datasets import load_iris
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score
```

### 4. **Добавляйте инструкции по установке**
```python
# Для работы примера установите: pip install scikit-learn pandas numpy

from sklearn.datasets import load_iris
from sklearn.ensemble import RandomForestClassifier
# ... остальной код
```

## 🔍 Диагностика проблем

### Ошибка: `NameError: name 'datasets' is not defined`
**Причина:** Неправильный импорт
**Решение:** 
```python
# Вместо этого:
from sklearn import datasets
iris = datasets.load_iris()

# Используйте это:
from sklearn.datasets import load_iris
iris = load_iris()
```

### Ошибка: `ModuleNotFoundError: No module named 'sklearn'`
**Причина:** Библиотека не установлена
**Решение:** 
```bash
pip install scikit-learn
```

### Ошибка: `ImportError: cannot import name 'RandomForestClassifier'`
**Причина:** Неправильная версия sklearn
**Решение:** 
```bash
pip install --upgrade scikit-learn
```

## 📋 Чек-лист для проверки

Перед запуском примера убедитесь, что:

- [ ] Все необходимые импорты присутствуют в начале файла
- [ ] Используются полные пути импорта (например, `sklearn.datasets`)
- [ ] Нет сокращений типа `datasets` без импорта
- [ ] Все функции и классы импортированы перед использованием
- [ ] Добавлены инструкции по установке для внешних библиотек
- [ ] Данные генерируются самостоятельно, а не загружаются из файлов

## 🎉 Результат

Следуя этому руководству, вы избежите:
- ❌ `NameError: name 'X' is not defined`
- ❌ `NameError: name 'datasets' is not defined`
- ❌ `NameError: name 'RandomForestClassifier' is not defined`
- ❌ `ModuleNotFoundError: No module named 'sklearn'`

И получите:
- ✅ Работающий код без ошибок
- ✅ Правильную структуру импортов
- ✅ Понятные сообщения об ошибках
- ✅ Легкость отладки и поддержки

**Правильные импорты - залог успешного выполнения кода!** 🐍✨ 