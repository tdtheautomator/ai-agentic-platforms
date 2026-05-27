# E-Commerce Demo — Quick Reference Guide

**Fast lookup for common tasks and information**

---

## File Locations

| Component | File | Lines | Purpose |
|-----------|------|-------|---------|
| **Main App** | `main.py` | ~200 | FastAPI application |
| **Pipeline** | `harness/pipeline.py` | ~650 | Order processing |
| **LLM Factory** | `llm/factory.py` | ~60 | Backend selection |
| **Memory Manager** | `memory/manager.py` | ~30 | Memory coordination |
| **Agent Defs** | `agents/definitions.py` | ~50 | Agent specs |
| **Tool Registry** | `tools/registry.py` | ~25 | Tool registration |
| **Data Models** | `data/models.py` | ~190 | Data structures |

---

## Module Overview

### `llm/` — LLM Backend Abstraction
```
Purpose: Abstract LLM provider with fallback chain
Pattern: Factory + Strategy
Files:   6 (backend, factory, openai, anthropic, ollama, mock)
Key:     LLMFactory.create() → auto-detect backend
```

### `memory/` — 4-Tier Memory System
```
Purpose: Multi-tier memory for different use cases
Tiers:   Context (list) → Episodic (SQLite) → Semantic (ChromaDB) → Working (Redis)
Pattern: Coordinator pattern
Files:   5 (manager, context, episodic, semantic, working)
Key:     MemoryManager coordinates all tiers
```

### `agents/` — Agent Definitions
```
Purpose: A2A agent specs and mock responses
Agents:  4 (Validation, Fulfilment, Pricing, Dispatch)
Pattern: Registry pattern
Files:   2 (definitions, mock_responses)
Key:     A2A_AGENTS dict with agent specs
```

### `tools/` — SDK Tools Registry
```
Purpose: Domain-organized tools for agents
Domains: Customer, Inventory, Pricing, Fraud
Pattern: Decorator-based registration
Files:   5 (registry, customer, inventory, pricing, fraud)
Key:     @register_tool decorator
```

### `harness/` — Pipeline Orchestration
```
Purpose: 5-stage order processing pipeline
Stages:  S1 Init → S2 Validation → S3 Fulfilment → S4 Pricing → S5 Dispatch
Pattern: Pipeline orchestrator
Files:   1 (pipeline.py)
Key:     run_pipeline() async generator
```

### `data/` — Data Models
```
Purpose: Data structures and dummy data
Data:    CUSTOMERS, PRODUCTS, PROMOTIONS, WAREHOUSES, POLICIES
Pattern: Static data
Files:   1 (models.py)
Key:     5 main data sets
```

### `tests/` — Unit Tests
```
Purpose: Test coverage for core modules
Tests:   12 total (6 tools, 5 memory, 3 agents)
Pattern: pytest with async support
Files:   3 (test_tools, test_memory, test_agents)
Key:     pytest tests/ -v
```

---

## API Quick Reference

### Status
```bash
GET /api/status
→ service, llm, model, mock, chroma_ready

GET /api/llm/status
→ backend, model, mock
```

### Data
```bash
GET /api/customers
→ list of customers

GET /api/products
→ list of products

GET /api/orders
→ recent orders

GET /api/events/{order_id}
→ events for order
```

### Registry
```bash
GET /api/tools
→ registered tools

GET /api/agents
→ agent definitions
```

### Memory
```bash
GET /api/memory/context
→ context memory

GET /api/memory/working
→ working memory (Redis)
```

### Pipeline
```bash
GET /api/run?customer=C001&cart=[...]
→ SSE stream of pipeline

GET /api/seed
→ sample orders
```

### UI
```bash
GET /
→ web interface
```

---

## Environment Variables

### LLM Configuration
```bash
OPENAI_API_KEY=sk-...              # OpenAI (priority 1)
ANTHROPIC_API_KEY=sk-ant-...       # Anthropic (priority 2)
OLLAMA_HOST=http://...             # Ollama (priority 3)
OLLAMA_MODEL=qwen3:0.6b            # Ollama model
ECOMMERCE_OLLAMA_MODEL=            # Override
```

### Data Storage
```bash
DATA_DIR=/data                      # Base directory
REDIS_URL=redis://redis:6379       # Redis connection
```

