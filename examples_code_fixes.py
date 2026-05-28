"""Исправление типичных ошибок в сгенерированном коде примеров.

LLM часто выдаёт make_classification с n_features=2 (падает в runtime)
и примеры на TensorFlow, когда пакет не установлен в среде notebook.
"""

from __future__ import annotations

import importlib.util
import re
from typing import Dict, List

# Надёжный пример классификации — без make_classification.
_IRIS_LOGISTIC_CODE = """from sklearn.datasets import load_iris
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression

X, y = load_iris(return_X_y=True)
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.3, random_state=42
)
model = LogisticRegression(max_iter=200)
model.fit(X_train, y_train)
accuracy = model.score(X_test, y_test)
print(f"Accuracy: {accuracy:.2f}")
"""

# Замена TensorFlow/Keras, если tensorflow не установлен.
_MLP_CLASSIFIER_CODE = """from sklearn.datasets import load_iris
from sklearn.model_selection import train_test_split
from sklearn.neural_network import MLPClassifier

X, y = load_iris(return_X_y=True)
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.3, random_state=42
)
model = MLPClassifier(hidden_layer_sizes=(64,), max_iter=500, random_state=42)
model.fit(X_train, y_train)
accuracy = model.score(X_test, y_test)
print(f"Accuracy: {accuracy:.2f}")
"""


def module_available(module_name: str) -> bool:
    """Проверяет, установлен ли модуль (без импорта side-effects)."""
    return importlib.util.find_spec(module_name) is not None


def _uses_tensorflow(code: str) -> bool:
    lower = code.lower()
    return "tensorflow" in lower or "keras" in lower


def _fix_make_classification(code: str) -> str:
    """Заменяет проблемный make_classification на load_iris."""
    if "make_classification" not in code:
        return code

    # n_features=1/2/3 почти всегда ломает make_classification с дефолтами.
    bad_features = re.search(r"n_features\s*=\s*([1-4])\b", code)
    if bad_features:
        return _IRIS_LOGISTIC_CODE

    # Явно задано n_features=2 в другом формате или без n_informative.
    if re.search(r"n_features\s*=\s*2\b", code):
        return _IRIS_LOGISTIC_CODE

    return code


def sanitize_example_code(code: str) -> str:
    """Чинит один блок кода примера."""
    fixed = _fix_make_classification(code)
    if _uses_tensorflow(fixed) and not module_available("tensorflow"):
        return _MLP_CLASSIFIER_CODE
    return fixed


def sanitize_example(example: Dict[str, str]) -> Dict[str, str]:
    """Возвращает копию примера с исправленным code и при необходимости title/description."""
    code = str(example.get("code") or "").strip()
    if not code:
        return example

    new_code = sanitize_example_code(code)
    if new_code == code:
        return example

    updated = dict(example)
    updated["code"] = new_code

    if _uses_tensorflow(code) and not module_available("tensorflow"):
        updated["title"] = "Нейросеть MLPClassifier (scikit-learn)"
        updated["description"] = (
            "Обучает простую нейросеть через MLPClassifier из scikit-learn. "
            "TensorFlow в среде не установлен — используется эквивалент из sklearn."
        )
    elif "make_classification" in code and new_code == _IRIS_LOGISTIC_CODE:
        if "logistic" in code.lower() or "LogisticRegression" in code:
            updated["description"] = (
                "Загружает Iris, обучает логистическую регрессию и выводит accuracy."
            )

    return updated


def sanitize_examples(examples: List[Dict[str, str]]) -> List[Dict[str, str]]:
    """Применяет sanitize_example ко всем элементам списка."""
    return [sanitize_example(ex) for ex in examples]
