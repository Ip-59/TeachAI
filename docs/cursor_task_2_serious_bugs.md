# Задача для Cursor: пакет 2 — серьёзные баги и надёжность (этапы 2а и 2б)

Скопируй файл целиком в чат Cursor. Исполнитель — Cursor-агент в проекте TeachAI на локальном компьютере. Работа идёт от коммита **`5b6669b`** (пакет 1: автотесты). Все правки ниже **проверены в прототипе** на копии этого коммита (Linux, Python 3.13): после обоих этапов набор даёт `104 passed, 1 skipped, 1 deselected, 13 xfailed` вместо `74 passed, 1 skipped, 1 deselected, 26 xfailed`. Ни один тест, кроме перечисленных ниже, не поменял результат.

Все номера строк даны по `5b6669b`. Диффы в тексте тоже сняты против `5b6669b`; применяй их как есть (вручную или `git apply`). Если контекст диффа не совпал с файлом, **остановись и напиши, что именно не совпало** — не подгоняй.

## 0. Жёсткие правила

1. **Менять можно только то, что описано ниже.** В этом пакете код приложения править разрешено, но только в указанных местах. Никакой «заодно» переделки соседнего кода, форматирования и переименований.
2. **Не трогать области решений D1–D9** (они в пакетах 3 и 4), даже если рядом лежит очевидная правка. Список «что не трогать» дан в п. 1. Если сомневаешься, относится ли строка к D1–D9, не меняй и спроси меня в отчёте.
3. **Два этапа — два коммита, два пуша.** Этап 2а (разделы A) и этап 2б (разделы B) независимы. После каждого этапа: полный прогон, отчёт мне, **`git push` только по моей команде** (я проверяю этап до пуша следующего). Без моей команды ничего не коммитить и не пушить.
4. **Какой venv.** Работай в venv **той машины, на которой сидишь**: `venv_W_L` на работе, `venv_H_L` дома. Новые зависимости не нужны; если всё-таки понадобятся, добавляй только в `requirements-dev.txt` и сообщай мне.
5. **Ключ и сеть.** Реальный `OPENAI_API_KEY` не печатать, не читать из `.env`, не копировать в тесты и отчёты. Тесты используют фальшивый `sk-test-not-a-real-key`, сети нет.
6. **Правило xfail из пакета 1 действует.** Когда баг исправлен, тест с `xfail(strict=True)` становится XPASS и краснеет. Тогда **маркер `xfail` снимается** (тест остаётся и теперь обязан проходить). Новых `xfail` не добавлять без согласования. Если после правки тест всё ещё падает по другой причине, это не повод снимать проверку: остановись и опиши.
7. **Реальные `data/`, `logs/`, `.env`, `.env.sample` не трогать.** Тесты работают во временных папках. После прогона `git status` не должен показывать изменённых `data/`, `.env`, `.env.sample`.
8. Порядок работы по каждому пункту: (а) прочитать пункт и нужные строки, (б) внести правку, (в) прогнать затронутые тесты, (г) только потом идти дальше. В конце этапа полный `python -m pytest -q -rx`.

## 1. Состав пакета и что НЕ входит

**Входит** (этап 2а — поведение интерфейса; этап 2б — надёжность данных и ответов модели):

| № | Сценарий | Суть | Этап |
|---|---|---|---|
| A1 | LSN-15 | после «Повторить урок» кнопка «← Назад к курсам» мертва (`engine=None`) | 2а |
| A2 | TST-02, TST-03 | в тесте заранее выбран 1-й вариант; пустой тест принимается | 2а |
| A3 | PRF-05 | верное КЗ дописывает фиктивную «попытку теста» | 2а |
| A4 | ZAP-01, KZ-18 | отладочные `print` в рабочем коде | 2а |
| A5 | LSN-06 | однострочный Python-пример отбрасывается | 2а |
| B1 | LLM-01 | 401 повторяется 3 раза и подаётся как «проблема прокси» | 2б |
| B2 | LLM-05 | ответ в обёртке ` ```json ` ломает план, тест, понятия, релевантность | 2б |
| B3 | LLM-06 | неверный индекс ответа в тесте даёт ошибку без повтора и с грязным текстом | 2б |
| B4 | ST-11, ST-12 | битый `state.json` затирается; запись `state.json` не атомарна | 2б |
| B5 | CRS-10 | id слота курса берётся из ответа модели, повторный старт плодит слот | 2б |
| B6 | ZAP-02 | `create_sample_env` затирает `.env.sample` | 2б |
| B7 | SEC-04 | `eval` на выводе программы | 2б |
| B8 | LEGACY | устаревшая проверка `relevance_prompt_checks.py` | 2б |

**Не входит, по сути решений (не трогать):**

| Что | Где | Куда отнесено |
|---|---|---|
| `completed_lessons` пополняется при показе урока (ST-01, PRF-03, PRF-04) | `learning_progress_manager.py:47-56`, `startup_dashboard.py:300-316` | **пакет 3, D1** (меняется само определение «пройден», нужен список `visited_lessons`) |
| эталонное решение показывается автоматически после ошибки (KZ-09) | `control_tasks_interface.py:482-490` | **пакет 3, D4** |
| «Повторить урок» удаляет лучший балл (TST-08), КЗ затирается пересдачей (KZ-12) | `learning_progress_manager.py:316-320`, `state_manager.py:368-372` | **пакет 3, D5** |
| понятия при открытии «Ключевых понятий» и при тесте >40% (LSN-04, D2) | `lesson_interaction.py:139,291`, `learning_progress_manager.py:119-122` | **пакет 3, D2** |
| `questions_count` для отклонённых вопросов (LSN-10) | `lesson_interaction.py:434-438` | **пакет 3, D8** |
| «Продолжить с текущей оценкой» (TST-09) | `assessment_results_handler.py` | **пакет 3, D3** |
| «вне области» не сохраняется (CRS-05) | `course_domain_ui.py:146` | **пакет 3, D7** |
| следующий урок «по позиции» (LSN-13) | `course_data_manager.py:177` | **пакет 3** (завязан на D1: «первый непройденный») |
| код ученика выполняется в процессе ядра (SEC-01, SEC-02, KZ-16) и `eval` в ячейках | `control_tasks_generator.py:64`, `cell_widget_base.py:145,176`, `interactive_cell_logic.py:27`, `examples_display.py:51`, `examples_validation.py:105` | **пакет 4, D9** |
| `from demo_cell_widget import …` в `cell_integration.py:14` (модуля нет) | `cell_integration.py:14-21` | **пакет 4, D9**, см. ниже |

Почему `demo_cell_widget` (ZAP-08) отложен в пакет 4. Модуля `demo_cell_widget.py` нет, поэтому `CELLS_AVAILABLE` всегда `False`, и `examples_display._create_code_widget` всегда берёт запасной вариант `_create_fallback_code_widget` (строка 68-79). Это **рабочий** путь, и именно он содержит `exec(code_area.value, {})` (`examples_display.py:51`), который D9 переведёт на дочерний процесс. «Починка» импорта включила бы другой, давно не запускавшийся путь (`create_demo_cell` из несуществующего модуля) и поменяла бы интерфейс примеров. Поэтому в пакете 2 эту область не трогаем; в пакете 4 вместе с D9 решим, удалить мёртвый путь или заменить.

## 2. Как применять диффы

Каждый раздел ниже содержит: **что не так** (с файлом и строкой), **как должно быть**, **правку** (дифф против `5b6669b`), **тесты** (что снять с `xfail`, что добавить), **чего не трогать**. Диффы проверены: после их применения тесты ведут себя, как сказано в разделе «Приёмка» этапа.


# ЭТАП 2а. Поведение интерфейса (A1–A5)

## A1. LSN-15: после «Повторить урок» кнопка «← Назад к курсам» не работает

**Что не так.** `LessonInterface` получает `engine` (`lesson_interface.py:47`), но создаёт свой `AssessmentInterface` без него (`lesson_interface.py:95-97`). Кнопки «Повторить урок» и «Вернуться к уроку» в `assessment_results_handler.py:324` и `assessment_interface.py:369` берут `engine=getattr(self, "engine", None)`, получают `None` и создают новый `LessonInterface` без `engine`. В нём «← Назад к курсам» не открывает дашборд. В `interface.py:84-86` `engine` проставляется только на «фасадный» `AssessmentInterface`, а не на тот, что живёт внутри `LessonInterface`.

**Как должно быть.** `engine` доходит до любого `LessonInterface`, созданного после «Повторить урок», «Вернуться к уроку» и «Следующий урок».

**Правка.** Один раз в `LessonInterface.__init__` проставить `engine` на внутренний `AssessmentInterface` и его `results_handler`; остальные места менять не надо — они уже читают `self.engine`.

```diff
--- a/lesson_interface.py
+++ b/lesson_interface.py
@@ -95,6 +95,12 @@
             self.assessment_interface = AssessmentInterface(
                 state_manager, assessment, system_logger, self
             )
