# AI Orchestration Workflow

This document describes the complete AI orchestration flow of the School AI Kiosk Service — from user query intake through dynamic planning, agent execution, prediction, recommendation, response synthesis, and audit logging.

---

## Table of Contents

- [High-Level Architecture](#high-level-architecture)
- [LangGraph Orchestrator](#langgraph-orchestrator)
- [Node-by-Node Walkthrough](#node-by-node-walkthrough)
- [Dynamic Routing Logic](#dynamic-routing-logic)
- [Execution Flow Diagrams](#execution-flow-diagrams)
- [Agent Architecture](#agent-architecture)
- [Engine Pipeline](#engine-pipeline)
- [Provider Fallback Chain](#provider-fallback-chain)
- [State Schema](#state-schema)
- [Example Scenarios](#example-scenarios)

---

## High-Level Architecture

The service follows a layered architecture where each layer has a distinct responsibility:

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          CLIENT REQUEST                                │
│                  (user_id, role, message, session_id)                   │
└──────────────────────────────┬──────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                        FastAPI Gateway                                  │
│               Routes → Schemas → Validation                             │
└──────────────────────────────┬──────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         AICopilot                                       │
│          Session management, graph invocation, memory update            │
└──────────────────────────────┬──────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                  LangGraph StateGraph Orchestrator                       │
│                                                                         │
│   ┌──────────┐   ┌─────────┐   ┌──────────────┐   ┌──────────────┐    │
│   │ Copilot  │──▶│ Planner │──▶│    Agent      │──▶│  Prediction  │    │
│   │  Node    │   │  Node   │   │  Execution    │   │    Node      │    │
│   └──────────┘   └─────────┘   └──────────────┘   └──────┬───────┘    │
│                                                           │            │
│                                       ┌───────────────────┘            │
│                                       ▼                                │
│                              ┌──────────────┐   ┌──────────────┐       │
│                              │Recommendation│──▶│  Response     │       │
│                              │    Node      │   │  Synthesis    │       │
│                              └──────────────┘   └──────┬───────┘       │
│                                                        │               │
│                                                        ▼               │
│                                                 ┌──────────────┐       │
│                                                 │ Audit Logger │       │
│                                                 └──────────────┘       │
└─────────────────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         JSON Response                                   │
│        answer, intent, agents_used, sources, reasoning, followups       │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## LangGraph Orchestrator

The orchestrator is built using **LangGraph's `StateGraph`** with 7 nodes and conditional edges. It is defined in `app/graph/graph.py` and compiled once at startup.

### Graph Definition

```
Nodes:
  1. copilot              — Request validation & session context
  2. planner              — Dynamic execution plan generation
  3. agent_execution      — Role-aware agent processing
  4. prediction           — Statistical prediction (conditional)
  5. recommendation       — Personalized recommendations (conditional)
  6. response_synthesis   — Human-friendly answer generation
  7. audit_logger         — Structured audit trail

Edges:
  START → copilot → planner → agent_execution
  
  agent_execution →  prediction          (if needs_prediction)
                  →  recommendation      (if needs_recommendation)
                  →  response_synthesis  (otherwise)
  
  prediction →  recommendation          (if needs_recommendation)
             →  response_synthesis      (otherwise)
  
  recommendation → response_synthesis
  response_synthesis → audit_logger → END
```

### Orchestrator Flow Diagram

```mermaid
flowchart TD
    START((START)) --> copilot["🛡️ Copilot Node<br/><i>Validate request<br/>Load session context</i>"]
    
    copilot --> planner["🧠 Planner Node<br/><i>Intent detection<br/>Entity extraction<br/>Agent & tool selection<br/>Prediction/Recommendation flags</i>"]
    
    planner --> agent_exec["⚡ Agent Execution Node<br/><i>Execute selected agents<br/>Invoke tools<br/>Collect sources</i>"]
    
    agent_exec --> route_agents{"Route Decision<br/><i>needs_prediction?<br/>needs_recommendation?</i>"}
    
    route_agents -->|"needs_prediction = true"| prediction["📊 Prediction Node<br/><i>Statistical risk scoring<br/>Trend analysis</i>"]
    route_agents -->|"needs_recommendation = true<br/>(no prediction)"| recommendation["💡 Recommendation Node<br/><i>Personalized action steps</i>"]
    route_agents -->|"neither"| response["✍️ Response Synthesis<br/><i>Reasoning trace<br/>Response formatting<br/>Safety validation</i>"]
    
    prediction --> route_pred{"Route Decision<br/><i>needs_recommendation?</i>"}
    
    route_pred -->|"yes"| recommendation
    route_pred -->|"no"| response
    
    recommendation --> response
    
    response --> audit["📋 Audit Logger<br/><i>Structured audit entry<br/>Performance metrics</i>"]
    
    audit --> END((END))

    style START fill:#10b981,stroke:#059669,color:#fff
    style END fill:#ef4444,stroke:#dc2626,color:#fff
    style copilot fill:#3b82f6,stroke:#2563eb,color:#fff
    style planner fill:#8b5cf6,stroke:#7c3aed,color:#fff
    style agent_exec fill:#f59e0b,stroke:#d97706,color:#fff
    style prediction fill:#06b6d4,stroke:#0891b2,color:#fff
    style recommendation fill:#ec4899,stroke:#db2777,color:#fff
    style response fill:#10b981,stroke:#059669,color:#fff
    style audit fill:#6b7280,stroke:#4b5563,color:#fff
    style route_agents fill:#fef3c7,stroke:#f59e0b,color:#000
    style route_pred fill:#fef3c7,stroke:#f59e0b,color:#000
```

---

## Node-by-Node Walkthrough

### 1. Copilot Node (`copilot_node`)

**File:** `app/graph/nodes.py`

**Purpose:** Entry gate — validates the incoming request and initializes session context.

**Steps:**
1. Extract `user_id`, `role`, `tenant_id`, `message`, `session_id` from state
2. Run `ValidationEngine.validate_request()` — checks for empty fields, invalid roles
3. Normalize the role via `SecurityValidator.normalize_role()` (e.g., "student" → "student_parent")
4. Initialize or retrieve session context via `ContextEngine.get_or_create_session()`
5. Return canonical role and success flag

**Output:** `{ role: str, success: bool }` or `{ error: str, success: false }`

---

### 2. Planner Node (`planner_node`)

**File:** `app/graph/nodes.py` → delegates to `app/copilot/planner.py`

**Purpose:** Construct a dynamic execution plan tailored to the query's complexity and the user's role.

**Steps:**
1. Detect intent via `IntentEngine.detect_intent(query, role)` — maps to one of: `attendance_inquiry`, `fees`, `timetable`, `marks_inquiry`, `admissions`, `alumni`, `notices`, `exam`, `leave_application`, etc.
2. Extract entities via `EntityExtractionEngine.extract_entities(query)` — dates, student names, subjects, etc.
3. Select agents and tools based on `(intent, role)` mapping
4. Set conditional flags:
   - `needs_prediction` — triggered by diagnostic keywords: "why", "low", "risk", "trend", "predict"
   - `needs_recommendation` — triggered by guidance keywords: "how to improve", "suggestions", "recommend"
   - `needs_rag` — triggered by policy/circular queries
   - `requires_confirmation` — triggered by sensitive actions (leave, transcript requests)
5. Return the complete `ExecutionPlan`

**Key Design Decision:** Simple queries like "What is my timetable?" set `needs_prediction=false` and `needs_recommendation=false`, ensuring only the minimum components are invoked. Complex queries like "Why is my attendance falling and how can I improve?" activate the full pipeline.

---

### 3. Agent Execution Node (`agent_execution_node`)

**File:** `app/graph/nodes.py`

**Purpose:** Execute only the agents selected by the planner, collect outputs, sources, and tool data.

**Steps:**
1. Retrieve selected agents from the `AgentRegistry` by ID
2. For each agent, call `agent.process(query, intent, entities, user_id, tenant_id)`
3. Each agent internally invokes its registered tools (e.g., `get_student_attendance`, `get_fee_details`)
4. Collect `AgentOutput` objects: findings, tool results, sources, confirmation flags
5. Merge all outputs and return combined results

**Agent Registry:** 29 agents organized by role group:

```mermaid
graph LR
    subgraph "Student / Parent — 9 agents"
        SA["StudentAssistant"]
        AT["Attendance"]
        AC["Academic"]
        EX["Exam"]
        FE["Fee"]
        TR["Transport"]
        NO["Notice"]
        LE["Learning"]
        FS["FamilySupport"]
    end
    
    subgraph "Teacher / Staff — 8 agents"
        TC["TeacherCopilot"]
        CL["Class"]
        AA["AttendanceAnalysis"]
        AS["Assessment"]
        LS["Lesson"]
        SK["StaffKnowledge"]
        HR["HRLeave"]
        RE["Resource"]
    end
    
    subgraph "Visitor / Applicant — 6 agents"
        AD["Admission"]
        VI["Visitor"]
        CN["CampusNavigation"]
        AP["Appointment"]
        AL["Application"]
        PK["PublicKnowledge"]
    end
    
    subgraph "Alumni / Ex-Employee — 6 agents"
        ALA["AlumniAssistant"]
        EV["Event"]
        RC["Records"]
        CO["Community"]
        ACH["Achievement"]
        OS["OfficeSupport"]
    end

    style SA fill:#3b82f6,stroke:#2563eb,color:#fff
    style AT fill:#3b82f6,stroke:#2563eb,color:#fff
    style AC fill:#3b82f6,stroke:#2563eb,color:#fff
    style EX fill:#3b82f6,stroke:#2563eb,color:#fff
    style FE fill:#3b82f6,stroke:#2563eb,color:#fff
    style TR fill:#3b82f6,stroke:#2563eb,color:#fff
    style NO fill:#3b82f6,stroke:#2563eb,color:#fff
    style LE fill:#3b82f6,stroke:#2563eb,color:#fff
    style FS fill:#3b82f6,stroke:#2563eb,color:#fff
    
    style TC fill:#8b5cf6,stroke:#7c3aed,color:#fff
    style CL fill:#8b5cf6,stroke:#7c3aed,color:#fff
    style AA fill:#8b5cf6,stroke:#7c3aed,color:#fff
    style AS fill:#8b5cf6,stroke:#7c3aed,color:#fff
    style LS fill:#8b5cf6,stroke:#7c3aed,color:#fff
    style SK fill:#8b5cf6,stroke:#7c3aed,color:#fff
    style HR fill:#8b5cf6,stroke:#7c3aed,color:#fff
    style RE fill:#8b5cf6,stroke:#7c3aed,color:#fff
    
    style AD fill:#f59e0b,stroke:#d97706,color:#fff
    style VI fill:#f59e0b,stroke:#d97706,color:#fff
    style CN fill:#f59e0b,stroke:#d97706,color:#fff
    style AP fill:#f59e0b,stroke:#d97706,color:#fff
    style AL fill:#f59e0b,stroke:#d97706,color:#fff
    style PK fill:#f59e0b,stroke:#d97706,color:#fff
    
    style ALA fill:#10b981,stroke:#059669,color:#fff
    style EV fill:#10b981,stroke:#059669,color:#fff
    style RC fill:#10b981,stroke:#059669,color:#fff
    style CO fill:#10b981,stroke:#059669,color:#fff
    style ACH fill:#10b981,stroke:#059669,color:#fff
    style OS fill:#10b981,stroke:#059669,color:#fff
```

---

### 4. Prediction Node (`prediction_node`)

**File:** `app/graph/nodes.py`

**Purpose:** Execute statistical prediction **only** when the planner flags `needs_prediction=true`.

**Prediction Models:**

| Model | Input | Output |
|---|---|---|
| `attendance_risk` | Attendance records | Risk level, score, trend |
| `academic_performance` | Marks/grade records | Performance trajectory |
| `class_performance` | Class-wide records | Aggregate class metrics |
| `admission_conversion` | Application records | Conversion probability |

**Output:** `PredictionResult` with `risk_level`, `score`, `trend`, `sufficient_data` flag.

---

### 5. Recommendation Node (`recommendation_node`)

**File:** `app/graph/nodes.py`

**Purpose:** Generate personalized, actionable recommendations **only** when the planner flags `needs_recommendation=true`.

**Strategy Selection:**

```mermaid
flowchart TD
    START["Recommendation Node"] --> check_intent{"Intent contains<br/>'attendance'?"}
    
    check_intent -->|yes| att["🎯 Attendance Improvement<br/><i>Morning routine, leave notification,<br/>recovery consultation</i>"]
    check_intent -->|no| check_marks{"Intent contains<br/>'marks' or 'academic'?"}
    
    check_marks -->|yes| study["📚 Academic Study Plan<br/><i>Structured revision, reference books,<br/>peer study groups</i>"]
    check_marks -->|no| check_visitor{"Role is<br/>'visitor'?"}
    
    check_visitor -->|yes| visitor["🏫 Visitor Next Steps<br/><i>Campus tour, counselling,<br/>document verification</i>"]
    check_visitor -->|no| check_alumni{"Role is<br/>'alumni'?"}
    
    check_alumni -->|yes| alumni["🎓 Alumni Activities<br/><i>Reunion, mentorship,<br/>heritage contribution</i>"]
    check_alumni -->|no| check_teacher{"Role is<br/>'teacher'?"}
    
    check_teacher -->|yes| teacher["👨‍🏫 Teacher Interventions<br/><i>Remedial cohort, worksheets,<br/>parent-teacher alignment</i>"]
    check_teacher -->|no| fallback["🎯 Attendance Improvement<br/><i>Default fallback</i>"]

    style START fill:#ec4899,stroke:#db2777,color:#fff
    style att fill:#3b82f6,stroke:#2563eb,color:#fff
    style study fill:#8b5cf6,stroke:#7c3aed,color:#fff
    style visitor fill:#f59e0b,stroke:#d97706,color:#fff
    style alumni fill:#10b981,stroke:#059669,color:#fff
    style teacher fill:#06b6d4,stroke:#0891b2,color:#fff
    style fallback fill:#6b7280,stroke:#4b5563,color:#fff
```

**Output:** `RecommendationResult` with `items[]` (title, category, description, priority) and `actionable_steps[]`.

---

### 6. Response Synthesis Node (`response_synthesis_node`)

**File:** `app/graph/nodes.py`

**Purpose:** Synthesize a human-friendly, safe, and grounded response from all preceding outputs.

**Steps:**
1. **Reasoning Trace** — `ReasoningEngine.construct_reasoning()` builds a step-by-step explanation:
   - Intent identification
   - Record retrieval count
   - Prediction results (if applicable)
   - Recommendation summary (if applicable)
   - Synthesis confirmation
2. **Response Formatting** — `ResponseGenerationEngine.format_response()` creates a role-appropriate, readable answer
3. **Safety Validation** — `ValidationEngine.validate_response_safety()` redacts sensitive data and enforces role boundaries
4. **Follow-up Questions** — Suggests contextual next steps

---

### 7. Audit Logger Node (`audit_logger_node`)

**File:** `app/graph/nodes.py`

**Purpose:** Record a structured audit trace for every query processed.

**Audit Entry Fields:**
- `request_id` — Unique request identifier
- `session_id`, `user_id`, `tenant_id`, `role` — Session context
- `intent` — Detected query intent
- `selected_agents`, `selected_tools` — Components invoked
- `model_provider` — Which LLM provider was used
- `latency_ms` — End-to-end processing time
- `success` — Whether the request completed without error
- `final_response_status` — `completed` or `pending_confirmation`

---

## Dynamic Routing Logic

The orchestrator uses two conditional routing functions:

### `route_after_agents(state)`

Called after `agent_execution`. Routes to:
- `prediction` — if `state["needs_prediction"]` is true
- `recommendation` — if `state["needs_recommendation"]` is true (but not prediction)
- `response_synthesis` — if neither flag is set

### `route_after_prediction(state)`

Called after `prediction`. Routes to:
- `recommendation` — if `state["needs_recommendation"]` is true
- `response_synthesis` — otherwise

This ensures the graph takes the **shortest path** for simple queries while enabling the full prediction → recommendation → synthesis pipeline for complex analytical queries.

---

## Execution Flow Diagrams

### Scenario A: Simple Query (Timetable)

> "What is my class timetable?"

```mermaid
flowchart LR
    A["START"] --> B["Copilot"]
    B --> C["Planner<br/><i>intent=timetable<br/>agents=[student_assistant]<br/>prediction=false<br/>recommendation=false</i>"]
    C --> D["Agent Execution<br/><i>get_timetable tool</i>"]
    D --> E["Response Synthesis"]
    E --> F["Audit Logger"]
    F --> G["END"]

    style A fill:#10b981,color:#fff
    style G fill:#ef4444,color:#fff
    style B fill:#3b82f6,color:#fff
    style C fill:#8b5cf6,color:#fff
    style D fill:#f59e0b,color:#fff
    style E fill:#10b981,color:#fff
    style F fill:#6b7280,color:#fff
```

**Nodes traversed:** 5 (minimum path)

---

### Scenario B: Diagnostic Query (Attendance Risk)

> "Why is my attendance falling? How can I improve?"

```mermaid
flowchart LR
    A["START"] --> B["Copilot"]
    B --> C["Planner<br/><i>intent=attendance_inquiry<br/>agents=[attendance_agent]<br/>prediction=true (risk)<br/>recommendation=true</i>"]
    C --> D["Agent Execution<br/><i>get_student_attendance</i>"]
    D --> E["Prediction<br/><i>attendance_risk model</i>"]
    E --> F["Recommendation<br/><i>attendance_improvement</i>"]
    F --> G["Response Synthesis"]
    G --> H["Audit Logger"]
    H --> I["END"]

    style A fill:#10b981,color:#fff
    style I fill:#ef4444,color:#fff
    style B fill:#3b82f6,color:#fff
    style C fill:#8b5cf6,color:#fff
    style D fill:#f59e0b,color:#fff
    style E fill:#06b6d4,color:#fff
    style F fill:#ec4899,color:#fff
    style G fill:#10b981,color:#fff
    style H fill:#6b7280,color:#fff
```

**Nodes traversed:** 7 (maximum path)

---

### Scenario C: Sensitive Action (Leave Application)

> "I want to apply for leave tomorrow for a medical appointment."

```mermaid
flowchart LR
    A["START"] --> B["Copilot"]
    B --> C["Planner<br/><i>intent=leave_application<br/>requires_confirmation=true<br/>agents=[family_support_agent]</i>"]
    C --> D["Agent Execution<br/><i>preview_leave_application</i>"]
    D --> E["Response Synthesis<br/><i>⚠️ Human-in-the-loop<br/>confirmation message</i>"]
    E --> F["Audit Logger<br/><i>status=pending_confirmation</i>"]
    F --> G["END"]

    style A fill:#10b981,color:#fff
    style G fill:#ef4444,color:#fff
    style B fill:#3b82f6,color:#fff
    style C fill:#8b5cf6,color:#fff
    style D fill:#f59e0b,color:#fff
    style E fill:#f97316,color:#fff
    style F fill:#6b7280,color:#fff
```

**Nodes traversed:** 5 | **Status:** `pending_human_approval`

---

### Scenario D: Teacher Performance Analysis

> "Show me class VIII A performance and suggest interventions."

```mermaid
flowchart LR
    A["START"] --> B["Copilot"]
    B --> C["Planner<br/><i>intent=academic_analysis<br/>agents=[assessment_agent]<br/>prediction=true (class_performance)<br/>recommendation=true</i>"]
    C --> D["Agent Execution<br/><i>get_student_marks</i>"]
    D --> E["Prediction<br/><i>class_performance model</i>"]
    E --> F["Recommendation<br/><i>teacher_interventions</i>"]
    F --> G["Response Synthesis"]
    G --> H["Audit Logger"]
    H --> I["END"]

    style A fill:#10b981,color:#fff
    style I fill:#ef4444,color:#fff
    style B fill:#3b82f6,color:#fff
    style C fill:#8b5cf6,color:#fff
    style D fill:#f59e0b,color:#fff
    style E fill:#06b6d4,color:#fff
    style F fill:#ec4899,color:#fff
    style G fill:#10b981,color:#fff
    style H fill:#6b7280,color:#fff
```

**Nodes traversed:** 7 (maximum path, teacher context)

---

## Engine Pipeline

The engines are stateless utility classes that perform specific processing tasks:

```mermaid
flowchart TD
    subgraph "Pre-Execution Engines"
        IE["IntentEngine<br/><i>detect_intent()</i>"]
        EE["EntityExtractionEngine<br/><i>extract_entities()</i>"]
        CE["ContextEngine<br/><i>get_or_create_session()</i>"]
        VE1["ValidationEngine<br/><i>validate_request()</i>"]
    end
    
    subgraph "Post-Execution Engines"
        RE["ReasoningEngine<br/><i>construct_reasoning()</i>"]
        RGE["ResponseGenerationEngine<br/><i>format_response()</i>"]
        VE2["ValidationEngine<br/><i>validate_response_safety()</i>"]
    end
    
    subgraph "Analytical Engines"
        PE["PredictionEngine<br/><i>4 prediction models</i>"]
        RCE["RecommendationEngine<br/><i>5 recommendation strategies</i>"]
        DAE["DataAnalysisEngine<br/><i>aggregation & statistics</i>"]
    end

    IE --> EE --> CE --> VE1
    RE --> RGE --> VE2
    
    style IE fill:#3b82f6,color:#fff
    style EE fill:#3b82f6,color:#fff
    style CE fill:#3b82f6,color:#fff
    style VE1 fill:#ef4444,color:#fff
    style RE fill:#8b5cf6,color:#fff
    style RGE fill:#8b5cf6,color:#fff
    style VE2 fill:#ef4444,color:#fff
    style PE fill:#06b6d4,color:#fff
    style RCE fill:#ec4899,color:#fff
    style DAE fill:#f59e0b,color:#fff
```

---

## Provider Fallback Chain

The `ProviderRouter` manages LLM provider selection with automatic cascading fallback:

```mermaid
flowchart TD
    REQ["LLM Request"] --> PREF{"Provider<br/>Preference?"}
    
    PREF -->|"nvidia/nim"| NIM["NVIDIA NIM<br/><i>moonshotai/kimi-k3</i>"]
    PREF -->|"groq"| GROQ1["Groq<br/><i>OpenAI-compatible</i>"]
    PREF -->|"deterministic"| DET1["Deterministic<br/><i>No external calls</i>"]
    PREF -->|"default"| NIM
    
    NIM -->|"✅ healthy"| RESP["LLM Response"]
    NIM -->|"❌ unhealthy/error"| GROQ2["Groq Fallback"]
    
    GROQ1 -->|"✅ healthy"| RESP
    GROQ1 -->|"❌ unhealthy/error"| NIM2["NIM Fallback"]
    
    GROQ2 -->|"✅ healthy"| RESP
    GROQ2 -->|"❌ unhealthy/error"| DET2["Deterministic Fallback"]
    
    NIM2 -->|"✅ healthy"| RESP
    NIM2 -->|"❌ unhealthy/error"| DET3["Deterministic Fallback"]
    
    DET1 --> RESP
    DET2 --> RESP
    DET3 --> RESP

    style REQ fill:#3b82f6,color:#fff
    style RESP fill:#10b981,color:#fff
    style NIM fill:#76b900,color:#fff
    style NIM2 fill:#76b900,color:#fff
    style GROQ1 fill:#f97316,color:#fff
    style GROQ2 fill:#f97316,color:#fff
    style DET1 fill:#6b7280,color:#fff
    style DET2 fill:#6b7280,color:#fff
    style DET3 fill:#6b7280,color:#fff
```

**Guarantee:** The deterministic provider always succeeds — it requires no external API calls, no credentials, and no network connectivity. Every query returns a safe, grounded answer.

---

## State Schema

The `OrchestratorState` (`app/graph/state.py`) is a `TypedDict` that flows through all nodes:

```
┌──────────────────────────────────────────────────────────────┐
│                     OrchestratorState                        │
├──────────────────────────────────────────────────────────────┤
│ REQUEST PARAMETERS                                           │
│   user_id: str                                               │
│   role: str                                                  │
│   tenant_id: str                                             │
│   session_id: str                                            │
│   message: str                                               │
│   provider_preference: str | None                            │
├──────────────────────────────────────────────────────────────┤
│ PLANNER OUTPUTS                                              │
│   intent: str                                                │
│   entities: dict                                             │
│   selected_agents: list[str]                                 │
│   selected_tools: list[str]                                  │
│   needs_prediction: bool                                     │
│   prediction_type: str | None                                │
│   needs_recommendation: bool                                 │
│   needs_rag: bool                                            │
│   requires_confirmation: bool                                │
│   confirmation_message: str | None                           │
├──────────────────────────────────────────────────────────────┤
│ EXECUTION OUTPUTS                                            │
│   agent_outputs: list[dict]                                  │
│   tool_data: Any                                             │
│   sources: list[dict]                                        │
│   prediction: dict | None                                    │
│   recommendation: dict | None                                │
├──────────────────────────────────────────────────────────────┤
│ RESPONSE & AUDIT                                             │
│   final_answer: str                                          │
│   reasoning_content: str | None                              │
│   followup_questions: list[str]                              │
│   provider_used: str                                         │
│   latency_ms: float                                          │
│   success: bool                                              │
│   error: str | None                                          │
└──────────────────────────────────────────────────────────────┘
```

---

## Example Scenarios

### Intent → Agent → Pipeline Mapping

| User Query | Role | Intent | Agents | Prediction | Recommendation | Path Length |
|---|---|---|---|---|---|---|
| "What is my timetable?" | Student | `timetable` | StudentAssistant | ❌ | ❌ | 5 nodes |
| "Show my fee details" | Parent | `fees` | Fee | ❌ | ❌ | 5 nodes |
| "How is my attendance?" | Student | `attendance_inquiry` | Attendance | ❌ | ❌ | 5 nodes |
| "Why is attendance falling?" | Student | `attendance_inquiry` | Attendance | ✅ risk | ❌ | 6 nodes |
| "How to improve attendance?" | Student | `attendance_inquiry` | Attendance | ✅ risk | ✅ improvement | 7 nodes |
| "Class VIII performance" | Teacher | `academic_analysis` | Assessment | ✅ class | ✅ interventions | 7 nodes |
| "How to improve in Math?" | Student | `marks_inquiry` | Academic | ❌ | ✅ study | 6 nodes |
| "Apply for leave tomorrow" | Student | `leave_application` | FamilySupport | ❌ | ❌ | 5 nodes ⚠️ |
| "Admission process?" | Visitor | `admissions` | Admission | ❌ | ✅ next steps | 6 nodes |
| "Reunion event details" | Alumni | `alumni` | Event | ❌ | ❌ | 5 nodes |
| "Any new circulars?" | Student | `notices` | Notice | ❌ | ❌ | 5 nodes (+ RAG) |

> ⚠️ = Requires human-in-the-loop confirmation before finalization.

---

*Last updated: September 2026*
