# 🏫 VAPS AI Agent — School Kiosk Service

A production-grade, **CSV-first FastAPI service** powering an intelligent school kiosk. It provides role-aware AI guidance for **Student, Parent, Teacher, Visitor, and Alumni / Ex-Employee** journeys through a dynamic LangGraph orchestrator with 29 specialized agents, statistical prediction, and personalized recommendations.

> [!NOTE]
> This is a demonstration service. It does not access live ERP records, execute payments, send messages, submit requests, or modify school data.

---

## 📑 Table of Contents

- [Architecture Overview](#-architecture-overview)
- [Quick Start](#-quick-start)
- [Project Structure](#-project-structure)
- [AI Orchestration Flow](#-ai-orchestration-flow)
- [Modules](#-modules)
- [Providers](#-providers)
- [Roles and Data Boundaries](#-roles-and-data-boundaries)
- [Payment and Request Safety](#-payment-and-request-safety)
- [API Reference](#-api-reference)
- [Tests and Quality Checks](#-tests-and-quality-checks)
- [Future ERP API Adapter](#-future-erp-api-adapter)
- [Documentation](#-documentation)

---

## 🏗 Architecture Overview

The service is built on a **modular, engine-driven architecture** with clear separation of concerns:

| Layer | Components | Responsibility |
|---|---|---|
| **API Gateway** | FastAPI routes, Pydantic schemas | HTTP interface, request validation |
| **Copilot** | `AICopilot`, `QueryPlanningEngine` | Session management, dynamic execution planning |
| **Orchestrator** | LangGraph `StateGraph` with 7 nodes | Stateful, conditional graph execution |
| **Agents** | 29 role-aware agents across 4 role groups | Domain-specific query processing with tool invocation |
| **Engines** | Intent, Entity, Context, Reasoning, Response, Validation | NLP analysis, reasoning traces, safe response synthesis |
| **Prediction** | `PredictionEngine` (4 models) | Statistical risk/performance scoring |
| **Recommendation** | `RecommendationEngine` (5 strategies) | Personalized, actionable guidance |
| **Providers** | NVIDIA NIM, Groq, Deterministic | LLM provider chain with automatic fallback |
| **RAG** | Qdrant vector store, embedding pipeline | Document retrieval for policies and circulars |
| **Data** | CSV repositories, Tool registry | Grounded data access from school records |

---

## 🚀 Quick Start

```bash
# 1. Create and activate virtual environment
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate

# 2. Install dependencies
python -m pip install -r requirements.txt

# 3. Configure environment
copy .env.example .env        # Windows
# cp .env.example .env        # macOS/Linux

# 4. Seed demonstration data
python seed_demo_csv.py

# 5. Start the service
uvicorn app.main:app --reload
```

Open `http://127.0.0.1:8000` for the dashboard or `http://127.0.0.1:8000/docs` for the OpenAPI documentation.

---

## 📂 Project Structure

```
AI_kisok/
├── app/
│   ├── agents/                  # 29 role-aware AI agents
│   │   ├── base.py              #   BaseAgent ABC & AgentOutput model
│   │   ├── registry.py          #   AgentRegistry — central agent lookup
│   │   ├── student/             #   9 student/parent agents
│   │   ├── teacher/             #   8 teacher/staff agents
│   │   ├── visitor/             #   6 visitor/applicant agents
│   │   └── alumni/              #   6 alumni/ex-employee agents
│   ├── ai/                      # AI utilities
│   ├── api/                     # API layer
│   ├── copilot/                 # AI Copilot & Query Planner
│   │   ├── copilot.py           #   AICopilot — chat entry point
│   │   └── planner.py           #   QueryPlanningEngine — dynamic routing
│   ├── core/                    # Core infrastructure
│   │   ├── config.py            #   CoreSettings (env-driven)
│   │   ├── logging.py           #   AgentAuditLog structured logging
│   │   └── security.py          #   SecurityValidator & role normalization
│   ├── engines/                 # Processing engines
│   │   ├── intent_engine.py     #   Intent detection
│   │   ├── entity_engine.py     #   Entity extraction
│   │   ├── context_engine.py    #   Session context management
│   │   ├── reasoning_engine.py  #   Step-by-step reasoning traces
│   │   ├── response_engine.py   #   Human-friendly response formatting
│   │   ├── validation_engine.py #   Request & response safety checks
│   │   └── data_analysis_engine.py # Data aggregation & analysis
│   ├── graph/                   # LangGraph orchestrator
│   │   ├── graph.py             #   StateGraph definition & compilation
│   │   ├── nodes.py             #   7 graph node functions
│   │   └── state.py             #   OrchestratorState TypedDict
│   ├── prediction/              # Statistical prediction engine
│   │   ├── base.py              #   PredictionResult model
│   │   └── engine.py            #   4 prediction models
│   ├── providers/               # LLM provider adapters
│   │   ├── base.py              #   BaseLLMProvider ABC
│   │   ├── deterministic.py     #   Zero-dependency fallback
│   │   ├── groq.py              #   Groq chat-completions adapter
│   │   ├── nim.py               #   NVIDIA NIM adapter
│   │   └── router.py            #   ProviderRouter with fallback chain
│   ├── rag/                     # RAG pipeline
│   │   ├── embeddings.py        #   Embedding generation
│   │   ├── ingestion.py         #   Document ingestion pipeline
│   │   ├── qdrant.py            #   Qdrant vector store client
│   │   └── retriever.py         #   Context retrieval
│   ├── recommendation/          # Recommendation engine
│   │   ├── base.py              #   RecommendationResult model
│   │   └── engine.py            #   5 recommendation strategies
│   ├── repositories/            # Data access layer
│   ├── routes/                  # FastAPI route handlers
│   ├── schemas/                 # Pydantic request/response models
│   ├── tools/                   # Tool registry & implementations
│   │   ├── base.py              #   ToolResult model
│   │   ├── registry.py          #   ToolRegistry — central tool lookup
│   │   ├── erp/                 #   ERP data tools
│   │   ├── mock/                #   Mock tools for development
│   │   └── rag/                 #   RAG retrieval tools
│   ├── config.py                # Application settings
│   ├── main.py                  # FastAPI application factory
│   └── models.py                # Database/domain models
├── data/                        # CSV data files (seeded)
├── docs/                        # Documentation
│   ├── ai_workflow.md           # AI orchestration workflow (detailed)
│   ├── api.md                   # API reference
│   └── data_dictionary.md       # Data dictionary
├── logs/                        # Application logs
├── static/                      # Static assets
├── tests/                       # Test suite
├── .env.example                 # Environment template
├── pyproject.toml               # Project metadata
├── requirements.txt             # Python dependencies
├── run.py                       # Application runner
└── seed_demo_csv.py             # CSV data seeder
```

---

## 🤖 AI Orchestration Flow

The service uses a **LangGraph StateGraph** with conditional routing to dynamically compose the execution pipeline per query. Simple queries (e.g., "What is my timetable?") invoke only the minimum components, while complex diagnostic queries stitch together agents, prediction, and recommendations.

**High-Level Flow:**

```
User Message → Copilot Intake → Dynamic Planner → Agent Execution
                                                        │
                                    ┌───────────────────┼───────────────────┐
                                    ▼                   ▼                   ▼
                              Prediction      Recommendation        Response
                              (conditional)   (conditional)        Synthesis
                                    │                   │                   │
                                    └───────────────────┴───────────────────┘
                                                        │
                                                  Audit Logger → END
```

> For the complete AI workflow documentation with detailed diagrams, see [`docs/ai_workflow.md`](docs/ai_workflow.md).

---

## 📦 Modules

### Agents (29 total)

| Role Group | Count | Agents |
|---|---|---|
| **Student / Parent** | 9 | StudentAssistant, Attendance, Academic, Exam, Fee, Transport, Notice, Learning, FamilySupport |
| **Teacher / Staff** | 8 | TeacherCopilot, Class, AttendanceAnalysis, Assessment, Lesson, StaffKnowledge, HRLeave, Resource |
| **Visitor / Applicant** | 6 | Admission, Visitor, CampusNavigation, Appointment, Application, PublicKnowledge |
| **Alumni / Ex-Employee** | 6 | AlumniAssistant, Event, Records, Community, Achievement, OfficeSupport |

### Prediction Models (4)

| Model | Scope |
|---|---|
| `attendance_risk` | Student attendance drop-off risk scoring |
| `academic_performance` | Individual academic trajectory prediction |
| `class_performance` | Class-wide performance aggregation |
| `admission_conversion` | Applicant-to-enrollment conversion likelihood |

### Recommendation Strategies (5)

| Strategy | Target Role |
|---|---|
| `attendance_improvement` | Students / Parents |
| `academic_study` | Students / Parents |
| `teacher_interventions` | Teachers / Staff |
| `visitor_next_steps` | Visitors / Applicants |
| `alumni_activities` | Alumni / Ex-Employees |

---

## ⚙ Providers

The service works without credentials using the **deterministic provider**. To enable an LLM provider:

| Provider | Config | Endpoint |
|---|---|---|
| **Deterministic** | Default, no credentials | Local engine |
| **NVIDIA NIM** | `AI_PROVIDER=nvidia` + `NVIDIA_API_KEY` | `https://integrate.api.nvidia.com/v1` |
| **Groq** | `AI_PROVIDER=groq` + `GROQ_API_KEY` | `https://api.groq.com` |

**Fallback chain:** The `ProviderRouter` automatically cascades through providers. If NIM is unavailable, it tries Groq; if Groq fails, it returns a safe deterministic answer. Credentials must remain in `.env` or a secret manager and must never be committed.

---

## 🔒 Roles and Data Boundaries

| Role | Data Access |
|---|---|
| **Student / Parent** | Selected Class VIII A demonstration context only |
| **Teacher / Staff** | Teaching, HRMS, inventory, aggregate support data |
| **Visitor / Applicant** | Public admissions, facilities, campus, events, notices |
| **Alumni / Ex-Employee** | Community and public school information |

Role validation occurs at the API model boundary and is enforced through `SecurityValidator.normalize_role()`. Roles are not inferred from free-form questions.

---

## 💳 Payment and Request Safety

- Fee questions explain installment amounts, due dates, payment methods, and receipt references.
- `/api/requests/preview` prepares a **review-only** payment guidance draft.
- The service **cannot**: contact a payment gateway, collect payment credentials, submit a request, send a message, or change any record.
- Sensitive actions (leave applications, transcript requests) require explicit **human-in-the-loop confirmation** before any draft is finalized.

---

## 📡 API Reference

See [`docs/api.md`](docs/api.md) for the complete API reference. Interactive documentation is available at `http://127.0.0.1:8000/docs` when the service is running.

---

## ✅ Tests and Quality Checks

```bash
pytest -q
ruff check app tests
mypy app
```

The test suite covers health, all-role dashboards, role-filtered feature access, grounded timetable answers, deterministic fallback, and payment-preview safety.

---

## 🔮 Future ERP API Adapter

`app/repositories/base.py` contains `ErpApiSchoolDataRepository`, which intentionally raises `NotImplementedError` until the ERP API contract is available. Implement the same `get_context` and `search` methods as `CsvSchoolDataRepository`, then inject the adapter through application configuration. Keep the AI service and role policy independent of the data source.

---

## 📚 Documentation

| Document | Description |
|---|---|
| [`docs/ai_workflow.md`](docs/ai_workflow.md) | Complete AI orchestration workflow with diagrams |
| [`docs/api.md`](docs/api.md) | API endpoint reference |
| [`docs/data_dictionary.md`](docs/data_dictionary.md) | Data model and CSV field definitions |