+            # engine нужен кнопкам «Повторить урок», «Вернуться к уроку» и
+            # «← Назад к курсам»: новые LessonInterface наследуют его отсюда.
+            self.assessment_interface.engine = engine
+            results_handler = getattr(self.assessment_interface, "results_handler", None)
+            if results_handler is not None:
+                results_handler.engine = engine
             self.logger.info("AssessmentInterface успешно инициализирован")
         except Exception as e:
             self.logger.error(f"Ошибка при инициализации AssessmentInterface: {str(e)}")
```

**Тесты.** Снять `@pytest.mark.xfail(...)` с `test_LSN_15_back_to_courses_works_after_repeat_lesson` (`tests/scenario/test_flow_core.py`). Тест должен пройти без других правок.

**Не трогать:** `interface.py:84-86`, сам сценарий «Повторить урок» (`mark_lesson_incomplete`, удаление баллов — это D5, пакет 3).

## A2. TST-02, TST-03: в тесте заранее выбран первый вариант, пустой тест принимается

**Что не так.** `widgets.RadioButtons(options=[...])` без `value` выбирает первый вариант (`assessment_questions_ui.py:94-100`). Ученик, не ответивший ни на один вопрос, нажимает «Завершить тест» и получает оценку за «ответ 1» на всех вопросах. Проверка «ответьте на вопросы» в `assessment_results_handler.py:81-96` уже есть и работает на `None`, но `None` в этом виджете не бывает.

**Как должно быть.** Ни один вариант не выбран; «Завершить тест» без ответов показывает «Пожалуйста, ответьте на вопросы…» и ничего не сохраняет.

**Правка.**

```diff
--- a/assessment_questions_ui.py
+++ b/assessment_questions_ui.py
@@ -93,6 +93,7 @@
         options = question["options"]
         radio_buttons = widgets.RadioButtons(
             options=[(option, j + 1) for j, option in enumerate(options)],
+            value=None,  # без предвыбранного варианта: иначе неотвеченный вопрос засчитывается
             description="",
             disabled=False,
             layout=widgets.Layout(margin="4px 10px", width="100%"),
```

**Тесты.** Снять `xfail` с `test_TST_02_no_option_preselected` и `test_TST_03_empty_test_is_not_accepted` (`tests/scenario/test_flow_core.py`). Хелпер `answer_test` выбирает ответы через `.value = N`, на нём ничего не меняется.

**Не трогать:** обработчик `handle_answer_change` (он уже игнорирует `None`), `collect_answers_from_widgets`, `assessment_results_handler.py`.

## A3. PRF-05: верное КЗ дописывает фиктивную «попытку теста»

**Что не так.** В `ControlTasksInterface._save_task_result` при верном КЗ вызывается `sm.save_lesson_assessment(lesson_id, sm.get_lesson_score(lesson_id), True)` (`control_tasks_interface.py:535-539`). Это не результат теста, но функция дописывает запись в `lesson_attempts` с `is_passed=True` (при обойдённом тесте — с баллом 0) и пересчитывает `total_assessments` и средний балл. История попыток теста и статистика искажаются.

**Как должно быть.** Верное КЗ только сохраняет результат КЗ и завершает урок через `mark_lesson_complete_manually`; `lesson_attempts` остаётся историей настоящих тестов.

**Правка** (в том же дифф-блоке, что и A4, ниже, — хунк «@@ -532,11 +519,8 @@»).

**Тесты.** Снять `xfail` с `test_PRF_05_correct_task_does_not_add_test_attempt` (`tests/unit/test_progress_state.py`). Остальные тесты пакета (`KZ-*`, `ST-*`) должны остаться зелёными: завершение урока идёт через `mark_lesson_complete_manually`, оно баллов не требует.

**Не трогать:** `mark_lesson_complete_manually`, `mark_lesson_concepts_passed` (понятия при завершении — D2), `can_open_control_tasks`, определение «урок пройден» (D1).

## A4. ZAP-01, KZ-18: отладочные `print` в рабочем коде

**Что не так.**
- `interface.py:65-67`: при каждом запуске печатается «🔍 ОТЛАДКА UserInterface.__init__», в вывод ячейки попадает объект `assessment`.
- `course_plan_generator.py:74-110`: при каждом создании плана печатается структура плана (ключи разделов, тем, уроков); ещё `print` в строках 218 и 282.
- `control_tasks_interface.py:372-396`: при каждой проверке решения печатаются `[DIAGNOSTIC]`, **ожидаемое значение/вывод** задания (то есть правильный ответ) и код ученика.

**Как должно быть.** В выводе ячеек ничего из этого нет; при необходимости остаётся запись в лог на уровне `debug`, **без ожидаемых значений**.

**Правка.**

`interface.py`:

```diff
--- a/interface.py
+++ b/interface.py
@@ -62,9 +62,7 @@
 
         # Инициализируем специализированные интерфейсы
         try:
-            print(f"🔍 ОТЛАДКА UserInterface.__init__:")
-            print(f"🔍 assessment = {assessment}")
-            print(f"🔍 type(assessment) = {type(assessment)}")
+            self.logger.debug("UserInterface.__init__: assessment=%s", type(assessment).__name__)
 
             self.setup_interface = SetupInterface(
                 state_manager, content_generator, system_logger, assessment
```

`course_plan_generator.py` (только `print` → логгер; остальное в файле — этап 2б):

```diff
--- a/course_plan_generator.py
+++ b/course_plan_generator.py
@@ -71,38 +71,15 @@
 
             course_plan = json.loads(response_content)
 
-            # ОТЛАДКА: Выводим структуру плана для диагностики
-            print("🔍 ОТЛАДКА: Структура полученного плана курса:")
-            print(f"Ключи верхнего уровня: {list(course_plan.keys())}")
+            self.logger.debug("Ключи плана от LLM: %s", list(course_plan.keys()))
 
             # ВАЛИДАЦИЯ И ИСПРАВЛЕНИЕ структуры
             course_plan = self._validate_and_fix_course_plan(
                 course_plan, course_data, total_study_hours, lesson_duration_minutes
             )
 
-            if "sections" in course_plan:
-                print(f"✅ Количество разделов: {len(course_plan['sections'])}")
-                if course_plan["sections"]:
-                    first_section = course_plan["sections"][0]
-                    print(f"✅ Ключи первого раздела: {list(first_section.keys())}")
-                    if "topics" in first_section:
-                        print(
-                            f"✅ Количество тем в первом разделе: {len(first_section['topics'])}"
-                        )
-                        if first_section["topics"]:
-                            first_topic = first_section["topics"][0]
-                            print(f"✅ Ключи первой темы: {list(first_topic.keys())}")
-                            if "lessons" in first_topic:
-                                print(
-                                    f"✅ Количество уроков в первой теме: {len(first_topic['lessons'])}"
-                                )
-                                if first_topic["lessons"]:
-                                    first_lesson = first_topic["lessons"][0]
-                                    print(
-                                        f"✅ Ключи первого урока: {list(first_lesson.keys())}"
-                                    )
-            else:
-                print("❌ Проблема с валидацией плана курса!")
+            if not course_plan.get("sections"):
+                self.logger.warning("После валидации в плане нет разделов")
 
             self.logger.info("Учебный план успешно сгенерирован через OpenAI API")
             return course_plan
@@ -215,7 +192,7 @@
             if "sections" not in course_plan or not isinstance(
                 course_plan["sections"], list
             ):
-                print("⚠️ Создаем минимальную структуру разделов...")
+                self.logger.warning("Создаем минимальную структуру разделов")
                 course_plan["sections"] = self._create_minimal_sections(
                     course_data, lesson_duration_minutes
                 )
@@ -279,7 +256,7 @@
                         if "keywords" not in lesson:
                             lesson["keywords"] = ["основы", "практика"]
 
-            print("✅ План курса валидирован и исправлен")
+            self.logger.debug("План курса валидирован и исправлен")
             return course_plan
 
         except Exception as e:
```

`control_tasks_interface.py` (хунк «@@ -369,31 +369,18 @@» — это A4, хунк «@@ -532,11 +519,8 @@» — это A3):

```diff
--- a/control_tasks_interface.py
+++ b/control_tasks_interface.py
@@ -369,31 +369,18 @@
             check_variable = task_data.get("check_variable")
             expected_variable_value = task_data.get("expected_variable_value")
 
-            print(f"\n🔍 [DIAGNOSTIC] Проверка решения:")
-            print(f"check_variable: {check_variable}")
-            print(f"expected_variable_value: {expected_variable_value}")
-            print(f"expected_output: {task_data.get('expected_output', 'НЕТ')}")
-            print(f"user_code: {user_code[:200]}...")
-
             # Проверяем выполнение
             validation_result = self.tasks_generator.validate_task_execution(
                 user_code,
                 task_data=task_data,
             )
 
-            print(f"Результат валидации: {validation_result}")
-            
-            # Дополнительная диагностика
-            if check_variable:
-                print(f"🔍 [DIAGNOSTIC] Проверка переменной '{check_variable}':")
-                print(f"   Ожидаемое значение: {expected_variable_value}")
-                print(f"   Фактическое значение: {validation_result.get('actual_variable')}")
-                print(f"   Совпадение: {validation_result.get('is_correct')}")
-            else:
-                print(f"🔍 [DIAGNOSTIC] Проверка вывода:")
-                print(f"   Ожидаемый вывод: '{task_data.get('expected_output', '')}'")
-                print(f"   Фактический вывод: '{validation_result.get('actual_output', '')}'")
-                print(f"   Совпадение: {validation_result.get('actual_output') == task_data.get('expected_output', '').strip()}")
+            # Ожидаемые значения в лог не пишем: это ответ на задание.
+            self.logger.debug(
+                "Проверка КЗ: check_variable=%s, is_correct=%s",
+                check_variable,
+                validation_result.get("is_correct"),
+            )
 
             # Создаем все виджеты для отображения
             result_widgets = []
@@ -532,11 +519,8 @@
                 if is_correct:
                     sm = self.lesson_interface.state_manager
                     if sm.can_open_control_tasks(lesson_id):
-                        sm.save_lesson_assessment(
-                            lesson_id,
-                            sm.get_lesson_score(lesson_id),
-                            True,
-                        )
+                        # Не вызываем save_lesson_assessment: это дописывало бы
+                        # в lesson_attempts фиктивную «попытку теста».
                         sm.mark_lesson_complete_manually(lesson_id)
                         self.logger.info(
                             "Урок %s завершён: КЗ верно, тест пройден или обойдён",
```

После правки переменная `expected_variable_value` в `control_tasks_interface.py` может остаться неиспользуемой: если так, удали только эту строку присваивания (`expected_variable_value = task_data.get("expected_variable_value")`), больше ничего.

`print` в `engine.py` (сообщения об отсутствии `.env`, ключа, успешной инициализации) **не трогать**: это сообщения пользователю, а не отладка. `print` в `cell_widget_base.py`, `control_tasks_logger.py` — вне этапа.

**Тесты.**
1. Снять `xfail` с `test_ZAP_01_no_debug_output_on_start`.
2. В `tests/nbdriver.py` метод `click` теперь **возвращает stdout обработчика** (раньше терял). Остальные вызовы `click(...)` от этого не ломаются.
3. Добавить в `tests/scenario/test_flow_core.py` два теста (рядом с ZAP-01):

```python
def test_ZAP_01_no_debug_output_on_course_start(nb):
    nb.start_teachai()
    nb.set_value("Имя", "Тест"); nb.set_value("Общее время", 3); nb.set_value("Длительность урока", 30)
    out = nb.click("Сохранить настройки") + nb.click("Начать курс")
    assert "ОТЛАДКА" not in out
    assert "Ключи" not in out


def test_KZ_18_checking_a_solution_prints_no_diagnostics(lesson):
    lesson.click("Пройти тест"); lesson.answer_test(5); lesson.click("Завершить тест")
    lesson.click("Контрольные задания")
    lesson.llm_use("task_validate", "task_validate_wrong")
    lesson.set_code("a = 2\nb = 3\ntotal = 1")
    out = lesson.click("Проверить решение")
    assert "DIAGNOSTIC" not in out
    assert "expected_output" not in out
```

Оба новых теста **должны быть красными на коде до A4** (проверено: падают на `5b6669b`) и зелёными после.

```diff
--- a/tests/nbdriver.py
+++ b/tests/nbdriver.py
@@ -131,12 +131,12 @@
             "and w.layout.display != 'none']"
         )
 
-    def click(self, text: str, nth: int = -1) -> None:
-        """Нажимает nth-ую (по умолчанию последнюю созданную) подходящую кнопку."""
+    def click(self, text: str, nth: int = -1) -> str:
+        """Нажимает nth-ую (по умолчанию последнюю созданную) подходящую кнопку; возвращает stdout обработчика."""
         found = [b for b in self.buttons(text) if not b["dis"]]
         assert found, f"нет активной кнопки «{text}». Есть: {[b['d'] for b in self.buttons()]}"
         idx = found[nth]["i"]
-        self.run(f"list(__import__('ipywidgets').Widget.widgets.values())[{idx}].click()")
+        return self.run(f"list(__import__('ipywidgets').Widget.widgets.values())[{idx}].click()")
 
     def set_value(self, description: str, value) -> None:
         """Меняет value у поля ввода/слайдера/списка по подписи (description содержит текст); берёт последнее созданное."""
```

**Не трогать:** логику проверки решения (`validate_task_execution`), текст сообщений ученику.

## A5. LSN-06: однострочный Python-пример отбрасывается

**Что не так.** `executable_examples` оставляет пример только если в нём не меньше двух строк кода (`examples_html_utils.py:158`: `len(lines) >= 2`). Так отсекали шаги установки и команды терминала, но заодно теряется `print(type(3.5))`. Дальше `ExamplesValidation.validate_examples_quality` отбрасывает такие примеры сам (`examples_validation.py:27,63`: `MIN_CODE_LINES = 2`), поэтому правки одного первого места мало: пример дойдёт до проверки качества и будет заменён запасным.

**Как должно быть.** Несколько строк кода остаются, как раньше. Одна строка годится, если она разбирается как Python (`ast.parse`) и похожа на Python (`looks_like_python_code`). `pip install numpy`, `python --version`, `$ pip install pandas` отбрасываются, как и раньше.

**Правка.** Общая функция `has_runnable_python`, её используют оба места.

```diff
--- a/examples_html_utils.py
+++ b/examples_html_utils.py
@@ -14,6 +14,7 @@
 from __future__ import annotations
 
 import html
+import ast
 import json
 from typing import Any, Dict, List
 
@@ -141,6 +142,29 @@
     return examples_notice(_student_notice(payload.get("notice")))
 
 
+def has_runnable_python(code: str) -> bool:
+    """Код — это Python, а не шаги установки или команда терминала.
+
+    Несколько строк кода остаются как раньше. Одна строка (`print(type(3.5))`)
+    годится, если она похожа на Python и разбирается как Python;
+    `pip install numpy` и `python --version` под это не подходят.
+    """
+    lines = [
+        line
+        for line in (code or "").splitlines()
+        if line.strip() and not line.strip().startswith("#")
+    ]
+    if len(lines) >= 2:
+        return True
+    if len(lines) == 1:
+        try:
+            ast.parse(code)
+        except SyntaxError:
+            return False
+        return looks_like_python_code(code)
+    return False
+
+
 def executable_examples(payload: Dict[str, Any]) -> List[Dict[str, str]]:
     """Оставляет примеры, чей code похож на Python из нескольких строк.
 
@@ -150,12 +174,7 @@
     normalized = normalize_examples_payload(payload)
     kept: List[Dict[str, str]] = []
     for example in normalized["examples"]:
-        lines = [
-            line
-            for line in example["code"].splitlines()
-            if line.strip() and not line.strip().startswith("#")
-        ]
-        if len(lines) >= 2:
+        if has_runnable_python(example["code"]):
             kept.append(example)
     return kept
 
```

```diff
--- a/examples_validation.py
+++ b/examples_validation.py
@@ -15,6 +15,7 @@
 from examples_code_fixes import sanitize_examples
 from examples_html_utils import (
     executable_examples,
+    has_runnable_python,
     looks_like_python_code,
     parse_examples_json_response,
 )
@@ -55,12 +56,7 @@
             code = (example.get("code") or "").strip()
             if not code or not looks_like_python_code(code):
                 continue
-            lines = [
-                line
-                for line in code.splitlines()
-                if line.strip() and not line.strip().startswith("#")
-            ]
-            if len(lines) < self.MIN_CODE_LINES:
+            if not has_runnable_python(code):
                 continue
             lower = code.lower()
             if any(marker in lower for marker in self.FORBIDDEN_MARKERS):
```

Константа `ExamplesValidation.MIN_CODE_LINES` после правки не используется: удали её (одна строка, `examples_validation.py:27`), если в проекте нет других обращений (`grep -rn MIN_CODE_LINES`).

**Тесты.**
1. Снять `xfail` с `test_LSN_06_one_line_example_is_kept` (`tests/unit/test_misc_bugs.py`).
2. Добавить в тот же файл (после этого теста):

```python
@pytest.mark.parametrize("code", ["pip install numpy", "python --version", "$ pip install pandas"])
def test_LSN_06_one_line_terminal_commands_are_still_dropped(code):
    from examples_html_utils import executable_examples

    payload = {"examples": [{"title": "Установка", "description": "", "code": code}]}
    assert executable_examples(payload) == []


def test_LSN_06_one_line_example_passes_quality_check():
    from examples_validation import ExamplesValidation

    checker = ExamplesValidation("sk-test-not-a-real-key")
    assert checker.validate_examples_quality(
        [{"title": "Тип", "description": "", "code": "print(type(3.5))"}]
    )
```

Второй новый тест (`...passes_quality_check`) красный на `5b6669b` и зелёный после правки `examples_validation.py`. Старые проверки `examples_payload_checks.py` (шаги установки, `practice_possible: false`) должны остаться зелёными; они запускаются через `tests/unit/test_legacy_checks.py`.

**Не трогать:** `looks_like_python_code`, `normalize_examples_payload`, запасные примеры `_create_fallback_python_example`, `exec`-проверку примеров (`examples_validation.py:105`: D9).

## Приёмка этапа 2а

Команда: `python -m pytest -q -rx` из venv текущей машины.

- Результат ожидается: **`86 passed, 1 skipped, 1 deselected, 20 xfailed`** (расчётно: 74 + 6 снятых `xfail` + 6 новых тестов; 26 − 6 = 20; цифру «86» подтверди своим прогоном, если у тебя другая — скажи точно какая).
- Сняты `xfail` ровно с шести тестов: `ZAP-01 (start)`, `TST-02`, `TST-03`, `LSN-15`, `PRF-05`, `LSN-06`. Остальные 20 `xfail` остались и по-прежнему XFAIL (не XPASS).
- Новые тесты: `ZAP-01 (course_start)`, `KZ-18`, `LSN-06` ×4 (3 параметра + `quality_check`).
- `git status`: изменены `lesson_interface.py`, `assessment_questions_ui.py`, `control_tasks_interface.py`, `interface.py`, `course_plan_generator.py`, `examples_html_utils.py`, `examples_validation.py`, `tests/nbdriver.py`, `tests/scenario/test_flow_core.py`, `tests/unit/test_misc_bugs.py`, `tests/unit/test_progress_state.py`. Никаких других файлов.
- Покажи мне: вывод `pytest -q -rx` (последние 40 строк), `git status`, `git diff --stat`. Пуш — только после моей команды.


# ЭТАП 2б. Надёжность данных и ответов модели (B1–B8)

Начинать после того, как этап 2а принят мной и запушен. Этап 2б независим от 2а по коду, кроме общего файла `tests/unit/test_misc_bugs.py` и `tests/scenario/test_flow_core.py`.

## B1. LLM-01: 401 повторяется 3 раза и подаётся как «проблема прокси»

**Что не так.** `make_api_request_with_retries` (`content_utils.py:589-632`) повторяет любой `Exception` три раза с паузами 2 и 4 секунды, затем выбрасывает «Сервер не отвечает… проверьте подключение и настройки прокси». Неверный ключ (401), запрет (403), несуществующая модель (404), плохой запрос (400) и нехватка квоты от повтора не лечатся: ученик ждёт 6 секунд и получает неверное объяснение.

**Как должно быть.** Для 400/401/403/404 и `insufficient_quota` — **один запрос, без пауз**, сообщение по-русски с причиной (для 401: «Неверный API-ключ или нет доступа (401). Проверьте ключ в .env.»). Таймауты, обрывы связи, 429 и 5xx повторяются как раньше, финальное сообщение для них не меняется.

Код статуса берётся из `exc.status_code` (исключения `openai`); если атрибута нет (как у тестовой подмены), из текста «Error code: NNN».

**Правка.** Заодно в этот же файл добавлен общий разбор JSON `parse_llm_json` (нужен для B2): весь `content_utils.py` ниже один дифф.

```diff
--- a/content_utils.py
+++ b/content_utils.py
@@ -33,6 +33,48 @@
     return answer_html
 
 
+
+def parse_llm_json(text):
+    """Разбирает JSON из ответа модели; снимает обёртку ```json ... ``` и лишний текст вокруг.
+
+    Raises:
+        ValueError: (json.JSONDecodeError — его подкласс), если JSON не найден.
+    """
+    raw = (text or "").strip()
+    fenced = re.match(r"^```[A-Za-z0-9_-]*[ \t]*\n?(.*?)\n?```\s*$", raw, re.S)
+    if fenced:
+        raw = fenced.group(1).strip()
+    try:
+        return json.loads(raw)
+    except ValueError:
+        starts = [i for i in (raw.find("{"), raw.find("[")) if i != -1]
+        end = max(raw.rfind("}"), raw.rfind("]"))
+        if starts and end > min(starts):
+            return json.loads(raw[min(starts) : end + 1])
+        raise
+
+
+_NON_RETRYABLE_STATUS = {400: "Запрос отклонён сервером (400).", 401: "Неверный API-ключ или нет доступа (401). Проверьте ключ в .env.",
+                         403: "Доступ запрещён (403). Проверьте ключ, регион и маршрут.", 404: "Модель или адрес API не найдены (404)."}
+
+
+def non_retryable_api_error(exc: Exception) -> str:
+    """Русское пояснение для ошибок, которые не лечатся повтором; "" — повторять можно.
+
+    401/403/404/400 и нехватка квоты не пройдут со второй попытки.
+    Таймауты, обрывы связи, 429 и 5xx повторяются как раньше.
+    """
+    status = getattr(exc, "status_code", None)
+    if status is None:
+        match = re.search(r"Error code:\s*(\d{3})", str(exc))
+        status = int(match.group(1)) if match else None
+    if status in _NON_RETRYABLE_STATUS:
+        return _NON_RETRYABLE_STATUS[status]
+    if "insufficient_quota" in str(exc).lower():
+        return "Недостаточно средств или превышена квота API."
+    return ""
+
+
 class ContentUtils:
     """Базовые утилиты для работы с контентом."""
 
@@ -612,6 +654,11 @@
                 )
             except Exception as e:
                 last_exception = e
+                fatal = non_retryable_api_error(e)
+                if fatal:
+                    # Повтор не поможет: ключ, права или запрос не изменятся.
+                    self.logger.error(f"Запрос к LLM не повторяется: {str(e)}")
+                    raise Exception(f"{fatal} Исходная ошибка: {str(e)}") from e
                 self.logger.warning(
                     f"Попытка {attempt}/{retries} неудачна: {str(e)}. "
                     f"Повтор через {delay} сек..."
```

**Тесты.** Снять `xfail` с `test_LLM_01_401_is_not_retried` (`tests/unit/test_misc_bugs.py`) и добавить в него последней строкой `assert "ключ" in str(err.value).lower()`.

**Не трогать:** `make_api_request` (низкоуровневый запрос), параметры `retries/backoff`, `llm_route.py`. `format_api_error` в `interface_utils.py` не менять: он и так переводит «401» в «Неверный API-ключ».

## B2. LLM-05: ответ в обёртке ```` ```json ```` ломает план, тест, понятия и релевантность

**Что не так.** Четыре разбора ответа модели используют `json.loads` как есть: `course_plan_generator.py:72`, `assessment_generator.py:94`, `concepts_generator.py:90` (и повтор в `:122`), `relevance_checker.py:123`. Если модель ответила ```` ```json {...} ``` ```` или добавила фразу перед JSON, ученик получает ошибку. Классификатор темы и проверка КЗ (`course_domain.py:36`, `control_task_llm_judge.py:29`) уже вырезают JSON регулярным выражением и в порядке.

**Как должно быть.** Один общий помощник `parse_llm_json` (в `content_utils.py`, см. B1) снимает обёртку и лишний текст вокруг; остальные разборы вызывают его. Текст не-JSON по-прежнему даёт `ValueError` (его ловят существующие обработчики, текст ошибок наружу не меняется).

**Правка.** В `content_utils.py` — в диффе B1. В четырёх файлах заменить вызов и импорт:

```diff
--- a/course_plan_generator.py
+++ b/course_plan_generator.py
@@ -4,7 +4,7 @@
 """
 
 import json
-from content_utils import BaseContentGenerator
+from content_utils import BaseContentGenerator, parse_llm_json
 
 
 class CoursePlanGenerator(BaseContentGenerator):
@@ -69,7 +69,7 @@
                 },
             )
 
