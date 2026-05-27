# E-Commerce Demo — Architecture Diagrams

**Visual representations of the system architecture**

---

## 1. High-Level System Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         CLIENT LAYER                               │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐ │
│  │   Web Browser    │  │   REST Client    │  │   Mobile App     │ │
│  │  (UI @ :8007)    │  │  (API @ :8007)   │  │  (API @ :8007)   │ │
│  └────────┬─────────┘  └────────┬─────────┘  └────────┬─────────┘ │
└───────────┼──────────────────────┼──────────────────────┼───────────┘
            │                      │                      │
            └──────────────────────┼──────────────────────┘
                                   │
                    ┌──────────────▼──────────────┐
                    │   FastAPI Application      │
                    │   (main.py @ :8007)        │
                    │  • REST Endpoints          │
                    │  • SSE Streaming           │
                    │  • CORS Middleware         │
                    └──────────────┬──────────────┘
                                   │
        ┌──────────────────────────┼──────────────────────────┐
        │                          │                          │
        ▼                          ▼                          ▼
    ┌────────────┐         ┌────────────┐         ┌────────────────┐
    │ LLM Layer  │         │   Memory   │         │  Pipeline      │
    │ (Factory)  │         │  (Manager) │         │  (Orchestrator)│
    └────────────┘         └────────────┘         └────────────────┘
        │                       │                          │
    ┌───┴─────────────┐     ┌───┴────────────┐        ┌───┴─────────┐
    │                 │     │                │        │             │
    ▼                 ▼     ▼                ▼        ▼             ▼
┌─────────┐ ┌──────────┐ ┌─────────┐ ┌──────────┐ ┌────────┐ ┌─────────┐
│ OpenAI  │ │Anthropic │ │ Ollama  │ │  Mock   │ │ Tools  │ │ Agents  │
│ (GPT)   │ │(Claude)  │ │(Local)  │ │ (Test)  │ │Registry│ │(4 types)│
└─────────┘ └──────────┘ └─────────┘ └──────────┘ └────────┘ └─────────┘
                                                        │
                    ┌───────────────────────────────────┼────────────┐
                    │                                   │            │
                    ▼                                   ▼            ▼
            ┌───────────────┐              ┌─────────────────┐ ┌──────────┐
            │   Data Layer  │              │  Memory System  │ │ Storage  │
            │  (Models)     │              │  (4-tier)       │ │ (Volumes)│
            └───────────────┘              └─────────────────┘ └──────────┘
                    │                              │                │
        ┌───────────┼───────────┐         ┌───────┼───────────┐    │
        │           │           │         │       │           │    │
        ▼           ▼           ▼         ▼       ▼           ▼    ▼
    ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐
    │Customers│ │Products│ │Promos  │ │Context │ │Episodic│ │Semantic│
    │         │ │        │ │        │ │(Memory)│ │(SQLite)│ │(Chroma)│
    └────────┘ └────────┘ └────────┘ └────────┘ └────────┘ └────────┘
                                                                    │
                                                                    ▼
                                                            ┌──────────────┐
                                                            │Working Memory│
                                                            │  (Redis)     │
                                                            │  @ :6379     │
                                                            └──────────────┘
