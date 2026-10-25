# Мини-отчёт: маршрут LLM через GPTunnel + выбор на дашборде

**Дата:** 2026-10-20  
**Контекст:** на рабочем ПК (мобильный интернет) OpenAI API даёт 403 geo даже при VPN/London IP; дома (оптоволокно) direct работает. Нужно не бить в api.openai.com с этого ПК.

---

## Решение

1. **Маршрут LLM** (`OPENAI_API_ROUTE`): `direct` | `gptunnel` | `proxy`.
2. Фабрика клиента в `llm_route.py`: для GPTunnel — `base_url`, снятие `Bearer`, `useWalletBalance` (как в бенчмарке).
3. На стартовом дашборде — RadioButtons: напрямую OpenAI / через GPTunnel (пишет preference в `data/llm_route_preference.json`).
4. В `.env` на этом ПК: `OPENAI_API_ROUTE=gptunnel` + уже существующий `GPTUNNEL_API_KEY`.

Источник истины — `.env`; кнопка на дашборде — удобный override до `engine.initialize()`.

---

## Проверка

Smoke-test из `venv_H_L`: маршрут gptunnel → `chat.completions` → ответ «Хорошо.» (OK).

---

## Изменённые файлы

| Файл | Роль |
|------|------|
| `llm_route.py` | новый: маршрут, клиент, UI-селектор |
| `config.py` | делегирование в llm_route, валидация ключей по маршруту |
| `content_utils.py` | `create_openai_client` + `extra_body` |
| `startup_dashboard.py` | выбор маршрута до init |
| `interface_utils.py` | понятные ошибки 403 / gptunnel |
| `run_teachai.py` | reload `llm_route` |
| `.env.sample` | документация маршрута |
| `.env` | локально `OPENAI_API_ROUTE=gptunnel` (не в git) |

Заглушек нет.

---

## Как пользоваться

1. Restart kernel, запустить TeachAI.
2. На дашборде выбрать **GPTunnel** (уже default из .env) → «Продолжить обучение».
3. Дома: выбрать **напрямую OpenAI** или в `.env` поставить `OPENAI_API_ROUTE=direct`.

---

## Следующее

- Повторить ручную проверку этапа 1 (тест без переклика) уже через GPTunnel.
- Затем этап 2 плана куратора (force вход в КЗ).
