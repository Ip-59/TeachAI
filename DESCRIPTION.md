# TeachAI — Project Description (English)

This document is derived **from source-code analysis** of the repository (May 2026). Outdated README files were not used as factual sources. Claims not supported by code or explicit config files (`courses.json`, `requirements.txt`, `.env.sample`) are omitted.

**Russian full report:** [ОПИСАНИЕ_ПРОЕКТА_TEACHAI.md](ОПИСАНИЕ_ПРОЕКТА_TEACHAI.md)  
**Quick start:** [README.md](README.md)

---

## Purpose and goals

### Purpose

Build an **interactive AI teacher** for learning Python and related topics inside **Jupyter Notebook**: a personalized learning path, on-demand generated materials, and knowledge checks—without a dedicated application server or a custom trained model.

Evidence in code: `engine.py` (system coordination), `content_generator.py` (lessons and Q&A via OpenAI), `interface.py` (Jupyter UI).

### Implemented goals

| Goal | Implementation |
|------|----------------|
| Learner profile | `SetupInterface`, `UserProfileManager` |
| Course catalog | `courses.json`, `CourseDataManager` |
| LLM-built syllabus | `CoursePlanGenerator` → `state["course_plan"]` |
| Lesson content | `LessonGenerator` + `ContentFormatterFinal` |
| In-lesson interaction (Q&A, examples, explanations, concepts) | `LessonInteraction`, specialized generators |
| On-topic questions | `RelevanceChecker` |
| Post-lesson quiz | `Assessment`, `AssessmentGenerator` |
| Code practice with auto-check | `ControlTasksGenerator`, `InteractiveCellWidget`, `ResultChecker` |
| Progress and resume | `LearningProgressManager`, `StartupDashboard` |
| Activity logging | `Logger` under `logs/` |
| Local persistence | `data/state.json` |

**Not** implemented: model fine-tuning, central app server, external textbook parsing as the main content source.

---

## Technology stack

| Layer | Technologies |
|-------|----------------|
| Runtime | Python 3, Jupyter, IPython, **ipywidgets** |
| LLM | **OpenAI API** (`openai`), default model **`gpt-4o-mini`** (`LLM_MODEL`), optional **`VALIDATION_MODEL`** for control tasks |
| HTTP | **httpx** with mandatory **proxy** (`OPENAI_PROXY` / `HTTPS_PROXY`) |
| Config | **python-dotenv** (`.env`) |
| Content rendering | markdown, pygments, latex2mathml, custom formatters |
| Subject libs (for running generated code) | pandas, numpy, matplotlib, seaborn, scipy, scikit-learn, tensorflow, flask, requests, yfinance (`requirements.txt`) |
| Storage | JSON (`courses.json`, `data/state.json`, `logs/*.json`) |

---

## Architecture

### Entry and orchestration

- **`TeachAI.ipynb`** / **`run_teachai.py`** → **`TeachAIEngine`** (`engine.py`)
- On repeat launch: **`StartupDashboard`** first; full init on “Continue learning”
- On first launch: **`initialize()`** then profile setup

### Major components

```
TeachAIEngine
├── ConfigManager          (.env, logs/, data/)
├── StateManager           (facade)
│   ├── UserProfileManager
│   ├── LearningProgressManager
│   └── CourseDataManager  (+ courses.json)
├── ContentGenerator       (facade → OpenAI generators)
├── Assessment
├── Logger
├── LoadingManager
├── StartupDashboard
└── UserInterface          (facade)
    ├── SetupInterface
    ├── LessonInterface    (Display, Navigation, Interaction)
    ├── AssessmentInterface
    └── CompletionInterface
```

### UI states (`InterfaceState`)

`INITIAL_SETUP` → `COURSE_SELECTION` → `LESSON_VIEW` → (`ASSESSMENT`, Q&A, …) → `COURSE_COMPLETION`

### Content generators (under `ContentGenerator`)

