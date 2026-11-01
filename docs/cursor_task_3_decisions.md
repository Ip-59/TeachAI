# Задача для Cursor: пакет 3 — решения D1–D8 (прогресс, UX)

Скопируй файл целиком в чат Cursor. Исполнитель — Cursor-агент в проекте TeachAI на локальном компьютере. Работа от коммита **`d9778b7`** (пакет 2 закрыт). Все правки ниже **проверены в прототипе** на копии `d9778b7` (Linux): после обоих этапов набор даёт `116 passed, 1 skipped, 1 deselected, 2 xfailed` (остаются только SEC-01/02 → пакет 4, D9). `content_utils.py` **не менялся** (679 строк — не раздувать).

Все номера строк — по `d9778b7`. Диффы сняты против него; применяй как есть. Если контекст не совпал — **остановись и напиши**, не подгоняй.

## 0. Жёсткие правила

1. Менять только то, что описано. Без «заодно»-рефакторинга и форматирования.
2. **Не трогать D9** (выполнение кода, `SEC-01/02`, `KZ-16`, `demo_cell_widget`, `eval`/`exec` в ячейках).
3. **`content_utils.py` не расширять.** Миграция и схема — в новом `state_migration.py` и в `learning_progress_manager.py` / `state_manager.py`.
4. Два этапа — два коммита, два пуша. После каждого: полный `pytest -q -rx`, отчёт мне; **`git push` только по моей команде**.
5. Venv текущей машины: `venv_W_L` / `venv_H_L`. Новых зависимостей нет.
6. Ключ не печатать. Тесты — `sk-test-not-a-real-key`.
7. Когда баг исправлен, снять `xfail(strict=True)`. Новых `xfail` без согласования не добавлять.
8. Реальные `data/`, `.env`, `.env.sample` не трогать. После прогона `git status` чист от них.

## 1. Схема state (итог пакета 3)

В `learning`:

| Поле | Смысл |
|---|---|
| `visited_lessons: list[str]` | Открытые уроки (D1) |
| `completed_lessons: list[str]` | Только **пройденные** (синхронизируется при `mark_lesson_complete_manually` / `mark_lesson_incomplete`) |
| `lesson_pass_mode: dict[str, str]` | `normal` \| `no_test` \| `task_not_required` \| `forced` (D3/D6) |
| `offtopic_count: dict[str, int]` | Вопросы scope=outside (D8) |
| `_schema_version: int` | `2` после миграции пакета 3 |

В `control_tasks[lesson_id]`:

```json
{
  "task_title": "...",
  "is_correct": true,
  "best_is_correct": true,
  "with_hint": false,
  "completed_at": "...",
  "attempts": [
    {"is_correct": true, "timestamp": "...", "with_hint": false}
  ]
}
```

В `courses[id].meta.domain_override: true` — курс вне области (D7). Также дублируется в `course_plan.domain_override`, чтобы переживать `snapshot_active`.

**Определение «пройден»** не меняем в `is_lesson_completed`: по-прежнему `lesson_completion_status` ИЛИ (тест/bypass + верное КЗ). Меняем только то, **кто** попадает в списки и что видит дашборд.

## 2. Миграция старого state.json (критично для прогресса Игоря)

При загрузке (`StateManager.__init__`), **идемпотентно**:

1. **Фаза 1** (до managers): создать отсутствующие ключи; у старых `control_tasks` без `attempts` сделать одну попытку из текущей записи.
2. **Фаза 2** (после `LearningProgressManager`): если `_schema_version < 2`:
   - все id из старого `completed_lessons` → в `visited_lessons`;
   - в `completed_lessons` оставить только те, для кого `is_lesson_completed(id)` истинно;
   - для закрытых без `lesson_pass_mode`: `normal`, если было верное КЗ, иначе `forced`;
   - выставить `_schema_version = 2`, сохранить.

**Как читается старый прогресс Игоря:**
- Уроки, которые он только **открыл** (баг ST-01 клал их в `completed_lessons`), после миграции становятся **посещёнными**, не пройденными — прогресс % может **уменьшиться**. Это правильное поведение по D1, не потеря данных.
- Уроки с `lesson_completion_status=true` или верным КЗ (+ тест/bypass) остаются пройденными.
- Лучшие баллы тестов и результаты КЗ не трогаем; у КЗ появляется `attempts`.

## 3. Состав этапов

| Этап | Решения | Что снимает с xfail | Ожидаемый pytest |
|---|---|---|---|
| **3а** | D1, D2, D3, D5, D6, TST-08, LSN-13 + миграция | ST-01, PRF-04, D2 (тест>40%), LSN-04, TST-08, KZ-12, LSN-13, TST-09 | **`113 passed, 1 skipped, 1 deselected, 5 xfailed`** (+1 тест миграции ST-16; 13−8=5: KZ-09, LSN-10, CRS-05, SEC-01, SEC-02) |
| **3б** | D4, D7, D8 | KZ-09, LSN-10, CRS-05 | **`116 passed, 1 skipped, 1 deselected, 2 xfailed`** (только SEC-01/02) |

Цифры 3а подтверждены коммитом `6e5981c` (113 passed, 5 xfailed). Диффы этапа 3б в этом файле **обновлены против `6e5981c`** (28.10.2026): старые хунки 3а из полного диффа убраны, чтобы `patch` ложился чисто.


## ЭТАП 3а. Модель прогресса (D1/D2/D3/D5/D6 + TST-08 + LSN-13 + миграция)


### A. Новый файл `state_migration.py`

Полный файл (создать в корне проекта рядом с `state_manager.py`):


