# IT Support Platform — Ticket Resolution & Escalation System

An AI agent system for automated IT support ticket management, built with FastAPI and multi-agent collaboration.

## Quick Start

### Prerequisites
- Python 3.11+
- Docker & Docker Compose
- (Optional) Ollama, OpenAI API key, or Anthropic API key

### Run IT Support Platform Locally

```bash
# Clone or navigate to the IT Support project
cd itsupport-platform

# Install dependencies
pip install -r requirements.txt

# Set environment variables (optional)
export OLLAMA_HOST=http://localhost:11434
export OLLAMA_MODEL=qwen3:0.6b

# Run the application
python main.py
```

Then visit: **http://localhost:8007** — Ticket resolution pipeline

### Run IT Support Platform with Docker

```bash
# Build Docker image
docker build -t itsupport-demo .

# Run with Docker
docker run -p 8007:8007 \
  -e OLLAMA_HOST=http://host.docker.internal:11434 \
  -v itsupport-data:/data \
  itsupport-demo
```

Then visit: **http://localhost:8007**

### Run IT Support with Docker Compose

```bash
# Start IT Support + Redis + data volumes
docker-compose -f docker-compose.yml up

# Access at http://localhost:8007
```

---

## Platform Overview

### IT Support Platform (Port 8007)
**Ticket Resolution Pipeline** — 4-agent support ticket system

- **Agents**: Triage → Diagnostic → Resolution → Escalation
- **Tools**: User profile, system health diagnostics, knowledge base search, SLA status check, similar ticket pattern detection (5 registered, 7 calls per run)
- **Use Case**: Automated ticket triage, root-cause diagnosis, step-by-step resolution, and escalation decision
- **Output**: AUTO-RESOLVE / ESCALATE L2 / ESCALATE L3 / EMERGENCY PROTOCOL

---

## Architecture

### Core Components
- **4 Specialist Agents**: Triage → Diagnostic → Resolution → Escalation
- **5 Registered Tools**: User profile, system health, KB search, SLA check, similar tickets
- **4 Memory Stores**: In-context, episodic (SQLite), semantic (ChromaDB), working (Redis)
- **Multi-Session Harness**: 5-session pipeline orchestration
- **FastAPI Backend**: RESTful API with streaming SSE support
- **Interactive Frontend**: Real-time ticket resolution UI

### 15-Module Structure

```
itsupport-platform/
├── main.py              # Entry point (75 lines)
├── config.py            # Centralized configuration (60 lines)
├── llm.py               # LLM backend resolution (70 lines)
├── memory/              # 4-store memory package (200 lines)
│   ├── __init__.py
│   ├── context.py       # In-context memory (auto-compaction at 10 turns)
│   ├── episodic.py      # SQLite audit log (/data/sqlite/itsupport.db)
│   ├── semantic.py      # ChromaDB embeddings (/data/chroma)
│   └── working.py       # Redis cache (with in-process fallback)
├── harness.py           # Pipeline orchestration (300 lines)
├── api.py               # FastAPI routes (160 lines)
├── ui.py                # Interactive frontend (430 lines)
├── data.py              # IT Support data (50 lines)
├── tools.py             # 5 SDK tools (85 lines)
├── agents.py            # 4 A2A agents (50 lines)
├── mock.py              # Deterministic mock responses (70 lines)
├── test_endpoints.py    # Endpoint verification tests
├── Dockerfile
└── requirements.txt
```

---

## Agents & Tools

### Agent Pipeline

| Stage | Agent | Role | Tools Called |
|-------|-------|------|--------------|
| 1 | **Triage** | Investigator | `get_user_profile`, `check_system_health` |
| 2 | **Diagnostic** | Investigator | `check_system_health`, `check_similar_tickets` |
| 3 | **Resolution** | Investigator | `search_knowledge_base`, `check_sla_status` + triage & diagnostic summaries |
| 4 | **Escalation** | Hybrid | `check_sla_status` + all 3 prior agent summaries |

