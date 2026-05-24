# Banking Demo — AI Agent Platform

A **production-grade AI agent platform** demonstrating a **multi-agent loan processing pipeline** for retail banking. This project showcases four core AI agent concepts working in concert: SDK layer (tool registration), harness (workflow orchestration), A2A protocol (agent-to-agent communication), and memory systems (context, episodic, semantic, working).

**Project Size:** 70 Python files | **Main Entry:** 1,059 lines | **Port:** 8005

---

## Table of Contents

- [Quick Start](#quick-start)
- [Tech Stack](#tech-stack)
- [Architecture](#architecture)
- [Folder Structure](#folder-structure)
- [Core Modules](#core-modules)
- [Component Interaction](#component-interaction)
- [Memory System](#memory-system)
- [REST API](#rest-api)
- [Deployment](#deployment)
- [Configuration](#configuration)
- [Observability](#observability)
- [Testing](#testing)

---

## Quick Start

### Prerequisites

- Python 3.9+
- Docker & Docker Compose
- Ollama (optional, for local LLM) or OpenAI/Anthropic API key

### Installation

```bash
# Clone the repository
git clone <repo-url>
cd banking-demo

# Install dependencies
pip install -r requirements.txt

# Create .env file
cp .env.example .env
# Edit .env with your API keys (OPENAI_API_KEY, ANTHROPIC_API_KEY, etc.)
```

### Run Locally

```bash
# Start the full stack (banking-demo + Redis + Prometheus + Grafana)
docker compose up --build

# Or run just the banking-demo service
python main.py

# Access the application
# - Banking Demo API: http://localhost:8005
# - Grafana: http://localhost:3000 (admin/admin)
# - Prometheus: http://localhost:9090
# - AlertManager: http://localhost:9093
```

### Test the Pipeline

```bash
# Execute a single loan application
curl "http://localhost:8005/api/run?customer_id=CUST001&amount=15000&term_months=36"

# Generate traffic (20, 30, or 50 applications)
curl "http://localhost:8005/api/generate-traffic/20"

# Seed 3 pre-populated applications
curl "http://localhost:8005/api/seed"
```

---

## Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Framework** | FastAPI 0.111.0 | REST API & SSE streaming |
| **Server** | Uvicorn 0.29.0 | ASGI application server |
| **LLM Backends** | OpenAI, Anthropic, Ollama | Multi-backend LLM support |
| **Memory** | ChromaDB 0.5.3, SQLite, Redis 5.0.4 | Vector DB, audit log, cache |
| **Embeddings** | Sentence Transformers 3.0.1 | Vector embeddings for semantic search |
| **Observability** | Prometheus, Grafana, AlertManager | Metrics, dashboards, alerts |
| **Logging** | structlog 24.0.0, python-json-logger | Structured logging |
| **Testing** | pytest, pytest-asyncio, pytest-cov | Unit & integration tests |
| **Containerization** | Docker, Docker Compose | Orchestration |
| **Database Migration** | Alembic 1.13.0 | Schema versioning |

---

## Architecture

### High-Level Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        CLIENT                                   │
│                   (Browser / CLI)                               │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
        ┌────────────────────────────────────┐
        │      FastAPI REST API              │
        │  /api/run (SSE streaming)          │
        └────────────┬───────────────────────┘
                     │
        ┌────────────▼───────────────────────┐
        │    HARNESS (Orchestration)         │
        │  5 Sequential Sessions             │
        └────────────┬───────────────────────┘
                     │
        ┌────────────▼───────────────────────────────────────┐
        │         AGENT SYSTEM (A2A Protocol)                │
        │  Intake → Risk → Fraud → Decision                  │
        │  (JSON-RPC 2.0 communication)                      │
        └────────────┬───────────────────────────────────────┘
                     │
        ┌────────────▼───────────────────────────────────────┐
        │         TOOL SYSTEM (SDK Layer)                    │
        │  Customer | Credit | Fraud | Compliance            │
        │  (@register_tool decorator)                        │
        └────────────┬───────────────────────────────────────┘
                     │
        ┌────────────▼───────────────────────────────────────┐
        │       LLM BACKEND (Multi-backend)                  │
        │  OpenAI | Anthropic | Ollama | Mock                │
        │  (Abstract factory pattern)                        │
        └────────────┬───────────────────────────────────────┘
                     │
        ┌────────────▼───────────────────────────────────────┐
        │      MEMORY SYSTEM (4-Tier)                        │
        │  ┌─────────────────────────────────────┐           │
        │  │ In-Context (Python list)            │           │
        │  │ Episodic (SQLite audit log)         │           │
        │  │ Semantic (ChromaDB vectors)         │           │
        │  │ Working (Redis cache)               │           │
        │  └─────────────────────────────────────┘           │
        └────────────┬───────────────────────────────────────┘
                     │
        ┌────────────▼───────────────────────────────────────┐
        │    OBSERVABILITY STACK                             │
        │  Prometheus → Grafana → AlertManager → Slack       │
        │  (20+ metrics, real-time dashboards, alerts)       │
        └────────────────────────────────────────────────────┘
```

---

## Folder Structure

```
banking-demo/
├── main.py                          # Entry point: FastAPI app + full pipeline (1,059 lines)
├── config.py                        # Pydantic Settings for configuration
├── requirements.txt                 # Dependencies
├── docker-compose.yml               # Full stack orchestration
├── Dockerfile                       # Container image
│
├── agents/                          # Agent definitions & orchestration
│   ├── __init__.py                  # Module exports
│   ├── base.py                      # Abstract Agent base class
│   ├── context.py                   # AgentContext (execution state)
│   ├── registry.py                  # A2A agent registry
│   ├── definitions.py               # Agent definitions
│   ├── intake.py                    # IntakeAgent implementation
│   ├── risk.py                      # RiskAgent implementation
│   ├── fraud.py                     # FraudAgent implementation
│   ├── decision.py                  # DecisionAgent implementation
│   ├── intake/                      # Intake agent subdirectory
│   ├── risk/                        # Risk agent subdirectory
│   ├── fraud/                       # Fraud agent subdirectory
│   └── decision/                    # Decision agent subdirectory
│
├── tools/                           # Tool implementations (SDK layer)
│   ├── __init__.py                  # Tool exports
│   ├── registry.py                  # Tool registry & @register_tool decorator
│   ├── customer/                    # Customer tools (profile, KYC)
│   ├── credit/                      # Credit tools (score, affordability)
│   ├── fraud/                       # Fraud tools (transaction scanning)
│   ├── compliance/                  # Compliance tools (rules queries)
│   └── README.md                    # Tool documentation
│
├── memory/                          # 4-tier memory system
│   ├── __init__.py                  # Module exports
│   ├── base.py                      # Abstract MemoryStore interface
│   ├── context.py                   # In-context memory (active session)
│   ├── episodic.py                  # Episodic memory (SQLite audit log)
│   ├── semantic.py                  # Semantic memory (ChromaDB vectors)
│   ├── working.py                   # Working memory (Redis cache)
│   └── manager.py                   # MemoryManager orchestration
│
├── llm/                             # LLM backend abstraction
│   ├── __init__.py                  # Module exports
│   ├── backend.py                   # Abstract LLMBackend interface
│   ├── factory.py                   # Backend factory (auto-detect)
│   ├── openai_client.py             # OpenAI implementation
│   ├── anthropic_client.py          # Anthropic implementation
│   ├── ollama_client.py             # Ollama implementation
│   └── mock_client.py               # Mock implementation (fallback)
│
├── harness/                         # Workflow orchestration
│   ├── __init__.py                  # Module exports
│   ├── session.py                   # Session state management
│   ├── pipeline.py                  # Pipeline orchestration
│   └── events.py                    # Event definitions
│
├── monitoring/                      # Observability configuration
│   ├── prometheus.yml               # Prometheus scrape config
│   ├── alert_rules.yml              # Alert rules (8.7 KB)
│   ├── recording_rules.yml          # Recording rules (6.0 KB)
│   ├── alertmanager.yml             # AlertManager config
│   ├── grafana/
│   │   ├── dashboards/              # Grafana dashboard definitions
│   │   └── provisioning/            # Grafana provisioning configs
│   └── Dockerfile.alertmanager      # AlertManager container
│
├── log_config/                      # Logging configuration
│   ├── __init__.py                  # Logging setup
│   └── __pycache__/
│
├── data/                            # Data fixtures
│   ├── chroma/                      # ChromaDB persistent storage
│   └── sqlite/                      # SQLite database
│
├── alembic/                         # Database migrations
│   ├── alembic.ini                  # Alembic configuration
│   └── versions/                    # Migration scripts
│
├── health_monitor.py                # Health check & monitoring
├── slack_notifier.py                # Slack notifications
├── generate_traffic.py              # Load testing utility
└── __pycache__/                     # Python cache
```

---

## Core Modules

### 1. Main Pipeline (`main.py`)

The entry point orchestrating the entire loan processing workflow.

**Responsibilities:**
- FastAPI application setup with CORS & Prometheus instrumentation
- LLM backend auto-detection (OpenAI → Anthropic → Ollama → Mock)
- 4-tier memory system initialization & orchestration
- Complete loan processing pipeline (5 harness sessions)
- REST API endpoints for application, memory, and metrics access
- Server-Sent Events (SSE) streaming for real-time pipeline visibility

**Key Functions:**
- `_run_pipeline()` — Main async generator orchestrating the entire workflow
- `_call_llm()` — Multi-backend LLM abstraction
- `_resolve_backend()` — Auto-detect available LLM backend
- Memory helpers: `ctx_add()`, `epi_log()`, `sem_add()`, `work_set()`

### 2. Agent System (`agents/`)

Four specialist agents coordinate via A2A (Agent-to-Agent) protocol.

**Base Agent (`agents/base.py`):**
- Abstract `Agent` class with `run()` method
- Structured logging via `structlog`
- Execution timing & status tracking

**4 Specialist Agents:**

| Agent | Role | Skills | Input | Output |
|-------|------|--------|-------|--------|
| **Intake** | Initial validation | loan_intake, kyc_verification, affordability_precheck | Customer profile, KYC status, DTI | Application completeness assessment |
| **Risk** | Credit evaluation | credit_risk, dti_analysis, income_verification | Credit score, DTI, income, loan amount | Risk level (LOW/MEDIUM/HIGH) |
| **Fraud** | Anomaly detection | fraud_screening, transaction_analysis, aml_check | Transaction history, fraud flags | Fraud verdict (proceed/review/block) |
| **Decision** | Final approval | credit_decision, offer_generation, decline_reasoning | All upstream assessments | APPROVED / CONDITIONAL / DECLINED |

### 3. Tool System (`tools/`)

Tools implement the SDK layer with automatic registration and discovery.

**Tool Registry (`tools/registry.py`):**
- `TOOLS` global dict: tool_name → {name, description, fn, args_schema}
- `@register_tool` decorator for automatic registration
- Tool discovery endpoint: `/api/tools`

**Tool Categories:**

| Category | Tools | Purpose |
|----------|-------|---------|
| **Customer** | `get_customer_profile()`, `verify_kyc_documents()` | Customer data retrieval, identity verification |
| **Credit** | `check_credit_score()`, `calculate_affordability()` | Credit bureau checks, DTI calculation |
| **Fraud** | `scan_transaction_history()` | Transaction anomaly detection |
| **Compliance** | `query_banking_rules()` | Regulatory rules lookup (ChromaDB semantic search) |

### 4. Memory System (`memory/`)

A 4-tier memory architecture enabling persistent, semantic, and real-time data access.

#### **1. In-Context Memory** (`memory/context.py`)
- **Storage:** Python list in-process
- **Capacity:** 10 turns (configurable)
- **Lifecycle:** Session-scoped
- **Compaction:** Auto-compact when limit reached (keep system msgs + last 4 turns)
- **Use Case:** Active conversation history for LLM context window

#### **2. Episodic Memory** (`memory/episodic.py`)
- **Storage:** SQLite database (`/data/sqlite/banking.db`)
- **Schema:** `loan_events` (id, app_id, session, agent, event, detail, outcome, ts)
- **Lifecycle:** Persistent across sessions
- **Use Case:** Audit trail, compliance logging, application history

#### **3. Semantic Memory** (`memory/semantic.py`)
- **Storage:** ChromaDB vector database (`/data/chroma/`)
- **Embeddings:** Sentence Transformers (all-MiniLM-L6-v2)
- **Content:** Banking rules, decision patterns, regulatory knowledge
- **Query:** Vector similarity search (cosine distance)
- **Use Case:** Regulatory knowledge base, pattern matching

#### **4. Working Memory** (`memory/working.py`)
- **Storage:** Redis (primary) with in-process fallback
- **TTL:** Per-key expiration (default 120-600s)
- **Keys:** `bank:{app_id}:{stage}` (e.g., `bank:LOAN-123:risk_level`)
- **Use Case:** Inter-agent communication, cache for downstream stages

### 5. LLM Backend System (`llm/`)

Multi-backend LLM abstraction with auto-detection.

**LLMBackend Interface (`llm/backend.py`):**
```python
async def call(system: str, user: str, max_tokens: int = 400) -> str
```

**Implementations:**

| Backend | Model | Endpoint | Timeout | Fallback |
|---------|-------|----------|---------|----------|
| **OpenAI** | gpt-4o-mini | api.openai.com | 60s | Next backend |
| **Anthropic** | claude-haiku-4-5 | api.anthropic.com | 60s | Next backend |
| **Ollama** | qwen3:0.6b (configurable) | localhost:11434 | 120s | Next backend |
| **Mock** | mock | in-process | instant | Final fallback |

**Backend Factory (`llm/factory.py`):**
- Auto-detection: checks for API keys, probes Ollama, falls back to mock
- Logged on startup: `[Banking Demo] LLM: {backend}/{model}`

### 6. Harness / Workflow Orchestration (`harness/`)

Manages multi-session workflows with progress tracking.

**Session Management (`harness/session.py`):**
- Tracks application state across 5 harness sessions
- Progress file: `{app_id}:progress` in working memory
- State includes: app_id, session_num, customer, loan, progress dict, results, timings

**Pipeline Orchestration (`harness/pipeline.py`):**
- Coordinates 5 sequential sessions:
  1. **INITIALIZER** — Setup, memory seeding
  2. **INTAKE** — Customer validation, KYC, affordability
  3. **RISK** — Credit risk assessment
  4. **FRAUD** — Fraud screening
  5. **DECISION** — Final credit decision

---

## Component Interaction

### End-to-End Loan Processing Pipeline

```
┌─────────────────────────────────────────────────────────────────────┐
│ CLIENT REQUEST: /api/run?customer_id=CUST001&amount=15000           │
└──────────────────────┬──────────────────────────────────────────────┘
                       │
        ┌──────────────▼───────────────────────┐
        │ HARNESS: Session 1 — INITIALIZER     │
        │ - Create app_id                      │
        │ - Initialize session state           │
        │ - Seed memory stores                 │
        └──────────────┬───────────────────────┘
                       │
        ┌──────────────▼───────────────────────────────────────┐
        │ HARNESS: Session 2 — INTAKE AGENT (A2A)             │
        │                                                      │
        │ 1. SDK: Dispatch tools                              │
        │    - get_customer_profile(CUST001)                  │
        │    - verify_kyc_documents(CUST001)                  │
        │    - calculate_affordability(...)                   │
        │                                                      │
        │ 2. METRICS: TOOL_CALLS++, TOOL_LATENCY observe      │
        │                                                      │
        │ 3. A2A: Discover Intake Agent via Agent Card        │
        │                                                      │
        │ 4. LLM: Call with system prompt + context           │
        │    Backend: OpenAI/Anthropic/Ollama/Mock            │
        │    Response: "Application complete. KYC pass..."    │
        │                                                      │
        │ 5. MEMORY: Store results                            │
        │    - In-Context: add assistant response             │
        │    - Working: cache intake_summary (TTL 600s)       │
        │    - Episodic: log intake_complete                  │
        │                                                      │
        │ 6. METRICS: AGENT_CALLS++, AGENT_LATENCY observe    │
        └──────────────┬───────────────────────────────────────┘
                       │
        ┌──────────────▼───────────────────────────────────────┐
        │ HARNESS: Session 3 — RISK AGENT (A2A)               │
        │                                                      │
        │ 1. MEMORY: Query Semantic                           │
        │    Query: "credit score DTI loan requirements"      │
        │    Result: [relevant banking rule]                  │
        │                                                      │
        │ 2. SDK: check_credit_score(CUST001)                 │
        │                                                      │
        │ 3. LLM: Risk assessment (2-sentence summary)        │
        │                                                      │
        │ 4. MEMORY: Store risk_level in Working (Redis)      │
        │    Key: {app_id}:risk_level                         │
        │    Value: LOW/MEDIUM/HIGH                           │
        └──────────────┬───────────────────────────────────────┘
                       │
        ┌──────────────▼───────────────────────────────────────┐
        │ HARNESS: Session 4 — FRAUD AGENT (A2A)              │
        │                                                      │
        │ 1. SDK: scan_transaction_history(CUST001)           │
        │                                                      │
        │ 2. MEMORY: Read Working (Redis)                     │
        │    Lookup: {app_id}:risk_level → "MEDIUM"           │
        │                                                      │
        │ 3. LLM: Fraud assessment                            │
        │                                                      │
        │ 4. CONTEXT COMPACTION (if needed)                   │
        │    Before: 10 turns                                 │
        │    After: 6 turns (keep system + last 4)            │
        │    Metric: COMPACTIONS++                            │
        └──────────────┬───────────────────────────────────────┘
                       │
        ┌──────────────▼───────────────────────────────────────┐
        │ HARNESS: Session 5 — DECISION AGENT (A2A)           │
        │                                                      │
        │ 1. LLM: Final decision                              │
        │    Input: All 3 upstream assessments                │
        │    Output: APPROVED / CONDITIONAL / DECLINED        │
        │                                                      │
        │ 2. METRICS: Record decision outcome                 │
        │    - APPLICATIONS_TOTAL++                           │
        │    - APPLICATIONS_APPROVED++ (if approved)          │
        │    - PIPELINE_DECISIONS[outcome]++                  │
        │    - PIPELINE_DURATION observe                      │
        │                                                      │
        │ 3. MEMORY: Store decision                           │
        │    - Episodic: final decision + status              │
        │    - Semantic: decision pattern for future ref      │
        │    - Working: decision (TTL 1hr)                    │
        │    - In-Context: add decision response              │
        │                                                      │
        │ 4. NOTIFICATIONS: Post to Slack                     │
        │    - Customer name, decision, reason                │
        │    - Agent timings, total pipeline time             │
        │                                                      │
        │ 5. HEALTH MONITOR: Record application               │
        │    - Track decision distribution                    │
        │    - Monitor pipeline latency                       │
        └──────────────┬───────────────────────────────────────┘
                       │
                       ▼
        ┌──────────────────────────────────────┐
        │ SSE: Send 'done' event to client     │
        │ - app_id, customer, decision         │
        │ - Sessions: 5, Compactions: 0-1      │
        │ - Agents: 4, Tools: 5, Memory: 4     │
        └──────────────────────────────────────┘
```

### Data Flow Example: Risk Agent Reading Intake Results

```
Session 2 (Intake):
  ├─ Tool: calculate_affordability() → DTI = 35%
  ├─ LLM: "Application complete. DTI passes..."
  └─ MEMORY: Working.set("LOAN-123:intake_summary", "...", TTL=600s)

Session 3 (Risk):
  ├─ MEMORY: Semantic.query("credit score DTI") → [banking rule]
  ├─ Tool: check_credit_score() → 742
  ├─ LLM: "Risk: LOW. Score 742 is above threshold..."
  └─ MEMORY: Working.set("LOAN-123:risk_level", "LOW", TTL=600s)

Session 4 (Fraud):
  ├─ Tool: scan_transaction_history() → 3 declined, 2 foreign
  ├─ MEMORY: Working.get("LOAN-123:risk_level") → "LOW" (cache hit)
  ├─ LLM: "No fraud. Upstream risk LOW..."
  └─ MEMORY: Episodic.log(app_id, 4, "fraud", "fraud_complete", "...")

Session 5 (Decision):
  ├─ LLM: Reads all 3 upstream assessments from In-Context
  ├─ Decision: "APPROVED: strong credit profile, manageable DTI..."
  └─ MEMORY: 
      ├─ Episodic: final decision + status
      ├─ Semantic: decision pattern stored
      └─ Working: decision cached (TTL=3600s)
```

---

## Memory System

### 4-Tier Architecture

The memory system provides multiple layers of persistence and retrieval:

```
┌─────────────────────────────────────────────────────────────┐
│ IN-CONTEXT MEMORY (Python list)                             │
│ - Active session conversation history                       │
│ - Auto-compaction at 10 turns                               │
│ - Provides LLM context window                               │
└─────────────────────────────────────────────────────────────┘
                           │
┌─────────────────────────────────────────────────────────────┐
│ EPISODIC MEMORY (SQLite)                                    │
│ - Persistent audit trail                                    │
│ - loan_events table: app_id, session, agent, event, outcome │
│ - loan_applications table: customer, amount, status         │
│ - Compliance & historical tracking                          │
└─────────────────────────────────────────────────────────────┘
                           │
┌─────────────────────────────────────────────────────────────┐
│ SEMANTIC MEMORY (ChromaDB)                                  │
│ - Vector embeddings (all-MiniLM-L6-v2)                      │
│ - Banking rules, decision patterns, regulatory knowledge    │
│ - Cosine similarity search                                  │
│ - Pattern matching & knowledge base                         │
└─────────────────────────────────────────────────────────────┘
                           │
┌─────────────────────────────────────────────────────────────┐
│ WORKING MEMORY (Redis)                                      │
│ - TTL-based cache (120-3600s)                               │
│ - Inter-agent communication                                 │
│ - High-speed lookup for downstream stages                   │
│ - Fallback: in-process dict                                 │
└─────────────────────────────────────────────────────────────┘
```

---

## REST API

### Core Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/status` | GET | Service status, LLM backend |
| `/api/llm/status` | GET | LLM backend details |
| `/api/customers` | GET | List dummy customers |
| `/api/applications` | GET | List processed applications |
| `/api/events/{app_id}` | GET | Episodic memory audit trail |
| `/api/tools` | GET | Registered tools metadata |
| `/api/agents` | GET | A2A agent definitions |
| `/api/memory/context` | GET | In-context memory state |
| `/api/memory/working` | GET | Working memory (Redis) items |
| `/api/memory/episodic` | GET | Episodic memory (SQLite) audit log |
| `/api/memory/semantic` | GET | Semantic memory (ChromaDB) knowledge base |
| `/api/memory/stats` | GET | Memory statistics across all 4 stores |
| `/api/memory/clear/episodic` | POST | Clear SQLite audit trail |
| `/api/memory/clear/semantic` | POST | Clear ChromaDB knowledge base |
| `/api/run` | GET | Execute full pipeline (SSE stream) |
| `/api/seed` | GET | Pre-populate 3 applications |
| `/api/generate-traffic/{count}` | GET | Load test (20/30/50 applications) |

### Example API Calls

```bash
# Check service status
curl http://localhost:8005/api/status

# List available tools
curl http://localhost:8005/api/tools

# List all agents
curl http://localhost:8005/api/agents

# Run a single application
curl "http://localhost:8005/api/run?customer_id=CUST001&amount=15000&term_months=36"

# View memory statistics
curl http://localhost:8005/api/memory/stats

# Generate load test
curl http://localhost:8005/api/generate-traffic/20

# View audit trail for an application
curl http://localhost:8005/api/events/LOAN-123456-001
```

---

## Deployment

### Docker Compose Stack

```
┌─────────────────────────────────────────────────────────────┐
│ Docker Network: banking-net                                 │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────────────┐  ┌──────────────────────┐         │
│  │ banking-demo:8005    │  │ redis:6379           │         │
│  │ - FastAPI app        │  │ - Working memory     │         │
│  │ - ChromaDB embedded  │  │ - TTL cache          │         │
│  │ - SQLite embedded    │  │ - 128MB max memory   │         │
│  └──────────────────────┘  └──────────────────────┘         │
│           │                         ▲                        │
│           └─────────────────────────┘                        │
│                                                              │
│  ┌──────────────────────┐  ┌──────────────────────┐         │
│  │ prometheus:9090      │  │ grafana:3000         │         │
│  │ - Metrics scraping   │  │ - Dashboards         │         │
│  │ - 30-day retention   │  │ - Visualization      │         │
│  └──────────────────────┘  └──────────────────────┘         │
│           ▲                         ▲                        │
│           └─────────────────────────┘                        │
│                                                              │
│  ┌──────────────────────┐                                   │
│  │ alertmanager:9093    │                                   │
│  │ - Alert routing      │                                   │
│  │ - Slack integration  │                                   │
│  └──────────────────────┘                                   │
│                                                              │
└─────────────────────────────────────────────────────────────┘

External:
  - Ollama (host.docker.internal:11434)
  - OpenAI API (api.openai.com)
  - Anthropic API (api.anthropic.com)
  - Slack Webhook
```

### Start the Stack

```bash
# Build and start all services
docker compose up --build

# View logs
docker compose logs -f banking-demo

# Stop the stack
docker compose down

# Clean up volumes
docker compose down -v
```

### Access Services

- **Banking Demo API:** http://localhost:8005
- **Grafana Dashboards:** http://localhost:3000 (admin/admin)
- **Prometheus Metrics:** http://localhost:9090
- **AlertManager:** http://localhost:9093
- **Prometheus Metrics Endpoint:** http://localhost:8005/metrics

---

## Configuration

### Environment Variables

```bash
# LLM Backend Selection
OPENAI_API_KEY=sk-...                    # Enable OpenAI
ANTHROPIC_API_KEY=sk-ant-...             # Enable Anthropic
OLLAMA_HOST=http://host.docker.internal:11434
OLLAMA_MODEL=qwen3:0.6b
COMBINED_OLLAMA_MODEL=...                # Override OLLAMA_MODEL

# Data Paths
DATA_DIR=/data                           # ChromaDB, SQLite location

# Redis
REDIS_URL=redis://redis:6379             # Working memory

# Observability
SLACK_WEBHOOK_URL=https://hooks.slack.com/...
GRAFANA_USER=admin
GRAFANA_PASSWORD=admin

# Logging
LOG_LEVEL=INFO
```

### .env Example

```bash
# Copy and customize
OPENAI_API_KEY=
ANTHROPIC_API_KEY=
OLLAMA_HOST=http://host.docker.internal:11434
OLLAMA_MODEL=qwen3:0.6b
DATA_DIR=/data
REDIS_URL=redis://redis:6379
SLACK_WEBHOOK_URL=
GRAFANA_PASSWORD=admin
LOG_LEVEL=INFO
```

---

## Observability

### Prometheus Metrics (20+)

**Pipeline Metrics:**
- `banking_pipeline_runs_total` — Total runs
- `banking_pipeline_duration_seconds` — End-to-end latency
- `banking_decisions_total[outcome]` — By outcome (approved/declined/conditional)

**Application Metrics:**
- `banking_applications_total` — Total processed
- `banking_applications_approved_total` — Approved count
- `banking_applications_declined_total` — Declined count
- `banking_applications_conditional_total` — Conditional count

**Risk & Fraud:**
- `banking_risk_alerts_total[risk_level]` — By level (low/medium/high)
- `banking_fraud_detections_total[fraud_type]` — By type

**Memory:**
- `banking_memory_items_total[memory_type]` — Items per store
- `banking_memory_operations_total[memory_type, operation]` — Ops per store

**Agent:**
- `banking_agent_calls_total[agent]` — Calls per agent
- `banking_agent_errors_total[agent, error_type]` — Errors per agent
- `banking_agent_duration_seconds[agent]` — Latency per agent

**LLM:**
- `banking_llm_requests_total[backend, status]` — Requests per backend
- `banking_llm_tokens_used_total[backend]` — Token usage
- `banking_llm_latency_seconds[backend]` — Response latency

**Tools:**
- `banking_tool_calls_total[tool_name]` — Calls per tool
- `banking_tool_duration_seconds[tool_name]` — Execution time
- `banking_tool_errors_total[tool_name, error_type]` — Errors per tool

### Grafana Dashboards

Pre-configured dashboards available at http://localhost:3000:
- **Pipeline Metrics** — Application decisions, throughput, latency
- **Agent Performance** — Per-agent latency, call counts, error rates
- **Memory Usage** — All 4 memory stores, compaction events
- **LLM Backend** — Request rates, token usage, latency by backend
- **Risk & Fraud** — Alert distribution, fraud detection patterns

### AlertManager

Alerts configured in `monitoring/alert_rules.yml`:
- High fraud rate (>5% of applications)
- Pipeline failures
- Agent timeouts
- Memory pressure

Alerts route to Slack webhook when configured.

---

## Testing

### Testing Framework

- **pytest** — Unit & integration tests
- **pytest-asyncio** — Async test support
- **pytest-cov** — Coverage reporting
- **pytest-mock** — Mocking utilities
- **responses** — HTTP mock responses
- **freezegun** — Time mocking

### Run Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=. --cov-report=html

# Run specific test file
pytest tests/test_agents.py

# Run with verbose output
pytest -v

# Run async tests
pytest -v --asyncio-mode=auto
```

### Load Testing

```bash
# Generate 20 random applications
curl http://localhost:8005/api/generate-traffic/20

# Generate 50 random applications
curl http://localhost:8005/api/generate-traffic/50

# Monitor metrics during load test
# Open Grafana: http://localhost:3000
```

---

## Design Patterns

### 1. Decorator Pattern (Tools)
```python
@register_tool(name="get_customer_profile", ...)
def get_customer_profile(customer_id: str) -> dict:
    # Auto-registered in TOOLS registry
```

### 2. Abstract Base Classes (Memory, LLM)
- `MemoryStore` ABC with 4 implementations
- `LLMBackend` ABC with 4 implementations
- Enables dependency injection & testing

### 3. Factory Pattern (LLM Backend)
- `_resolve_backend()` auto-detects available backend
- Fallback chain: OpenAI → Anthropic → Ollama → Mock

### 4. Registry Pattern (Agents, Tools)
- Global `A2A_AGENTS` dict for agent discovery
- Global `TOOLS` dict for tool discovery
- Agent Cards for A2A protocol

### 5. Event Streaming (SSE)
- Real-time pipeline visibility
- `_ev()` helper generates SSE events
- Client receives: harness_session, sdk_tool, a2a_request, memory, done

### 6. Context Compaction
- Automatic when in-context memory exceeds limit
- Keeps system messages + last 4 turns
- Maintains session continuity

---

## Key Features

✅ **Multi-Agent Orchestration** — 4 specialist agents (Intake, Risk, Fraud, Decision) coordinating via A2A protocol

✅ **4-Tier Memory System** — In-context, episodic (SQLite), semantic (ChromaDB), working (Redis)

✅ **Multi-Backend LLM Support** — OpenAI, Anthropic, Ollama, Mock with auto-detection

✅ **Tool Registration** — Decorator-based tool discovery and execution

✅ **Comprehensive Observability** — 20+ Prometheus metrics, Grafana dashboards, AlertManager integration

✅ **Real-Time Streaming** — Server-Sent Events for pipeline visibility

✅ **Production-Ready** — Docker Compose, health checks, error handling, structured logging

✅ **Extensible Architecture** — Abstract base classes for memory, LLM, agents, tools

---

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## License

This project is licensed under the MIT License — see the LICENSE file for details.

---

## Support

For issues, questions, or feedback:
- Open an issue on GitHub
- Check existing documentation in `/tools/README.md`
- Review the monitoring dashboards at http://localhost:3000

---

## Summary

This Banking Demo showcases a **production-grade AI agent platform** with:

- **SDK Layer** — Tool registration, structured dispatch
- **Harness** — Multi-session workflow orchestration
- **A2A Protocol** — Agent-to-agent JSON-RPC communication
- **Memory System** — 4-tier architecture (context, episodic, semantic, working)
- **LLM Abstraction** — Multi-backend support with auto-detection
- **Observability** — Prometheus metrics, Grafana dashboards, alerts
- **Scalability** — Docker Compose, Redis caching, async/await

The **loan processing pipeline** demonstrates real-world complexity: customer validation, credit risk assessment, fraud detection, and final decision-making — all coordinated through memory systems and observable via comprehensive metrics.