```python
"""Миграция state.json к схеме D1–D8.

Вызывается при загрузке состояния. Идемпотентна: повторный вызов безвреден.
Старые файлы без visited_lessons / lesson_pass_mode / offtopic_count приводятся
к новой схеме, прогресс ученика не обнуляется.
"""
from __future__ import annotations

import logging

logger = logging.getLogger(__name__)

SCHEMA_VERSION = 2  # 1 = до пакета 3; 2 = D1–D8


def ensure_learning_fields(state: dict) -> bool:
    """Гарантирует наличие новых ключей. Не трогает смысл completed_lessons."""
    changed = False
    learning = state.setdefault("learning", {})
    for key, blank in (
        ("visited_lessons", list),
        ("lesson_pass_mode", dict),
        ("offtopic_count", dict),
        ("completed_lessons", list),
        ("lesson_completion_status", dict),
    ):
        if key not in learning:
            learning[key] = blank()
            changed = True
    return changed


def migrate_control_task_attempts(state: dict) -> bool:
    changed = False
    for lid, rec in list((state.get("control_tasks") or {}).items()):
        if not isinstance(rec, dict):
            continue
        if "attempts" not in rec:
            attempt = {
                "is_correct": bool(rec.get("is_correct")),
                "timestamp": rec.get("completed_at") or "",
                "with_hint": bool(rec.get("with_hint", False)),
            }
            rec["attempts"] = [attempt]
            rec.setdefault("best_is_correct", bool(rec.get("is_correct")))
            changed = True
        else:
            if "best_is_correct" not in rec:
                rec["best_is_correct"] = bool(rec.get("is_correct"))
                changed = True
    return changed


def migrate_visited_and_completed(state: dict, is_lesson_completed) -> bool:
    """Разделяет старый completed_lessons (открытые) на visited + реально пройденные."""
    learning = state.setdefault("learning", {})
    if learning.get("_schema_version", 1) >= SCHEMA_VERSION:
        return False

    visited = learning.setdefault("visited_lessons", [])
    completed = list(learning.get("completed_lessons") or [])
    for lid in completed:
        if lid not in visited:
            visited.append(lid)

    kept = [lid for lid in completed if is_lesson_completed(lid)]
    learning["completed_lessons"] = kept

    modes = learning.setdefault("lesson_pass_mode", {})
    status = learning.get("lesson_completion_status") or {}
    for lid, done in status.items():
        if not done or lid in modes:
            continue
        ct = (state.get("control_tasks") or {}).get(lid) or {}
        if ct.get("is_correct") or ct.get("best_is_correct"):
            modes[lid] = "normal"
        else:
            modes[lid] = "forced"

    learning["_schema_version"] = SCHEMA_VERSION
    logger.info(
        "Миграция state schema=%s: visited=%d, completed=%d (было %d)",
        SCHEMA_VERSION,
        len(visited),
        len(kept),
        len(completed),
    )
    return True


def migrate_learning_state(state: dict, *, is_lesson_completed=None) -> bool:
    changed = ensure_learning_fields(state)
    changed = migrate_control_task_attempts(state) or changed
    if is_lesson_completed is not None:
        changed = migrate_visited_and_completed(state, is_lesson_completed) or changed
    return changed
```


### B. `state_manager.py`

```diff
--- a/state_manager.py
+++ b/state_manager.py
@@ -37,6 +37,7 @@
 
         # Загружаем состояние
         self.state = self._load_state()
+        self._run_state_migrations()
         from course_portfolio import migrate_state
 
         if migrate_state(self.state):
@@ -46,6 +47,7 @@
         # Инициализируем специализированные менеджеры
         self.user_profile = UserProfileManager(self)
         self.learning_progress = LearningProgressManager(self)
+        self._finish_state_migrations()
         self.course_data = CourseDataManager(self)
 
         self.logger.info(
@@ -130,6 +132,9 @@
                 "current_topic": "",
                 "current_lesson": "",
                 "completed_lessons": [],
+                "visited_lessons": [],
+                "lesson_pass_mode": {},
+                "offtopic_count": {},
                 "lesson_scores": {},
                 "lesson_attempts": {},
                 "lesson_completion_status": {},
@@ -158,6 +163,34 @@
             },
         }
 
+    def _run_state_migrations(self):
+        """Фаза 1: новые ключи и attempts. Фильтрация completed — после managers."""
+        try:
+            from state_migration import ensure_learning_fields, migrate_control_task_attempts
+
+            changed = ensure_learning_fields(self.state)
+            changed = migrate_control_task_attempts(self.state) or changed
+            self._migration_dirty = changed
+        except Exception as e:
+            self.logger.error(f"Ошибка миграции состояния (фаза 1): {e}")
+            self._migration_dirty = False
+
+    def _finish_state_migrations(self):
+        """Фаза 2: разделить visited/completed (нужен is_lesson_completed)."""
+        try:
+            from state_migration import migrate_visited_and_completed
+
+            changed = migrate_visited_and_completed(
+                self.state, self.is_lesson_completed
+            )
+            if changed or getattr(self, "_migration_dirty", False):
+                self.save_state()
+            self._migration_dirty = False
+        except Exception as e:
+            self.logger.error(f"Ошибка миграции состояния (фаза 2): {e}")
+            self._migration_dirty = False
+
+
     def save_state(self):
         """
         Сохраняет текущее состояние в файл.
@@ -270,8 +303,10 @@
     def is_lesson_completed(self, lesson_id):
         return self.learning_progress.is_lesson_completed(lesson_id)
 
-    def mark_lesson_complete_manually(self, lesson_id):
-        return self.learning_progress.mark_lesson_complete_manually(lesson_id)
+    def mark_lesson_complete_manually(self, lesson_id, pass_mode: str = "forced"):
+        return self.learning_progress.mark_lesson_complete_manually(
+            lesson_id, pass_mode=pass_mode
+        )
 
     def is_test_passed(self, lesson_id):
         return self.learning_progress.is_test_passed(lesson_id)
@@ -297,6 +332,12 @@
     def get_questions_count(self, lesson_id):
         return self.learning_progress.get_questions_count(lesson_id)
 
+    def increment_offtopic_count(self, lesson_id):
+        return self.learning_progress.increment_offtopic_count(lesson_id)
+
+    def get_offtopic_count(self, lesson_id):
+        return self.learning_progress.get_offtopic_count(lesson_id)
+
     def reset_questions_count(self, lesson_id):
         return self.learning_progress.reset_questions_count(lesson_id)
 
@@ -371,35 +412,38 @@
         return self.course_data.get_lesson_data(section_id, topic_id, lesson_id)
 
     def save_control_task_result(
-        self, lesson_id: str, task_title: str, is_correct: bool
+        self, lesson_id: str, task_title: str, is_correct: bool, with_hint: bool = False
     ):
-        """
-        Сохраняет результат выполнения контрольного задания.
-
-        Args:
-            lesson_id (str): ID урока
-            task_title (str): Название задания
-            is_correct (bool): Правильно ли выполнено задание
-        """
+        """Сохраняет попытку КЗ: лучший результат + история (D4/D5)."""
         try:
-            # Инициализируем секцию контрольных заданий если её нет
-            if "control_tasks" not in self.state:
-                self.state["control_tasks"] = {}
-
-            # Сохраняем результат
-            self.state["control_tasks"][lesson_id] = {
+            tasks = self.state.setdefault("control_tasks", {})
+            rec = tasks.get(lesson_id) or {}
+            attempts = list(rec.get("attempts") or [])
+            attempts.append(
+                {
+                    "is_correct": bool(is_correct),
+                    "timestamp": datetime.now().isoformat(),
+                    "with_hint": bool(with_hint),
+                }
+            )
+            prev_best = bool(rec.get("best_is_correct", rec.get("is_correct", False)))
+            best = prev_best or bool(is_correct)
+            tasks[lesson_id] = {
                 "task_title": task_title,
-                "is_correct": is_correct,
+                "is_correct": best,  # совместимость: «лучший»
+                "best_is_correct": best,
+                "with_hint": bool(rec.get("with_hint", False)) or bool(with_hint),
                 "completed_at": datetime.now().isoformat(),
+                "attempts": attempts,
             }
-
-            # Сохраняем состояние
             self.save_state()
-
             self.logger.info(
-                f"Результат контрольного задания сохранен: {lesson_id} - {is_correct}"
+                "Результат КЗ сохранён: %s correct=%s best=%s hint=%s",
+                lesson_id,
+                is_correct,
+                best,
+                with_hint,
             )
-
         except Exception as e:
             self.logger.error(f"Ошибка при сохранении результата контрольного задания: {str(e)}")
 
```