### Tools (5 Registered, 7 Calls per Run)

| # | Tool | Purpose | Called By |
|---|------|---------|-----------|
| 1 | `get_user_profile` | Retrieve user details and tier | Triage |
| 2 | `check_system_health` | System diagnostics & logs | Triage, Diagnostic |
| 3 | `search_knowledge_base` | Find resolution articles | Resolution |
| 4 | `check_sla_status` | Check SLA and outage status | Resolution, Escalation |
| 5 | `check_similar_tickets` | Find similar historical tickets | Diagnostic |

### Escalation Decision Matrix

| Condition | Decision | Ticket Status |
|-----------|----------|---------------|
| Priority = CRITICAL | EMERGENCY PROTOCOL | emergency |
| Category = Security/Malware | EMERGENCY PROTOCOL | emergency |
| User tier ≥ 2 + Priority = HIGH/MEDIUM | ESCALATE L2 | escalated_l2 |
| SLA warning or outage detected | ESCALATE L3 | escalated_l3 |
| All other cases | AUTO-RESOLVE | resolved |

---

## Harness & Sessions

### Multi-Session Workflow (5 Sessions per Pipeline Run)

| Session | Purpose | Agent | Progress |
|---------|---------|-------|----------|
| 1 | Initialize | — | Ticket created, episodic log written |
| 2 | Triage | Triage | Classify ticket + priority |
| 3 | Diagnostic | Diagnostic | Health check + log analysis |
| 4 | Resolution | Resolution | KB search + SLA check + triage & diagnostic summaries |
| 5 | Escalation | Escalation | SLA check + all 3 prior summaries (hybrid) |

### Context Management

- **In-Context Memory**: Active conversation turns with auto-compaction at 10 turns
- **Episodic Memory**: SQLite audit log for persistence (`/data/sqlite/itsupport.db`)
- **Semantic Memory**: ChromaDB vector embeddings for knowledge base (`/data/chroma`)
- **Working Memory**: Redis cache with in-process fallback (`redis://redis:6379`)

---

## API Endpoints

### Common Endpoints

```
GET  /api/status              # Service health & LLM status
GET  /                        # Interactive UI
GET  /api/agents              # List agents (4 agents)
GET  /api/tools               # List tools (5 tools)
GET  /api/memory/context      # In-context memory
GET  /api/memory/working      # Working cache
GET  /metrics                 # Prometheus metrics
```

### IT Support Specific Endpoints

```
GET  /api/users               # List users
GET  /api/tickets             # List tickets
GET  /api/events/{ticket_id}  # Ticket audit log (episodic memory)
GET  /api/run                 # Start ticket pipeline (streaming SSE)
```

### Endpoint Examples

#### Get Service Status
```bash
curl http://localhost:8007/api/status
# Returns: {"service": "itsupport-demo", "llm": "ollama", "model": "qwen3:0.6b", "mock": false, "chroma_ready": true}
```

#### List Users
```bash
curl http://localhost:8007/api/users
# Returns: [{"user_id": "USER001", "name": "Alice Johnson", "tier": 1, ...}, ...]
```

#### List Tickets
```bash
curl http://localhost:8007/api/tickets
# Returns: [{"ticket_id": "TICKET001", "user_id": "USER001", "category": "Network", ...}, ...]
```

#### Run Ticket Pipeline (Streaming)
```bash
curl http://localhost:8007/api/run?user_id=USER001&category=Network&priority=HIGH
# Streams SSE events in real-time
```

#### View Ticket Audit Log
```bash
curl http://localhost:8007/api/events/TICKET001
# Returns: [{"ts": "14:30:45", "agent": "triage", "summary": "..."}, ...]
```

---

## Streaming Response Format

All `/api/run` endpoints return **Server-Sent Events** (SSE):