```

---

## 2. Module Dependency Graph

```
                          ┌─────────────────┐
                          │   main.py       │
                          │  (FastAPI App)  │
                          └────────┬────────┘
                                   │
                ┌──────────────────┼──────────────────┐
                │                  │                  │
                ▼                  ▼                  ▼
            ┌────────┐         ┌────────┐        ┌──────────┐
            │  llm   │         │ memory │        │ harness  │
            │(Factory)         │(Manager)        │(Pipeline)
            └────────┘         └────────┘        └──────────┘
                │                  │                  │
        ┌───────┼───────┐      ┌────┴────┐      ┌────┴────┐
        │       │       │      │         │      │         │
        ▼       ▼       ▼      ▼         ▼      ▼         ▼
    ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐
    │OpenAI│ │Claude│ │Ollama│ │Context│ │Episod│ │Semant│ │agents│
    └──────┘ └──────┘ └──────┘ └──────┘ └──────┘ └──────┘ └──────┘
                                                                │
                                                                ▼
                                                            ┌──────────┐
                                                            │  tools   │
                                                            │(Registry)│
                                                            └──────────┘
                                                                │
                                                    ┌───────────┼───────────┐
                                                    │           │           │
                                                    ▼           ▼           ▼
                                                ┌────────┐ ┌────────┐ ┌────────┐
                                                │customer│ │pricing │ │ fraud  │
                                                └────────┘ └────────┘ └────────┘
                                                    │
                                                    ▼
                                                ┌──────────┐
                                                │   data   │
                                                │ (Models) │
                                                └──────────┘
```

---

## 3. Memory System Architecture

```
                    ┌──────────────────────────┐
                    │   MemoryManager          │
                    │   (Coordinator)          │
                    └────────┬─────────────────┘
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                    │
        ▼                    ▼                    ▼
    ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
    │ Context      │ │ Episodic     │ │ Semantic     │
    │ Memory       │ │ Memory       │ │ Memory       │
    │              │ │              │ │              │
    │ Storage:     │ │ Storage:     │ │ Storage:     │
    │ Python List  │ │ SQLite       │ │ ChromaDB     │
    │              │ │              │ │              │
    │ Scope:       │ │ Scope:       │ │ Scope:       │
    │ In-process   │ │ Persistent   │ │ Persistent   │
    │              │ │              │ │              │
    │ Limit: 10    │ │ Limit: None  │ │ Limit: None  │
    │ TTL: None    │ │ TTL: None    │ │ TTL: None    │
    │              │ │              │ │              │
    │ Use:         │ │ Use:         │ │ Use:         │
    │ Current      │ │ Order        │ │ Policy       │
    │ conversation │ │ history      │ │ search       │
    └──────────────┘ └──────────────┘ └──────────────┘
                             │
                             ▼
                    ┌──────────────────┐
                    │ Working Memory   │
                    │                  │
                    │ Storage: Redis   │
                    │ Port: 6379       │
                    │                  │
                    │ Scope: Distrib.  │
                    │ TTL: Configurable│
                    │                  │
                    │ Use: Temp cache  │
                    └──────────────────┘
```

---

## 4. LLM Backend Selection Flow

```
                    ┌──────────────────────┐
                    │ LLMFactory.create()  │
                    └──────────┬───────────┘
                               │
                    ┌──────────▼──────────┐
                    │ Check env vars      │
                    └──────────┬──────────┘
                               │
                ┌──────────────┼──────────────┐
                │              │              │
        ┌───────▼────────┐     │              │
        │ OPENAI_API_KEY │     │              │
        │ set?           │     │              │
        └────┬────────┬──┘     │              │
             │ YES    │ NO     │              │
             │        └────────┼──────────┐   │
             │                 │          │   │
        ┌────▼──────┐  ┌───────▼────────┐ │   │
        │ OpenAI    │  │ ANTHROPIC_     │ │   │
        │ Client    │  │ API_KEY set?   │ │   │
        │ ✓ Ready   │  └────┬────────┬──┘ │   │
        └───────────┘       │ YES    │ NO │   │
                            │        └────┼───┼──┐
                        ┌───▼──────┐     │   │  │
                        │ Anthropic│     │   │  │
                        │ Client   │     │   │  │
                        │ ✓ Ready  │     │   │  │
                        └──────────┘     │   │  │
                                         │   │  │
                                    ┌────▼───▼──┼─┐
                                    │ Probe      │ │
                                    │ Ollama     │ │
                                    │ health?    │ │
                                    └────┬───┬──┘ │
                                         │   │    │
                                    ┌────▼─┐ │    │
                                    │ YES  │ │    │
                                    │      │ │    │
                                ┌───▼────┐│ │    │
                                │ Ollama ││ │    │
                                │ Client ││ │    │
                                │✓ Ready ││ │    │
                                └────────┘│ │    │
                                          │ NO   │
                                          │      │
                                      ┌───▼──────▼──┐
                                      │ Mock LLM    │
                                      │ (Fallback)  │
                                      │ ✓ Ready     │
                                      └─────────────┘