### C. `learning_progress_manager.py`

**Суть:** `update_learning_progress` → `visited_lessons`; убрать понятия при тесте; `mark_lesson_complete_manually(lesson_id, pass_mode=...)`; `mark_lesson_incomplete` не удаляет `lesson_scores`; счётчики offtopic.

```diff
--- a/learning_progress_manager.py
+++ b/learning_progress_manager.py
@@ -46,15 +46,12 @@
 
             if lesson is not None:
                 self.state_manager.state["learning"]["current_lesson"] = lesson
-                # Добавляем урок в список пройденных, если его там еще нет
+                # D1: открытие = посещение, не прохождение.
                 lesson_id = f"{section}:{topic}:{lesson}"
-                if (
-                    lesson_id
-                    not in self.state_manager.state["learning"]["completed_lessons"]
-                ):
-                    self.state_manager.state["learning"]["completed_lessons"].append(
-                        lesson_id
-                    )
+                learning = self.state_manager.state["learning"]
+                visited = learning.setdefault("visited_lessons", [])
+                if lesson_id not in visited:
+                    visited.append(lesson_id)
 
             self.logger.debug(
                 f"Прогресс обучения обновлен: course={course}, section={section}, topic={topic}, lesson={lesson}"
@@ -116,10 +113,7 @@
                     f"Тест по уроку {lesson_id} пройден с оценкой {score}% (урок ещё не завершен)"
                 )
 
-            if is_passed:
-                from student_knowledge import mark_lesson_concepts_passed
-
-                mark_lesson_concepts_passed(self.state_manager, lesson_id)
+            # D2: понятия не засчитываются при тесте — только при переходе дальше.
 
             # Пересчитываем общую статистику
             self._recalculate_course_statistics()
@@ -179,25 +173,31 @@
             )
             return False
 
-    def mark_lesson_complete_manually(self, lesson_id):
+    def mark_lesson_complete_manually(self, lesson_id, pass_mode: str = "forced"):
         """
-        Отмечает урок как завершенный принудительно (для кнопки "Продолжить с текущим результатом").
-        
+        Отмечает урок как завершённый и засчитывает понятия (D1/D2/D3).
+
         Args:
-            lesson_id (str): ID урока
-            
-        Returns:
-            bool: True если операция прошла успешно, иначе False
+            lesson_id: ID урока
+            pass_mode: normal | no_test | task_not_required | forced
         """
         try:
-            # Инициализируем структуру, если её нет
-            if "lesson_completion_status" not in self.state_manager.state["learning"]:
-                self.state_manager.state["learning"]["lesson_completion_status"] = {}
+            learning = self.state_manager.state["learning"]
+            learning.setdefault("lesson_completion_status", {})
+            learning.setdefault("lesson_pass_mode", {})
+            learning.setdefault("completed_lessons", [])
+            learning.setdefault("visited_lessons", [])
+
+            learning["lesson_completion_status"][lesson_id] = True
+            learning["lesson_pass_mode"][lesson_id] = pass_mode
+            if lesson_id not in learning["completed_lessons"]:
+                learning["completed_lessons"].append(lesson_id)
+            if lesson_id not in learning["visited_lessons"]:
+                learning["visited_lessons"].append(lesson_id)
 
-            # Отмечаем урок как завершенный принудительно
-            self.state_manager.state["learning"]["lesson_completion_status"][lesson_id] = True
-
-            self.logger.info(f"Урок {lesson_id} отмечен как завершенный принудительно")
+            self.logger.info(
+                "Урок %s отмечен как завершённый (mode=%s)", lesson_id, pass_mode
+            )
             from student_knowledge import mark_lesson_concepts_passed
 
             mark_lesson_concepts_passed(self.state_manager, lesson_id)
@@ -308,16 +308,17 @@
             if "lesson_completion_status" not in self.state_manager.state["learning"]:
                 self.state_manager.state["learning"]["lesson_completion_status"] = {}
 
-            # Отмечаем урок как незавершенный
-            self.state_manager.state["learning"]["lesson_completion_status"][
-                lesson_id
-            ] = False
-
-            # Также удаляем оценку (урок нужно пересдать)
-            if "lesson_scores" in self.state_manager.state["learning"]:
-                self.state_manager.state["learning"]["lesson_scores"].pop(
-                    lesson_id, None
-                )
+            learning = self.state_manager.state["learning"]
+            learning.setdefault("lesson_completion_status", {})
+            learning["lesson_completion_status"][lesson_id] = False
+            # D5/TST-08: лучший балл теста сохраняем; урок просто снова открыт.
+            completed = learning.setdefault("completed_lessons", [])
+            if lesson_id in completed:
+                completed.remove(lesson_id)
+            # pass_mode прошлого прохождения оставляем в истории? Сбрасываем —
+            # иначе дашборд покажет «пройден без сдачи» у незавершённого.
+            modes = learning.setdefault("lesson_pass_mode", {})
+            modes.pop(lesson_id, None)
 
             self.logger.info(f"Урок {lesson_id} отмечен как незавершенный")
 
@@ -421,6 +422,21 @@
         except Exception as e:
             self.logger.error(f"Ошибка при пересчете статистики курса: {str(e)}")
 
+    def increment_offtopic_count(self, lesson_id):
+        """Увеличивает счётчик вопросов вне курса (D8)."""
+        learning = self.state_manager.state["learning"]
+        counts = learning.setdefault("offtopic_count", {})
+        counts[lesson_id] = int(counts.get(lesson_id) or 0) + 1
+        self.state_manager.save_state()
+        return counts[lesson_id]
+
+    def get_offtopic_count(self, lesson_id):
+        return int(
+            (self.state_manager.state["learning"].get("offtopic_count") or {}).get(
+                lesson_id, 0
+            )
+        )
+
     def get_lesson_score(self, lesson_id):
         """
         Получает лучший результат по уроку.
```


