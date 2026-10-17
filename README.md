# 🏫 Green Valley Public School — Smart Campus Kiosk & GREEN_AI Ecosystem (2026)

A state-of-the-art, touch-interactive Digital Campus Kiosk and comprehensive Role-Based Portal system built for **Green Valley Public School**. Designed for physical touchscreen kiosk deployment across campus terminals (100dvh kiosk mode) as well as cross-device responsive portal access.

---

## 🌟 Architecture Overview

```
                      ┌───────────────────────────────────────────┐
                      │    Campus Touchscreen Kiosk Terminal      │
                      │    Next.js 16 + React 19 (App Router)     │
                      │    Port: http://localhost:3000            │
                      └─────────────────────┬─────────────────────┘
                                            │
                                            │ 1. User Interaction / Touch Prompts
                                            │ 2. Live VAPS ERP Session State
                                            ▼
                      ┌───────────────────────────────────────────┐
                      │    Next.js API Gateway (/api/ai/chat)     │
                      │    - Session Authentication Validation    │
                      │    - UI Context Packaging & Forwarding    │
                      │    - Automated Local Failover Buffer      │
                      └─────────────────────┬─────────────────────┘
                                            │
                                            │ HTTP POST /api/v1/green-ai/chat
                                            │ (Dynamic UI Context, Zero CSV reads)
                                            ▼
                      ┌───────────────────────────────────────────┐
                      │     FastAPI Multi-Agent Backend Engine    │
                      │     Port: http://127.0.0.1:8000           │
                      ├───────────────────────────────────────────┤
                      │ • LangGraph State Machine & Supervisor    │
                      │ • Dynamic UI ERP Client (ui_client.py)    │
                      │ • Role Guardrails & Grounding Validator   │
                      │ • NVIDIA NIM / Groq LLM Inference         │
                      └───────────────────────────────────────────┘
```

---

## 🚀 Key Features

### 1. 🤖 GREEN_AI Role-Based Dual-Zone Workspaces
Each user role features a dedicated, touch-optimized **GREEN_AI Space** accessed directly from dashboard quick actions (e.g. `title="Launch Student GREEN_AI Space"`):
- **Left Zone (`RoleAIFeatureExplorer`)**: Interactive catalog of mapped AI capabilities with category tabs (`Academic`, `Compliance`, `Schedule`, `Administrative`, `Navigation`, `General`), search filter, dynamic/static grounding badges, and one-tap prompt chips.
- **Right Zone (Interactive Chat Workspace)**: Real-time conversational agent grounded in verified data, with reasoning badges, agent source indicators, and follow-up suggestion pills.

---

### 2. 📋 Role-Based AI Feature Mapping