-            course_plan = json.loads(response_content)
+            course_plan = parse_llm_json(response_content)
 
             self.logger.debug("Ключи плана от LLM: %s", list(course_plan.keys()))
 
@@ -171,8 +171,12 @@
         """
         try:
             # Убеждаемся, что есть основные ключи
-            if "id" not in course_plan:
-                course_plan["id"] = course_data.get("id", "course-1")
+            # id слота курса всегда берём из каталога/запроса, а не из ответа модели:
+            # иначе повторный старт курса не найдёт слот и создаст второй.
+            if course_data.get("id"):
+                course_plan["id"] = course_data["id"]
+            elif "id" not in course_plan:
+                course_plan["id"] = "course-1"
 
             if "title" not in course_plan:
                 course_plan["title"] = course_data.get("title", "Курс")
```

```diff
--- a/concepts_generator.py
+++ b/concepts_generator.py
@@ -5,7 +5,7 @@
 
 import json
 import re
-from content_utils import BaseContentGenerator
+from content_utils import BaseContentGenerator, parse_llm_json
 from student_content import render_student_content
 
 
@@ -87,7 +87,7 @@
                 },
             )
 
-            concepts_data = json.loads(response_content)
+            concepts_data = parse_llm_json(response_content)
             concepts = self._extract_concepts_from_response(concepts_data)
 
             if not concepts or len(concepts) == 0:
@@ -119,7 +119,7 @@
                         response_format={"type": "json_object"},
                     )
                     
-                    concepts_data = json.loads(response_content)
+                    concepts_data = parse_llm_json(response_content)
                     concepts = self._extract_concepts_from_response(concepts_data)
                     
                     if not concepts or len(concepts) == 0:
```

```diff
--- a/relevance_checker.py
+++ b/relevance_checker.py
@@ -5,7 +5,7 @@
 """
 
 import json