### Observability
```bash
SLACK_WEBHOOK_URL=                  # Slack alerts
GRAFANA_USER=admin                  # Grafana login
GRAFANA_PASSWORD=admin              # Grafana password
```

---

## Docker Compose Services

| Service | Port | Image | Purpose |
|---------|------|-------|---------|
| **ecommerce-demo** | 8007 | Custom | Main app |
| **redis** | 6379 | redis:7.2-alpine | Working memory |
| **prometheus** | 9090 | prom/prometheus | Metrics |
| **grafana** | 3000 | grafana/grafana | Dashboards |
| **alertmanager** | 9093 | Custom | Alerts |

---

## Common Commands

### Docker
```bash
# Start all services
docker compose up --build

# Stop services
docker compose down

# View logs
docker compose logs -f ecommerce-demo

# Rebuild specific service
docker compose up --build ecommerce-demo
```

### Testing
```bash
# All tests
pytest tests/ -v

# Specific file
pytest tests/test_tools.py -v

# Specific test
pytest tests/test_tools.py::test_get_customer -v

# With coverage
pytest tests/ --cov=. --cov-report=html
```

### Local Development
```bash
# Install dependencies
pip install -r requirements.txt

# Run locally (requires Redis)
python -m uvicorn main:app --reload --port 8007

# Run with Ollama
OLLAMA_HOST=http://localhost:11434 python -m uvicorn main:app --port 8007
```

---

## Data Structures

### Customer
```python
{
    "id": "C001",
    "name": "Lena Fischer",
    "email": "lena@example.com",
    "tier": "gold",  # gold, silver, bronze
    "address": "12 Maple Street, London, SW1A 1AA",
    "orders_ytd": 14,
    "loyalty_pts": 2840,
    "flagged": False
}
```

### Product
```python
{
    "sku": "SKU-001",
    "name": "Wireless Noise-Cancelling Headphones",
    "category": "Electronics",
    "price": 149.99,
    "stock": 23,
    "weight_kg": 0.35,
    "warehouse": "LDN-EAST"
}
```

### Order
```python
{
    "id": "ORD-20260527-001",
    "customer_id": "C001",
    "customer_name": "Lena Fischer",
    "items": "[{\"sku\": \"SKU-001\", \"qty\": 2}]",
    "subtotal": 299.98,
    "discount": 60.00,
    "shipping": 9.99,
    "total": 249.97,
    "status": "confirmed",
    "warehouse": "LDN-EAST"
}
```

### Agent Spec
```python
{
    "name": "Validation Agent",
    "description": "Verifies order details...",
    "skills": ["order_validation", "fraud_pre_check", ...],
    "system_prompt": "You are an e-commerce order validation specialist..."
}
```

---

## Tool Functions

### Customer Tools
```python
get_customer(customer_id: str) → dict
validate_address(address: str) → dict
get_customer_tier(customer_id: str) → str
```

### Inventory Tools
```python
check_inventory(sku: str) → dict
get_stock_level(sku: str) → int
warehouse_select(items: list) → str
```

### Pricing Tools
```python
apply_promotions(customer_id: str, amount: float, category: str) → dict
calculate_shipping(weight_kg: float, distance_km: float) → float
loyalty_discount(customer_id: str, amount: float) → float
```

### Fraud Tools
```python
run_fraud_check(customer_id: str, amount: float) → dict
search_policies(query: str) → list
get_risk_score(customer_id: str) → float
```

---

## Memory Operations

### Context Memory
```python
memory.context.add(role: str, message: str)
memory.context.get_all() → list
memory.context.clear()
```

### Episodic Memory
```python
memory.episodic.upsert_order(order_data: dict)
memory.episodic.get_order(order_id: str) → dict
memory.episodic.get_recent_orders(limit: int) → list
```

### Semantic Memory
```python
memory.semantic.add(text: str, metadata: dict)
memory.semantic.query(query: str, limit: int) → list
memory.semantic.is_ready() → bool
```

### Working Memory
```python
memory.working.set(key: str, value: str, ttl: int)
memory.working.get(key: str) → str
memory.working.delete(key: str)
```

---

## Metrics

### Counters
```
ecommerce_pipeline_runs_total
ecommerce_pipeline_stage_executions_total{stage, status}
ecommerce_agent_tool_calls_total{agent, tool}
```