| Role | Grounding Mode | Key AI Capabilities | Sample Quick Prompts |
|---|---|---|---|
| **🎓 Student & Parent** | `LIVE DYNAMIC`<br>*(Real VAPS ERP session data)* | • Attendance Risk Diagnostics (CBSE 75% threshold)<br>• Academic Performance & Marks Trajectory<br>• Fee Ledger & Installment Balance<br>• Daily Timetable & Room Allotments<br>• Homework Diary & Submission Deadlines<br>• Term Exam Date Sheets & Reporting Hours<br>• Library Books & Reference Locator<br>• Formal Student Leave Preview | *"What is my attendance rate?"*<br>*"Am I at risk of falling below 75%?"*<br>*"Do I have pending fee balance?"*<br>*"What is my timetable today?"*<br>*"Show homework diary"* |
| **👨‍🏫 Teacher & Staff** | `LIVE DYNAMIC`<br>*(Real faculty roster & grading data)* | • Teaching Schedule & Room Briefings<br>• Class 10A Gradebook & Marks Analytics<br>• Chronic Absenteeism Risk Scoring<br>• Lesson Preparation & Quiz Formulator<br>• Academic Meetings & Sync Briefings<br>• CBSE Norms & Competency Rubrics<br>• Casual Leave Requisition Preview | *"What are my classes today?"*<br>*"Show student grading status"*<br>*"Which students have chronic absence risk?"*<br>*"Lesson plan for Quadratic Equations"*<br>*"CBSE Term-2 assessment guidelines"* |
| **🏛️ Campus Visitor** | `STATIC GUIDE`<br>*(Curated campus directory & FAQs)* | • Admissions Guidance & Eligibility (Nursery - XII)<br>• Application & Enquiry BCE/ENQ/2026/114 Tracking<br>• Campus Wayfinding & Navigation to STEM labs<br>• Guided Campus Tour & Consultation Booking<br>• CBSE Affiliation #1930421 & NAAC A++ Info | *"What is the admission procedure for Class VI?"*<br>*"What is the annual fee structure?"*<br>*"Where is the Kalam STEM Center?"*<br>*"Track status for enquiry BCE/ENQ/2026/114"* |
| **🤝 Alumni & Legacy** | `STATIC GUIDE`<br>*(Alumni directory & archives)* | • Official Graduation Transcript Procedures<br>• Founders Day & Batch Reunion Calendars<br>• Student Mentorship & Career Volunteer Registry<br>• Notable Alumni Hall of Fame & Archives<br>• Former Faculty Service Certificates | *"When is the next Alumni Meet?"*<br>*"How do I request my transcripts?"*<br>*"How can I mentor current students?"*<br>*"Tell me about Class of 2015"* |
| **⚙️ Administrator** | Unmodified | Management dashboard with campus KPIs, fee collection, staff rosters, and hardware diagnostics *(Admin executive intelligence tools explicitly isolated per system specs)*. | Admin controls only |

---

### 3. ⚡ Zero-CSV Dynamic Context Pipeline
- **Legacy CSV Deprecation**: Static `.csv` disk files in `backend/data/` have been removed in favor of real-time payload grounding.
- **Dynamic UI ERP Client (`backend/app/tools/erp/ui_client.py`)**: Seamlessly parses incoming `ui_context` (student attendance metrics, fee records, examination scores, faculty rosters) directly from the Next.js UI session state.
- **In-Memory Fallback**: When offline or in test environments, in-memory repositories provide fallback data without throwing file I/O exceptions.

---

## 🛠️ Technology Stack