```

---

## 5. Pipeline Execution Flow

```
                            ┌─────────────┐
                            │ Order Input │
                            │ (customer,  │
                            │  cart)      │
                            └──────┬──────┘
                                   │
                        ┌──────────▼──────────┐
                        │ S1: INITIALISER     │
                        │                     │
                        │ • Generate order ID │
                        │ • Calculate subtotal│
                        │ • Find warehouse    │
                        │ • Store in memory   │
                        └──────────┬──────────┘
                                   │
                        ┌──────────▼──────────────┐
                        │ S2: VALIDATION AGENT   │
                        │                        │
                        │ • Customer eligible?   │
                        │ • Fraud check          │
                        │ • Address valid?       │
                        │ • Stock available?     │
                        │ • Tools: get_customer()│
                        │          run_fraud()   │
                        │          check_inv()   │
                        └──────────┬─────────────┘
                                   │
                        ┌──────────▼──────────────┐
                        │ S3: FULFILMENT AGENT   │
                        │                        │
                        │ • Select warehouse     │
                        │ • Check capacity       │
                        │ • Schedule pick        │
                        │ • Tools: check_inv()   │
                        │          warehouse()   │
                        └──────────┬─────────────┘
                                   │
                        ┌──────────▼──────────────┐
                        │ S4: PRICING AGENT      │
                        │                        │
                        │ • Apply promotions     │
                        │ • Loyalty discount     │
                        │ • Calculate shipping   │
                        │ • Tools: apply_promo() │
                        │          calc_ship()   │
                        └──────────┬─────────────┘
                                   │
                        ┌──────────▼──────────────┐
                        │ S5: DISPATCH AGENT     │
                        │                        │
                        │ • Final decision       │
                        │ • Select carrier       │
                        │ • Generate tracking    │
                        │ • Tools: fraud_check() │
                        └──────────┬─────────────┘
                                   │
                        ┌──────────▼──────────────┐
                        │ COMPLETE               │
                        │                        │
                        │ • Store final order    │
                        │ • Record metrics       │
                        │ • Return status        │
                        └────────────────────────┘
```

---

## 6. Tool Registry Architecture

```
                    ┌────────────────────────┐
                    │   TOOLS Registry       │
                    │   (Global Dict)        │
                    └────────────┬───────────┘
                                 │
        ┌────────────────────────┼────────────────────────┐
        │                        │                        │
        ▼                        ▼                        ▼
    ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
    │ Customer     │     │ Inventory    │     │ Pricing      │
    │ Domain       │     │ Domain       │     │ Domain       │
    │              │     │              │     │              │
    │ • get_       │     │ • check_     │     │ • apply_     │
    │   customer() │     │   inventory()│     │   promotions()
    │              │     │              │     │              │
    │ • validate_  │     │ • get_stock()│     │ • calc_      │
    │   address()  │     │              │     │   shipping() │
    │              │     │              │     │              │
    │ • get_tier() │     │ • warehouse_ │     │ • loyalty_   │
    │              │     │   select()   │     │   discount() │
    └──────────────┘     └──────────────┘     └──────────────┘
        │                        │                        │
        └────────────────────────┼────────────────────────┘
                                 │
                    ┌────────────▼──────────┐
                    │ Fraud Domain         │
                    │                      │
                    │ • run_fraud_check()  │
                    │ • search_policies()  │
                    │ • get_risk_score()   │
                    └──────────────────────┘