-from content_utils import BaseContentGenerator
+from content_utils import BaseContentGenerator, parse_llm_json
 
 
 class RelevanceChecker(BaseContentGenerator):
@@ -120,7 +120,7 @@
                 },
             )
 
-            relevance_data = json.loads(response_content)
+            relevance_data = parse_llm_json(response_content)
             result = self._extract_relevance_from_response(relevance_data)
 
             self.logger.info(
```

(Диффы `course_plan_generator.py` выше содержат и правку B5. `import json` в этих файлах мог остаться неиспользуемым — удалять его не нужно.)

**Тесты.** В `tests/unit/test_followup_state.py` снять `xfail` с `test_LLM_05_fenced_json_for_plan_test_and_concepts` и добавить тесты разбора (весь дифф файла дан в B3–B5 ниже: он содержит и их).

**Не трогать:** `examples_html_utils.parse_examples_json_response`, `control_tasks_generator.py:462,1008`, `course_domain.py`, `control_task_llm_judge.py` — они уже терпимы к обёртке.

## B3. LLM-06: неверный индекс ответа в тесте

**Что не так.** `AssessmentGenerator._extract_questions_from_response` бросает «Некорректный индекс правильного ответа…» (`assessment_generator.py:186`), если `correct_option` не 1–3 (после 0→1). Повторного запроса нет: одна ошибка модели из пяти вопросов — и ученик видит ошибку. Текст ошибки сейчас обёрнут в три слоя («Не удалось сгенерировать вопросы для теста: Не удалось сгенерировать вопросы для урока 'X': … Некорректный индекс … {словарь}»).

**Как должно быть.**
- Ошибка **формата** ответа (не JSON, нет `questions`, нет `options`/`text`/`correct_option`, индекс не 1–3, пустой список) → **один повторный запрос**.
- Если и повтор плохой: одно понятное сообщение, без технического «хвоста» и без словаря: «Не удалось сгенерировать вопросы для урока 'X': модель дважды вернула тест в неподходящем виде. Вернитесь к уроку и откройте тест ещё раз.» Подробная причина — только в лог.
- Ошибки **сети/API** (401, таймаут) повтором здесь не лечатся: они идут как раньше.
- Один слой префикса вместо трёх.

**Правка.** Новый класс `AssessmentFormatError`, метод `_parse_questions`, цикл из двух попыток; в `assessment.py` и `assessment_interface.py` не оборачивать сообщение второй раз.

```diff
--- a/assessment_generator.py
+++ b/assessment_generator.py
@@ -6,7 +6,11 @@
 import json
 import re
 import random
-from content_utils import BaseContentGenerator
+from content_utils import BaseContentGenerator, parse_llm_json
+
+
+class AssessmentFormatError(Exception):
+    """Ответ модели не удалось превратить в тест (формат, число вариантов, индекс ответа)."""
 
 
 class AssessmentGenerator(BaseContentGenerator):
@@ -70,32 +74,45 @@
                 {"role": "user", "content": prompt},
             ]
 
