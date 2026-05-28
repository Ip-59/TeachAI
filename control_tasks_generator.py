#!/usr/bin/env python3
"""
Генератор контрольных заданий для TeachAI.
Создает практические задачи с эталонным кодом для проверки знаний.
"""

import io
import logging
import json
import os
import re
from contextlib import redirect_stdout
from typing import Dict, List, Any, Optional, Tuple

from content_utils import BaseContentGenerator
from examples_code_fixes import sanitize_example_code
from result_checker import ResultChecker, values_equal, stdout_outputs_equal


class ControlTasksGenerator(BaseContentGenerator):
    """Генератор контрольных заданий."""

    _RESULT_CHECKER = ResultChecker()
    _SEED = 42
    _SKLEARN_STABILIZE_FUNCS = (
        "make_classification",
        "train_test_split",
        "KMeans",
        "RandomForestClassifier",
        "LogisticRegression",
    )

    def __init__(self, api_key: str):
        super().__init__(api_key)
        self.logger = logging.getLogger(__name__)
        self.validation_model = os.getenv(
            "VALIDATION_MODEL",
            os.getenv("LLM_MODEL", "gpt-4o-mini"),
        )

    @staticmethod
    def resolve_executable_code(task_code: str, editor_code: str) -> str:
        editor = (editor_code or "").strip()
        starter = (task_code or "").strip()
        if not editor:
            return starter
        if starter and (editor == starter or editor.startswith(starter)):
            return editor
        return ControlTasksGenerator.combine_code(starter, editor)

    @staticmethod
    def combine_code(task_code: str, user_code: str) -> str:
        starter = (task_code or "").strip()
        student = (user_code or "").strip()
        if starter and student:
            return f"{starter}\n{student}"
        return starter or student

    @staticmethod
    def execute_code(code: str) -> Tuple[str, Dict[str, Any]]:
        output_buffer = io.StringIO()
        local_vars: Dict[str, Any] = {}
        with redirect_stdout(output_buffer):
            exec(code, {}, local_vars)
        return output_buffer.getvalue().strip(), local_vars

    @classmethod
    def _inject_random_state(cls, func_name: str, args: str) -> str:
        if "random_state" in args:
            return f"{func_name}({args})"
        args = args.strip()
        if func_name == "KMeans":
            if args:
                return f"KMeans({args}, random_state={cls._SEED}, n_init=10)"
            return f"KMeans(n_clusters=3, random_state={cls._SEED}, n_init=10)"
        if args:
            return f"{func_name}({args}, random_state={cls._SEED})"
        return f"{func_name}(random_state={cls._SEED})"

    @classmethod
    def stabilize_sklearn_code(cls, code: str) -> str:
        """Добавляет random_state в вызовы sklearn для воспроизводимой проверки."""
        stabilized = code
        for func_name in cls._SKLEARN_STABILIZE_FUNCS:
            pattern = rf"{func_name}\(([^)]*)\)"

            def _replace(match: re.Match, name: str = func_name) -> str:
                return cls._inject_random_state(name, match.group(1))

            stabilized = re.sub(pattern, _replace, stabilized)
        return stabilized

    @classmethod
    def _collect_assigned_names(cls, code: str) -> List[str]:
        names: List[str] = []
        for line in code.splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            if stripped.startswith(
                (
                    "import ",
                    "from ",
                    "def ",
                    "class ",
                    "for ",
                    "while ",
                    "if ",
                    "elif ",
                    "else:",
                    "return ",
                    "print(",
                )
            ):
                continue
            match = re.match(r"^([A-Za-z_]\w*(?:\s*,\s*[A-Za-z_]\w*)*)\s*=", stripped)
            if not match:
                continue
            for part in match.group(1).split(","):
                names.append(part.strip())
        return names

    @classmethod
    def infer_printed_variables(cls, solution_code: str) -> List[str]:
        variables: List[str] = []
        for line in solution_code.splitlines():
            stripped = line.strip()
            if not stripped.startswith("print("):
                continue
            match = re.search(r"print\([^)]*,\s*([A-Za-z_]\w*)\s*\)", stripped)
            if match:
                variables.append(match.group(1))
            else:
                match = re.search(r"print\(([A-Za-z_]\w*)\s*\)", stripped)
                if match:
                    variables.append(match.group(1))
        return variables

    @classmethod
    def _is_sklearn_estimator(cls, value: Any) -> bool:
        return (
            value is not None
            and hasattr(value, "fit")
            and hasattr(value, "predict")
            and not isinstance(value, type)
        )

    @classmethod
    def _looks_like_result_variable(cls, name: str, value: Any) -> bool:
        result_name_patterns = (
            r".*_pred$",
            r"^predictions",
            r"^clusters$",
            r".*_labels$",
            r"^cluster_labels$",
            r"^semi_pred$",
            r"^regression_pred$",
            r"^my_list$",
        )
        if any(re.match(pattern, name) for pattern in result_name_patterns):
            return True
        try:
            import numpy as np

            if isinstance(value, (np.ndarray, list, tuple, dict, str, int, float, bool)):
                return True
        except Exception:
            pass
        return False

    @classmethod
    def infer_check_variables(
        cls,
        task_data: Dict[str, Any],
        solution_code: str,
        local_vars: Dict[str, Any],
    ) -> List[str]:
        """Определяет переменные для структурной проверки."""
        explicit = task_data.get("check_variables") or []
        if isinstance(explicit, str):
            explicit = [explicit] if explicit else []
        if task_data.get("check_variable"):
            explicit.append(task_data["check_variable"])

        candidates: List[str] = []
        for name in explicit:
            if name and name in local_vars and name not in candidates:
                candidates.append(name)
        if candidates:
            return candidates

        for name in cls.infer_printed_variables(solution_code):
            if name and name in local_vars and name not in candidates:
                if cls._looks_like_result_variable(name, local_vars[name]):
                    candidates.append(name)

        if candidates:
            return candidates

        assigned = cls._collect_assigned_names(solution_code)
        for name in reversed(assigned):
            if name not in local_vars or name in candidates:
                continue
            value = local_vars[name]
            if name in {"X", "y", "X_train", "X_test", "y_train", "y_test", "data", "target"}:
                continue
            if cls._looks_like_result_variable(name, value) and not cls._is_sklearn_estimator(value):
                candidates.insert(0, name)
            elif cls._is_sklearn_estimator(value) and not candidates:
                candidates.insert(0, name)
        return candidates

    @classmethod
    def format_expected_value_for_criterion(cls, value: Any) -> str:
        """Форматирует ожидаемое значение переменной для показа студенту."""
        if value is None:
            return "None"
        if cls._is_sklearn_estimator(value):
            return f"обученная модель {type(value).__name__}"
        if isinstance(value, str):
            return repr(value)
        if isinstance(value, (bool, int, float)):
            return repr(value)
        if isinstance(value, dict):
            text = repr(value)
            if len(text) <= 140:
                return text
            return f"словарь с ключами {list(value.keys())}"
        if isinstance(value, (list, tuple)):
            text = repr(value)
            if len(text) <= 140:
                return text
            return f"{type(value).__name__} из {len(value)} элементов"
        try:
            import numpy as np

            if isinstance(value, np.ndarray):
                return cls.serialize_value_for_llm(value, max_items=8)
        except Exception:
            pass
        text = repr(value)
        if len(text) > 140:
            return text[:140] + "..."
        return text

    @classmethod
    def build_validation_criteria(
        cls,
        task_data: Dict[str, Any],
        check_variables: List[str],
        expected_vars: Optional[Dict[str, Any]] = None,
    ) -> List[str]:
        """Формирует понятные критерии проверки с конкретными ожидаемыми значениями."""
        criteria: List[str] = []
        expected_vars = expected_vars or {}

        condition_rule = (task_data.get("condition_rule") or "").strip()
        if condition_rule:
            criteria.append(f"Условие: {condition_rule}")

        for var_name in check_variables:
            if var_name in expected_vars:
                expected_text = cls.format_expected_value_for_criterion(
                    expected_vars[var_name]
                )
                criteria.append(
                    f"Переменная `{var_name}` должна быть равна: {expected_text}"
                )
            else:
                criteria.append(
                    f"Переменная `{var_name}` должна быть создана и соответствовать "
                    "шагам задания."
                )

        output_format = (task_data.get("output_format") or "").strip()
        if output_format:
            criteria.append(f"Формат вывода print: {output_format}")

        expected_output = (task_data.get("expected_output") or "").strip()
        if expected_output and not output_format:
            preview = expected_output if len(expected_output) <= 200 else expected_output[:200] + "..."
            criteria.append(f"Ожидаемый вывод программы: {preview}")

        steps = task_data.get("student_steps") or []
        if steps and not check_variables:
            criteria.extend(steps)

        if not criteria:
            criteria.append("Код должен выполняться без ошибок и соответствовать шагам задания.")

        criteria.append(
            "Проверка выполняется нейросетью по смыслу решения: "
            "важна логика и корректность результата, а не дословное совпадение текста."
        )
        return criteria

    @classmethod
    def serialize_value_for_llm(cls, value: Any, max_items: int = 24) -> str:
        """Сериализует значение переменной для передачи в промпт проверки."""
        if value is None:
            return "None"
        try:
            import numpy as np

            if isinstance(value, np.ndarray):
                flat = value.ravel()
                if flat.size <= max_items:
                    return f"ndarray shape={value.shape}, values={value.tolist()}"
                preview = flat[:max_items].tolist()
                return (
                    f"ndarray shape={value.shape}, dtype={value.dtype}, "
                    f"preview={preview}, ... (всего {flat.size} элементов)"
                )
        except Exception:
            pass

        if isinstance(value, (list, tuple)):
            if len(value) <= max_items:
                return repr(value)
            return f"{type(value).__name__} len={len(value)}, head={repr(value[:max_items])}"

        if cls._is_sklearn_estimator(value):
            parts = [f"{type(value).__name__}("]
            for attr in (
                "n_features_in_",
                "n_clusters",
                "classes_",
                "n_iter_",
                "labels_",
                "coef_",
                "intercept_",
            ):
                if hasattr(value, attr):
                    attr_val = getattr(value, attr)
                    parts.append(f"  {attr}={cls.serialize_value_for_llm(attr_val, max_items=8)}")
            parts.append(")")
            return "\n".join(parts)

        text = repr(value)
        if len(text) > 800:
            return text[:800] + "..."
        return text

    @classmethod
    def build_variables_snapshot(
        cls,
        local_vars: Dict[str, Any],
        variable_names: List[str],
    ) -> Dict[str, str]:
        """Формирует снимок переменных для LLM-проверки."""
        snapshot: Dict[str, str] = {}
        for name in variable_names:
            if name in local_vars:
                snapshot[name] = cls.serialize_value_for_llm(local_vars[name])
            else:
                snapshot[name] = "<переменная не создана>"
        return snapshot

    @classmethod
    def extract_student_code_part(cls, task_code: str, user_code: str) -> str:
        """Выделяет код, написанный студентом (без дублирования starter-кода)."""
        starter = (task_code or "").strip()
        editor = (user_code or "").strip()
        if not starter:
            return editor
        if editor == starter:
            return ""
        if editor.startswith(starter):
            student_part = editor[len(starter) :].strip()
            return student_part or editor
        return editor

    def build_llm_validation_prompt(
        self,
        task_data: Dict[str, Any],
        student_code: str,
        student_stdout: str,
        student_vars: Dict[str, Any],
        reference_stdout: str,
        reference_vars: Dict[str, Any],
        execution_error: Optional[str] = None,
    ) -> str:
        """Строит промпт для интеллектуальной проверки решения студента."""
        check_variables = task_data.get("check_variables") or []
        if not check_variables and task_data.get("check_variable"):
            check_variables = [task_data["check_variable"]]

        student_part = self.extract_student_code_part(
            task_data.get("task_code", ""), student_code
        )
        steps = task_data.get("student_steps") or []
        criteria = task_data.get("validation_criteria") or []

        return f"""
Проверь решение студента по контрольному заданию.

=== ЗАДАНИЕ ===
Название: {task_data.get("title", "")}
Описание:
{task_data.get("description", "")}

Шаги для студента:
{json.dumps(steps, ensure_ascii=False, indent=2)}

Критерии проверки:
{json.dumps(criteria, ensure_ascii=False, indent=2)}

Проверяемые переменные (если заданы): {json.dumps(check_variables, ensure_ascii=False)}
Формат вывода (если задан): {task_data.get("output_format") or "не указан"}

=== ЭТАЛОННОЕ РЕШЕНИЕ (solution_code) ===
{task_data.get("solution_code", "")}

=== ВЫПОЛНЕНИЕ ЭТАЛОНА ===
stdout:
{reference_stdout or "<пусто>"}

переменные:
{json.dumps(self.build_variables_snapshot(reference_vars, check_variables), ensure_ascii=False, indent=2)}

=== КОД СТУДЕНТА ===
Полный код в редакторе:
{student_code}

Код, написанный студентом (без starter task_code):
{student_part or "<студент не дописал код>"}

=== ВЫПОЛНЕНИЕ СТУДЕНТА ===
ошибка выполнения: {execution_error or "нет"}

stdout:
{student_stdout or "<пусто>"}

переменные:
{json.dumps(self.build_variables_snapshot(student_vars, check_variables), ensure_ascii=False, indent=2)}

=== ПРАВИЛА ОЦЕНКИ ===
1. is_correct=true ТОЛЬКО если решение полностью выполняет ВСЕ шаги задания.
2. Оценивай СМЫСЛ и КОРРЕКТНОСТЬ, а не дословное совпадение print/пробелов.
3. Для sklearn/ML при random_state=42 численные результаты должны быть эквивалентны эталону.
4. Если в задании указаны конкретные имена переменных — они обязательны.
5. Если код не выполняется или студент не дописал решение — is_correct=false.
6. Неверный алгоритм, не те данные, пропущенный шаг — is_correct=false.
7. feedback — кратко и по-русски, конструктивно; failure_reason — конкретная причина отказа.

Верни ТОЛЬКО JSON:
{{
  "is_correct": true,
  "score": 100,
  "feedback": "краткая обратная связь студенту",
  "failure_reason": ""
}}
"""

    @staticmethod
    def parse_llm_validation_response(response: str) -> Dict[str, Any]:
        """Парсит JSON-ответ LLM-проверки."""
        start_idx = response.find("{")
        end_idx = response.rfind("}") + 1
        if start_idx == -1 or end_idx == 0:
            raise ValueError("JSON не найден в ответе проверки")
        data = json.loads(response[start_idx:end_idx])
        return {
            "is_correct": bool(data.get("is_correct", False)),
            "score": int(data.get("score", 0)),
            "feedback": str(data.get("feedback", "")).strip(),
            "failure_reason": str(data.get("failure_reason", "")).strip(),
        }

    def validate_solution_with_llm(
        self,
        task_data: Dict[str, Any],
        student_code: str,
        student_stdout: str,
        student_vars: Dict[str, Any],
        reference_stdout: str,
        reference_vars: Dict[str, Any],
        execution_error: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Проверяет решение студента через LLM."""
        prompt = self.build_llm_validation_prompt(
            task_data=task_data,
            student_code=student_code,
            student_stdout=student_stdout,
            student_vars=student_vars,
            reference_stdout=reference_stdout,
            reference_vars=reference_vars,
            execution_error=execution_error,
        )
        messages = [
            {
                "role": "system",
                "content": (
                    "Ты — строгий, но справедливый преподаватель Python и машинного обучения. "
                    "Проверяешь контрольные задания по смыслу решения. "
                    "Отвечай только валидным JSON на русском языке в полях feedback и failure_reason."
                ),
            },
            {"role": "user", "content": prompt},
        ]
        response = self.make_api_request_with_retries(
            messages=messages,
            temperature=0.1,
            max_tokens=1200,
            response_format={"type": "json_object"},
            model=self.validation_model,
        )
        result = self.parse_llm_validation_response(response)
        result["validation_method"] = "llm"
        return result

    def _validate_structured_fallback(
        self,
        materialized: Dict[str, Any],
        user_code: str,
        task_code: str,
        validation_mode: str,
        check_variables: List[str],
        actual_output: str,
        local_vars: Dict[str, Any],
        expected_output: str,
    ) -> Tuple[bool, str, str]:
        """Резервная проверка без LLM (при недоступности API)."""
        failure_reason = ""
        is_correct = False
        solution_code = materialized.get("solution_code", "")

        if validation_mode in {"structured", "llm"} and check_variables and solution_code:
            matched, reason = self.compare_structured_variables(
                solution_code,
                user_code,
                task_code,
                check_variables,
            )
            is_correct = matched
            failure_reason = reason or ""
        elif validation_mode in {"variable", "both"} and materialized.get("check_variable"):
            var_name = materialized["check_variable"]
            actual_var = local_vars.get(var_name)
            expected_val = materialized.get("expected_variable_value")
            is_correct = (
                values_equal(actual_var, expected_val)
                if expected_val is not None
                else actual_var is not None
            )
            if not is_correct:
                failure_reason = f"Неверное значение переменной `{var_name}`"
        elif expected_output:
            is_correct = stdout_outputs_equal(actual_output, expected_output.strip())
            if not is_correct:
                failure_reason = "Вывод программы не совпадает с ожидаемым"
        else:
            is_correct = True

        feedback = (
            "Решение принято."
            if is_correct
            else (failure_reason or "Решение не принято.")
        )
        return is_correct, failure_reason, feedback

    def compare_structured_variables(
        self,
        solution_code: str,
        user_code: str,
        task_code: str,
        check_variables: List[str],
    ) -> Tuple[bool, Optional[str]]:
        """Сравнивает ключевые переменные эталона и решения студента."""
        if not check_variables:
            return False, "Не заданы переменные для проверки"

        stable_task = self.stabilize_sklearn_code(task_code)
        stable_solution = self.stabilize_sklearn_code(solution_code)
        stable_user = self.stabilize_sklearn_code(
            self.resolve_executable_code(stable_task, user_code)
        )

        try:
            _, solution_vars = self.execute_code(stable_solution)
            _, user_vars = self.execute_code(stable_user)
        except Exception as exc:
            return False, f"Ошибка выполнения: {exc}"

        for var_name in check_variables:
            if var_name not in user_vars:
                return False, f"Не найдена переменная `{var_name}`"
            if not values_equal(user_vars.get(var_name), solution_vars.get(var_name)):
                return False, f"Неверное значение переменной `{var_name}`"
        return True, None

    def materialize_validation_metadata(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Выполняет solution_code и вычисляет параметры проверки."""
        task_data["task_code"] = self.stabilize_sklearn_code(
            sanitize_example_code((task_data.get("task_code") or "").strip())
        )
        solution_code = self.stabilize_sklearn_code(
            sanitize_example_code((task_data.get("solution_code") or "").strip())
        )
        task_data["solution_code"] = solution_code

        if not solution_code:
            return task_data

        try:
            actual_output, local_vars = self.execute_code(solution_code)
        except Exception as exc:
            self.logger.warning("Не удалось выполнить solution_code: %s", exc)
            task_data["is_needed"] = False
            task_data["skip_reason"] = f"Эталонное решение не выполняется: {exc}"
            return task_data

        if actual_output:
            task_data["expected_output"] = actual_output

        check_variables = self.infer_check_variables(task_data, solution_code, local_vars)
        task_data["check_variables"] = check_variables

        validation_mode = (task_data.get("validation_mode") or "").strip().lower()
        if validation_mode in {"", "both", "variable", "stdout", "structured"}:
            validation_mode = "llm"

        if check_variables:
            task_data["check_variable"] = check_variables[-1]
            task_data["expected_variable_value"] = local_vars.get(check_variables[-1])
            task_data["expected_variable_values"] = {
                name: local_vars.get(name) for name in check_variables
            }
        else:
            task_data.pop("check_variable", None)
            task_data.pop("expected_variable_value", None)
            task_data.pop("expected_variable_values", None)

        task_data["validation_mode"] = validation_mode
        task_data["validation_criteria"] = self.build_validation_criteria(
            task_data,
            check_variables,
            expected_vars={
                name: local_vars[name]
                for name in check_variables
                if name in local_vars
            },
        )
        return task_data

    def _determine_lesson_subject(
        self,
        course_context: Optional[Dict[str, Any]],
        lesson_content: str,
        lesson_data: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Определяет предметную область по текущему уроку (не по названию всего курса)."""
        lesson_data = lesson_data or {}
        lesson_title = lesson_data.get("title", "").lower()
        lesson_description = lesson_data.get("description", "").lower()
        topic_title = ""
        if course_context and isinstance(course_context, dict):
            topic_title = (course_context.get("topic_title") or "").lower()

        keywords = lesson_data.get("keywords", [])
        if isinstance(keywords, list):
            keywords_str = " ".join(str(k) for k in keywords).lower()
        else:
            keywords_str = str(keywords or "").lower()

        lesson_signals = " ".join(
            [lesson_title, lesson_description, topic_title, keywords_str]
        )

        def _match_subject(text: str) -> Optional[str]:
            text = text.lower()
            ml_markers = (
                "sklearn",
                "scikit",
                "tensorflow",
                "keras",
                "нейрон",
                "классификац",
                "регресс",
                "машинн",  # машинное / машинного обучения
                "machine learning",
                "mnist",
                "iris",
                "библиотек",
            )
            data_markers = (
                "pandas",
                "numpy",
                "matplotlib",
                "dataframe",
                "анализ данных",
                "data analysis",
                "визуализац",
            )
            web_markers = ("flask", "django", "fastapi", "веб", "web", "api", "сайт")
            basics_markers = (
                "основы python",
                "синтаксис",
                "переменн",
                "цикл",
                "список",
                "словар",
                "функци",
                "условн",
                "тип данных",
            )

            if any(m in text for m in ml_markers):
                return "машинное обучение с Python"
            if any(m in text for m in data_markers):
                return "анализ данных с Python"
            if any(m in text for m in web_markers):
                return "веб-разработка на Python"
            if any(m in text for m in basics_markers):
                return "программирование на Python"
            return None

        subject = _match_subject(lesson_signals)
        if subject:
            return subject

        subject = _match_subject(lesson_content or "")
        if subject:
            return subject

        if course_context and isinstance(course_context, dict):
            course_title = (course_context.get("course_title") or "").lower()
            subject = _match_subject(course_title)
            if subject:
                return subject
            if "финанс" in course_title:
                return "программирование на Python для финансов"

        return "программирование на Python"

    @staticmethod
    def _is_basics_shaped_task(task_data: Dict[str, Any]) -> bool:
        """True, если задание по форме — «Основы Python» (age/status/арифметика)."""
        combined = " ".join(
            [
                task_data.get("title") or "",
                task_data.get("description") or "",
                task_data.get("task_code") or "",
                task_data.get("solution_code") or "",
                " ".join(task_data.get("student_steps") or []),
                task_data.get("condition_rule") or "",
            ]
        ).lower()
        basics_signals = (
            "совершеннолет",
            "несовершеннолет",
            "age = ",
            "age=",
            "status = ",
            "вычислите a = 10",
            "переменные и типы",
            "тип данных",
        )
        ml_signals = (
            "sklearn",
            "scikit",
            "tensorflow",
            "keras",
            "load_iris",
            "logisticregression",
            "mlpclassifier",
            "fit(",
            "predict(",
            "train_test_split",
            "pandas",
            "dataframe",
        )
        if any(m in combined for m in ml_signals):
            return False
        return any(m in combined for m in basics_signals)

    def _task_matches_subject(
        self, task_data: Dict[str, Any], course_subject: str
    ) -> bool:
        """Проверяет, что задание соответствует предметной области урока."""
        if "машинное обучение" in course_subject:
            return not self._is_basics_shaped_task(task_data)
        return True

    def generate_control_task(
        self,
        lesson_data: Dict[str, Any],
        lesson_content: str,
        communication_style: str = "friendly",
        course_context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        try:
            lesson_title = lesson_data.get("title", "")
            content_for_prompt = self.prepare_lesson_text_for_analysis(
                lesson_content,
                course_context=course_context,
                max_chars=6000,
                lesson_title=lesson_title,
            )
            course_subject = self._determine_lesson_subject(
                course_context, content_for_prompt, lesson_data
            )

            prompt = self._build_control_task_prompt(
                lesson_data,
                content_for_prompt,
                communication_style,
                course_context,
                course_subject,
            )
            messages = [
                {
                    "role": "system",
                    "content": (
                        f"Ты — преподаватель {course_subject}. "
                        "Создавай однозначные контрольные задания СТРОГО по материалу "
                        f"урока «{lesson_title}». Ответ — только JSON."
                    ),
                },
                {"role": "user", "content": prompt},
            ]
            response = self.make_api_request(
                messages=messages,
                temperature=0.3,
                max_tokens=2000,
                response_format={"type": "json_object"},
            )
            task_data = self._parse_control_task_response(response, lesson_data)

            if not self._task_matches_subject(task_data, course_subject):
                self.logger.warning(
                    "Контрольное задание не по теме урока (%s), повторная генерация",
                    course_subject,
                )
                strict_prompt = (
                    prompt
                    + f"\n\nПОВТОР: предыдущий ответ был про «Основы Python», "
                    f"а нужно задание по «{course_subject}» и уроку «{lesson_title}». "
                    "Используй библиотеки и концепции из lesson_content (sklearn, load_iris и т.д.). "
                    "ЗАПРЕЩЕНО: age, status, совершеннолетний, a=10+b."
                )
                response = self.make_api_request(
                    messages=[
                        messages[0],
                        {"role": "user", "content": strict_prompt},
                    ],
                    temperature=0.2,
                    max_tokens=2000,
                    response_format={"type": "json_object"},
                )
                task_data = self._parse_control_task_response(response, lesson_data)

            return task_data
        except Exception as e:
            self.logger.error("Ошибка при генерации контрольного задания: %s", e)
            return {
                "title": "Ошибка генерации",
                "description": f"Не удалось сгенерировать задание: {e}",
                "task_code": "",
                "expected_output": "",
                "solution_code": "",
                "is_needed": False,
                "skip_reason": f"Ошибка генерации: {e}",
            }

    def _build_control_task_prompt(
        self,
        lesson_data: Dict[str, Any],
        lesson_content: str,
        communication_style: str,
        course_context: Optional[Dict[str, Any]] = None,
        course_subject: str = "программирование на Python",
    ) -> str:
        lesson_title = lesson_data.get("title", "")
        lesson_description = lesson_data.get("description", "")

        if "машинное обучение" in course_subject:
            subject_rules = """
=== ПРАВИЛА ДЛЯ ML-УРОКА ===
- Задание должно использовать sklearn / TensorFlow / Keras — то, что разбирается в уроке.
- Предпочитай load_iris() вместо make_classification с малым n_features.
- random_state=42 для всех генераторов данных и моделей.
- Студент дописывает fit(), predict() или score() — не «age/status» из основ Python.
- ЗАПРЕЩЕНО задания про переменные, if age >= 18, арифметику a=10+b без ML-библиотек.
"""
            example_block = """
ПРИМЕР корректного ML-задания:
- task_code: from sklearn.datasets import load_iris + train_test_split + данные + "# Ваш код здесь"
- student_steps: «Обучите LogisticRegression на X_train/y_train», «Вычислите accuracy на X_test»
- check_variables: ["model", "accuracy"] или ["accuracy"]
"""
        elif "анализ данных" in course_subject:
            subject_rules = """
=== ПРАВИЛА ДЛЯ АНАЛИЗА ДАННЫХ ===
- Используй pandas/numpy/matplotlib из урока.
- Данные задавай в task_code (словари, списки, DataFrame.from_dict) — без read_csv.
"""
            example_block = """
ПРИМЕР: task_code создаёт DataFrame, студент считает mean/sum или строит простую агрегацию.
"""
        else:
            subject_rules = ""
            example_block = """
ПРИМЕР корректного задания (переменные + условие):
- task_code содержит: age = 17, name = "Анна"
- student_steps: «Вычислите a = 10 + 5 и b = a * 2», «По правилу condition_rule создайте status»
- condition_rule: «если age >= 18 → status = "совершеннолетний", иначе → status = "несовершеннолетний"»
- check_variables: ["a", "b", "status"]
"""

        return f"""
Создай ОДНОЗНАЧНОЕ контрольное задание СТРОГО по lesson_content урока «{lesson_title}».
Предметная область: {course_subject}. Не используй темы из других модулей курса.

НАЗВАНИЕ УРОКА: {lesson_title}
ОПИСАНИЕ УРОКА: {lesson_description}

lesson_content:
{lesson_content}
{subject_rules}

ГЛАВНОЕ ПРАВИЛО: студент должен понять задание с ОДНОГО прочтения и решить ЕДИНСТВЕННЫМ способом.

=== ИСХОДНЫЕ ДАННЫЕ (task_code) ===
- ВСЕ константы и входные данные (age, name, numbers, X, y, списки, словари) — ТОЛЬКО в task_code.
- НЕ проси в description/student_steps «создайте age = 17» — данные уже в task_code.
- В student_steps пиши: «используйте переменную age из task_code», «допишите код после # Ваш код здесь».
- task_code: импорты + данные + комментарий "# Ваш код здесь".
- Без fit(), predict(), print(), plt.show() в task_code.
- ВСЕ генераторы случайных данных: random_state=42.

=== УСЛОВИЯ (if/elif/else) ===
Если задание включает условие — ОБЯЗАТЕЛЬНО явно укажи:
1. Порог сравнения: «если age >= 18», «если score > 50» (конкретное число/знак).
2. Значение результата для КАЖДОЙ ветки: «status = "совершеннолетний"» / «status = "несовершеннолетний"».
3. age и другие данные для условия — уже заданы в task_code (не «в воздухе»).
4. Поле condition_rule — одной строкой для студента, например:
   «если age >= 18 → status = "совершеннолетний", иначе → status = "несовершеннолетний"».

=== ШАГИ И ОПИСАНИЕ ===
- Каждый шаг — конкретное действие: «вычислите a = 10 + 5», «создайте status по правилу выше».
- Не используй «и т.д.», «например», «на ваше усмотрение», «подобным образом».
- Если нужен print — укажи ТОЧНЫЕ подписи в output_format.
- Имена переменных в задании и в solution_code должны совпадать.
- check_variables — только переменные, которые создаёт/изменяет студент (результаты).

=== solution_code ===
- Полное решение = task_code + код студента (без дублирования starter-данных).
- Должно выполняться без ошибок и давать однозначный результат.

validation_mode: всегда "llm".

Если в lesson_content нет практики с кодом — is_needed: false.

Формат JSON:
{{
  "title": "...",
  "description": "Краткое описание задания для студента",
  "student_steps": [
    "Шаг 1: ...",
    "Шаг 2: ..."
  ],
  "condition_rule": "если age >= 18 → status = \"совершеннолетний\", иначе → \"несовершеннолетний\" (или \"\", если условий нет)",
  "task_code": "age = 17\nname = \"Анна\"\n# Ваш код здесь",
  "solution_code": "полное решение",
  "validation_mode": "llm",
  "check_variables": ["a", "b", "status"],
  "output_format": "print('a:', a) print('status:', status) — если нужен вывод",
  "hints": ["..."],
  "is_needed": true,
  "skip_reason": ""
}}

{example_block}

Верни только JSON.
"""

    def _parse_control_task_response(
        self, response: str, lesson_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        try:
            start_idx = response.find("{")
            end_idx = response.rfind("}") + 1
            if start_idx == -1 or end_idx == 0:
                raise ValueError("JSON не найден в ответе")

            task_data = json.loads(response[start_idx:end_idx])
            for field in (
                "title",
                "description",
                "task_code",
                "expected_output",
                "solution_code",
            ):
                task_data.setdefault(field, "")

            task_data.setdefault("hints", [])
            task_data.setdefault("student_steps", [])
            task_data.setdefault("validation_mode", "llm")
            task_data.setdefault("check_variables", [])
            task_data.setdefault("check_variable", "")
            task_data.setdefault("output_format", "")
            task_data.setdefault("validation_criteria", [])
            task_data.setdefault("condition_rule", "")

            if task_data.get("is_needed", True) and task_data.get("solution_code", "").strip():
                task_data = self.materialize_validation_metadata(task_data)

            return task_data
        except Exception as e:
            self.logger.error("Ошибка при парсинге ответа: %s", e)
            lesson_title = (lesson_data or {}).get("title", "Задание")
            return self._create_fallback_task(lesson_title)

    def _create_fallback_task(self, lesson_title: str) -> Dict[str, Any]:
        self.logger.warning(
            "Сработал fallback для контрольного задания по теме: %s", lesson_title
        )
        return {
            "is_needed": False,
            "title": f"Задание по теме '{lesson_title}'",
            "description": "Не удалось сгенерировать задание автоматически.",
            "task_code": "",
            "expected_output": "",
            "solution_code": "",
            "hints": [],
            "skip_reason": "Ошибка генерации задания",
        }

    def validate_task_execution(
        self,
        user_code: str,
        task_data: Optional[Dict[str, Any]] = None,
        expected_output: str = "",
        check_variable: Optional[str] = None,
        expected_variable_value: Optional[Any] = None,
        task_code: str = "",
    ) -> Dict[str, Any]:
        """Проверяет решение студента через LLM; structured — только fallback при сбое API."""
        task_data = task_data or {}
        task_code = task_data.get("task_code", task_code)
        solution_code = task_data.get("solution_code", "")

        materialized = dict(task_data)
        if solution_code:
            materialized = self.materialize_validation_metadata(dict(task_data))

        validation_mode = materialized.get("validation_mode", "llm")
        check_variables = materialized.get("check_variables") or []
        expected_output = materialized.get("expected_output", expected_output)

        student_stdout = ""
        local_vars: Dict[str, Any] = {}
        execution_error: Optional[str] = None

        try:
            full_code = self.resolve_executable_code(task_code, user_code)
            student_stdout, local_vars = self.execute_code(
                self.stabilize_sklearn_code(full_code)
            )
        except Exception as exc:
            execution_error = str(exc)
            student_stdout = ""

        reference_stdout = ""
        reference_vars: Dict[str, Any] = {}
        if solution_code:
            try:
                reference_stdout, reference_vars = self.execute_code(
                    self.stabilize_sklearn_code(materialized["solution_code"])
                )
            except Exception as exc:
                self.logger.warning("Эталонное решение не выполнилось: %s", exc)

        is_correct = False
        failure_reason = execution_error or ""
        feedback = ""
        validation_method = "llm"

        if getattr(self, "client", None):
            try:
                llm_result = self.validate_solution_with_llm(
                    task_data=materialized,
                    student_code=user_code,
                    student_stdout=student_stdout,
                    student_vars=local_vars,
                    reference_stdout=reference_stdout,
                    reference_vars=reference_vars,
                    execution_error=execution_error,
                )
                is_correct = llm_result["is_correct"]
                failure_reason = llm_result.get("failure_reason") or failure_reason
                feedback = llm_result.get("feedback", "")
                validation_method = "llm"
            except Exception as exc:
                self.logger.error("LLM-проверка недоступна, fallback: %s", exc)
                validation_method = "structured_fallback"
                is_correct, failure_reason, feedback = self._validate_structured_fallback(
                    materialized,
                    user_code,
                    task_code,
                    validation_mode,
                    check_variables,
                    student_stdout,
                    local_vars,
                    expected_output,
                )
                feedback = (
                    f"{feedback} (нейросеть временно недоступна, применена резервная проверка)"
                )
        else:
            validation_method = "structured_fallback"
            is_correct, failure_reason, feedback = self._validate_structured_fallback(
                materialized,
                user_code,
                task_code,
                validation_mode,
                check_variables,
                student_stdout,
                local_vars,
                expected_output,
            )

        return {
            "is_correct": is_correct,
            "actual_output": student_stdout,
            "actual_variable": local_vars.get(materialized.get("check_variable", "")),
            "error_message": failure_reason,
            "failure_reason": failure_reason,
            "feedback": feedback,
            "validation_method": validation_method,
        }