```
data: {"kind": "session_start", "ts": "14:30:45", "session": 1, ...}

data: {"kind": "agent_start", "ts": "14:30:46", "agent": "triage", ...}

data: {"kind": "agent_complete", "ts": "14:30:48", "agent": "triage", "summary": "User is tier 1, system shows CPU spike", ...}

data: {"kind": "escalation_decision", "ts": "14:30:52", "level": "NONE", "response": "AUTO-RESOLVE", ...}

data: {"kind": "pipeline_complete", "ts": "14:30:52", "status": "resolved", ...}
```

Frontend consumes via `EventSource` API for real-time updates.

---

## LLM Backend Resolution

Automatic fallback chain:

1. **OpenAI** (if `OPENAI_API_KEY` set) → gpt-4o-mini
2. **Anthropic** (if `ANTHROPIC_API_KEY` set) → claude-haiku-4-5-20251001
3. **Ollama** (if available at `OLLAMA_HOST`) → qwen3:0.6b (default)
4. **Mock** (fallback) → Deterministic responses

---

## Environment Variables

### LLM Configuration

```bash
OPENAI_API_KEY=sk-...                    # Optional
ANTHROPIC_API_KEY=sk-ant-...             # Optional
OLLAMA_HOST=http://host.docker.internal:11434  # Docker default
OLLAMA_MODEL=qwen3:0.6b                  # Default model
```

### Data Persistence

```bash
DATA_DIR=/data                           # Default: /data
REDIS_URL=redis://redis:6379             # Default: redis://redis:6379
```

### Service Configuration

```bash
SERVICE_NAME=itsupport-demo              # Service identifier
SERVICE_PORT=8007                        # Port to listen on
```

---

## Data Persistence

- **SQLite**: `/data/sqlite/itsupport.db` — Audit logs and ticket records
- **ChromaDB**: `/data/chroma` — Vector embeddings for knowledge base
- **Redis**: `redis://redis:6379` — Session cache (with in-process fallback)

---

## Testing

### Run Endpoint Tests

```bash
cd itsupport-platform
python test_endpoints.py
```

Expected output:
```
Testing all endpoints:
  [OK] /api/status: 200
  [OK] /: 200 (29467 bytes)
  [OK] /api/users: 200 (10 users)
  [OK] /api/tickets: 200 (5 tickets)
  [OK] /api/agents: 200 (4 agents)
  [OK] /api/tools: 200 (5 tools)
  [OK] /api/run: 200 (10+ events)

STATUS: ALL ENDPOINTS WORKING
```

### Test Escalation Logic

The test suite verifies:
- ✅ CRITICAL priority → EMERGENCY PROTOCOL
- ✅ Security/Malware category → EMERGENCY PROTOCOL
- ✅ Tier-2 user + HIGH priority → ESCALATE L2
- ✅ Tier-1 user + LOW priority → AUTO-RESOLVE
- ✅ SLA warning detected → ESCALATE L3
- ✅ All agents using real LLM responses

---

## Metrics & Monitoring

### Prometheus Endpoint

```bash
curl http://localhost:8007/metrics
```

### Key Metrics

- `itsupport_pipeline_runs_total` — Total pipeline invocations
- `itsupport_agent_duration_seconds` — Per-agent latency (histogram with agent label)
  - Labels: `agent` (triage, diagnostic, resolution, escalation)

---

## Production Considerations

### Scalability

- **Horizontal**: Run multiple instances behind a load balancer
- **Vertical**: Increase worker processes with `uvicorn --workers N`
- **Async**: All endpoints are async-ready

### Reliability

- **Graceful Degradation**: Falls back to mock responses if LLM unavailable
- **Memory Fallbacks**: In-process dict if Redis offline, keyword matching if ChromaDB fails
- **Health Checks**: Docker health check probes `/api/status` every 25 seconds

### Security

- **CORS**: Enabled for all origins (configure in production)
- **Input Validation**: FastAPI Pydantic validation on all endpoints
- **Rate Limiting**: Can be added via middleware or API gateway

### Performance