```

---

## 7. Agent Communication Pattern

```
                    ┌─────────────────────┐
                    │  Pipeline           │
                    │  (Orchestrator)     │
                    └──────────┬──────────┘
                               │
                ┌──────────────┼──────────────┐
                │              │              │
                ▼              ▼              ▼
        ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
        │ Agent Call   │ │ Agent Call   │ │ Agent Call   │
        │ (JSON-RPC)   │ │ (JSON-RPC)   │ │ (JSON-RPC)   │
        │              │ │              │ │              │
        │ {            │ │ {            │ │ {            │
        │   "method":  │ │   "method":  │ │   "method":  │
        │   "invoke",  │ │   "invoke",  │ │   "invoke",  │
        │   "params":  │ │   "params":  │ │   "params":  │
        │   {...}      │ │   {...}      │ │   {...}      │
        │ }            │ │ }            │ │ }            │
        └──────┬───────┘ └──────┬───────┘ └──────┬───────┘
               │                │                │
               ▼                ▼                ▼
        ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
        │ Validation   │ │ Fulfilment   │ │ Pricing      │
        │ Agent        │ │ Agent        │ │ Agent        │
        │              │ │              │ │              │
        │ • Calls LLM  │ │ • Calls LLM  │ │ • Calls LLM  │
        │ • Uses tools │ │ • Uses tools │ │ • Uses tools │
        │ • Returns    │ │ • Returns    │ │ • Returns    │
        │   decision   │ │   warehouse  │ │   total      │
        └──────┬───────┘ └──────┬───────┘ └──────┬───────┘
               │                │                │
               └────────────────┼────────────────┘
                                │
                                ▼
                        ┌──────────────┐
                        │ Dispatch     │
                        │ Agent        │
                        │              │
                        │ • Calls LLM  │
                        │ • Uses tools │
                        │ • Final      │
                        │   decision   │
                        └──────────────┘
```

---

## 8. Data Flow: Order Processing

```
Customer Request
    │
    ├─→ Order Data
    │   • customer_id
    │   • items (SKU, qty)
    │   • address
    │
    ▼
┌─────────────────────────────────────┐
│ S1: INITIALISER                     │
│ • Generate order_id                 │
│ • Calculate subtotal                │
│ • Identify warehouse                │
└──────────────┬──────────────────────┘
               │
               ├─→ Store in Context Memory
               ├─→ Store in Episodic Memory
               │
               ▼
┌─────────────────────────────────────┐
│ S2: VALIDATION AGENT                │
│ • Query: get_customer(customer_id)  │
│ • Query: check_inventory(skus)      │
│ • Query: run_fraud_check(customer)  │
│ • LLM: Generate validation summary  │
└──────────────┬──────────────────────┘
               │
               ├─→ Validation Result
               │   • PASS / REVIEW / REJECT
               │
               ▼
┌─────────────────────────────────────┐
│ S3: FULFILMENT AGENT                │
│ • Query: check_inventory(skus)      │
│ • Query: warehouse_select(items)    │
│ • LLM: Generate fulfilment plan     │
└──────────────┬──────────────────────┘
               │
               ├─→ Fulfilment Result
               │   • warehouse_code
               │   • dispatch_time
               │
               ▼
┌─────────────────────────────────────┐
│ S4: PRICING AGENT                   │
│ • Query: apply_promotions(...)      │
│ • Query: calculate_shipping(...)    │
│ • LLM: Generate pricing summary     │
└──────────────┬──────────────────────┘
               │
               ├─→ Pricing Result
               │   • discount_amount
               │   • shipping_cost
               │   • final_total
               │
               ▼
┌─────────────────────────────────────┐
│ S5: DISPATCH AGENT                  │
│ • Query: run_fraud_check(order)     │
│ • LLM: Final decision               │
└──────────────┬──────────────────────┘
               │
               ├─→ Final Decision
               │   • CONFIRMED
               │   • HOLD FOR REVIEW
               │   • CANCELLED
               │
               ▼