### Histograms
```
ecommerce_pipeline_duration_seconds
ecommerce_agent_duration_seconds{agent}
ecommerce_pipeline_stage_duration_seconds{stage}
ecommerce_agent_tool_call_duration_seconds{agent, tool}
```

---

## SSE Event Types

### harness_session
```json
{
  "kind": "harness_session",
  "ts": "14:30:45",
  "session": 1,
  "type": "INITIALIZER",
  "msg": "Harness initialised..."
}
```

### agent_call
```json
{
  "kind": "agent_call",
  "ts": "14:30:46",
  "agent": "validation",
  "msg": "Calling Validation Agent..."
}
```

### agent_response
```json
{
  "kind": "agent_response",
  "ts": "14:30:48",
  "agent": "validation",
  "response": "Order passes validation..."
}
```

### pipeline_complete
```json
{
  "kind": "pipeline_complete",
  "ts": "14:30:55",
  "status": "confirmed",
  "order_id": "ORD-20260527-001"
}
```

---

## Troubleshooting

### Issue: "Ollama not connecting"
**Solution:**
```bash
# Check Ollama is running on Windows
# Verify OLLAMA_HOST environment variable
# App falls back to mock if unavailable
```

### Issue: "Redis connection failed"
**Solution:**
```bash
# Check Redis container is healthy
docker compose ps redis

# Restart Redis
docker compose restart redis
```

### Issue: "ChromaDB initialization error"
**Solution:**
```bash
# Check /data/chroma directory permissions
# Verify disk space
# Restart app
docker compose restart ecommerce-demo
```

### Issue: "Port already in use"
**Solution:**
```bash
# Find process using port
netstat -ano | findstr :8007

# Kill process or use different port
docker compose up -p custom_project
```

---

## Performance Tips

### Optimize LLM Calls
- Use smaller models (qwen3:0.6b, phi3:mini)
- Reduce max_tokens if possible
- Cache responses in working memory

### Optimize Memory
- Limit context memory to 10 items
- Archive old orders to episodic
- Use Redis TTL for temporary data

### Optimize Pipeline
- Parallelize independent agent calls (if possible)
- Cache tool results
- Use mock LLM for testing

---

## Security Checklist

- [ ] API keys in environment variables
- [ ] No hardcoded secrets
- [ ] Redis behind firewall
- [ ] SQLite file permissions
- [ ] CORS configured appropriately
- [ ] No sensitive data in logs
- [ ] Health checks enabled
- [ ] Monitoring alerts configured

---

## Deployment Checklist

- [ ] All environment variables set
- [ ] Docker images built
- [ ] Volumes created
- [ ] Network configured
- [ ] Health checks passing
- [ ] Metrics collecting
- [ ] Dashboards visible
- [ ] Alerts configured
- [ ] Logs accessible
- [ ] Backups scheduled

---

## Learning Resources

### Quick Start (15 min)
1. Read this file
2. Review folder structure
3. Run `docker compose up --build`
4. Visit http://localhost:8007

### Deep Dive (2 hours)
1. Read CODEBASE_ANALYSIS.md
2. Review ARCHITECTURE_DIAGRAMS.md
3. Study key modules
4. Run tests

### Advanced (4+ hours)
1. Study each module
2. Review pipeline logic
3. Implement extensions
4. Optimize performance

---

## Key Takeaways

| Concept | Details |
|---------|---------|
| **Architecture** | Modular, layered, production-ready |
| **LLM** | Pluggable backends with fallback chain |
| **Memory** | 4-tier system for different use cases |
| **Agents** | 4 specialist agents via A2A protocol |
| **Pipeline** | 5-stage order processing orchestration |
| **Tools** | Domain-organized SDK tools |
| **Testing** | 12 unit tests with pytest |
| **Observability** | Prometheus + Grafana + AlertManager |
| **Deployment** | Docker Compose with 5 services |
| **Status** | Production-ready ✅ |

---

## Contact & Support

- **Issues**: Check logs in `docker compose logs`
- **Docs**: See CODEBASE_ANALYSIS.md and ARCHITECTURE_DIAGRAMS.md
- **Tests**: Run `pytest tests/ -v`
- **Feedback**: Review code and suggest improvements

---

**Last Updated**: May 27, 2026  
**Status**: Production-Ready ✅