-            content = self.make_api_request(
-                messages=messages,
-                temperature=0.5,  # Уменьшаем temperature для более точного следования материалу
-                max_tokens=3000,
-                response_format={"type": "json_object"},
-            )
-
-            # Сохраняем отладочную информацию
-            self.save_debug_response(
-                "assessment",
-                prompt,
-                content,
-                {
-                    "course": course,
-                    "section": section,
-                    "topic": topic,
-                    "lesson": lesson_title,
-                    "num_questions": num_questions,
-                },
-            )
-
-            questions_data = json.loads(content)
-            questions = self._extract_questions_from_response(questions_data)
-
-            if not questions or len(questions) == 0:
-                raise Exception("API вернул пустой список вопросов")
+            questions = None
+            for attempt in (1, 2):
+                content = self.make_api_request(
+                    messages=messages,
+                    temperature=0.5,  # Уменьшаем temperature для более точного следования материалу
+                    max_tokens=3000,
+                    response_format={"type": "json_object"},
+                )
+
+                # Сохраняем отладочную информацию
+                self.save_debug_response(
+                    "assessment",
+                    prompt,
+                    content,
+                    {
+                        "course": course,
+                        "section": section,
+                        "topic": topic,
+                        "lesson": lesson_title,
+                        "num_questions": num_questions,
+                        "attempt": attempt,
+                    },
+                )
+
+                try:
+                    questions = self._parse_questions(content)
+                    break
+                except AssessmentFormatError as format_error:
+                    self.logger.warning(
+                        "Тест, попытка %s/2: модель вернула неверный формат: %s",
+                        attempt,
+                        format_error,
+                    )
+
+            if questions is None:
+                raise AssessmentFormatError(
+                    "модель дважды вернула тест в неподходящем виде. "
+                    "Вернитесь к уроку и откройте тест ещё раз."
+                )
 
             # ПРИНУДИТЕЛЬНАЯ РАНДОМИЗАЦИЯ - поскольку API не следует инструкциям
             randomized_questions = self._force_randomize_questions(questions)
@@ -111,6 +128,22 @@
                 f"Не удалось сгенерировать вопросы для урока '{lesson}': {str(e)}"
             )
 