┌─────────────────────────────────────┐
│ COMPLETE                            │
│ • Store final order in Episodic     │
│ • Update metrics in Prometheus      │
│ • Return status to client           │
└─────────────────────────────────────┘
```

---

## 9. Observability Stack

```
                    ┌──────────────────────┐
                    │  FastAPI App         │
                    │  (Instrumented)      │
                    └──────────┬───────────┘
                               │
                               │ Metrics
                               │ (Prometheus format)
                               │
                    ┌──────────▼───────────┐
                    │  Prometheus          │
                    │  (Scraper & TSDB)    │
                    │  Port: 9090          │
                    │                      │
                    │ Collects:            │
                    │ • Pipeline runs      │
                    │ • Stage duration     │
                    │ • Agent latency      │
                    │ • Tool calls         │
                    │ • HTTP requests      │
                    └──────────┬───────────┘
                               │
                ┌──────────────┼──────────────┐
                │              │              │
                ▼              ▼              ▼
        ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
        │ Grafana      │ │ AlertManager │ │ Dashboards   │
        │ (Visualize)  │ │ (Alert)      │ │              │
        │ Port: 3000   │ │ Port: 9093   │ │ • Pipeline   │
        │              │ │              │ │ • Agents     │
        │ • Dashboards │ │ • Rules      │ │ • Tools      │
        │ • Graphs     │ │ • Routing    │ │ • Customers  │
        │ • Tables     │ │ • Slack      │ │              │
        └──────────────┘ └──────────────┘ └──────────────┘
```

---

## 10. Docker Compose Services

```
┌─────────────────────────────────────────────────────────────┐
│                   Docker Network: ecommerce-net             │
│                                                             │
│  ┌─────────────────┐  ┌─────────────────┐  ┌────────────┐ │
│  │ ecommerce-demo  │  │ redis           │  │ prometheus │ │
│  │ :8007           │  │ :6379           │  │ :9090      │ │
│  │                 │  │                 │  │            │ │
│  │ • FastAPI       │  │ • Working Memory│  │ • Scraper  │ │
│  │ • Main app      │  │ • TTL cache     │  │ • TSDB     │ │
│  │ • Volumes:      │  │ • 128MB max     │  │ • 30d ret. │ │
│  │   - chroma      │  │ • LRU policy    │  │            │ │
│  │   - sqlite      │  │                 │  │            │ │
│  └─────────────────┘  └─────────────────┘  └────────────┘ │
│                                                             │
│  ┌─────────────────┐  ┌─────────────────┐  ┌────────────┐ │
│  │ grafana         │  │ alertmanager    │  │ (external) │ │
│  │ :3000           │  │ :9093           │  │ Slack      │ │
│  │                 │  │                 │  │            │ │
│  │ • Dashboards    │  │ • Alert routing │  │ • Webhooks │ │
│  │ • Visualize     │  │ • Rules         │  │            │ │
│  │ • Datasource:   │  │ • Slack integ.  │  │            │ │
│  │   Prometheus    │  │                 │  │            │ │
│  └─────────────────┘  └─────────────────┘  └────────────┘ │
│                                                             │
│  Volumes:                                                   │
│  • ecommerce_chroma       (ChromaDB data)                  │
│  • ecommerce_sqlite       (SQLite data)                    │
│  • ecommerce_redis        (Redis data)                     │
│  • ecommerce_prometheus   (Prometheus data)                │
│  • ecommerce_alertmanager (AlertManager data)              │
│  • ecommerce_grafana      (Grafana data)                   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 11. Request/Response Cycle