`CoursePlanGenerator`, `LessonGenerator`, `ExamplesGenerator`, `ExplanationGenerator`, `ConceptsGenerator`, `QAGenerator`, `AssessmentGenerator`, `RelevanceChecker` — all extend **`BaseContentGenerator`** (shared OpenAI client, retries, lesson text cleanup).

---

## AI teacher pipeline

### 1. Startup

`start_jupyter()` → `load_dotenv` → `TeachAIEngine.start()` → dashboard or initial setup.

### 2. Profile and syllabus

User sets name, total hours, lesson length, communication style (`formal` | `friendly` | `casual` | `brief`).  
Selected course from **`courses.json`** (5 courses).  
`generate_course_plan()` returns JSON: sections → topics → lessons; saved to state.

### 3. Lesson display

`LessonDisplay.show_lesson`:

1. Cache key `section:topic:lesson`
2. Use `lesson_content_cache` in state, in-memory cache, or call **`LessonGenerator`**
3. LLM returns markdown → **`ContentFormatterFinal`** → HTML; store **`raw_content`**
4. Update progress, log to `lesson_history.md`
5. Render ipywidgets UI (lesson body, actions, navigation)

**Note:** automatic `cell_integration` in lessons is **disabled** (`CELLS_INTEGRATION_AVAILABLE = False` in `lesson_display.py`). Control tasks use **`ControlTasksInterface`**.

### 4. User question

`LessonInteraction.setup_enhanced_qa_container`:

1. Increment question counter per lesson
2. **`check_question_relevance`** (breadcrumb stripping, HTML cleanup, LLM JSON)
3. If irrelevant → polite redirect; if relevant → **`QAGenerator.answer_question`**
4. After more than 3 questions → reminder to follow the course plan

### 5. Quiz

`AssessmentGenerator` builds questions from lesson text.  
Pass threshold: **score > 40%** (`LearningProgressManager`, `assessment_results_handler`).  
Passing the quiz alone does **not** complete the lesson.

### 6. Control task

Generated task + **`InteractiveCellWidget`**; execution checked by **`ResultChecker`** (multiple check types).  
Success → `control_tasks[lesson_id].is_correct = true`.

### 7. Lesson completion

Lesson is **completed** when:

- (**test score > 40%** AND **control task correct**), **or**
- manual flag in `lesson_completion_status`

Then `get_next_lesson()` or course completion screen.

---

## Course catalog (`courses.json`)

| ID | Title |
|----|-------|
| `python-basics` | Python basics |
| `data-analysis` | Data analysis with Python |
| `machine-learning` | Introduction to machine learning |
| `web-development` | Web development with Python (Flask) |
| `python-for-finance` | Python for finance |

---

## Notable implementation features

1. Facade pattern for UI and content generation with backward-compatible APIs  
2. Persistent + in-memory lesson caching to reduce API calls  
3. Separate `raw_content` vs formatted HTML for LLM downstream tasks  
4. Relevance gate before Q&A with course/section/topic header removal  
5. Dual mastery check: quiz + runnable code task  
6. Communication-style-aware prompts  
7. API retries with backoff  
8. Structured logs under `logs/`  
9. Lazy heavy initialization after dashboard  
10. LaTeX/tables rendering for `widgets.HTML` in Jupyter  

---

## Limitations (from code)

- Requires OpenAI API key and proxy  
- No multi-device sync  
- Content correctness depends on the external LLM  
- `archive/` is not part of runtime  

---

## Documentation files compared

| File | Language | Role |
|------|----------|------|
| `README.md` | Russian | Short practical guide |
| `ОПИСАНИЕ_ПРОЕКТА_TEACHAI.md` | Russian | Full report for committee / reviewers |
| `DESCRIPTION.md` | English | Same facts for international readers |

The duplication exists for **audience and language**, not because the projects differ.

---

*Description based on repository source analysis; not generated from legacy markdown docs.*