+    def _parse_questions(self, content):
+        """JSON ответа -> список вопросов; любой сбой формата — AssessmentFormatError."""
+        try:
+            questions_data = parse_llm_json(content)
+        except ValueError as exc:
+            raise AssessmentFormatError(f"ответ не JSON: {exc}") from exc
+        try:
+            questions = self._extract_questions_from_response(questions_data)
+        except AssessmentFormatError:
+            raise
+        except Exception as exc:
+            raise AssessmentFormatError(str(exc)) from exc
+        if not questions:
+            raise AssessmentFormatError("API вернул пустой список вопросов")
+        return questions
+
     def _clean_html_for_analysis(self, lesson_content):
         """
         Очищает HTML теги для анализа содержания.
```

```diff
--- a/assessment.py
+++ b/assessment.py
@@ -104,6 +104,8 @@
             )
 
             self.logger.error(f"Критическая ошибка при генерации вопросов: {str(e)}")
+            if str(e).startswith("Не удалось сгенерировать вопросы"):
+                raise  # сообщение уже понятное, не оборачиваем второй раз
             raise Exception(
                 f"Не удалось сгенерировать вопросы для урока '{lesson}': {str(e)}"
             )
```

```diff
--- a/assessment_interface.py
+++ b/assessment_interface.py
@@ -156,9 +156,12 @@
                 )
             except Exception as e:
                 self.logger.error(f"ОШИБКА при генерации вопросов: {str(e)}")
+                shown = str(e)
+                if not shown.startswith("Не удалось сгенерировать вопросы"):
+                    shown = f"Не удалось сгенерировать вопросы для теста: {shown}"
                 return self._create_error_interface(
                     "Ошибка при генерации теста",
-                    f"Не удалось сгенерировать вопросы для теста: {str(e)}",
+                    shown,
                     current_section,
                     current_topic,
                     current_lesson,
```

**Тесты.** В `tests/unit/test_followup_state.py` старый `test_LLM_06_correct_option_zero_and_four` заменён тремя тестами (дифф ниже); в `tests/scenario/test_flow_core.py` добавляется сценарий:

```python
def test_LLM_06_bad_test_twice_shows_one_clear_message(lesson):
    bad = {"questions": [{"text": "В?", "options": ["a", "b", "c"], "correct_option": 4, "explanation": "x"}]}
    lesson.llm_use("assessment", bad)
    lesson.click("Пройти тест")
    assert lesson.llm_calls().count("assessment") == 2
    texts = lesson.eval(
        "[w.value for w in __import__('ipywidgets').Widget.widgets.values() "
        "if type(w).__name__ == 'HTML' and 'дважды' in w.value]")
    assert texts, "ученик не увидел понятного сообщения"
    assert texts[-1].count("Не удалось сгенерировать вопросы") == 1
    assert "Некорректный индекс" not in texts[-1]
    assert lesson.buttons("Вернуться к уроку")
```

**Не трогать:** `_force_randomize_questions`, нормализацию `correct_option == 0 → 1`, промпт теста, порог `score > 40` (D-решения не затронуты).

## B4. ST-11, ST-12: битый `state.json` затирается; запись не атомарна

**Что не так.**
1. `StateManager._load_state` (`state_manager.py:78-98`) при любом сбое чтения возвращает пустое состояние, а ближайший `save_state` перезаписывает им файл: **весь прогресс ученика пропадает** без возможности восстановить (даже если файл можно было починить руками).
2. `save_state` пишет прямо в `state.json` (`state_manager.py:166-167`): сбой во время записи оставляет обрезанный файл — это и есть путь к предыдущему пункту.

**Как должно быть.** Нечитаемый файл сначала копируется рядом как `state.json.broken-ГГГГММДД-ЧЧММСС`, в лог пишется путь копии, затем создаётся пустое состояние. Запись идёт во временный `state.json.tmp` + `fsync` + `os.replace`; при сбое старый `state.json` цел, `.tmp` убран, `save_state` возвращает `False`.

**Правка.**

```diff
--- a/state_manager.py
+++ b/state_manager.py
@@ -5,6 +5,7 @@
 """
 
 import os
+import shutil
 import json
 import logging
 from pathlib import Path
@@ -95,8 +96,20 @@
                 return self._create_default_state()
         except Exception as e:
             self.logger.error(f"Ошибка при загрузке состояния: {str(e)}")
+            self._backup_unreadable_state()
             return self._create_default_state()
 
+    def _backup_unreadable_state(self):
+        """Сохраняет нечитаемый state.json рядом, чтобы следующее сохранение его не затёрло."""
+        try:
+            if self.state_file.exists():
+                stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
+                backup = self.state_file.with_name(f"{self.state_file.name}.broken-{stamp}")
+                shutil.copy2(self.state_file, backup)
+                self.logger.error(f"Нечитаемый файл состояния сохранён как {backup}")
+        except Exception as backup_error:
+            self.logger.error(f"Не удалось сохранить копию файла состояния: {backup_error}")
+
     def _create_default_state(self):
         """
         Создает структуру состояния по умолчанию.
@@ -162,9 +175,18 @@
             # Создаем директорию, если она не существует
             self.state_file.parent.mkdir(exist_ok=True, parents=True)
 
-            # Сохраняем состояние в файл
-            with open(self.state_file, "w", encoding="utf-8") as f:
-                json.dump(self.state, f, ensure_ascii=False, indent=2)
+            # Пишем во временный файл и подменяем одним действием: сбой посреди
+            # записи не оставит state.json обрезанным.
+            tmp_file = self.state_file.with_name(self.state_file.name + ".tmp")
+            try:
+                with open(tmp_file, "w", encoding="utf-8") as f:
+                    json.dump(self.state, f, ensure_ascii=False, indent=2)
+                    f.flush()
+                    os.fsync(f.fileno())
+                os.replace(tmp_file, self.state_file)
+            finally:
+                if tmp_file.exists():
+                    tmp_file.unlink()
 
             self.logger.debug(f"Состояние успешно сохранено в {self.state_file}")
             return True
```

**Тесты.** В `tests/unit/test_followup_state.py` (дифф ниже): `test_ST_11_...` проверяет, что копия создана и содержит исходный текст; `xfail` с `test_ST_12_save_state_is_atomic` снят; добавлен `test_ST_12_failed_write_keeps_previous_state`. Оба проверенно красные на `5b6669b`.

**Не трогать:** `_create_default_state`, `reset_learning_and_course_data`, формат файла, `snapshot_active`.

## B5. CRS-10: id слота курса берётся из ответа модели

**Что не так.** `CoursePlanGenerator._validate_and_fix_course_plan` подставляет id курса, только если модель его не вернула (`course_plan_generator.py:174-175` на HEAD `0b10de9`: `if "id" not in course_plan`). Если модель назвала план по-своему, слот в `state["courses"]` создаётся под её id (`course_portfolio.bind_new_plan`, `:234-249`), а повторный старт ищет id каталога (`course_selection_ui._start_course`, `:303-312`: `has_course(state, course["id"])`) — не находит и **генерирует план заново, плодя второй слот**.

**Как должно быть.** id слота всегда равен id курса из каталога/запроса. Если у `course_data` нет id, остаётся прежнее поведение (`"course-1"` либо то, что вернула модель).

**Правка.** Хунк «@@ -171,8 +171,12 @@» в диффе `course_plan_generator.py` выше (в B2).

**Тесты.** Тест `test_CRS_10_...` из пакета 1 воспроизводил `_start_course` собственным кодом, поэтому правка в самом `_start_course` его не изменила бы. Он **переписан**: теперь вызывает настоящий `course_selection_ui._start_course` (подменены только показ сообщений и открытие урока), `xfail` снят. Дифф ниже. Проверено: на `5b6669b` с новым телом тест красный (`AssertionError: повторный старт сгенерировал план заново`), после правки зелёный.

**Не трогать:** `course_portfolio.py`, `course_data_manager.save_course_plan`, формат `courses`.

## B6. ZAP-02: `create_sample_env` затирает `.env.sample`

**Что не так.** `ConfigManager.create_sample_env` открывает файл на запись без проверки (`config.py:139-149`) и вызывается при каждом запуске без `.env` (`engine.py:91,315`): отредактированный пользователем `.env.sample` затирается.

**Как должно быть.** Если файл уже есть, он не перезаписывается, функция возвращает `True`.

**Правка.**

```diff
--- a/config.py
+++ b/config.py
@@ -144,9 +144,13 @@
             file_path (str): Путь для сохранения образца файла
 
         Returns:
-            bool: True если файл создан успешно, иначе False
+            bool: True если файл создан или уже существует, иначе False
         """
         try:
+            if os.path.exists(file_path):
+                # Образец мог быть отредактирован пользователем: не затираем.
+                self.logger.info(f"Образец .env уже есть, не перезаписываем: {file_path}")
+                return True
             with open(file_path, "w", encoding="utf-8") as f:
                 f.write("# Конфигурационный файл для TeachAI\n\n")
                 f.write("# API ключ OpenAI (маршрут direct / proxy)\n")