### D. `course_data_manager.py` (LSN-13)

```diff
--- a/course_data_manager.py
+++ b/course_data_manager.py
@@ -166,27 +166,12 @@
                         )
                         # Продолжаем поиск следующего урока
 
-            # Если текущего урока нет или он завершен, ищем следующий урок
+            # D1/LSN-13: следующий = первый незавершённый в плане (не «следующий по позиции»).
             if not current_section or not current_topic or not current_lesson:
                 self.logger.info(
-                    "Текущий урок не найден, возвращаем первый урок из плана"
+                    "Текущий урок не найден, возвращаем первый незавершённый"
                 )
-                return self._get_first_lesson_from_plan(course_plan)
-
-            # ИСПРАВЛЕНО: Ищем следующий урок после завершенного текущего
-            next_lesson = self._find_next_lesson_in_plan(
-                course_plan, current_section, current_topic, current_lesson
-            )
-
-            if next_lesson:
-                section_id, topic_id, lesson_id, lesson_data = next_lesson
-                self.logger.info(
-                    f"Найден следующий урок: {section_id}:{topic_id}:{lesson_id}"
-                )
-                return section_id, topic_id, lesson_id, lesson_data
-            else:
-                self.logger.info("Все уроки курса пройдены")
-                return None, None, None, None
+            return self._find_first_unfinished_lesson(course_plan)
 
         except Exception as e:
             self.logger.error(f"Ошибка при определении следующего урока: {str(e)}")
@@ -228,6 +213,27 @@
             self.logger.error(f"Ошибка при получении первого урока: {str(e)}")
             return None, None, None, None
 
+    def _find_first_unfinished_lesson(self, course_plan):
+        """Первый урок плана, для которого is_lesson_completed ложно (LSN-13)."""
+        try:
+            from lesson_outline import iter_plan_lessons
+
+            for item in iter_plan_lessons(course_plan):
+                section_id = item["section_id"]
+                topic_id = item["topic_id"]
+                lesson_id = item["lesson_id"]
+                full = f"{section_id}:{topic_id}:{lesson_id}"
+                if not self.state_manager.learning_progress.is_lesson_completed(full):
+                    self.logger.info("Первый незавершённый урок: %s", full)
+                    lesson_data = self.get_lesson_data(section_id, topic_id, lesson_id)
+                    return section_id, topic_id, lesson_id, lesson_data
+            self.logger.info("Все уроки курса пройдены")
+            return None, None, None, None
+        except Exception as e:
+            self.logger.error(f"Ошибка поиска незавершённого урока: {e}")
+            return None, None, None, None
+
+
     def _find_next_lesson_in_plan(
         self, course_plan, current_section, current_topic, current_lesson
     ):
```


### E. `course_portfolio.py` — только `empty_learning` (+ поля). Правки `domain_override` / `snapshot` — **этап 3б**.

В 3а добавь в `empty_learning()` ключи `visited_lessons`, `lesson_pass_mode`, `offtopic_count` (пустые list/dict). Полный дифф файла содержит и 3б — применяй в 3а **только** хунк `empty_learning`; остальные хунки — в 3б.

```diff
--- a/course_portfolio.py
+++ b/course_portfolio.py
@@ -29,6 +29,9 @@
         "current_topic": "",
         "current_lesson": "",
         "completed_lessons": [],
+        "visited_lessons": [],
+        "lesson_pass_mode": {},
+        "offtopic_count": {},
         "lesson_scores": {},
         "lesson_attempts": {},
         "lesson_completion_status": {},
@@ -61,14 +64,17 @@
     title = plan.get("title") or course_id or "Курс"
     source = plan.get("source") or "catalog"
     status = "completed" if _looks_completed(state) else "active"
-    return {
-        "meta": {
+    meta = {
             "course_id": course_id,
             "title": title,
             "source": source,
             "status": status,
             "updated_at": _now(),
-        },
+        }
+    if plan.get("domain_override"):
+        meta["domain_override"] = True
+    return {
+        "meta": meta,
         "learning": copy.deepcopy(learning),
         "course_plan": copy.deepcopy(plan),
         "lesson_content_cache": copy.deepcopy(
@@ -154,6 +160,9 @@
     slot = _slot_from_mirror(state, cid)
     created = (existing.get("meta") or {}).get("created_at")
     slot["meta"]["created_at"] = created or _now()
+    # D7: не терять пометку «вне области» при каждом save_state
+    if (existing.get("meta") or {}).get("domain_override"):
+        slot["meta"]["domain_override"] = True
     if (existing.get("meta") or {}).get("status") == "completed":
         slot["meta"]["status"] = "completed"
     state["courses"][cid] = slot
@@ -174,6 +183,7 @@
                 "source": meta.get("source") or "catalog",
                 "status": meta.get("status") or "active",
                 "is_active": cid == active,
+                "domain_override": bool(meta.get("domain_override")),
                 "current_lesson": learning.get("current_lesson") or "",
                 "current_section": learning.get("current_section") or "",
                 "current_topic": learning.get("current_topic") or "",
@@ -247,6 +257,9 @@
     meta["updated_at"] = _now()
     if "created_at" not in meta:
         meta["created_at"] = _now()
+    # D7: курс вне области
+    if course_plan.get("domain_override"):
+        meta["domain_override"] = True
 
 
 def mark_active_completed(state: dict) -> None:
```


### F. `startup_dashboard.py`