| Layer | Technology | Details |
|---|---|---|
| **Frontend Framework** | [Next.js 16](https://nextjs.org/) (App Router) | Turbopack-powered high performance bundler |
| **UI Library** | [React 19](https://react.dev/) | Modern hooks, concurrent rendering, transition states |
| **Language** | [TypeScript 5](https://www.typescriptlang.org/) | Strict type contracts across models & props |
| **Styling** | [Tailwind CSS v4](https://tailwindcss.com/) + Custom CSS | Glassmorphism, 100dvh kiosk viewport, responsive grids |
| **Icons** | [Lucide React](https://lucide.dev/) | Accessible SVG icons for touch kiosks |
| **Backend Framework** | [FastAPI](https://fastapi.tiangolo.com/) + Uvicorn | Asynchronous Python REST microservice |
| **AI Orchestration** | [LangGraph](https://langchain-ai.github.io/langgraph/) | Role-scoped multi-agent graphs with state tracking |
| **LLM Inference** | NVIDIA NIM / Groq / OpenAI | Low-latency inference with reasoning traces |

---

## 📁 Directory Structure

```text
Kisok/
├── src/
│   ├── app/
│   │   ├── api/
│   │   │   └── ai/chat/route.ts      # Server-side AI proxy to FastAPI backend
│   │   ├── admin/                    # Administrator portal
│   │   ├── alumni/                   # Alumni legacy network
│   │   ├── campus-info/              # Public information & wayfinding portal
│   │   ├── login/                    # Universal role authentication
│   │   ├── staff/                    # Faculty & teacher workspace
│   │   ├── student/                  # Student & parent academic command portal
│   │   ├── visitor/                  # Visitor admissions & reception portal
│   │   ├── dashboards.css            # Kiosk design system & AI Space styles
│   │   └── globals.css               # Core global tokens & animations
│   ├── components/
│   │   ├── shared/
│   │   │   └── RoleAIFeatureExplorer.tsx  # Reusable mapped AI capabilities component
│   │   ├── StudentDashboard.tsx      # Student portal with dual-zone AI Space
│   │   ├── StaffDashboard.tsx        # Staff portal with dual-zone AI Space
│   │   ├── VisitorDashboard.tsx      # Visitor helpdesk with static guide
│   │   ├── AlumniDashboard.tsx       # Alumni concierge with legacy guide
│   │   └── AdminDashboard.tsx        # Executive management dashboard
│   ├── config/
│   │   ├── api.ts                    # API endpoints configuration
│   │   └── roleAiFeatures.ts         # Central role-based AI features registry
│   └── lib/
│       ├── greenAiClient.ts          # Frontend GREEN_AI query client
│       └── session.ts                # Session management & token storage
├── backend/
│   ├── app/
│   │   ├── api/routes/green_ai.py    # /api/v1/green-ai/chat endpoint
│   │   ├── copilot/copilot.py        # Copilot orchestrator with ui_context
│   │   ├── engines/context_engine.py # Context scoping engine
│   │   ├── graph/                    # LangGraph multi-agent nodes & state
│   │   ├── prediction/engine.py      # Academic trajectory & marks predictor
│   │   ├── schemas/green_ai.py       # Pydantic request/response schemas
│   │   └── tools/erp/ui_client.py    # Dynamic UI ERP client (zero CSV)
│   ├── tests/                        # 66-test pytest validation suite
│   ├── requirements.txt              # Python dependencies
│   └── run.py                        # Uvicorn server launcher
├── package.json                      # Next.js scripts & packages
├── tsconfig.json                     # TypeScript compiler configuration
└── README.md                         # Comprehensive documentation
```

---

## 🚀 Running the Project Locally

### 1. Prerequisites
- **Node.js**: v18.17.0+ (Node 20 or 22 recommended)
- **Python**: 3.11 or 3.12+
- **Package Managers**: `npm` (frontend) and `pip` (backend)

---

### 2. Start the FastAPI Backend

Open a terminal and run:

```bash
cd backend

# Install dependencies (virtual environment recommended)
pip install -r requirements.txt

# Start the FastAPI server on port 8000
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

The backend will be available at:
- **API Base URL**: `http://127.0.0.1:8000`
- **Interactive OpenAPI Docs**: `http://127.0.0.1:8000/docs`
- **Health Check**: `http://127.0.0.1:8000/health`

---

### 3. Start the Next.js Frontend

Open a second terminal at the project root:

```bash
# Install frontend dependencies
npm install

# Start Next.js development server
npm run dev
```

The frontend will be available at:
- **Campus Kiosk URL**: `http://localhost:3000`

---

## 🧪 Testing & Verification

### Run Backend Pytest Suite
```bash
cd backend
pytest tests/test_dynamic_ui.py tests/test_green_ai.py tests/test_service.py tests/test_v1_orchestration.py tests/test_voice_and_ui.py
```
> **Result**: `66 passed, 0 failures` (Verifies dynamic UI ingestion, LangGraph node execution, Copilot context scoping, and voice endpoints).

### Run Frontend TypeScript & Build Check
```bash
# Verify TypeScript types
npx tsc --noEmit

# Verify Next.js production build
npm run build
```
> **Result**: `Compiled successfully`, all 26 static/dynamic routes generated cleanly with zero errors.

---

## 🖥️ Deploying in Kiosk Terminal Mode

For dedicated physical touchscreen kiosks (Raspberry Pi 5, Intel NUC, or Windows Touch Terminal):

1. **Build and start production**:
   ```bash
   npm run build
   npm run start
   ```

2. **Launch Chromium in Fullscreen Kiosk Mode**:
   ```bash
   chromium-browser --kiosk --noerrdialogs --disable-infobars --check-for-update-interval=31536000 http://localhost:3000
   ```

3. **Touch Interaction Standards**:
   - Minimum touch-target sizes &ge; 44px
   - Dual-zone layouts with independent smooth scrolling
   - Auto-scrolling chat history with quick one-tap suggestion chips

---

## 📝 License & Attribution

Developed for **Green Valley Public School**. Built with Next.js 16, React 19, FastAPI, LangGraph, and Tailwind CSS.