```
┌─────────────────────────────────────────────────────────────┐
│ Client Browser                                              │
│ GET /api/run?customer=C001&cart=[...]                      │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│ FastAPI Application (main.py)                               │
│ @app.get("/api/run")                                        │
│ async def api_run(customer: str, cart: str):               │
│     order_id = generate_id()                                │
│     customer_data = CUSTOMERS[customer]                     │
│     cart_items = parse_cart(cart)                           │
│     return StreamingResponse(                               │
│         run_pipeline(order_id, customer_data, cart_items),  │
│         media_type="text/event-stream"                      │
│     )                                                       │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│ Pipeline Orchestrator (harness/pipeline.py)                │
│ async def run_pipeline(order_id, customer, cart):          │
│     S1: Initialize                                          │
│     S2: Validation Agent (LLM + Tools)                     │
│     S3: Fulfilment Agent (LLM + Tools)                     │
│     S4: Pricing Agent (LLM + Tools)                        │
│     S5: Dispatch Agent (LLM + Tools)                       │
│     return final_status                                     │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│ SSE Event Stream                                            │
│ data: {"kind": "harness_session", "ts": "14:30:45", ...}  │
│ data: {"kind": "agent_call", "agent": "validation", ...}  │
│ data: {"kind": "agent_response", "result": "...", ...}    │
│ data: {"kind": "pipeline_complete", "status": "...", ...} │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│ Client Browser                                              │
│ Receives SSE events and updates UI in real-time            │
└─────────────────────────────────────────────────────────────┘
```

---

## 12. Error Handling & Fallback Chain

```
                    ┌──────────────────┐
                    │ Request          │
                    │ (Order Process)  │
                    └────────┬─────────┘
                             │
                    ┌────────▼─────────┐
                    │ Try LLM Call     │
                    └────────┬────┬────┘
                             │    │
                        ┌────▼─┐  │
                        │Error?│  │
                        └──┬───┘  │
                           │      │ No
                        Yes│      │
                           │      ▼
                           │   ┌──────────────┐
                           │   │ Process      │
                           │   │ Response     │
                           │   └──────────────┘
                           │
                    ┌──────▼──────────┐
                    │ Try Mock        │
                    │ Response        │
                    └────────┬────┬───┘
                             │    │
                        ┌────▼─┐  │
                        │Error?│  │
                        └──┬───┘  │
                           │      │ No
                        Yes│      │
                           │      ▼
                           │   ┌──────────────┐
                           │   │ Continue     │
                           │   │ Pipeline     │
                           │   └──────────────┘
                           │
                    ┌──────▼──────────┐
                    │ Log Error       │
                    │ Return Default  │
                    │ Response        │
                    └─────────────────┘
```

---

## 13. Configuration Hierarchy

```
┌─────────────────────────────────────────────────────────────┐
│ Environment Variables (.env)                                │
│                                                             │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ LLM Configuration                                       │ │
│ │ • OPENAI_API_KEY (highest priority)                    │ │
│ │ • ANTHROPIC_API_KEY                                    │ │
│ │ • OLLAMA_HOST (default: http://host.docker.internal)  │ │
│ │ • OLLAMA_MODEL (default: qwen3:0.6b)                  │ │
│ │ • ECOMMERCE_OLLAMA_MODEL (override)                   │ │
│ └─────────────────────────────────────────────────────────┘ │
│                                                             │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ Data Storage                                            │ │
│ │ • DATA_DIR (default: /data)                            │ │
│ │   ├─ /data/chroma (ChromaDB)                           │ │
│ │   └─ /data/sqlite (SQLite)                             │ │
│ └─────────────────────────────────────────────────────────┘ │
│                                                             │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ Redis                                                   │ │
│ │ • REDIS_URL (default: redis://redis:6379)             │ │
│ └─────────────────────────────────────────────────────────┘ │
│                                                             │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ Observability                                           │ │
│ │ • SLACK_WEBHOOK_URL (optional)                         │ │
│ │ • GRAFANA_USER (default: admin)                        │ │
│ │ • GRAFANA_PASSWORD (default: admin)                    │ │
│ └─────────────────────────────────────────────────────────┘ │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 14. Testing Architecture

```
┌─────────────────────────────────────────────────────────────┐
│ Test Suite (pytest)                                         │
│                                                             │
│ ┌──────────────────────────────────────────────────────┐   │
│ │ tests/test_tools.py (6 tests)                        │   │
│ │ • test_get_customer()                                │   │
│ │ • test_check_inventory()                             │   │
│ │ • test_apply_promotions()                            │   │
│ │ • test_calculate_shipping()                          │   │
│ │ • test_run_fraud_check()                             │   │
│ │ • test_search_policies()                             │   │
│ └──────────────────────────────────────────────────────┘   │
│                                                             │
│ ┌──────────────────────────────────────────────────────┐   │
│ │ tests/test_memory.py (5 tests)                       │   │
│ │ • test_context_memory()                              │   │
│ │ • test_episodic_memory()                             │   │
│ │ • test_semantic_memory()                             │   │
│ │ • test_working_memory()                              │   │
│ │ • test_memory_manager()                              │   │
│ └──────────────────────────────────────────────────────┘   │
│                                                             │
│ ┌──────────────────────────────────────────────────────┐   │
│ │ tests/test_agents.py (3 tests)                       │   │
│ │ • test_agent_definitions()                           │   │
│ │ • test_mock_responses()                              │   │
│ │ • test_agent_invocation()                            │   │
│ └──────────────────────────────────────────────────────┘   │
│                                                             │
│ Total: 12 tests                                             │
│ Coverage: Core modules + tools + memory + agents            │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 15. Deployment Topology