```diff
--- a/startup_dashboard.py
+++ b/startup_dashboard.py
@@ -297,28 +297,16 @@
             state = self.state_manager.state
             learning = state.get("learning", {})
             
-            completed_lessons = learning.get("completed_lessons", [])
-            course_plan = state.get("course_plan", {})
-            sections = course_plan.get("sections", [])
-            
-            # Подсчитываем общее количество уроков
-            total_lessons = 0
-            for section in sections:
-                for topic in section.get("topics", []):
-                    total_lessons += len(topic.get("lessons", []))
-            
-            # Процент завершения
-            progress_percent = learning.get("course_progress_percent", 0)
-            if total_lessons > 0:
-                progress_percent = (len(completed_lessons) / total_lessons) * 100
-            
+            # D1: один источник — is_lesson_completed через calculate_course_progress.
+            progress = self.state_manager.learning_progress.calculate_course_progress()
             return {
-                "completed_lessons_count": len(completed_lessons),
-                "total_lessons_count": total_lessons,
-                "progress_percent": round(progress_percent, 1),
+                "completed_lessons_count": progress["completed"],
+                "total_lessons_count": progress["total"],
+                "progress_percent": round(progress["percent"], 1),
                 "current_lesson": learning.get("current_lesson", ""),
                 "current_section": learning.get("current_section", ""),
-                "current_topic": learning.get("current_topic", "")
+                "current_topic": learning.get("current_topic", ""),
+                "lesson_pass_mode": learning.get("lesson_pass_mode") or {},
             }
         except Exception as e:
             self.logger.error(f"Ошибка при получении статистики прогресса: {str(e)}")
@@ -345,9 +333,9 @@
             # Общее время обучения (примерная оценка)
             user_profile = state.get("user", {})
             lesson_duration = user_profile.get("lesson_duration_minutes", 30)
-            completed_lessons = state.get("learning", {}).get("completed_lessons", [])
-            
-            estimated_total_time = len(completed_lessons) * lesson_duration
+            # D1: время только по реально пройденным.
+            progress = self.state_manager.learning_progress.calculate_course_progress()
+            estimated_total_time = progress["completed"] * lesson_duration
             
             return {
                 "days_since_last_access": days_since_last,
```


### G. `assessment_results_handler.py` (D3: `no_test`)

```diff
--- a/assessment_results_handler.py
+++ b/assessment_results_handler.py
@@ -333,8 +333,10 @@
                 display(lesson_widget)
 
             def on_continue_anyway_clicked(b):
-                # ИСПРАВЛЕНО: Принудительно отмечаем урок как завершенный
-                self.state_manager.mark_lesson_complete_manually(lesson_id)
+                # D3: пройден без сдачи теста
+                self.state_manager.mark_lesson_complete_manually(
+                    lesson_id, pass_mode="no_test"
+                )
 
                 # Активируем кнопку "Контрольные задания"
                 self._activate_control_tasks_button()
```


### H. `control_tasks_interface.py` — только pass_mode (D3/D5/D6)

В 3а: вызовы `mark_lesson_complete_manually(..., pass_mode="normal"|"forced"|"task_not_required")`.
**Не** убирай автопоказ эталона и **не** добавляй кнопку «Показать решение» — это 3б.

Фрагменты pass_mode (сделай вручную по смыслу, если полный дифф сразу тянет D4):

1. При верном КЗ: `sm.mark_lesson_complete_manually(lesson_id, pass_mode="normal")`.
2. В `_force_next_lesson`: `pass_mode="forced"`.
3. В «Задание не требуется»: `pass_mode="task_not_required"`.

Полный дифф файла (3а+3б) ниже в этапе 3б — после 3а можно отложить его применение.

### I. `lesson_interaction.py` — только D2

Удалить оба вызова `self._remember_concepts(concepts)` (строки ~139 и ~291 на `d9778b7`). Метод `_remember_concepts` можно оставить мёртвым или удалить. Правки счётчиков вопросов — **этап 3б**.

### J. `student_knowledge.py`

```diff
--- a/student_knowledge.py
+++ b/student_knowledge.py
@@ -1,8 +1,8 @@
 """Что студент уже проходил — для заданий, а не для угадывания темы.
 
 Перечень понятий строится вместе с уроком и лежит в кэше урока.
-В профиль как пройденные он попадает, если ученик открыл понятия
-или урок засчитан: успешный тест либо принудительный переход.
+В профиль как пройденные он попадает только при переходе к следующему
+уроку (верное КЗ, «не требуется», «Продолжить с текущей оценкой» и т.п.).
 """
 
 from __future__ import annotations
```

### K. Тесты этапа 3а

1. Снять `xfail` с: `test_ST_01`, `test_KZ_12`, `test_TST_08`, `test_LSN_13`, `test_D2_concepts_not_counted_on_test_pass`, `test_PRF_04` (`tests/unit/test_progress_state.py`); `test_TST_09`, `test_LSN_04` (`tests/scenario/test_flow_core.py`).
2. Усилить ST-01 и KZ-12; добавить `test_ST_16_migration_...` — см. дифф:

