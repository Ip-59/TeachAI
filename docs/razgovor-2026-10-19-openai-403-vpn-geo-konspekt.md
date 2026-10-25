# Конспект: OpenAI 403 / VPN / geo (19.10.2026, вечер на работе)

**Проект:** `/media/ip-59/64GB/TeachAI`  
**Связанный чат:** `docs/chat_logs/1-261019 chat_log.md` (основная сессия куратора)  
**Контекст:** после этапа 1 (фикс теста) при проверке в Jupyter упала генерация вопросов.

Папка `docs/` в git не входит — файл на флешке для продолжения дома.

---

## Симптом

```
Error code: 403 - {'error': {'code': 'unsupported_country_region_territory',
 'message': 'Country, region, or territory not supported',
 'type': 'request_forbidden'}}
```

Проявляется при генерации теста (и любом вызове OpenAI API), не из‑за кода этапа 1.

---

## Что проверили

| Проверка | Результат |
|----------|-----------|
| VPN включён | да |
| IP из Jupyter / venv (`api.ipify.org`) | `213.193.255.154` — **London, GB** |
| `OPENAI_CONNECTION_MODE` | `direct` (прокси в приложении нет — ожидается VPN ОС) |
| Вывод при старте TeachAI | `OpenAI: прямое подключение (без прокси…)` |
| `models.list` / `chat.completions` из `venv_H_L` и `venv_W_L` с ключом из `.env` | тот же **403** |
| platform.openai.com / home | org Personal, **$9.67**, лимит $120, **usage = 0**, баннера блокировки нет |
| Сырой HTTP к `api.openai.com/v1/models` с Bearer | 403, тело то же; cf-ray `…-ARN` (Stockholm edge) |

**Вывод:** сеть уже «разрешённая» (GB). OpenAI режет **API по ключу/проекту/org**, а не «VPN не работает». Веб-кабинет ≠ политика API.

Ключ в `.env`: `sk-proj-…` (длина ~164), хвост для сверки: `…HwUA`.

---

## Почему кабинет «зелёный», а API — 403

- Кредиты есть, запросов 0 — согласуется с тем, что API не принимается.
- UI часто открывается через VPN; API для org с «неподдерживаемым» регионом биллинга/налогов всё равно отвечает `unsupported_country_region_territory` без баннера на home.

---

## План действий дома (по порядку)

1. **Сверить ключ** с Platform → API keys: есть ли ключ с хвостом `…HwUA` у этой Personal org. Если нет — в `.env` чужой/старый ключ.
2. **Создать новый secret key** в этой org при VPN → заменить `OPENAI_API_KEY` в `.env` → **Restart kernel** → снова тест/`models.list`.
3. Settings → Organization / Billing: страна налогового адреса / payment. Если РФ — VPN не спасёт API.
4. Если **новый** ключ снова 403 → обход для TeachAI: **шлюз** (GPTunnel как в бенчмарке, или OpenRouter) + `base_url` в клиенте (`content_utils.py` сейчас без `OPENAI_BASE_URL`).

Не тратить время на «починить VPN» — IP уже London.

---

## Конфиг на момент обрыва

```env
OPENAI_CONNECTION_MODE=direct
OPENAI_USE_PROXY=false
# OPENAI_PROXY не используется в direct
LLM_MODEL=gpt-4o-mini   # (типично)
```

Бенчмарк уже умел GPTunnel (`model_benchmark/`, `base_url: https://gptunnel.ru/v1`); основной TeachAI — прямой `api.openai.com`.

---

## Решение (20.10.2026, рабочий ПК)

Реализован маршрут **GPTunnel** в основном TeachAI (не только бенчмарк):

- модуль `llm_route.py`, `OPENAI_API_ROUTE=gptunnel` в `.env`;
- выбор на стартовом дашборде (direct / GPTunnel);
- smoke-test chat через шлюз — OK.

Отчёт: `docs/otchet-gptunnel-route-2026-10-20.md`.

VPN на мобильном интернете по-прежнему не считать «починенным»; на этом ПК работать через GPTunnel.

---

## Бриф на продолжение

```
Маршрут LLM: docs/otchet-gptunnel-route-2026-10-20.md
На рабочем ПК — GPTunnel; дома можно direct.
Повторить проверку этапа 1 (тест) через GPTunnel → этап 2 (force КЗ).
Конспект доработок: docs/razgovor-2026-10-19-kurator-dorabotki-plan-konspekt.md
```