```

**Тесты.** Снять `xfail` с `test_ZAP_02_sample_env_not_overwritten` (`tests/unit/test_misc_bugs.py`).

**Не трогать:** относительный путь `.env.sample` (привязка к рабочей папке остаётся как есть), `create_env_file`, `engine.py`.

## B7. SEC-04: `eval` на выводе программы

**Что не так.** `result_checker.extract_numpy_arrays` делает `eval(match.group(0))` над текстом, который напечатал код ученика (`result_checker.py:358`). Ученик печатает `[__import__('os').system('…')]` — выполняется вне любой защиты.

**Как должно быть.** Только литералы: `ast.literal_eval`. Для обычных массивов `[1, 2, 3]` результат тот же; всё остальное пропускается так же, как раньше (`except Exception: continue`).

**Правка.**

```diff
--- a/result_checker.py
+++ b/result_checker.py
@@ -3,6 +3,7 @@
 Содержит различные типы проверок для контрольных заданий.
 """
 
+import ast
 import math
 import inspect
 import re
@@ -355,7 +356,7 @@
     arrays = []
     for match in re.finditer(r"\[[^\]]+\]", str(text)):
         try:
-            arrays.append(np.array(eval(match.group(0))))
+            arrays.append(np.array(ast.literal_eval(match.group(0))))
         except Exception:
             continue
     return arrays
```

**Тесты.** Снять `xfail` с `test_SEC_04_no_eval_on_program_output` (`tests/unit/test_misc_bugs.py`). Тесты сравнения вывода КЗ остаются зелёными.

**Не трогать:** остальные `eval`/`exec` (`cell_widget_base.py:145,176`, `control_tasks_generator.py:64` и т. д.) — это D9, пакет 4.

## B8. LEGACY: устаревшая проверка `relevance_prompt_checks.py`

**Что не так.** `relevance_prompt_checks.py:18` требует в промпте фразу «как преподаватель». Промпт релевантности переписан на три уровня `scope` (`relevance_checker.py:331-394`); роль «преподавателя» теперь только в system-сообщении (`relevance_checker.py:91-98`), в самом промпте её нет. Проверка отстала от кода, а не код от проверки.

**Решение.** Правим **проверку**, не промпт: она должна проверять то, что промпт гарантирует сейчас, то есть что вопрос оценивается по смыслу, а не сверкой фраз (`«не сверка фраз с текстом»`, `«точной фразы в тексте может не быть»`), и что описаны все три уровня `scope=lesson/course/outside`. Остальные утверждения (нет «если понятие или термин из вопроса встречается», нет «3.15», есть «не рассматривается в тексте») оставлены.

```diff
--- a/relevance_prompt_checks.py
+++ b/relevance_prompt_checks.py
@@ -15,11 +15,13 @@
         "Урок про установщик и флажок Add Python to PATH.",
     )
     lowered = prompt.lower()
-    assert "как преподаватель" in lowered
+    assert "не сверка фраз с текстом" in lowered
     assert "точной фразы в тексте может не быть" in lowered
     assert "если понятие или термин из вопроса встречается" not in lowered
     assert "не рассматривается в тексте" in lowered
+    assert "scope=lesson" in lowered
     assert "scope=course" in lowered
+    assert "scope=outside" in lowered
     assert "3.15" not in lowered
 
 
```

В `tests/unit/test_legacy_checks.py` словарь `STALE` очищен (устаревших проверок больше нет), строка в докстринге обновлена:

```diff
--- a/tests/unit/test_legacy_checks.py
+++ b/tests/unit/test_legacy_checks.py
@@ -1,6 +1,6 @@
 """Существующие проверки в корне проекта (*_checks.py) запускаются как есть, но в изолированной среде.
 
-Файлы *_checks.py не двигаем и не правим — только вызываем их функции test_*.
+Файлы *_checks.py не двигаем; если проверка разошлась с кодом, её правят осознанно (так было с relevance_prompt_checks в пакете 2).
 """
 import importlib
 import inspect
@@ -11,11 +11,9 @@
 ROOT = Path(__file__).resolve().parents[2]
 pytestmark = pytest.mark.unit
 
-# Устаревшие проверки (сами проверки правит пакет 2, здесь они помечены xfail).
-STALE = {
-    "relevance_prompt_checks::test_relevance_prompt_is_a_teacher_judgment":
-        "LEGACY: в промпте релевантности больше нет фразы «как преподаватель» (промпт переписан на scope, relevance_checker.py)",
-}
+# Устаревшие проверки: сейчас таких нет. Если проверка разошлась с кодом, правьте её или код,
+# а не добавляйте сюда запись без причины.
+STALE: dict[str, str] = {}
 
 
 def _cases():
```

**Тесты.** `relevance_prompt_checks::test_relevance_prompt_is_a_teacher_judgment` теперь обычный зелёный тест.

## Дифф тестов `tests/unit/test_followup_state.py` (B2–B5 целиком)

В нём: `xfail` сняты с `CRS-10`, `ST-12`, `LLM-05`; `CRS-10` переписан на настоящий `_start_course`; `ST-11` и `ST-12` усилены; добавлены тесты `LLM-05` (релевантность, `parse_llm_json`) и три теста `LLM-06`.

```diff
--- a/tests/unit/test_followup_state.py
+++ b/tests/unit/test_followup_state.py
@@ -5,6 +5,7 @@
 import json
 import logging
 import os
+from types import SimpleNamespace
 
 import pytest
 
@@ -68,13 +69,14 @@
         sm = StateManager()
     assert "user" in sm.state and "learning" in sm.state
     assert "Ошибка при загрузке состояния" in caplog.text
+    # битый файл не должен пропасть при ближайшем сохранении
+    assert sm.save_state() is True
+    backups = list(path.parent.glob("state.json.broken-*"))
+    assert len(backups) == 1
+    assert backups[0].read_text(encoding="utf-8") == "{битый"
+    assert json.loads(path.read_text(encoding="utf-8"))["user"] == sm.state["user"]
 
 
-@pytest.mark.xfail(
-    strict=True,
-    raises=AssertionError,
-    reason="ST-12: save_state пишет state.json напрямую, без tmp+rename (state_manager.py:166-167)",
-)
 def test_ST_12_save_state_is_atomic(monkeypatch):
     renamed: list[tuple[str, str]] = []
     real_replace = os.replace
@@ -90,6 +92,22 @@
     assert renamed, "запись state не проходит через rename/replace"
 
 
+def test_ST_12_failed_write_keeps_previous_state(monkeypatch):
+    sm = make_state()
+    path = sm.state_file
+    before = path.read_text(encoding="utf-8")
+    sm.state["user"]["name"] = "Новое имя"
+
+    def broken_dump(obj, fp, *args, **kwargs):
+        fp.write('{"оборвано')
+        raise OSError("диск переполнен")
+
+    monkeypatch.setattr(json, "dump", broken_dump)
+    assert sm.save_state() is False
+    assert path.read_text(encoding="utf-8") == before
+    assert not list(path.parent.glob("*.tmp"))
+
+
 def test_LSN_12_locked_lesson_is_rejected(caplog):
     from types import SimpleNamespace
 
@@ -106,38 +124,40 @@
     assert sm.state["learning"]["current_lesson"] == "lesson-1-1-1"
 
 
-@pytest.mark.xfail(
-    strict=True,
-    raises=AssertionError,
-    reason="CRS-10: слот пишется по id плана, а повтор ищет id каталога (course_selection_ui.py:307, course_portfolio.py:236)",
-)
-def test_CRS_10_plan_id_other_than_catalog_stays_one_slot(fake_llm):
-    """Повторный старт каталожного курса не должен плодить слот с id из ответа модели."""
-    from course_plan_generator import CoursePlanGenerator
-    from course_portfolio import begin_new_course, has_course
+def test_CRS_10_plan_id_other_than_catalog_stays_one_slot(fake_llm, monkeypatch):
+    """Повторный старт каталожного курса не должен плодить слот с id из ответа модели.
+
+    Идёт через настоящий course_selection_ui._start_course; подменены только показ
+    сообщений и открытие урока.
+    """
+    import course_selection_ui
+    from content_generator import ContentGenerator
     from helpers import load_plan
     from state_manager import StateManager
 
     plan = load_plan()
     plan["id"] = "llm-renamed-id"
     fake_llm.use("plan", plan)
+    monkeypatch.setattr(course_selection_ui, "_open_lesson_after_plan", lambda *_a, **_k: None)
+    monkeypatch.setattr(course_selection_ui, "display", lambda *_a, **_k: None)
     sm = StateManager()
-    gen = CoursePlanGenerator("sk-test-not-a-real-key")
+    setup = SimpleNamespace(
+        state_manager=sm,
+        content_generator=ContentGenerator("sk-test-not-a-real-key"),
+        system_logger=SimpleNamespace(log_activity=lambda **_k: None),
+        utils=SimpleNamespace(
+            create_styled_message=lambda text, *_a, **_k: text,
+            format_api_error=lambda exc, context="": f"{context}: {exc}",
+        ),
+    )
+    profile = {"total_study_hours": 3, "lesson_duration_minutes": 30}
 
-    def start_once() -> str:
-        if has_course(sm.state, COURSE["id"]):
-            return "resume"
-        begin_new_course(sm.state)
-        course_plan = gen.generate_course_plan(COURSE, 3, 30)
-        course_plan["source"] = COURSE["source"]
-        sm.save_course_plan(course_plan)
-        sm.update_learning_progress(course=COURSE["id"])
-        return "created"
-
-    assert start_once() == "created"
-    assert start_once() == "resume"
-    assert len(sm.state["courses"]) == 1
-    assert COURSE["id"] in sm.state["courses"]
+    course_selection_ui._start_course(setup, COURSE, profile)
+    assert fake_llm.count("plan") == 1
+    course_selection_ui._start_course(setup, COURSE, profile)
+    assert fake_llm.count("plan") == 1, "повторный старт сгенерировал план заново"
+    assert list(sm.state["courses"]) == [COURSE["id"]]
+    assert sm.state["active_course_id"] == COURSE["id"]
 
 
 def test_LLM_04_broken_json_is_a_clear_error(fake_llm):
@@ -188,11 +208,6 @@
     assert "Traceback" not in verdict.reason
 
 
-@pytest.mark.xfail(
-    strict=True,
-    raises=AssertionError,
-    reason="LLM-05: json.loads не снимает обёртку ```json (course_plan_generator.py:72, assessment_generator.py:94, concepts_generator.py:90)",
-)
 def test_LLM_05_fenced_json_for_plan_test_and_concepts(fake_llm):
     from assessment_generator import AssessmentGenerator
     from concepts_generator import ConceptsGenerator
@@ -251,28 +266,82 @@
     assert classify_course_topic("Кройка", generator=api).status == "out"
 
 
-def test_LLM_06_correct_option_zero_and_four(fake_llm):
-    """0 приводится к 1. Индекс 4 сразу даёт ошибку: повторного запроса к модели нет.
+def test_LLM_05_fenced_json_for_relevance(fake_llm):
+    fake_llm.use(
+        "relevance",
+        _fenced({"scope": "lesson", "is_relevant": True, "confidence": 90, "reason": "По теме."}),
+    )
+    from relevance_checker import RelevanceChecker
 