```diff
--- a/tests/unit/test_progress_state.py
+++ b/tests/unit/test_progress_state.py
@@ -38,23 +38,24 @@
     assert sm.is_test_passed(L1)
 
 
-@pytest.mark.xfail(strict=True, raises=AssertionError, reason="ST-01: открытие урока кладёт его в completed_lessons (learning_progress_manager.py:47-56)")
 def test_ST_01_opening_lesson_does_not_complete_it():
     sm = make_state()
     sm.update_learning_progress(section=SEC, topic=TOP, lesson="lesson-1-1-1")
     assert L1 not in sm.state["learning"]["completed_lessons"]
+    assert L1 in sm.state["learning"]["visited_lessons"]
+    assert not sm.is_lesson_completed(L1)
 
 
 
-@pytest.mark.xfail(strict=True, raises=AssertionError, reason="KZ-12: верный результат КЗ затирается неверной пересдачей (state_manager.py:368-372)")
 def test_KZ_12_wrong_resubmission_keeps_best_result():
     sm = make_state()
     sm.save_control_task_result(L1, "Сумма", True)
     sm.save_control_task_result(L1, "Сумма", False)
     assert sm.state["control_tasks"][L1]["is_correct"] is True
+    assert sm.state["control_tasks"][L1]["best_is_correct"] is True
+    assert len(sm.state["control_tasks"][L1]["attempts"]) == 2
 
 
-@pytest.mark.xfail(strict=True, raises=AssertionError, reason="TST-08: «Повторить урок» удаляет лучший балл (learning_progress_manager.py:316-320)")
 def test_TST_08_repeat_lesson_keeps_best_score():
     sm = make_state()
     sm.save_lesson_assessment(L1, 80, True)
@@ -62,7 +63,6 @@
     assert sm.get_lesson_score(L1) == 80
 
 
-@pytest.mark.xfail(strict=True, raises=AssertionError, reason="LSN-13: следующий урок ищется по позиции, а не первый незавершённый (course_data_manager.py:177)")
 def test_LSN_13_next_lesson_is_first_unfinished():
     sm = make_state()
     for lid in (L1, L2):
@@ -84,7 +84,6 @@
     assert len(sm.state["learning"]["lesson_attempts"][L1]) == 2
 
 
-@pytest.mark.xfail(strict=True, raises=AssertionError, reason="D2: понятия записываются в профиль уже при тесте >40% (learning_progress_manager.py:119-122); по D2 — только при переходе")
 def test_D2_concepts_not_counted_on_test_pass():
     sm = make_state()
     sm.state["lesson_content_cache"] = {L1: {"concepts": [{"name": "Переменная", "description": "x"}]}}
@@ -99,7 +98,6 @@
     assert L1 in sm.state["learning"]["lesson_concepts"]
 
 
-@pytest.mark.xfail(strict=True, raises=AssertionError, reason="PRF-04: дашборд считает открытые уроки как пройденные (startup_dashboard.py:300-316, learning_progress_manager.py:47-56)")
 def test_PRF_04_dashboard_progress_ignores_opened_lessons():
     from startup_dashboard import StartupDashboard
 
@@ -119,3 +117,45 @@
     sm.mark_lesson_complete_manually(L1)
     stats = StartupDashboard(sm, None)._get_progress_statistics()
     assert stats["total_lessons_count"] == 3
+
+
+def test_ST_16_migration_moves_opened_lessons_to_visited(isolated_project):
+    """Старый state: completed_lessons = открытые. После загрузки — visited + реально пройденные."""
+    import json
+    from state_manager import StateManager
+
+    path = isolated_project / "data" / "state.json"
+    path.parent.mkdir(parents=True, exist_ok=True)
+    raw = {
+        "user": {"name": "Игорь", "total_study_hours": 3, "lesson_duration_minutes": 30,
+                 "communication_style": "friendly"},
+        "learning": {
+            "current_course": "python-basics",
+            "current_section": SEC,
+            "current_topic": TOP,
+            "current_lesson": "lesson-1-1-1",
+            "completed_lessons": [L1, L2],  # оба «открыты», реально пройден только L1
+            "lesson_scores": {L1: 80},
+            "lesson_attempts": {},
+            "lesson_completion_status": {L1: True},
+            "control_task_bypass": {},
+            "questions_count": {},
+            "average_score": 0,
+            "total_assessments": 0,
+            "total_score": 0,
+            "course_progress_percent": 0,
+        },
+        "course_plan": {"id": "python-basics", "title": "Основы", "sections": []},
+        "active_course_id": "python-basics",
+        "courses": {},
+        "control_tasks": {},
+        "lesson_content_cache": {},
+        "system": {"first_run": False, "last_access": "2026-01-01T00:00:00", "version": "1.0.0"},
+    }
+    path.write_text(json.dumps(raw, ensure_ascii=False), encoding="utf-8")
+    sm = StateManager()
+    learn = sm.state["learning"]
+    assert L1 in learn["visited_lessons"] and L2 in learn["visited_lessons"]
+    assert L1 in learn["completed_lessons"]
+    assert L2 not in learn["completed_lessons"]
+    assert learn.get("_schema_version") == 2
```

Для `test_flow_core.py` в 3а сними только xfail с TST-09 и LSN-04 (и при желании добавь `assert ... lesson_pass_mode ... == "normal"` в KZ-10). Xfail KZ-09 / LSN-10 / CRS-05 оставь до 3б.

### Приёмка 3а

`python -m pytest -q -rx` → ожидается около **`113 passed, 1 skipped, 1 deselected, 5 xfailed`**.
Оставшиеся xfail: KZ-09, LSN-10, CRS-05, SEC-01, SEC-02.
`content_utils.py` не в `git status`. Покажи хвост pytest, `git status`, `git diff --stat`. Пуш — по моей команде.


---

## ЭТАП 3б. UX: эталон (D4), вне области (D7), счётчики вопросов (D8)

Начинать после принятия 3а. Диффы ниже сняты против HEAD **`6e5981c`** (после 3а): хунки pass_mode / удаления `_remember_concepts` / снятия xfail TST-09·LSN-04 в них **уже нет** — только остаток 3б.

### L. `control_tasks_interface.py` (D4)

На `6e5981c` автопоказ эталона — около строки **471**. Нужны: флаг `_solution_revealed`, кнопка «Показать решение» в интерфейсе задания и после неверной сдачи вместо авто-HTML, `with_hint` в `save_control_task_result`.

```diff
--- a/control_tasks_interface.py
+++ b/control_tasks_interface.py
@@ -33,6 +33,8 @@
         self.task_result = None
         # ИСПРАВЛЕНО: Флаг для предотвращения множественных вызовов
         self.is_checking = False
+        # D4: ученик открывал эталон для текущего задания
+        self._solution_revealed = False
 
     def show_control_task(self, lesson_data: Dict[str, Any], lesson_content: str):
         """
@@ -256,6 +258,9 @@
             layout=widgets.Layout(width="200px", margin="10px 0"),
         )
 
+        self._solution_revealed = False
+        show_solution_button = self._make_show_solution_button(task_data)
+
         # ИСПРАВЛЕНО: Контейнер для результатов как VBox вместо Output
         results_output = widgets.VBox(layout=widgets.Layout(margin="10px 0"))
 
@@ -325,7 +330,7 @@
 
         # Создаем контейнер с кнопками
         buttons_container = widgets.HBox(
-            [execute_button, check_button],
+            [execute_button, check_button, show_solution_button],
             layout=widgets.Layout(justify_content="space-around", margin="10px 0"),
         )
 
@@ -465,14 +470,8 @@
                     )
                 result_widgets.append(error_html)
 
-                # Эталонное решение
-                solution_html = widgets.HTML(
-                    value=f"<div style='background-color: #fff3cd; border: 1px solid #ffeaa7; border-radius: 5px; padding: 15px; margin: 10px 0;'>"
-                    f"<h4 style='color: #856404; margin: 0;'>Эталонное решение:</h4>"
-                    f"<pre style='background-color: #f8f9fa; padding: 10px; border-radius: 3px; margin: 10px 0;'>{task_data.get('solution_code', '')}</pre>"
-                    f"</div>"
-                )
-                result_widgets.append(solution_html)
+                # D4: эталон не показываем автоматически — только по кнопке.
+                result_widgets.append(self._make_show_solution_button(task_data))
 
                 # Сохраняем результат
                 self._save_task_result(task_data, False)
@@ -497,6 +496,38 @@
             # ИСПРАВЛЕНО: Сбрасываем флаг проверки
             self.is_checking = False
 
+    def _make_show_solution_button(self, task_data: Dict[str, Any]) -> widgets.Widget:
+        """Кнопка «Показать решение» (D4); доступна в любой момент."""
+        box = widgets.VBox()
+        btn = widgets.Button(
+            description="Показать решение",
+            button_style="warning",
+            layout=widgets.Layout(width="220px", margin="8px 0"),
+        )
+        out = widgets.HTML(value="")
+
+        def on_show(_b):
+            self._solution_revealed = True
+            code = task_data.get("solution_code") or ""
+            import html as html_lib
+            safe = html_lib.escape(code)
+            out.value = (
+                "<div style='background-color:#fff3cd;border:1px solid #ffeaa7;"
+                "border-radius:5px;padding:15px;margin:10px 0;'>"
+                "<h4 style='color:#856404;margin:0;'>Эталонное решение</h4>"
+                f"<pre style='background:#f8f9fa;padding:10px;border-radius:3px;"
+                f"margin:10px 0;'>{safe}</pre>"
+                "<p style='color:#856404;margin:0;font-size:0.9em;'>"
+                "Сдача после просмотра будет с пометкой «с подсказкой».</p>"
+                "</div>"
+            )
+            btn.disabled = True
+
+        btn.on_click(on_show)
+        box.children = (btn, out)
+        return box
+
+
     def _save_task_result(self, task_data: Dict[str, Any], is_correct: bool):
         """
         Сохраняет результат выполнения задания.
@@ -511,7 +542,10 @@
             lesson_id = self.lesson_interface.current_lesson_id
             if lesson_id:
                 self.lesson_interface.state_manager.save_control_task_result(
-                    lesson_id, task_data.get("title", "Задание"), is_correct
+                    lesson_id,
+                    task_data.get("title", "Задание"),
+                    is_correct,
+                    with_hint=bool(self._solution_revealed),
                 )
                 
                 # ИСПРАВЛЕНО: Если контрольное задание выполнено правильно И тест пройден - урок завершен
@@ -520,7 +554,9 @@
                     if sm.can_open_control_tasks(lesson_id):
                         # Не вызываем save_lesson_assessment: это дописывало бы
                         # в lesson_attempts фиктивную «попытку теста».
-                        sm.mark_lesson_complete_manually(lesson_id, pass_mode="normal")
+                        sm.mark_lesson_complete_manually(
+                            lesson_id, pass_mode="normal"
+                        )
                         self.logger.info(
                             "Урок %s завершён: КЗ верно, тест пройден или обойдён",
                             lesson_id,
```