- **Context Compaction**: Automatic at 10 turns to manage token usage
- **Streaming**: SSE for real-time updates without polling
- **Caching**: Redis working memory for cross-session data

---

## Customization

### Add a New Tool

```python
# In tools.py
@tool
def my_new_tool(param: str) -> dict:
    """Tool description."""
    return {"result": "..."}

# Automatically registered in TOOLS dict
```

### Add a New Agent

```python
# In agents.py
A2A_AGENTS["my_agent"] = {
    "name": "My Agent",
    "description": "...",
    "system_prompt": "...",
    "skills": [...]
}

# In harness.py
agents_sequence = ["triage", "diagnostic", "resolution", "my_agent"]
```

### Change LLM Backend

```python
# In llm.py - add new backend case
if _llm_backend == "my_llm":
    # Call your LLM API
    response = my_llm_api.call(system, user)
    return response
```

---

## Known Constraints

1. **Prometheus Integration** - The project doesn't integrate with prometheus
2. **No cross-platform code sharing** — This is a standalone project
3. **Single-threaded context** — `_context` is global; concurrent pipelines may interleave
4. **ChromaDB persistence** — Clearing `/data/chroma` resets knowledge base
5. **SQLite concurrency** — Multiple concurrent writes may block
6. **Redis TTL simulation** — In-process fallback uses wall-clock time

---

## Troubleshooting

### Port Already in Use

```bash
# Kill process on port 8007
lsof -ti:8007 | xargs kill -9
```

### Memory Store Failures

- **Redis offline**: Check `docker ps` and `docker logs redis`
- **ChromaDB error**: Clear `/data/chroma` and restart
- **SQLite locked**: Restart the service

### LLM Backend Issues

- **Ollama not found**: Ensure Ollama is running at `OLLAMA_HOST`
- **API key invalid**: Check `OPENAI_API_KEY` or `ANTHROPIC_API_KEY`
- **Mock mode**: Verify with `curl http://localhost:8007/api/status`

### Escalation Not Working

- Verify escalation agent is in `agents_sequence` in `harness.py`
- Check that escalation response contains decision keywords
- Review agent system prompt in `agents.py`

### Tests Failing

- Clear Python cache: `rm -rf __pycache__`
- Verify all dependencies installed: `pip install -r requirements.txt`
- Check database initialization: `/data/sqlite/itsupport.db`

---

## Repository Structure

```
itsupport-platform/
├── README.md                      ← This file
├── .env.example                   ← Environment variables template
├── docker-compose.yml             ← Docker Compose configuration
│
├── main.py                        ← Entry point
├── config.py                      ← Centralized configuration
├── llm.py                         ← LLM backend resolution
├── memory/                        ← 4-store memory package
│   ├── __init__.py
│   ├── context.py
│   ├── episodic.py
│   ├── semantic.py
│   └── working.py
├── harness.py                     ← Pipeline orchestration
├── api.py                         ← FastAPI routes
├── ui.py                          ← Interactive frontend
├── data.py                        ← IT Support data
├── tools.py                       ← 5 SDK tools
├── agents.py                      ← 4 A2A agents
├── mock.py                        ← Deterministic mock responses
├── test_endpoints.py              ← Endpoint verification tests
├── Dockerfile                     ← Docker image configuration
└── requirements.txt               ← Python dependencies
```

---

## Next Steps

### For Development

1. Modify tools in `tools.py`
2. Update agents in `agents.py`
3. Customize mock responses in `mock.py`
4. Run `python test_endpoints.py` to verify

### For Deployment

1. Set environment variables in `.env`
2. Build Docker image: `docker build -t itsupport-demo .`
3. Push to registry: `docker push registry/itsupport-demo`
4. Deploy with orchestration tool (Kubernetes, Docker Swarm, etc.)

### For Scaling

1. Run multiple instances behind a load balancer
2. Configure Redis for distributed caching
3. Enable ChromaDB for semantic search
4. Add monitoring with Prometheus metrics

---