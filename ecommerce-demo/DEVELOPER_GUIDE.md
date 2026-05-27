# E-Commerce Demo — Developer Guide

**Complete guide for developers working on this project**

---

## Table of Contents

1. [Getting Started](#getting-started)
2. [Development Environment](#development-environment)
3. [Project Structure](#project-structure)
4. [Core Concepts](#core-concepts)
5. [Working with Modules](#working-with-modules)
6. [Adding Features](#adding-features)
7. [Testing](#testing)
8. [Debugging](#debugging)
9. [Performance Optimization](#performance-optimization)
10. [Deployment](#deployment)
11. [Best Practices](#best-practices)
12. [Troubleshooting](#troubleshooting)

---

## Getting Started

### Prerequisites

```bash
# Python 3.10+
python --version

# Git
git --version

# Docker (optional, for containerized development)
docker --version
```

### Initial Setup

```bash
# 1. Clone repository
git clone <repo-url>
cd ecommerce-demo

# 2. Create virtual environment
python -m venv venv

# 3. Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# 4. Install dependencies
pip install -r requirements.txt

# 5. Copy environment template
cp .env.example .env

# 6. Edit .env with your configuration
# (Set LLM API keys, data directory, etc.)
```

### First Run

```bash
# Option 1: With Docker Compose (easiest)
docker compose up --build

# Option 2: Local development
# Terminal 1: Start Redis
docker run -d -p 6379:6379 redis:7.2-alpine

# Terminal 2: Start app
python -m uvicorn main:app --reload --port 8007

# Visit http://localhost:8007
```

---

## Development Environment

### IDE Setup

#### VS Code

```json
// .vscode/settings.json
{
  "python.defaultInterpreterPath": "${workspaceFolder}/venv/bin/python",
  "python.linting.enabled": true,
  "python.linting.pylintEnabled": true,
  "python.formatting.provider": "black",
  "editor.formatOnSave": true,
  "[python]": {
    "editor.defaultFormatter": "ms-python.python",
    "editor.formatOnSave": true,
    "editor.codeActionsOnSave": {
      "source.organizeImports": true
    }
  }
}
```

#### PyCharm

1. Open project
2. Configure interpreter: Settings → Project → Python Interpreter
3. Select `venv/bin/python`
4. Enable code inspections

### Development Tools

```bash
# Install development dependencies
pip install -r requirements.txt

# Code formatting
black .

# Linting
pylint llm memory agents tools harness

# Type checking
mypy llm memory agents tools harness

# Testing
pytest tests/ -v

# Coverage
pytest tests/ --cov=. --cov-report=html
```

### Environment Variables

Create `.env` file:

```bash
# LLM Configuration
OPENAI_API_KEY=sk-...              # Optional: OpenAI
ANTHROPIC_API_KEY=sk-ant-...       # Optional: Anthropic
OLLAMA_HOST=http://localhost:11434 # Local Ollama
OLLAMA_MODEL=qwen3:0.6b            # Ollama model

# Data Storage
DATA_DIR=./data                     # Local data directory

# Redis
REDIS_URL=redis://localhost:6379   # Local Redis

# Observability
SLACK_WEBHOOK_URL=                  # Optional: Slack alerts
GRAFANA_USER=admin
GRAFANA_PASSWORD=admin
```

---

## Project Structure

### Directory Layout

```
ecommerce-demo/
│
├── 📄 main.py                      # FastAPI application entry point
├── 📄 transaction_summary.py       # Transaction metrics
├── 📄 requirements.txt             # Python dependencies
├── 📄 docker-compose.yml           # Docker orchestration
├── 📄 Dockerfile                   # App container image
├── 📄 .env.example                 # Environment template
├── 📄 .gitignore                   # Git ignore rules
│
├── 📁 llm/                         # LLM Backend Layer
│   ├── __init__.py
│   ├── backend.py                  # Abstract base class
│   ├── factory.py                  # Factory pattern
│   ├── mock_client.py              # Mock LLM
│   ├── ollama_client.py            # Ollama integration
│   ├── openai_client.py            # OpenAI integration
│   └── anthropic_client.py         # Anthropic integration
│
├── 📁 memory/                      # 4-Tier Memory System
│   ├── __init__.py
│   ├── manager.py                  # Memory coordinator
│   ├── context.py                  # In-context memory
│   ├── episodic.py                 # Episodic memory (SQLite)
│   ├── semantic.py                 # Semantic memory (ChromaDB)
│   └── working.py                  # Working memory (Redis)
│
├── 📁 agents/                      # Agent Definitions
│   ├── __init__.py
│   ├── definitions.py              # Agent specs
│   └── mock_responses.py           # Mock responses
│
├── 📁 tools/                       # Tools Registry
│   ├── __init__.py
│   ├── registry.py                 # Tool registration
│   ├── customer.py                 # Customer tools
│   ├── inventory.py                # Inventory tools
│   ├── pricing.py                  # Pricing tools
│   └── fraud.py                    # Fraud tools
│
├── 📁 data/                        # Data Models
│   ├── __init__.py
│   └── models.py                   # Data structures
│
├── 📁 harness/                     # Pipeline Orchestration
│   ├── __init__.py
│   └── pipeline.py                 # Order processing pipeline
│
├── 📁 tests/                       # Unit Tests
│   ├── __init__.py
│   ├── test_tools.py               # Tool tests
│   ├── test_memory.py              # Memory tests
│   └── test_agents.py              # Agent tests
│
├── 📁 monitoring/                  # Observability Configuration
│   ├── prometheus.yml              # Prometheus config
│   ├── alert_rules.yml             # Alert rules
│   ├── alertmanager.yml            # AlertManager config
│   ├── Dockerfile.alertmanager     # AlertManager image
│   └── grafana/                    # Grafana configuration
│
├── 📁 data/                        # Runtime Data (volumes)
│   ├── chroma/                     # ChromaDB data
│   └── sqlite/                     # SQLite databases
│
└── 📁 docs/                        # Documentation
    ├── README.md                   # Getting started
    ├── DEVELOPER_GUIDE.md          # This file
    ├── ANALYSIS_SUMMARY.md         # Analysis summary
    ├── CODEBASE_ANALYSIS.md        # Technical reference
    ├── ARCHITECTURE_DIAGRAMS.md    # Visual diagrams
    ├── QUICK_REFERENCE.md          # Quick lookup
    └── INDEX.md                    # Module navigation
```

### Module Responsibilities

| Module | Responsibility | Key Files |
|--------|-----------------|-----------|
| **llm** | Abstract LLM backends | backend.py, factory.py, *_client.py |
| **memory** | 4-tier memory coordination | manager.py, context.py, episodic.py, semantic.py, working.py |
| **agents** | Agent definitions & specs | definitions.py, mock_responses.py |
| **tools** | SDK tools registry | registry.py, customer.py, inventory.py, pricing.py, fraud.py |
| **data** | Data models & dummy data | models.py |
| **harness** | Pipeline orchestration | pipeline.py |
| **tests** | Unit tests | test_tools.py, test_memory.py, test_agents.py |

---

## Core Concepts

### 1. Factory Pattern (LLM Backend)

**Purpose**: Automatic LLM backend selection with fallback chain

**Location**: `llm/factory.py`

**How it works:**
```python
# Priority order: OpenAI → Anthropic → Ollama → Mock
llm = await LLMFactory.create()

# Returns first available backend:
# 1. OpenAI (if OPENAI_API_KEY set)
# 2. Anthropic (if ANTHROPIC_API_KEY set)
# 3. Ollama (if reachable)
# 4. Mock (always available)
```

**Adding a new backend:**
```python
# 1. Create new client in llm/new_backend.py
class NewBackend(LLMBackend):
    async def call(self, system: str, user: str, max_tokens: int = 350) -> str:
        # Implementation
        pass
    
    def get_name(self) -> str:
        return "new_backend"
    
    def get_model(self) -> str:
        return "model_name"

# 2. Import in llm/factory.py
from .new_backend import NewBackend

# 3. Add to LLMFactory.create()
if new_condition:
    return NewBackend()
```

### 2. Registry Pattern (Tools)

**Purpose**: Decorator-based tool discovery and registration

**Location**: `tools/registry.py`

**How it works:**
```python
# Define tool with decorator
@register_tool
def get_customer(customer_id: str) -> dict:
    """Fetch customer profile."""
    return CUSTOMERS[customer_id]

# Tool is automatically registered in TOOLS dict
# TOOLS["get_customer"] = {
#     "name": "get_customer",
#     "description": "Fetch customer profile.",
#     "params": ["customer_id"],
#     "fn": get_customer
# }
```

**Adding a new tool:**
```python
# 1. Create in tools/domain.py
from tools.registry import register_tool

@register_tool
def my_tool(param: str) -> dict:
    """My tool description."""
    return {"result": "..."}

# 2. Import in tools/__init__.py
from .domain import my_tool

# 3. Tool is now available to agents
```

### 3. Coordinator Pattern (Memory)

**Purpose**: Unified interface for 4-tier memory system

**Location**: `memory/manager.py`

**How it works:**
```python
memory = MemoryManager(data_dir)

# Coordinates all memory tiers
memory.context.add("role", "message")      # In-memory
memory.episodic.upsert_order(order_data)   # SQLite
memory.semantic.query("policy")             # ChromaDB
memory.working.set("key", "value", ttl=300) # Redis
```

**Memory tiers:**

| Tier | Storage | Scope | TTL | Use Case |
|------|---------|-------|-----|----------|
| **Context** | Python list | In-process | None | Current conversation |
| **Episodic** | SQLite | Persistent | None | Order history |
| **Semantic** | ChromaDB | Persistent | None | Policy/knowledge search |
| **Working** | Redis | Distributed | Yes | Temporary state |

### 4. Pipeline Orchestrator Pattern

**Purpose**: Sequential stage execution with event streaming

**Location**: `harness/pipeline.py`

**How it works:**
```python
async def run_pipeline(order_id, customer, cart, llm, memory):
    # S1: Initialize
    yield _ev("harness_session", ...)
    
    # S2-S5: Agent stages
    for stage in [S2, S3, S4, S5]:
        yield _ev("agent_call", ...)
        result = await invoke_agent(stage, ...)
        yield _ev("agent_response", ...)
    
    # Complete
    yield _ev("pipeline_complete", ...)
```

**SSE Events:**
```json
{"kind": "harness_session", "ts": "14:30:45", ...}
{"kind": "agent_call", "agent": "validation", ...}
{"kind": "agent_response", "response": "...", ...}
{"kind": "pipeline_complete", "status": "confirmed", ...}
```

---

## Working with Modules

### LLM Module (`llm/`)

#### Understanding the LLM Layer

```python
# Abstract interface
class LLMBackend(ABC):
    @abstractmethod
    async def call(self, system: str, user: str, max_tokens: int = 350) -> str:
        pass
    
    @abstractmethod
    def get_name(self) -> str:
        pass
    
    @abstractmethod
    def get_model(self) -> str:
        pass
```

#### Using LLM in Code

```python
from llm import LLMFactory

# Create backend (auto-detection)
llm = await LLMFactory.create()

# Call LLM
response = await llm.call(
    system="You are an order validator.",
    user="Validate this order: ...",
    max_tokens=350
)

# Get backend info
print(llm.get_name())    # "openai", "anthropic", "ollama", "mock"
print(llm.get_model())   # "gpt-4o-mini", "claude-haiku", "qwen3:0.6b", etc.
```

#### Testing with Mock LLM

```python
# Mock LLM returns empty string, triggering mock responses
# Useful for testing without API calls

# Set in .env
OPENAI_API_KEY=
ANTHROPIC_API_KEY=
OLLAMA_HOST=http://unreachable:11434

# App will use mock LLM
```

### Memory Module (`memory/`)

#### Understanding Memory Tiers

```python
from memory import MemoryManager
from pathlib import Path

memory = MemoryManager(Path("/data"))

# Context Memory (in-process, 10 items)
memory.context.add("user", "Hello")
messages = memory.context.get_all()
memory.context.clear()

# Episodic Memory (SQLite, persistent)
memory.episodic.upsert_order({
    "id": "ORD-001",
    "customer_id": "C001",
    "total": 100.0,
    "status": "confirmed"
})
order = memory.episodic.get_order("ORD-001")
recent = memory.episodic.get_recent_orders(limit=10)

# Semantic Memory (ChromaDB, embeddings)
memory.semantic.add("Shipping policy: ...", {"type": "policy"})
results = memory.semantic.query("shipping", limit=5)
is_ready = memory.semantic.is_ready()

# Working Memory (Redis, TTL)
memory.working.set("session_key", "value", ttl=300)
value = memory.working.get("session_key")
memory.working.delete("session_key")
```

#### Extending Memory

```python
# Add new memory tier
# memory/custom.py
class CustomMemory:
    def add(self, item): ...
    def query(self, q): ...

# memory/manager.py
from .custom import CustomMemory

class MemoryManager:
    def __init__(self, data_dir: Path):
        self.context = ContextMemory(limit=10)
        self.episodic = EpisodicMemory(...)
        self.semantic = SemanticMemory(...)
        self.working = WorkingMemory()
        self.custom = CustomMemory()  # Add here
```

### Agents Module (`agents/`)

#### Understanding Agents

```python
# agents/definitions.py
A2A_AGENTS = {
    "validation": {
        "name": "Validation Agent",
        "description": "Verifies order details...",
        "skills": ["order_validation", "fraud_pre_check", ...],
        "system_prompt": "You are an e-commerce order validation specialist..."
    },
    # ... more agents
}
```

#### Adding a New Agent

```python
# agents/definitions.py
A2A_AGENTS["my_agent"] = {
    "name": "My Agent",
    "description": "My agent description",
    "skills": ["skill1", "skill2", "skill3"],
    "system_prompt": "You are a specialist in..."
}

# agents/mock_responses.py
def get_mock_response(agent_name: str, context: dict) -> str:
    if agent_name == "my_agent":
        return "My agent response..."
    # ... handle other agents
```

#### Invoking Agents

```python
from agents import A2A_AGENTS, get_mock_response
from llm import LLMBackend

async def invoke_agent(agent_name: str, context: dict, llm: LLMBackend) -> str:
    agent = A2A_AGENTS[agent_name]
    
    # Build prompt
    system = agent["system_prompt"]
    user = f"Context: {context}"
    
    # Call LLM
    response = await llm.call(system, user)
    
    # Fallback to mock if empty
    if not response:
        response = get_mock_response(agent_name, context)
    
    return response
```

### Tools Module (`tools/`)

#### Understanding Tools

```python
# tools/registry.py
TOOLS: dict[str, dict] = {}

def register_tool(fn):
    TOOLS[fn.__name__] = {
        "name": fn.__name__,
        "description": fn.__doc__ or "",
        "params": list(fn.__code__.co_varnames[:fn.__code__.co_argcount]),
        "fn": fn,
    }
    return fn
```

#### Adding a New Tool

```python
# tools/custom.py
from tools.registry import register_tool

@register_tool
def my_custom_tool(param1: str, param2: int) -> dict:
    """My custom tool description."""
    return {
        "param1": param1,
        "param2": param2,
        "result": "..."
    }

# tools/__init__.py
from .custom import my_custom_tool

# Now available as:
# from tools import my_custom_tool
# from tools import TOOLS  # includes my_custom_tool
```

#### Using Tools in Agents

```python
from tools import TOOLS, get_customer, check_inventory

# Direct call
customer = get_customer("C001")
inventory = check_inventory("SKU-001")

# Via registry
tool_fn = TOOLS["get_customer"]["fn"]
customer = tool_fn("C001")

# List all tools
for name, spec in TOOLS.items():
    print(f"{name}: {spec['description']}")
```

### Data Module (`data/`)

#### Understanding Data Models

```python
# data/models.py
CUSTOMERS = [
    {"id": "C001", "name": "Lena Fischer", "tier": "gold", ...},
    ...
]

PRODUCTS = [
    {"sku": "SKU-001", "name": "Headphones", "price": 149.99, ...},
    ...
]

PROMOTIONS = [
    {"code": "SUMMER20", "discount": 0.20, ...},
    ...
]

WAREHOUSES = [
    {"code": "LDN-EAST", "city": "London", ...},
    ...
]

POLICIES = [
    {"id": "P001", "title": "Shipping Policy", "content": "..."},
    ...
]
```

#### Adding Test Data

```python
# data/models.py
CUSTOMERS.append({
    "id": "C999",
    "name": "Test Customer",
    "email": "test@example.com",
    "tier": "bronze",
    "address": "123 Test St",
    "orders_ytd": 0,
    "loyalty_pts": 0,
    "flagged": False
})
```

### Pipeline Module (`harness/`)

#### Understanding the Pipeline

```python
# harness/pipeline.py
async def run_pipeline(
    order_id: str,
    customer: dict,
    cart: list[dict],
    llm: LLMBackend,
    memory: MemoryManager,
) -> AsyncGenerator[str, None]:
    """
    5-stage order processing pipeline:
    S1: Initialize
    S2: Validation Agent
    S3: Fulfilment Agent
    S4: Pricing Agent
    S5: Dispatch Agent
    """
    # Implementation
    pass
```

#### Extending the Pipeline

```python
# Add new stage
async def run_pipeline(...):
    # ... existing stages ...
    
    # S6: New Stage
    yield _ev("new_stage_start", ...)
    result = await new_stage_logic(...)
    yield _ev("new_stage_complete", ...)
    
    # ... rest of pipeline ...
```

---

## Adding Features

### Adding a New Tool

**Step 1: Create tool file**
```python
# tools/shipping.py
from tools.registry import register_tool

@register_tool
def calculate_express_shipping(weight_kg: float, distance_km: float) -> dict:
    """Calculate express shipping cost."""
    base_rate = 5.0
    weight_charge = weight_kg * 0.5
    distance_charge = distance_km * 0.01
    total = base_rate + weight_charge + distance_charge
    return {
        "cost": total,
        "delivery_days": 1,
        "method": "express"
    }
```

**Step 2: Import in tools/__init__.py**
```python
from .shipping import calculate_express_shipping
```

**Step 3: Use in agents**
```python
from tools import calculate_express_shipping

cost = calculate_express_shipping(weight_kg=2.5, distance_km=100)
```

### Adding a New Agent

**Step 1: Define agent**
```python
# agents/definitions.py
A2A_AGENTS["shipping"] = {
    "name": "Shipping Agent",
    "description": "Determines optimal shipping method",
    "skills": ["shipping_calculation", "carrier_selection"],
    "system_prompt": "You are a shipping logistics specialist..."
}
```

**Step 2: Add mock response**
```python
# agents/mock_responses.py
def get_mock_response(agent_name: str, context: dict) -> str:
    if agent_name == "shipping":
        return "Shipping via FedEx overnight delivery..."
    # ... other agents
```

**Step 3: Integrate into pipeline**
```python
# harness/pipeline.py
# Add new stage after S5
yield _ev("agent_call", agent="shipping", ...)
shipping_result = await invoke_agent("shipping", context, llm)
yield _ev("agent_response", response=shipping_result, ...)
```

### Adding a New LLM Backend

**Step 1: Create backend**
```python
# llm/cohere_client.py
import httpx
from .backend import LLMBackend

class CohereClient(LLMBackend):
    def __init__(self, api_key: str, model: str = "command"):
        self.api_key = api_key
        self.model = model
    
    async def call(self, system: str, user: str, max_tokens: int = 350) -> str:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.cohere.ai/v1/generate",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={
                    "prompt": f"{system}\n{user}",
                    "max_tokens": max_tokens,
                    "model": self.model
                }
            )
        return response.json()["generations"][0]["text"]
    
    def get_name(self) -> str:
        return "cohere"
    
    def get_model(self) -> str:
        return self.model
```

**Step 2: Update factory**
```python
# llm/factory.py
from .cohere_client import CohereClient

@staticmethod
async def create() -> LLMBackend:
    cohere_key = os.getenv("COHERE_API_KEY", "").strip()
    
    if cohere_key:
        return CohereClient(cohere_key)
    
    # ... rest of fallback chain
```

**Step 3: Add environment variable**
```bash
# .env
COHERE_API_KEY=sk-...
```

### Adding a New Memory Tier

**Step 1: Create memory class**
```python
# memory/elasticsearch.py
from elasticsearch import Elasticsearch

class ElasticsearchMemory:
    def __init__(self, host: str = "localhost", port: int = 9200):
        self.es = Elasticsearch([{"host": host, "port": port}])
    
    def add(self, doc_id: str, data: dict):
        self.es.index(index="memory", id=doc_id, body=data)
    
    def query(self, query: str, limit: int = 10) -> list:
        results = self.es.search(
            index="memory",
            body={"query": {"match": {"content": query}}},
            size=limit
        )
        return [hit["_source"] for hit in results["hits"]["hits"]]
```

**Step 2: Integrate into MemoryManager**
```python
# memory/manager.py
from .elasticsearch import ElasticsearchMemory

class MemoryManager:
    def __init__(self, data_dir: Path):
        self.context = ContextMemory(limit=10)
        self.episodic = EpisodicMemory(...)
        self.semantic = SemanticMemory(...)
        self.working = WorkingMemory()
        self.elasticsearch = ElasticsearchMemory()  # Add here
```

---

## Testing

### Test Structure

```
tests/
├── test_tools.py       # 6 tests
├── test_memory.py      # 5 tests
└── test_agents.py      # 3 tests
```

### Running Tests

```bash
# All tests
pytest tests/ -v

# Specific file
pytest tests/test_tools.py -v

# Specific test
pytest tests/test_tools.py::test_get_customer -v

# With coverage
pytest tests/ --cov=. --cov-report=html

# Watch mode
pytest-watch tests/
```

### Writing Tests

```python
# tests/test_custom.py
import pytest
from tools import my_tool

@pytest.mark.asyncio
async def test_my_tool():
    """Test my custom tool."""
    result = my_tool("test_param")
    assert result["status"] == "success"
    assert "result" in result

@pytest.mark.asyncio
async def test_my_tool_error():
    """Test my tool with invalid input."""
    with pytest.raises(ValueError):
        my_tool(None)
```

### Test Best Practices

1. **Use descriptive names** — `test_get_customer_returns_dict`
2. **Test one thing** — Each test should test one behavior
3. **Use fixtures** — Share common setup
4. **Mock external calls** — Don't call real APIs
5. **Test edge cases** — Empty, null, invalid inputs
6. **Keep tests fast** — Use mocks, not real services

### Example Test

```python
import pytest
from unittest.mock import patch, MagicMock
from tools import get_customer

def test_get_customer_success():
    """Test successful customer retrieval."""
    result = get_customer("C001")
    assert result["id"] == "C001"
    assert result["name"] == "Lena Fischer"
    assert result["tier"] == "gold"

def test_get_customer_not_found():
    """Test customer not found."""
    with pytest.raises(KeyError):
        get_customer("C999")

@pytest.mark.asyncio
async def test_pipeline_with_mock_llm():
    """Test pipeline with mock LLM."""
    from llm import MockLLMClient
    from memory import MemoryManager
    from harness import run_pipeline
    
    llm = MockLLMClient()
    memory = MemoryManager(Path("/tmp"))
    
    events = []
    async for event in run_pipeline("ORD-001", {...}, [...], llm, memory):
        events.append(event)
    
    assert len(events) > 0
    assert any("pipeline_complete" in e for e in events)
```

---

## Debugging

### Enable Debug Logging

```python
# main.py
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Now use in code
logger.debug(f"Processing order: {order_id}")
logger.info(f"Agent response: {response}")
logger.warning(f"Slow operation: {duration}s")
logger.error(f"Error: {error}")
```

### Debug with Print Statements

```python
# Quick debugging
print(f"DEBUG: order_id={order_id}")
print(f"DEBUG: customer={customer}")
print(f"DEBUG: cart={cart}")
```

### Debug with Debugger

```bash
# VS Code: Add breakpoint and run
python -m debugpy --listen 5678 -m uvicorn main:app --reload

# Or use pdb
import pdb; pdb.set_trace()
```

### Debug Docker Containers

```bash
# View logs
docker compose logs -f ecommerce-demo

# Execute command in container
docker compose exec ecommerce-demo bash

# Inspect container
docker inspect agent-ecommerce-demo
```

### Common Debugging Scenarios

**Issue: LLM not responding**
```python
# Check LLM status
from llm import LLMFactory
llm = await LLMFactory.create()
print(f"LLM: {llm.get_name()}/{llm.get_model()}")

# Test LLM call
response = await llm.call("test", "test")
print(f"Response: {response}")
```

**Issue: Memory not persisting**
```python
# Check memory status
from memory import MemoryManager
memory = MemoryManager(Path("/data"))

# Test each tier
memory.context.add("test", "message")
print(f"Context: {memory.context.get_all()}")

memory.episodic.upsert_order({"id": "TEST", "status": "test"})
print(f"Episodic: {memory.episodic.get_order('TEST')}")

memory.semantic.add("test", {})
print(f"Semantic ready: {memory.semantic.is_ready()}")

memory.working.set("test", "value")
print(f"Working: {memory.working.get('test')}")
```

**Issue: Agent not responding**
```python
# Check agent definition
from agents import A2A_AGENTS
print(f"Agents: {list(A2A_AGENTS.keys())}")

# Check agent spec
agent = A2A_AGENTS["validation"]
print(f"Agent: {agent}")

# Test agent invocation
from agents import get_mock_response
response = get_mock_response("validation", {})
print(f"Mock response: {response}")
```

---

## Performance Optimization

### Profiling

```bash
# Profile with cProfile
python -m cProfile -s cumulative -m uvicorn main:app

# Profile with py-spy
pip install py-spy
py-spy record -o profile.svg -- python -m uvicorn main:app

# Profile with line_profiler
pip install line_profiler
kernprof -l -v main.py
```

### Optimization Tips

**LLM Calls:**
```python
# Use smaller models
OLLAMA_MODEL=phi3:mini  # Faster than qwen3:0.6b

# Reduce max_tokens
response = await llm.call(system, user, max_tokens=100)

# Cache responses
memory.working.set(f"llm_cache:{key}", response, ttl=3600)
```

**Memory Operations:**
```python
# Limit context memory
memory.context = ContextMemory(limit=5)  # Reduce from 10

# Archive old orders
old_orders = memory.episodic.get_recent_orders(limit=1000)
for order in old_orders:
    # Archive to external storage
    pass

# Use Redis TTL
memory.working.set("temp", value, ttl=60)  # Auto-expire
```

**Pipeline:**
```python
# Parallelize independent operations
import asyncio

results = await asyncio.gather(
    invoke_agent("validation", context, llm),
    invoke_agent("fulfilment", context, llm),
    invoke_agent("pricing", context, llm),
)

# Cache tool results
cache_key = f"tool:{tool_name}:{args}"
if cache_key in memory.working.get(cache_key):
    return memory.working.get(cache_key)
```

### Benchmarking

```python
import time

# Simple benchmark
start = time.perf_counter()
result = await llm.call(system, user)
elapsed = time.perf_counter() - start
print(f"LLM call: {elapsed:.2f}s")

# Benchmark with statistics
import statistics

times = []
for _ in range(10):
    start = time.perf_counter()
    await llm.call(system, user)
    times.append(time.perf_counter() - start)

print(f"Mean: {statistics.mean(times):.2f}s")
print(f"Median: {statistics.median(times):.2f}s")
print(f"Stdev: {statistics.stdev(times):.2f}s")
```

---

## Deployment

### Local Development

```bash
# Start with hot reload
python -m uvicorn main:app --reload --port 8007

# With debug logging
LOGLEVEL=DEBUG python -m uvicorn main:app --reload
```

### Docker Development

```bash
# Build image
docker build -t ecommerce-demo:dev .

# Run container
docker run -p 8007:8007 \
  -e OLLAMA_HOST=http://host.docker.internal:11434 \
  -e DATA_DIR=/data \
  -v ecommerce_data:/data \
  ecommerce-demo:dev

# Run with docker-compose
docker compose up --build
```

### Production Deployment

```bash
# Build production image
docker build -t ecommerce-demo:latest .

# Push to registry
docker tag ecommerce-demo:latest myregistry/ecommerce-demo:latest
docker push myregistry/ecommerce-demo:latest

# Deploy with docker-compose
docker compose -f docker-compose.yml up -d

# Monitor
docker compose logs -f
docker compose ps
```

### Health Checks

```bash
# Check application health
curl http://localhost:8007/api/status

# Check LLM status
curl http://localhost:8007/api/llm/status

# Check Redis
docker compose exec redis redis-cli ping

# Check Prometheus
curl http://localhost:9090/-/healthy

# Check Grafana
curl http://localhost:3000/api/health
```

---

## Best Practices

### Code Style

```python
# Use type hints
def get_customer(customer_id: str) -> dict:
    pass

# Use docstrings
def my_function(param: str) -> str:
    """
    Brief description.
    
    Args:
        param: Parameter description
    
    Returns:
        Return value description
    
    Raises:
        ValueError: When something is wrong
    """
    pass

# Use meaningful names
customer_data = get_customer("C001")  # Good
cd = get_customer("C001")  # Bad

# Keep functions small
def process_order(order):
    validate_order(order)
    calculate_total(order)
    save_order(order)
```

### Error Handling

```python
# Use specific exceptions
try:
    customer = get_customer(customer_id)
except KeyError:
    logger.error(f"Customer not found: {customer_id}")
    raise ValueError(f"Invalid customer: {customer_id}")

# Use context managers
with database.transaction():
    update_order(order)
    send_notification(customer)

# Log errors
try:
    result = await llm.call(system, user)
except Exception as e:
    logger.error(f"LLM call failed: {e}", exc_info=True)
    raise
```

### Documentation

```python
# Document modules
"""
Order processing pipeline module.

This module orchestrates the 5-stage order processing pipeline:
- S1: Initialization
- S2: Validation
- S3: Fulfilment
- S4: Pricing
- S5: Dispatch
"""

# Document classes
class MemoryManager:
    """
    Unified memory management system.
    
    Coordinates 4 memory tiers:
    - Context: In-process (Python list)
    - Episodic: Persistent (SQLite)
    - Semantic: Embeddings (ChromaDB)
    - Working: Distributed (Redis)
    """

# Document functions
async def run_pipeline(
    order_id: str,
    customer: dict,
    cart: list[dict],
    llm: LLMBackend,
    memory: MemoryManager,
) -> AsyncGenerator[str, None]:
    """
    Run order processing pipeline.
    
    Args:
        order_id: Unique order identifier
        customer: Customer data dictionary
        cart: List of cart items with sku and qty
        llm: LLM backend instance
        memory: Memory manager instance
    
    Yields:
        SSE event strings
    
    Raises:
        ValueError: If order data is invalid
    """
```

### Testing

```python
# Write tests for all new code
def test_my_feature():
    pass

# Test edge cases
def test_my_feature_with_empty_input():
    pass

def test_my_feature_with_invalid_input():
    pass

# Use fixtures
@pytest.fixture
def customer_data():
    return {"id": "C001", "name": "Test"}

def test_with_fixture(customer_data):
    pass
```

### Version Control

```bash
# Use meaningful commit messages
git commit -m "Add express shipping tool"  # Good
git commit -m "fix"  # Bad

# Keep commits focused
git add tools/shipping.py
git commit -m "Add express shipping tool"

# Use branches for features
git checkout -b feature/express-shipping
# ... make changes ...
git push origin feature/express-shipping
# Create PR

# Keep history clean
git rebase -i HEAD~3  # Interactive rebase
```

---

## Troubleshooting

### Common Issues

**Issue: Import errors**
```bash
# Reinstall dependencies
pip install -r requirements.txt

# Check Python path
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Verify imports
python -c "from llm import LLMFactory; print('OK')"
```

**Issue: Database errors**
```bash
# Check SQLite database
sqlite3 /data/sqlite/ecommerce.db ".tables"

# Reset database
rm -rf /data/sqlite/ecommerce.db
docker compose restart ecommerce-demo
```

**Issue: Redis connection**
```bash
# Check Redis
redis-cli ping

# Restart Redis
docker compose restart redis

# Check connection
redis-cli -u redis://localhost:6379
```

**Issue: Slow performance**
```bash
# Profile application
python -m cProfile -s cumulative main.py

# Check memory usage
docker stats

# Check CPU usage
docker top agent-ecommerce-demo

# Optimize
# - Use smaller LLM model
# - Reduce max_tokens
# - Cache responses
# - Parallelize operations
```

**Issue: Tests failing**
```bash
# Run with verbose output
pytest tests/ -vv

# Run with print statements
pytest tests/ -s

# Run specific test
pytest tests/test_tools.py::test_get_customer -vv

# Check test dependencies
pip install -r requirements.txt
```

---

## Resources

### Documentation
- [README.md](README.md) — Getting started
- [CODEBASE_ANALYSIS.md](CODEBASE_ANALYSIS.md) — Technical reference
- [ARCHITECTURE_DIAGRAMS.md](ARCHITECTURE_DIAGRAMS.md) — Visual diagrams
- [QUICK_REFERENCE.md](QUICK_REFERENCE.md) — Quick lookup

### External Resources
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Python Async/Await](https://docs.python.org/3/library/asyncio.html)
- [pytest Documentation](https://docs.pytest.org/)
- [Docker Documentation](https://docs.docker.com/)
- [Prometheus Documentation](https://prometheus.io/docs/)

### Tools
- [VS Code](https://code.visualstudio.com/)
- [PyCharm](https://www.jetbrains.com/pycharm/)
- [Docker Desktop](https://www.docker.com/products/docker-desktop)
- [Postman](https://www.postman.com/) — API testing

---

## Support

### Getting Help

1. **Check documentation** — See resources above
2. **Review test files** — Examples in `tests/` directory
3. **Check logs** — `docker compose logs ecommerce-demo`
4. **Review code** — Well-commented source code
5. **Ask team** — Slack, email, or team meeting

### Reporting Issues

1. Describe the problem
2. Provide reproducible steps
3. Include error messages
4. Share environment details
5. Suggest solution if possible

---

## Checklist for New Developers

- [ ] Clone repository
- [ ] Set up virtual environment
- [ ] Install dependencies
- [ ] Create .env file
- [ ] Run `docker compose up --build`
- [ ] Visit http://localhost:8007
- [ ] Read README.md
- [ ] Read CODEBASE_ANALYSIS.md
- [ ] Run tests: `pytest tests/ -v`
- [ ] Review project structure
- [ ] Understand core concepts
- [ ] Try adding a simple feature
- [ ] Write a test
- [ ] Commit changes

---

**Last Updated**: May 27, 2026  
**Version**: 1.0.0  
**Status**: ✅ Production-Ready