### M. `lesson_interaction.py` (D8)

На `6e5981c` `increment_questions_count` ещё **до** проверки релевантности (~строка 433); отказ с заголовком «Это уже другой урок» (~467). Вызовы `_remember_concepts` уже убраны в 3а — в диффе их нет.

```diff
--- a/lesson_interaction.py
+++ b/lesson_interaction.py
@@ -136,7 +136,6 @@
                         )
                         # Сохраняем результат для последующих кликов
                         self.lesson_interface.current_lesson_concepts = concepts
-
                     # Создаем список понятий
                     concepts_list = []
                     for concept_data in concepts:
@@ -287,7 +286,6 @@
                             )
                         )
                         self.lesson_interface.current_lesson_concepts = concepts
-
                     concepts_list = []
                     for concept_data in concepts:
                         concept_button = widgets.Button(
@@ -426,17 +424,12 @@
                     # Получаем информацию о курсе для правильного вызова методов
                     course_info = self.lesson_interface.current_course_info
 
-                    # Увеличиваем счетчик вопросов
-                    # Создаем уникальный ID урока для счетчика
-                    lesson_full_id = f"{course_info.get('section_id', 'unknown')}:{course_info.get('topic_id', 'unknown')}:{course_info.get('lesson_id', 'unknown')}"
-                    questions_count = (
-                        self.lesson_interface.state_manager.increment_questions_count(
-                            lesson_full_id
-                        )
+                    lesson_full_id = (
+                        f"{course_info.get('section_id', 'unknown')}:"
+                        f"{course_info.get('topic_id', 'unknown')}:"
+                        f"{course_info.get('lesson_id', 'unknown')}"
                     )
 
-                    self.logger.info(f"Счетчик вопросов обновлен: {questions_count}")
-
                     # Проверяем релевантность вопроса.
                     # Передаём course_context, чтобы из тела урока была срезана
                     # breadcrumb-шапка и LLM учитывал именно материал урока
@@ -451,26 +444,41 @@
 
                     self.logger.info(f"Релевантность вопроса: {relevance_result}")
 
-                    # Если вопрос нерелевантен
-                    if not relevance_result.get("is_relevant", True):
-                        self.logger.warning("Вопрос нерелевантен уроку")
+                    # D8: outside → offtopic_count, не questions_count.
+                    scope = relevance_result.get("scope") or (
+                        "outside" if not relevance_result.get("is_relevant", True) else "lesson"
+                    )
+                    if scope == "outside" or not relevance_result.get("is_relevant", True):
+                        self.logger.warning("Вопрос вне курса")
                         import html as html_lib
 
+                        n = self.lesson_interface.state_manager.increment_offtopic_count(
+                            lesson_full_id
+                        )
                         safe_question = html_lib.escape(question)
                         safe_reason = html_lib.escape(
                             relevance_result.get("reason")
-                            or "Этот вопрос уже про другое занятие."
+                            or "Этот вопрос не про урок и не про курс."
                         )
                         answer_area.value = f"""
                         <div style='background-color: #fff3cd; color: #856404; padding: 15px;
                                     border-radius: 8px; border: 1px solid #ffeaa7;'>
-                            <h4>Это уже другой урок</h4>
+                            <h4>Вопрос вне курса</h4>
                             <p><strong>Ваш вопрос:</strong> {safe_question}</p>
                             <p>{safe_reason}</p>
+                            <p>Это уже {n}-й вопрос не в тему урока и не в тему курса.</p>
                         </div>
                         """
                         return
 
+                    # Отвеченный вопрос (lesson или course) — в questions_count.
+                    questions_count = (
+                        self.lesson_interface.state_manager.increment_questions_count(
+                            lesson_full_id
+                        )
+                    )
+                    self.logger.info(f"Счетчик вопросов обновлен: {questions_count}")
+
                     # Генерируем ответ
                     self.logger.info("Генерируем ответ на вопрос")
 
```

### N. D7: портфель и старт курса

`course_selection_ui.py` — прокинуть `domain_override` в план; `course_portfolio.py` — писать/сохранять флаг в meta при `bind_new_plan`, `_slot_from_mirror` и `snapshot_active` (иначе `save_state` затирает); `course_portfolio_ui.py` — бейдж «вне области».

