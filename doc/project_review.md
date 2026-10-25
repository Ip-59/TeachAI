# TeachAI — Comprehensive Code Review

## Project Overview

TeachAI is a Jupyter-notebook-based educational platform that generates personalized Python programming courses using LLM APIs (OpenAI / Azure / OpenRouter). It features:
- Dynamic course plan creation, lesson generation, assessments, Q&A, and interactive code cells
- An `ipywidgets`-based UI rendered inside Jupyter
- State persistence via JSON, activity/assessment logging

The codebase spans **~40 Python files** and ~15 000 lines of code.

---

## 🔴 Critical Issues

### 1. Two Parallel, Incompatible LLM Client Systems

> [!CAUTION]
> The project contains **two completely separate** mechanisms for calling the LLM API, with different models, different proxy logic, and different error handling.

| Aspect | `LLMGenerator` ([llm.py](file:///media/ip-59/64GB/TeachAI/llm.py)) | `BaseContentGenerator` ([content_utils.py](file:///media/ip-59/64GB/TeachAI/content_utils.py)) |
|---|---|---|
| **Model** | `os.getenv("LLM_MODEL", "gpt-4")` | Hard-coded `gpt-3.5-turbo-16k` |
| **Proxy** | Reads 5 env vars, configures `httpx.Client` with custom `HTTPTransport` | Reads 3 env vars, creates its own `httpx.Client` |
| **Used by** | `ContentGenerator` (facade), `CoursePlanGenerator` (indirectly) | Every `*Generator` class: `LessonGenerator`, `QAGenerator`, `AssessmentGenerator`, `ExplanationGenerator`, `ExamplesGenerator`, `ConceptsGenerator`, `ControlTasksGenerator`, `RelevanceChecker` |
| **Error handling** | `_safe_chat` with region-restriction detection | Generic `try/except` |

**Impact**: If a user sets `LLM_MODEL=gpt-4o` via env var, course plans will use it but all other content silently uses `gpt-3.5-turbo-16k`. The proxy configuration may also differ. This is almost certainly a bug, not a design choice.

**Recommendation**: Eliminate `BaseContentGenerator.make_api_request` and have all generators use the `LLMGenerator` singleton.

---

### 2. `exec()` Without Sandboxing

> [!CAUTION]
> User-submitted code is executed via `exec()` with **no sandboxing** in multiple files.

- [control_tasks_generator.py](file:///media/ip-59/64GB/TeachAI/control_tasks_generator.py) — `validate_task_execution()` (line 543), `_parse_control_task_response()` (line 342)
- [interactive_cell_logic.py](file:///media/ip-59/64GB/TeachAI/interactive_cell_logic.py)
- [control_tasks_interface.py](file:///media/ip-59/64GB/TeachAI/control_tasks_interface.py)

In `_parse_control_task_response`, the LLM's generated `solution_code` is executed as part of validation — an LLM output going straight into `exec()`. Even though `eval()` uses `{"__builtins__": {}}`, `exec()` does not, giving full access to `os`, `subprocess`, etc.

**Recommendation**: At minimum pass `{"__builtins__": {}}` to `exec()`, or use `RestrictedPython` / `subprocess` with resource limits.

---

### 3. Three Near-Identical Content Formatters

> [!WARNING]
> There are **three copies** of essentially the same Markdown→HTML formatter:

| File | Class | Lines |
|---|---|---|
| [content_formatter.py](file:///media/ip-59/64GB/TeachAI/content_formatter.py) | `ContentFormatter` | 373 |
| [content_formatter_v2.py](file:///media/ip-59/64GB/TeachAI/content_formatter_v2.py) | `ContentFormatterV2` | 375 |
| [content_formatter_final.py](file:///media/ip-59/64GB/TeachAI/content_formatter_final.py) | `ContentFormatterFinal` | 488 |

`ContentFormatter` and `ContentFormatterV2` are copied verbatim (same CSS, same logic). `ContentFormatterFinal` adds:
- `font-weight: 900 !important` on virtually every element (headings, paragraphs, lists, code, *even italics*)
- Black-on-white theme with white-on-black code blocks
- `text-shadow` on everything

All three duplicate the same Markdown parsing (headings, bold, italic, lists, code blocks) with minor bug-fix variations.

**Recommendation**: Keep only `ContentFormatterFinal`, delete the other two. Better yet, replace the hand-rolled Markdown parser with the `markdown` library + `Pygments` for syntax highlighting.

---

## 🟡 Significant Issues

### 4. Massive CSS Duplication

CSS styles are defined as Python strings in at least **7 different files**:

| File | CSS Area |
|---|---|
| `content_formatter.py` | Lesson content (148 lines) |
| `content_formatter_v2.py` | Same (148 lines, identical copy) |
| `content_formatter_final.py` | Same (211 lines, high-contrast variant) |
| `content_utils.py` | `BASE_CSS_STYLES`, `EXAMPLES_CSS_STYLES`, `EXPLANATION_CSS_STYLES` |
| `qa_generator.py` | QA answer styles |
| `relevance_checker.py` | Non-relevant question styles |
| `assessment.py` | Assessment/quiz styles |
| `startup_dashboard.py` | Dashboard styles (inline) |

**Total**: ~800+ lines of duplicated CSS embedded in Python strings. Every style change requires hunting through multiple files.

**Recommendation**: Extract all CSS to a single `styles.py` module or, preferably, a `.css` file loaded at runtime.

---

### 5. Diagnostic `print()` Statements Throughout Production Code

> [!WARNING]
> The codebase is littered with `print()` debugging output that goes to Jupyter's stdout.

Examples from [control_tasks_generator.py](file:///media/ip-59/64GB/TeachAI/control_tasks_generator.py):
```python
print("\n" + "="*80)
print("🔍 [DIAGNOSTIC] generate_control_task ВЫЗВАН")
print(f"Длина промпта: {len(prompt)} символов")
print(f"Первые 500 символов: {prompt[:500]}...")
```

Similar statements appear in `assessment_generator.py`, `course_plan_generator.py`, `lesson_generator.py`, `examples_generator.py`, `concepts_generator.py` and others.

**Impact**: These contaminate the notebook output with debugging noise and may expose prompt internals / API responses to end users.

**Recommendation**: Replace all diagnostic `print()` with `logging.debug()`. They can then be enabled via log level when needed, without affecting end users.

---

### 6. Regex Bug in `_remove_greetings`

In [qa_generator.py](file:///media/ip-59/64GB/TeachAI/qa_generator.py), the `_remove_greetings` method uses a broad regex to strip greetings from LLM responses. Patterns like:

```python
r"^(Привет|Здравствуйте|Добрый день|...)[\s\S]*?[.!?\n]"
```

The `[\s\S]*?` can match across multiple sentences. If the LLM starts with "Здравствуйте, сегодня мы рассмотрим...", the entire first sentence (including the actual content) gets stripped.

**Recommendation**: Replace `[\s\S]*?` with `[^.!?\n]*?` to limit matching to the greeting sentence only.

---

### 7. `_clean_content` Destroys Existing HTML

In all three content formatters, `_clean_content` strips `<div>` and `<p>` tags unconditionally:

```python
content = re.sub(r'<div[^>]*>|</div>', '', content)
content = re.sub(r'<p[^>]*>|</p>', '', content)
```

If the LLM returns valid HTML (which it sometimes does), this destroys the structure before the Markdown parser creates new (possibly incorrect) tags.

Additionally, `ContentFormatter._clean_content` strips language identifiers from code fences:
```python
content = re.sub(r'```\w*\n?', '```', content)
```
This removes the `python` language hint, making all code blocks default to `python` anyway — but losing the original signal.

---

### 8. `ContentFormatterFinal` CSS Over-Engineering

The "high contrast" theme in [content_formatter_final.py](file:///media/ip-59/64GB/TeachAI/content_formatter_final.py) applies extreme styling:

```css
.lesson-content * { color: #000000 !important; }
.lesson-content, .lesson-content * {
    text-shadow: 0 0 1px rgba(0,0,0,0.5) !important;
}
```

- `font-weight: 900 !important` on **everything** including italics and paragraphs makes all text look the same
- The wildcard `*` selectors with `!important` make it impossible to override styles for specific elements
- `text-shadow` on all elements adds visual noise

---

## 🔵 Code Quality & Architecture

### 9. Hand-Rolled Markdown Parser

All three formatters implement a basic Markdown→HTML converter using regex:
- `# heading` → `<h1>`
- `**bold**` → `<strong>`
- `*italic*` → `<em>`
- `- item` → `<ul><li>`

This approach has known issues:
- Processing `__bold__` as `<strong>` conflicts with code placeholder names (`__CODE_BLOCK_0__`)
- Italic regex `*text*` can collide with bold regex `**text**` (greedy matching)
- No support for nested lists, numbered lists, tables, links, or images
- The `ContentFormatterV2` added a workaround for the placeholder collision but it's fragile

**Recommendation**: Use `import markdown` (standard library-compatible, pip install) instead. It handles all edge cases and supports extensions for code highlighting.

---

### 10. `BaseContentGenerator` Re-Initializes for Every Generator Instance

Each `*Generator` class inherits from `BaseContentGenerator` and calls `super().__init__(api_key)`, which creates:
- A new `httpx.Client` with proxy configuration
- A new `OpenAI` client instance

If the system creates ~8 generator instances (lesson, QA, assessment, explanation, examples, concepts, control tasks, relevance), it creates **8 separate HTTP clients** and **8 separate OpenAI SDK instances**. This wastes connections, memory, and makes proxy changes inconsistent.

**Recommendation**: Use a shared `LLMGenerator` singleton and inject it into generators via constructor.

---

### 11. Logging System

The [logger.py](file:///media/ip-59/64GB/TeachAI/logger.py) `Logger` class is well-structured for its purpose (JSON log files for activities, assessments, questions). However:

- It reads the entire log file, appends to the list, and writes the whole file back on every event (`_load_json_log` + `_save_json_log`). For long courses with many activities, this becomes O(n²) in total I/O.
- The `log_lesson()` method truncates lesson content to 1000 chars — reasonable, but the magic number should be a constant.

---

### 12. Prompt Engineering Patterns

The prompts are extensive and in Russian (appropriate for the target audience). Key observations:

- **Prompt repetition**: The same formatting instructions (e.g., "КАЖДЫЙ ОПЕРАТОР НА ОТДЕЛЬНОЙ СТРОКЕ!", "НЕ ПИШИ КОД В ОДНУ СТРОКУ!") are repeated 5–8 times within a single prompt in [lesson_generator.py](file:///media/ip-59/64GB/TeachAI/lesson_generator.py). While repetition can help, this level is excessive and inflates token usage.
- **Python comments leaking into prompts**: Lines like `# Ограничиваем длину для запроса` appear inside f-strings and get sent to the LLM as part of the prompt.
- **Quadruple-brace escaping**: In [control_tasks_generator.py](file:///media/ip-59/64GB/TeachAI/control_tasks_generator.py), JSON examples use `{{{{` and `}}}}` for f-string escaping, which is correct Python but hard to read. Consider using `str.format()` or `string.Template` for prompt construction.

---

## 📋 Summary of Recommendations (Prioritized)

| Priority | Issue | Action |
|---|---|---|
| 🔴 P0 | Two parallel LLM clients | Eliminate `BaseContentGenerator.make_api_request`; use `LLMGenerator` everywhere |
| 🔴 P0 | `exec()` on LLM output | Sandbox `exec()` calls; at minimum restrict `__builtins__` |
| 🔴 P0 | Hardcoded `gpt-3.5-turbo-16k` | Use env-var model from `LLMGenerator` consistently |
| 🟡 P1 | 3 duplicate formatters | Delete v1 and v2; keep only `ContentFormatterFinal` |
| 🟡 P1 | 800+ lines of duplicated CSS | Extract to single `styles.py` |
| 🟡 P1 | `print()` debugging in production | Replace with `logging.debug()` |
| 🟡 P1 | `_remove_greetings` regex bug | Limit match to greeting sentence only |
| 🔵 P2 | Hand-rolled Markdown parser | Replace with `markdown` library |
| 🔵 P2 | Multiple HTTP clients | Share a single client across all generators |
| 🔵 P2 | CSS `font-weight: 900 !important` everywhere | Tone down; use proper hierarchy |
| 🔵 P2 | O(n²) log I/O | Append-only JSON Lines format |
| ⚪ P3 | Prompt repetition/token waste | Consolidate repeated instructions |
| ⚪ P3 | Code comments leaking into prompts | Audit f-string contents |

---

## ✅ What Works Well

- **Modular architecture**: Clear separation into generators, interfaces, formatters, and state management
- **Facade pattern** in `UserInterface` and `ContentGenerator` — good for backward compatibility
- **Course plan validation** in `CoursePlanGenerator._validate_and_fix_course_plan` — robustly handles malformed LLM output
- **Assessment answer randomization** — clever workaround for LLM non-compliance
- **Control task validation** — executing `solution_code` to verify `expected_output` matches is a solid idea (just needs sandboxing)
- **Startup dashboard** — well-designed with progress bars, statistics, and visual hierarchy
- **State persistence** — reliable JSON-based state management with auto-save
- **Logging** — structured JSON logs for activities, assessments, and questions