```
┌─────────────────────────────────────────────────────────────┐
│ Development Environment                                     │
│                                                             │
│ ┌─────────────────────────────────────────────────────┐   │
│ │ Local Machine (Windows)                             │   │
│ │                                                     │   │
│ │ ┌──────────────────────────────────────────────┐   │   │
│ │ │ Docker Desktop                               │   │   │
│ │ │                                              │   │   │
│ │ │ ┌────────────────────────────────────────┐  │   │   │
│ │ │ │ Docker Network: ecommerce-net          │  │   │   │
│ │ │ │                                        │  │   │   │
│ │ │ │ • ecommerce-demo (:8007)              │  │   │   │
│ │ │ │ • redis (:6379)                       │  │   │   │
│ │ │ │ • prometheus (:9090)                  │  │   │   │
│ │ │ │ • grafana (:3000)                     │  │   │   │
│ │ │ │ • alertmanager (:9093)                │  │   │   │
│ │ │ │                                        │  │   │   │
│ │ │ │ Volumes:                              │  │   │   │
│ │ │ │ • ecommerce_chroma                    │  │   │   │
│ │ │ │ • ecommerce_sqlite                    │  │   │   │
│ │ │ │ • ecommerce_redis                     │  │   │   │
│ │ │ │ • ecommerce_prometheus                │  │   │   │
│ │ │ │ • ecommerce_alertmanager              │  │   │   │
│ │ │ │ • ecommerce_grafana                   │  │   │   │
│ │ │ └────────────────────────────────────────┘  │   │   │
│ │ │                                              │   │   │
│ │ │ External Services:                           │   │   │
│ │ │ • Ollama (:11434) - on Windows host         │   │   │
│ │ │ • OpenAI API (if configured)                │   │   │
│ │ │ • Anthropic API (if configured)             │   │   │
│ │ └──────────────────────────────────────────────┘   │   │
│ │                                                     │   │
│ └─────────────────────────────────────────────────────┘   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Summary

These diagrams provide a comprehensive visual representation of:

1. **System Architecture** - Overall component layout
2. **Module Dependencies** - How modules relate
3. **Memory System** - 4-tier memory architecture
4. **LLM Selection** - Backend fallback chain
5. **Pipeline Flow** - 5-stage order processing
6. **Tool Registry** - Tool organization
7. **Agent Communication** - A2A protocol
8. **Data Flow** - Order processing data journey
9. **Observability** - Monitoring stack
10. **Docker Services** - Container orchestration
11. **Request/Response** - HTTP/SSE cycle
12. **Error Handling** - Fallback mechanisms
13. **Configuration** - Environment hierarchy
14. **Testing** - Test suite organization
15. **Deployment** - Development topology

All diagrams use ASCII art for easy viewing in any text editor or terminal.

