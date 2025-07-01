# TeachAI - Настройка виртуального окружения и MCP

## Проблема

Пользователь пытался создать виртуальное окружение командой
`python -m venv venv`, но получал ошибку.

## Диагностика

- Команда `python` не работает в Windows PowerShell
- Команда `py` работает корректно (Python Launcher)
- Политика выполнения PowerShell: `RemoteSigned` (нормально)

## Решение

1. **Использовать `py` вместо `python`:**

   ```powershell
   py -m venv venv
   ```

2. **Активировать виртуальное окружение:**

   ```powershell
   .env\Scripts\Activate.ps1
   ```

3. **Обновить pip:**

   ```powershell
   py -m pip install --upgrade pip setuptools wheel
   ```

## Проблемы при установке

- Ошибка с `pywin32` - файл занят другим процессом
- Ошибка с `notebook` - файл занят другим процессом
- Возможные причины: антивирус, фоновые процессы Windows

## Рекомендации

1. **Перезагрузить систему** для освобождения занятых файлов

2. **После перезагрузки:**

   ```powershell
   .env\Scripts\Activate.ps1
   py -m pip install -r requirements.txt
   ```

## Настройка MCP (Model Context Protocol)

### Установленные компоненты

- ✅ **mcp** - основная библиотека MCP
- ✅ **httpx-sse** - для Server-Sent Events
- ✅ **pydantic-settings** - для конфигурации
- ✅ **starlette** - веб-фреймворк
- ✅ **uvicorn** - ASGI сервер

### Созданные файлы

- `mcp_config.json` - конфигурация MCP серверов
- `mcp_integration.py` - интеграция MCP с TeachAI
- `test_mcp_integration.py` - тесты интеграции

### Возможности MCP

- 🔍 **Поиск в интернете** через Brave Search
- 🌤️ **Получение погоды** через OpenWeather API
- 📁 **Работа с файлами** через filesystem сервер
- ⚙️ **Расширенная конфигурация** модели

### Результаты тестирования

```text
✅ Доступные серверы: ['filesystem', 'brave-search', 'weather']
✅ Модель по умолчанию: gpt-4
✅ Температура: 0.7
✅ Максимум токенов: 4000
✅ Все тесты пройдены успешно!
```

### Использование

```python
from mcp_integration import TeachAIMCPIntegration

# Инициализация
mcp = TeachAIMCPIntegration()

# Поиск в интернете
results = await mcp.search_web("Python programming")

# Получение погоды
weather = await mcp.get_weather("Москва")

# Список доступных серверов
servers = mcp.get_available_servers()
```

### Следующие шаги для полной интеграции

1. **Получить API ключи:**
   - Brave Search API для поиска
   - OpenWeather API для погоды
2. **Настроить реальные серверы MCP**
3. **Интегрировать в основной движок TeachAI**

## Важные команды для Windows

- `py --version` - проверить версию Python
- `py -m venv venv` - создать виртуальное окружение
- `.env\Scripts\Activate.ps1` - активировать окружение
- `py -m pip install --no-cache-dir` - установить без кэша (если проблемы)

## Статус проекта TeachAI

- Система стабильна (согласно PROJECT_STATUS.md)
- Все критические ошибки исправлены
- MCP интеграция настроена и протестирована
- Готов к работе после настройки окружения
