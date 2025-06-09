"""
Ядро управления состоянием TeachAI.
Основные операции загрузки, сохранения и валидации состояния.
"""

import json
import os
import logging
from pathlib import Path
import shutil
from datetime import datetime


class StateManagerCore:
    """Базовая функциональность управления состоянием."""

    def __init__(self, state_file="data/state.json"):
        """
        Инициализация менеджера состояния.

        Args:
            state_file (str): Путь к файлу состояния
        """
        self.logger = logging.getLogger(__name__)
        self.state_file = state_file
        self.backup_dir = os.path.join("data", "state_backups")

        # Создаем необходимые директории
        self._ensure_data_directories()

        # Инициализируем состояние
        self.state = self._load_or_create_state()

        # Если файл не существовал, сохраняем новое состояние
        if not os.path.exists(self.state_file):
            self.save_state()
            self.logger.info(f"Новое состояние сохранено в файл: {self.state_file}")

        self.logger.info(
            f"StateManagerCore инициализирован с файлом: {self.state_file}"
        )

    def _ensure_data_directories(self):
        """Создает необходимые директории в папке data/."""
        try:
            # Создаем основную папку data/
            data_dir = "data"
            if not os.path.exists(data_dir):
                os.makedirs(data_dir, exist_ok=True)
                self.logger.info(f"Создана папка {data_dir}/")

            # Создаем папку для резервных копий
            if not os.path.exists(self.backup_dir):
                os.makedirs(self.backup_dir, exist_ok=True)
                self.logger.info(f"Создана папка {self.backup_dir}/")

            # Создаем папку для логов
            logs_dir = os.path.join("data", "logs")
            if not os.path.exists(logs_dir):
                os.makedirs(logs_dir, exist_ok=True)
                self.logger.info(f"Создана папка {logs_dir}/")

        except Exception as e:
            self.logger.error(f"Ошибка создания директорий: {str(e)}")

    def _load_or_create_state(self):
        """Загружает состояние из файла или создает новое."""
        try:
            if os.path.exists(self.state_file):
                with open(self.state_file, "r", encoding="utf-8") as f:
                    state = json.load(f)
                self.logger.info(f"Состояние загружено из файла: {self.state_file}")
                return self._validate_and_migrate_state(state)
            else:
                self.logger.info("Файл состояния не найден, создается новое состояние")
                return self._create_default_state()
        except Exception as e:
            self.logger.error(f"Ошибка загрузки состояния: {str(e)}")
            self.logger.info("Создается резервное состояние")
            return self._create_default_state()

    def _create_default_state(self):
        """Создает состояние по умолчанию."""
        default_state = {
            "user": {},
            "settings": {
                "first_run": True,
                "created_at": datetime.now().isoformat(),
                "version": "2.0",
            },
            "course_plan": {},
            "learning": {},
            "completed_lessons": [],
            "metadata": {"last_saved": datetime.now().isoformat(), "save_count": 0},
        }
        self.logger.info("Создано состояние по умолчанию")
        return default_state

    def _validate_and_migrate_state(self, state):
        """
        Валидирует и мигрирует состояние при необходимости.

        Args:
            state (dict): Загруженное состояние

        Returns:
            dict: Валидированное и мигрированное состояние
        """
        try:
            # Проверяем основные разделы
            required_sections = ["user", "settings", "course_plan", "learning"]
            for section in required_sections:
                if section not in state:
                    state[section] = {}
                    self.logger.info(f"Добавлен отсутствующий раздел: {section}")

            # Проверяем массивы
            if "completed_lessons" not in state:
                state["completed_lessons"] = []
                self.logger.info("Добавлен массив completed_lessons")

            # Проверяем metadata
            if "metadata" not in state:
                state["metadata"] = {
                    "last_saved": datetime.now().isoformat(),
                    "save_count": 0,
                }
                self.logger.info("Добавлены метаданные")

            # Проверяем настройки
            if "first_run" not in state["settings"]:
                state["settings"]["first_run"] = True
                self.logger.info("Добавлен флаг первого запуска")

            # Обновляем версию если нужно
            if state["settings"].get("version") != "2.0":
                state["settings"]["version"] = "2.0"
                state["metadata"]["migrated_at"] = datetime.now().isoformat()
                self.logger.info("Состояние мигрировано на версию 2.0")

            self.logger.info("Состояние успешно валидировано")
            return state

        except Exception as e:
            self.logger.error(f"Ошибка валидации состояния: {str(e)}")
            self.logger.info("Создается новое состояние вместо поврежденного")
            return self._create_default_state()

    def save_state(self):
        """
        Сохраняет текущее состояние в файл.

        Returns:
            bool: True если сохранение прошло успешно, иначе False
        """
        try:
            # Создаем резервную копию если файл существует
            if os.path.exists(self.state_file):
                self._create_backup()

            # Обновляем метаданные
            self.state["metadata"]["last_saved"] = datetime.now().isoformat()
            self.state["metadata"]["save_count"] = (
                self.state["metadata"].get("save_count", 0) + 1
            )

            # Создаем директорию если не существует
            os.makedirs(os.path.dirname(self.state_file), exist_ok=True)

            # Сохраняем в временный файл
            temp_file = f"{self.state_file}.tmp"
            with open(temp_file, "w", encoding="utf-8") as f:
                json.dump(self.state, f, indent=2, ensure_ascii=False)

            # Атомарно перемещаем временный файл
            shutil.move(temp_file, self.state_file)

            self.logger.debug(f"Состояние сохранено в файл: {self.state_file}")
            return True

        except Exception as e:
            self.logger.error(f"Ошибка сохранения состояния: {str(e)}")
            # Удаляем временный файл если он существует
            temp_file = f"{self.state_file}.tmp"
            if os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                except:
                    pass
            return False

    def _create_backup(self):
        """Создает резервную копию текущего файла состояния."""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"state_backup_{timestamp}.json"
            backup_path = os.path.join(self.backup_dir, backup_filename)

            shutil.copy2(self.state_file, backup_path)
            self.logger.debug(f"Создана резервная копия: {backup_path}")

            # Очищаем старые резервные копии (оставляем только последние 10)
            self._cleanup_old_backups()

        except Exception as e:
            self.logger.warning(f"Не удалось создать резервную копию: {str(e)}")

    def _cleanup_old_backups(self):
        """Удаляет старые резервные копии, оставляя только последние 10."""
        try:
            if not os.path.exists(self.backup_dir):
                return

            backup_files = []
            for filename in os.listdir(self.backup_dir):
                if filename.startswith("state_backup_") and filename.endswith(".json"):
                    file_path = os.path.join(self.backup_dir, filename)
                    file_time = os.path.getmtime(file_path)
                    backup_files.append((file_time, file_path))

            # Сортируем по времени (новые первыми)
            backup_files.sort(reverse=True)

            # Удаляем старые (оставляем 10 последних)
            for _, file_path in backup_files[10:]:
                try:
                    os.remove(file_path)
                    self.logger.debug(f"Удалена старая резервная копия: {file_path}")
                except Exception as e:
                    self.logger.warning(
                        f"Не удалось удалить резервную копию {file_path}: {str(e)}"
                    )

        except Exception as e:
            self.logger.warning(f"Ошибка очистки старых резервных копий: {str(e)}")

    def load_state(self):
        """
        Перезагружает состояние из файла.

        Returns:
            bool: True если загрузка прошла успешно, иначе False
        """
        try:
            self.state = self._load_or_create_state()
            self.logger.info("Состояние перезагружено из файла")
            return True
        except Exception as e:
            self.logger.error(f"Ошибка перезагрузки состояния: {str(e)}")
            return False

    def get_state(self):
        """
        Возвращает копию текущего состояния.

        Returns:
            dict: Текущее состояние системы
        """
        return self.state.copy()

    def update_state(self, updates):
        """
        Обновляет состояние системы.

        Args:
            updates (dict): Словарь с обновлениями

        Returns:
            bool: True если обновление прошло успешно, иначе False
        """
        try:
            self.state.update(updates)
            result = self.save_state()
            if result:
                self.logger.debug("Состояние обновлено")
            return result
        except Exception as e:
            self.logger.error(f"Ошибка обновления состояния: {str(e)}")
            return False

    def clear_state(self):
        """
        Очищает состояние, создавая новое по умолчанию.

        Returns:
            bool: True если очистка прошла успешно, иначе False
        """
        try:
            self.state = self._create_default_state()
            result = self.save_state()
            if result:
                self.logger.info("Состояние очищено и сброшено к умолчанию")
            return result
        except Exception as e:
            self.logger.error(f"Ошибка очистки состояния: {str(e)}")
            return False

    def get_backup_list(self):
        """
        Возвращает список доступных резервных копий.

        Returns:
            list: Список файлов резервных копий с информацией
        """
        backups = []
        try:
            if not os.path.exists(self.backup_dir):
                return backups

            for filename in os.listdir(self.backup_dir):
                if filename.startswith("state_backup_") and filename.endswith(".json"):
                    file_path = os.path.join(self.backup_dir, filename)
                    file_stats = os.stat(file_path)

                    backups.append(
                        {
                            "filename": filename,
                            "path": file_path,
                            "size": file_stats.st_size,
                            "created": datetime.fromtimestamp(
                                file_stats.st_mtime
                            ).isoformat(),
                            "timestamp": file_stats.st_mtime,
                        }
                    )

            # Сортируем по времени создания (новые первыми)
            backups.sort(key=lambda x: x["timestamp"], reverse=True)

        except Exception as e:
            self.logger.error(f"Ошибка получения списка резервных копий: {str(e)}")

        return backups

    def restore_from_backup(self, backup_filename):
        """
        Восстанавливает состояние из резервной копии.

        Args:
            backup_filename (str): Имя файла резервной копии

        Returns:
            bool: True если восстановление прошло успешно, иначе False
        """
        try:
            backup_path = os.path.join(self.backup_dir, backup_filename)

            if not os.path.exists(backup_path):
                self.logger.error(f"Резервная копия не найдена: {backup_path}")
                return False

            # Создаем резервную копию текущего состояния
            if os.path.exists(self.state_file):
                self._create_backup()

            # Загружаем состояние из резервной копии
            with open(backup_path, "r", encoding="utf-8") as f:
                backup_state = json.load(f)

            # Валидируем и применяем
            self.state = self._validate_and_migrate_state(backup_state)

            # Сохраняем восстановленное состояние
            result = self.save_state()

            if result:
                self.logger.info(
                    f"Состояние восстановлено из резервной копии: {backup_filename}"
                )

            return result

        except Exception as e:
            self.logger.error(f"Ошибка восстановления из резервной копии: {str(e)}")
            return False

    def validate_state_integrity(self):
        """
        Проверяет целостность состояния.

        Returns:
            dict: Результат проверки с деталями
        """
        issues = []
        warnings = []

        try:
            # Проверяем основные разделы
            required_sections = ["user", "settings", "course_plan", "learning"]
            for section in required_sections:
                if section not in self.state:
                    issues.append(f"Отсутствует раздел: {section}")
                elif not isinstance(self.state[section], dict):
                    issues.append(f"Раздел {section} должен быть словарем")

            # Проверяем массивы
            if "completed_lessons" not in self.state:
                issues.append("Отсутствует массив completed_lessons")
            elif not isinstance(self.state["completed_lessons"], list):
                issues.append("completed_lessons должен быть массивом")

            # Проверяем metadata
            if "metadata" not in self.state:
                warnings.append("Отсутствуют метаданные")

            # Проверяем настройки
            if "first_run" not in self.state.get("settings", {}):
                warnings.append("Отсутствует флаг первого запуска")

            # Проверяем версию
            version = self.state.get("settings", {}).get("version")
            if version != "2.0":
                warnings.append(f"Устаревшая версия состояния: {version}")

            # Проверяем размер состояния
            state_str = json.dumps(self.state)
            if len(state_str) > 1024 * 1024:  # 1MB
                warnings.append("Состояние превышает 1MB")

            result = {
                "valid": len(issues) == 0,
                "issues": issues,
                "warnings": warnings,
                "size_bytes": len(state_str),
                "sections_count": len(
                    [k for k in self.state.keys() if isinstance(self.state[k], dict)]
                ),
                "completed_lessons_count": len(self.state.get("completed_lessons", [])),
                "checked_at": datetime.now().isoformat(),
            }

            if result["valid"]:
                self.logger.info("Проверка целостности состояния прошла успешно")
            else:
                self.logger.warning(f"Проверка целостности выявила проблемы: {issues}")

            return result

        except Exception as e:
            self.logger.error(f"Ошибка проверки целостности состояния: {str(e)}")
            return {
                "valid": False,
                "issues": [f"Ошибка проверки: {str(e)}"],
                "warnings": [],
                "error": str(e),
            }