-    Пакет 2: один повтор, затем понятное сообщение ученику.
-    """
+    result = RelevanceChecker("sk-test-not-a-real-key").check_question_relevance(
+        user_question="Что такое переменная?",
+        lesson_content="<p>Переменная хранит значение.</p>",
+        lesson_data=LESSON_META,
+        lesson_raw_content="Переменная хранит значение.",
+    )
+    assert result["is_relevant"] is True
+
+
+@pytest.mark.parametrize(
+    "text",
+    [
+        '{"a": 1}',
+        '```json\n{"a": 1}\n```',
+        '```\n{"a": 1}\n```',
+        'Вот ответ:\n```json\n{"a": 1}\n```',
+        '  {"a": 1}  ',
+    ],
+)
+def test_LLM_05_parse_llm_json_variants(text):
+    from content_utils import parse_llm_json
+
+    assert parse_llm_json(text) == {"a": 1}
+
+
+def test_LLM_05_parse_llm_json_rejects_garbage():
+    from content_utils import parse_llm_json
+
+    with pytest.raises(ValueError):
+        parse_llm_json("это не json")
+
+
+def _one_question(index: int) -> dict:
+    return {
+        "questions": [
+            {"text": "Вопрос?", "options": ["a", "b", "c"], "correct_option": index, "explanation": "x"}
+        ]
+    }
+
+
+def test_LLM_06_correct_option_zero_is_normalized_to_one():
     from assessment_generator import AssessmentGenerator
 
     gen = AssessmentGenerator("sk-test-not-a-real-key")
+    normalized = gen._extract_questions_from_response(_one_question(0))
+    assert normalized[0]["correct_option"] == 1
 
-    def questions(index: int) -> dict:
-        return {
-            "questions": [
-                {
-                    "text": "Вопрос?",
-                    "options": ["a", "b", "c"],
-                    "correct_option": index,
-                    "explanation": "x",
-                }
-            ]
-        }
 
-    normalized = gen._extract_questions_from_response(questions(0))
-    assert normalized[0]["correct_option"] == 1
-    with pytest.raises(Exception, match="Некорректный индекс"):
-        gen._extract_questions_from_response(questions(4))
+def test_LLM_06_bad_index_then_good_answer_is_retried_once(fake_llm):
+    from assessment_generator import AssessmentGenerator
+
+    fake_llm.use("assessment", _one_question(4), _one_question(2))
+    got = AssessmentGenerator("sk-test-not-a-real-key").generate_assessment(
+        "Курс", "Раздел", "Тема", "Урок", "Текст урока", 1
+    )
+    assert fake_llm.count("assessment") == 2
+    assert len(got) == 1
+
+
+def test_LLM_06_two_bad_answers_give_a_clear_message(fake_llm):
+    from assessment_generator import AssessmentGenerator
+
+    fake_llm.use("assessment", _one_question(4))
+    with pytest.raises(Exception) as err:
+        AssessmentGenerator("sk-test-not-a-real-key").generate_assessment(
+            "Курс", "Раздел", "Тема", "Урок", "Текст урока", 1
+        )
+    assert fake_llm.count("assessment") == 2
+    message = str(err.value)
+    assert "дважды" in message
+    assert "Некорректный индекс" not in message
+    assert "{" not in message and "Traceback" not in message
```

## Приёмка этапа 2б

Команда: `python -m pytest -q -rx` из venv текущей машины.

- Ожидается: **`104 passed, 1 skipped, 1 deselected, 13 xfailed`** (проверено в прототипе; суммарно после обоих этапов).
- Сняты `xfail` ещё с семи тестов: `LLM-01`, `LLM-05`, `ST-12`, `CRS-10`, `ZAP-02`, `SEC-04`, `relevance_prompt_checks` (последний — через очистку `STALE`).
- Остаются ровно эти 13 `xfail` (все — решения D1–D9, пакеты 3 и 4): `KZ-09`, `TST-09`, `LSN-04`, `LSN-10`, `CRS-05`, `SEC-01`, `SEC-02`, `ST-01`, `KZ-12`, `TST-08`, `LSN-13`, `D2 (тест >40%)`, `PRF-04`. Ни один из них не должен стать XPASS: если стал, значит, ты залез в чужую область, — откати.
- Пропущен (skip) один: `KZ-16` (бесконечный цикл, пакет 4).
- `git status`: изменены `content_utils.py`, `course_plan_generator.py`, `assessment_generator.py`, `assessment.py`, `assessment_interface.py`, `concepts_generator.py`, `relevance_checker.py`, `state_manager.py`, `config.py`, `result_checker.py`, `relevance_prompt_checks.py`, `tests/unit/test_followup_state.py`, `tests/unit/test_legacy_checks.py`, `tests/unit/test_misc_bugs.py`, `tests/scenario/test_flow_core.py`. Ничего больше; ни `data/state.json`, ни `.env.sample` не изменены.
- Покажи мне: последние 40 строк `pytest -q -rx`, `git status`, `git diff --stat`. Пуш — только после моей команды.


# Что сообщить мне в конце каждого этапа

1. Результат полного прогона (последние строки `pytest -q -rx`) и сравнение с ожидаемым числом из «Приёмки».
2. Список файлов из `git status` и подтверждение, что `data/`, `.env`, `.env.sample`, `logs/` не изменены.
3. Любое место, где дифф не лёг на код, и что ты сделал вместо этого (одной фразой на место).
4. Любой тест, который вёл себя иначе, чем здесь описано (даже если ты его «починил»).
5. Любая правка, которой нет в этом файле. Таких быть не должно; если понадобилась — она требует моего согласования.

# Что дальше (для понимания, делать сейчас не нужно)

- **Пакет 3 (D1–D8):** определение «урок пройден» и список `visited_lessons` (в нём же уйдёт `ST-01/PRF-03/PRF-04`), `lesson_pass_mode`, отложенный учёт понятий, лучший результат КЗ и теста, эталонное решение по кнопке, `domain_override`, счётчики вопросов.
- **Пакет 4 (D9):** выполнение кода в дочернем процессе с таймаутом 10 с; в нём же решаются `demo_cell_widget`, `SEC-01/02`, `KZ-16`, `eval` в ячейках.