```diff
--- a/course_selection_ui.py
+++ b/course_selection_ui.py
@@ -322,6 +322,8 @@
         )
         if course.get("source"):
             course_plan["source"] = course["source"]
+        if course.get("domain_override"):
+            course_plan["domain_override"] = True
 
         begin_new_course(setup.state_manager.state)
         success = setup.state_manager.save_course_plan(course_plan)
```

```diff
--- a/course_portfolio.py
+++ b/course_portfolio.py
@@ -64,14 +64,17 @@
     title = plan.get("title") or course_id or "Курс"
     source = plan.get("source") or "catalog"
     status = "completed" if _looks_completed(state) else "active"
-    return {
-        "meta": {
+    meta = {
             "course_id": course_id,
             "title": title,
             "source": source,
             "status": status,
             "updated_at": _now(),
-        },
+        }
+    if plan.get("domain_override"):
+        meta["domain_override"] = True
+    return {
+        "meta": meta,
         "learning": copy.deepcopy(learning),
         "course_plan": copy.deepcopy(plan),
         "lesson_content_cache": copy.deepcopy(
@@ -157,6 +160,9 @@
     slot = _slot_from_mirror(state, cid)
     created = (existing.get("meta") or {}).get("created_at")
     slot["meta"]["created_at"] = created or _now()
+    # D7: не терять пометку «вне области» при каждом save_state
+    if (existing.get("meta") or {}).get("domain_override"):
+        slot["meta"]["domain_override"] = True
     if (existing.get("meta") or {}).get("status") == "completed":
         slot["meta"]["status"] = "completed"
     state["courses"][cid] = slot
@@ -177,6 +183,7 @@
                 "source": meta.get("source") or "catalog",
                 "status": meta.get("status") or "active",
                 "is_active": cid == active,
+                "domain_override": bool(meta.get("domain_override")),
                 "current_lesson": learning.get("current_lesson") or "",
                 "current_section": learning.get("current_section") or "",
                 "current_topic": learning.get("current_topic") or "",
@@ -250,6 +257,9 @@
     meta["updated_at"] = _now()
     if "created_at" not in meta:
         meta["created_at"] = _now()
+    # D7: курс вне области
+    if course_plan.get("domain_override"):
+        meta["domain_override"] = True
 
 
 def mark_active_completed(state: dict) -> None:
```

```diff
--- a/course_portfolio_ui.py
+++ b/course_portfolio_ui.py
@@ -170,11 +170,12 @@
         active = " · текущий" if row.get("is_active") else ""
         source = "свой" if row.get("source") == "user" else "каталог"
         badge = "завершён" if status == "completed" else "в процессе"
+        override = " · вне области" if row.get("domain_override") else ""
         info = widgets.HTML(
             value=(
                 f"<div style='padding:8px 0;'><strong>{title}</strong>"
                 f"<br><span style='color:#6c757d;font-size:13px;'>"
-                f"{badge}{active} · {source} · {percent:.0f}%</span></div>"
+                f"{badge}{active}{override} · {source} · {percent:.0f}%</span></div>"
             )
         )
         open_btn = widgets.Button(
```

### O. Тесты этапа 3б

Снять `xfail` с `test_KZ_09`, `test_LSN_10`, `test_CRS_05`. Усилить KZ-09 (кнопка «Показать решение») и LSN-10 (`offtopic_count`). Проверка `lesson_pass_mode == "normal"` в KZ-10 уже есть с 3а — в диффе не дублируется.

```diff
--- a/tests/scenario/test_flow_core.py
+++ b/tests/scenario/test_flow_core.py
@@ -73,7 +73,6 @@
     assert not st["learning"]["lesson_completion_status"].get(L1)
 
 
-@pytest.mark.xfail(strict=True, raises=AssertionError, reason="KZ-09/D4: эталонное решение показывается автоматически после первой ошибки (control_tasks_interface.py:482-490)")
 def test_KZ_09_reference_solution_not_shown_after_wrong_attempt(lesson):
     lesson.click("Пройти тест"); lesson.answer_test(3); lesson.click("Завершить тест")
     lesson.click("Контрольные задания")
@@ -81,6 +80,7 @@
     lesson.set_code("a = 2\nb = 3\ntotal = 1")
     lesson.click("Проверить решение")
     assert not any("Эталонное решение" in t for t in lesson.html_texts())
+    assert lesson.buttons("Показать решение")
 
 
 def test_KZ_10_correct_solution_completes_lesson(lesson):
@@ -108,7 +108,6 @@
     assert L1 not in (lesson.state()["learning"].get("lesson_concepts") or {})
 
 
-@pytest.mark.xfail(strict=True, raises=AssertionError, reason="LSN-10/D8: отклонённый вопрос увеличивает questions_count (lesson_interaction.py:434-438)")
 def test_LSN_10_outside_question_not_counted_as_answered(lesson):
     lesson.click("Задать вопрос")
     lesson.llm_use("relevance", "relevance_outside")
@@ -116,6 +115,7 @@
     lesson.click("Отправить вопрос")
     assert "qa" not in lesson.llm_calls()
     assert lesson.state()["learning"]["questions_count"].get(L1, 0) == 0
+    assert lesson.state()["learning"]["offtopic_count"].get(L1, 0) == 1
 
 
 def test_LSN_08_relevant_question_is_answered_and_counted(lesson):
@@ -152,7 +152,6 @@
     assert not nb.state().get("courses")
 
 
-@pytest.mark.xfail(strict=True, raises=AssertionError, reason="CRS-05/D7: пометка «вне области» не сохраняется в state (course_domain_ui.py:146 пишет domain_override только в локальный dict)")
 def test_CRS_05_forced_out_of_domain_course_is_marked_in_state(nb):
     _start_custom_out_of_domain(nb)
     nb.click("Всё равно начать")
```

### Приёмка 3б

`python -m pytest -q -rx` → **`116 passed, 1 skipped, 1 deselected, 2 xfailed`** (только SEC-01, SEC-02).
`content_utils.py` не трогать. Покажи хвост pytest, `git status`, `git diff --stat`. Пуш — только по моей команде.


# Что сообщить мне в конце каждого этапа

1. Хвост `pytest -q -rx` и сравнение с ожидаемым числом.
2. `git status` / `git diff --stat`; подтверждение, что `data/`, `.env` не изменены и `content_utils.py` не тронут.
3. Места, где дифф не лёг.
4. Любая правка вне этого файла — только с моим согласием.

# Что дальше

- **Пакет 4 (D9):** дочерний процесс, таймаут 10 с, SEC-01/02, KZ-16, `demo_cell_widget`.
