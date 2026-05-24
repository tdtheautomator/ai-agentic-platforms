"""
Combined Banking Demo — Agent Platform in Action
=================================================
Scenario: End-to-end retail banking loan application pipeline.

Shows all four AI agent concepts working together:

  SDK Layer    — Tool registration (@tool pattern), agent definitions,
                  structured tool dispatch (credit check, fraud scan, etc.)

  Harness      — Multi-session workflow (Day 1: intake → Day 2: review →
                  Day 3: decision), progress tracking, context compaction

  A2A Protocol — Four specialist agents collaborate via JSON-RPC 2.0:
                  IntakeAgent → RiskAgent → FraudAgent → DecisionAgent

  Memory       — In-context (active session), Episodic (audit log / SQLite),
                  Semantic (banking rules / ChromaDB), Working (Redis cache)

Port: 8005
"""

from __future__ import annotations

import asyncio
import json
import os
import random
import sqlite3
import time
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import AsyncGenerator

import httpx
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, StreamingResponse
from prometheus_fastapi_instrumentator import Instrumentator
from prometheus_client import Counter, Histogram, Gauge

from log_config import configure_logging, get_logger
from slack_notifier import post_application_outcome, post_pipeline_error
from health_monitor import health_monitor, start_health_monitor_loop
from tools import (
    TOOLS,
    get_customer_profile,
    verify_kyc_documents,
    check_credit_score,
    calculate_affordability,
    scan_transaction_history,
    query_banking_rules,
)

# ── App ───────────────────────────────────────────────────────────────────────
app = FastAPI(title="Banking Agent Demo")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
Instrumentator().instrument(app).expose(app)

# ── Prometheus Metrics ─────────────────────────────────────────────────────────
# Pipeline Metrics
PIPELINE_RUNS           = Counter("banking_pipeline_runs_total", "Total loan pipeline runs")
PIPELINE_DECISIONS      = Counter("banking_decisions_total", "Total decisions by outcome", ["outcome"])
AGENT_LATENCY           = Histogram("banking_agent_duration_seconds", "Per-agent duration", ["agent"])
PIPELINE_DURATION       = Histogram("banking_pipeline_duration_seconds", "End-to-end pipeline duration")

# Application Metrics
APPLICATIONS_TOTAL      = Counter("banking_applications_total", "Total applications processed")
APPLICATIONS_APPROVED   = Counter("banking_applications_approved_total", "Approved applications")
APPLICATIONS_DECLINED   = Counter("banking_applications_declined_total", "Declined applications")
APPLICATIONS_CONDITIONAL= Counter("banking_applications_conditional_total", "Conditional applications")

# Risk & Fraud Metrics
RISK_ALERTS             = Counter("banking_risk_alerts_total", "Risk assessment alerts", ["risk_level"])
FRAUD_DETECTIONS        = Counter("banking_fraud_detections_total", "Fraud detections by type", ["fraud_type"])

# Memory Metrics
MEMORY_ITEMS            = Gauge("banking_memory_items_total", "Total items in memory store", ["memory_type"])
MEMORY_OPERATIONS       = Counter("banking_memory_operations_total", "Memory operations", ["memory_type", "operation"])

# Agent Metrics
AGENT_CALLS             = Counter("banking_agent_calls_total", "Total agent calls", ["agent"])
AGENT_ERRORS            = Counter("banking_agent_errors_total", "Agent errors", ["agent", "error_type"])

# LLM Metrics
LLM_REQUESTS            = Counter("banking_llm_requests_total", "LLM API requests", ["backend", "status"])
LLM_TOKENS_USED         = Counter("banking_llm_tokens_used_total", "LLM tokens used", ["backend"])
LLM_LATENCY             = Histogram("banking_llm_latency_seconds", "LLM request latency", ["backend"])

# Tool Metrics
TOOL_CALLS              = Counter("banking_tool_calls_total", "Tool execution calls", ["tool_name"])
TOOL_LATENCY            = Histogram("banking_tool_duration_seconds", "Tool execution duration", ["tool_name"])
TOOL_ERRORS             = Counter("banking_tool_errors_total", "Tool execution errors", ["tool_name", "error_type"])

# Transaction Tracing
TRANSACTION_TRACES      = {}  # app_id → trace data for end-to-end visibility

# ── LLM Backend ───────────────────────────────────────────────────────────────
_SERVICE_NAME = "Banking Demo"
OPENAI_KEY    = os.getenv("OPENAI_API_KEY",   "").strip()
ANTHROPIC_KEY = os.getenv("ANTHROPIC_API_KEY","").strip()
OLLAMA_HOST   = os.getenv("OLLAMA_HOST", "http://host.docker.internal:11434")
OLLAMA_MODEL  = (os.getenv("COMBINED_OLLAMA_MODEL") or os.getenv("OLLAMA_MODEL") or "qwen3:0.6b").strip()

_llm_backend = "mock"
_llm_model   = "mock"

async def _probe_ollama() -> bool:
    try:
        async with httpx.AsyncClient(timeout=4) as c:
            r = await c.get(f"{OLLAMA_HOST}/api/tags")
            return r.status_code == 200
    except Exception:
        return False

async def _resolve_backend() -> None:
    global _llm_backend, _llm_model
    if OPENAI_KEY:
        _llm_backend, _llm_model = "openai", "gpt-4o-mini"
    elif ANTHROPIC_KEY:
        _llm_backend, _llm_model = "anthropic", "claude-haiku-4-5-20251001"
    elif await _probe_ollama():
        _llm_backend, _llm_model = "ollama", OLLAMA_MODEL
    else:
        _llm_backend, _llm_model = "mock", "mock"
    print(f"[{_SERVICE_NAME}] LLM: {_llm_backend}/{_llm_model}")

async def _call_llm(system: str, user: str, max_tokens: int = 400) -> str:
    try:
        if _llm_backend == "openai":
            async with httpx.AsyncClient(timeout=60) as c:
                r = await c.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers={"Authorization": f"Bearer {OPENAI_KEY}", "Content-Type": "application/json"},
                    json={"model": _llm_model, "max_tokens": max_tokens,
                          "messages": [{"role":"system","content":system},{"role":"user","content":user}]},
                )
                return r.json()["choices"][0]["message"]["content"].strip()
        if _llm_backend == "anthropic":
            async with httpx.AsyncClient(timeout=60) as c:
                r = await c.post(
                    "https://api.anthropic.com/v1/messages",
                    headers={"x-api-key": ANTHROPIC_KEY, "anthropic-version": "2023-06-01",
                             "Content-Type": "application/json"},
                    json={"model": _llm_model, "max_tokens": max_tokens, "system": system,
                          "messages": [{"role":"user","content":user}]},
                )
                return r.json()["content"][0]["text"].strip()
        if _llm_backend == "ollama":
            async with httpx.AsyncClient(timeout=120) as c:
                r = await c.post(
                    f"{OLLAMA_HOST}/api/chat",
                    json={"model": _llm_model, "stream": False,
                          "messages": [{"role":"system","content":system},{"role":"user","content":user}]},
                )
                return r.json()["message"]["content"].strip()
    except Exception as exc:
        print(f"[{_SERVICE_NAME}] _call_llm ({_llm_backend}): {exc}")
    return ""

# ── Memory — Paths ────────────────────────────────────────────────────────────
DATA_DIR    = Path(os.getenv("DATA_DIR", "/data"))
CHROMA_DIR  = DATA_DIR / "chroma"
SQLITE_PATH = DATA_DIR / "sqlite" / "banking.db"
SQLITE_PATH.parent.mkdir(parents=True, exist_ok=True)
CHROMA_DIR.mkdir(parents=True, exist_ok=True)

# ── Memory 1: In-Context ──────────────────────────────────────────────────────
_context: list[dict] = []
CTX_LIMIT = 10

def ctx_add(role: str, content: str) -> dict:
    entry = {"role": role, "content": content,
             "ts": datetime.utcnow().strftime("%H:%M:%S")}
    _context.append(entry)
    if len(_context) > CTX_LIMIT:
        # Compaction: keep system messages + last 4 turns
        summary = f"[COMPACTED] Prior context: {len(_context)-4} turns about loan application processing."
        kept = [m for m in _context if m["role"] == "system"][:1]
        kept.append({"role": "system", "content": summary, "ts": datetime.utcnow().strftime("%H:%M:%S")})
        kept.extend(_context[-4:])
        _context.clear()
        _context.extend(kept)
    return entry

def ctx_clear():
    _context.clear()

# ── Memory 2: Episodic (SQLite) ───────────────────────────────────────────────
def _db():
    c = sqlite3.connect(str(SQLITE_PATH))
    c.row_factory = sqlite3.Row
    return c

def _init_db():
    with _db() as c:
        c.execute("""CREATE TABLE IF NOT EXISTS loan_events (
            id TEXT PRIMARY KEY, application_id TEXT, session_num INTEGER,
            agent TEXT, event TEXT, detail TEXT, outcome TEXT, ts TEXT
        )""")
        c.execute("""CREATE TABLE IF NOT EXISTS loan_applications (
            id TEXT PRIMARY KEY, customer_id TEXT, customer_name TEXT,
            amount REAL, purpose TEXT, status TEXT, credit_score INTEGER,
            annual_income REAL, created_at TEXT, updated_at TEXT
        )""")
        c.commit()

_init_db()

def epi_log(app_id: str, session: int, agent: str, event: str, detail: str, outcome: str = ""):
    with _db() as c:
        c.execute(
            "INSERT INTO loan_events VALUES (?,?,?,?,?,?,?,?)",
            (str(uuid.uuid4())[:8], app_id, session, agent, event, detail, outcome,
             datetime.utcnow().isoformat(timespec="seconds"))
        )
        c.commit()

def epi_list(app_id: str) -> list[dict]:
    with _db() as c:
        rows = c.execute(
            "SELECT * FROM loan_events WHERE application_id=? ORDER BY ts", (app_id,)
        ).fetchall()
    return [dict(r) for r in rows]

def app_upsert(app: dict):
    with _db() as c:
        c.execute("""INSERT OR REPLACE INTO loan_applications
            VALUES (:id,:customer_id,:customer_name,:amount,:purpose,:status,
                    :credit_score,:annual_income,:created_at,:updated_at)""", app)
        c.commit()

def app_list(limit: int = 10) -> list[dict]:
    with _db() as c:
        rows = c.execute(
            "SELECT * FROM loan_applications ORDER BY created_at DESC LIMIT ?", (limit,)
        ).fetchall()
    return [dict(r) for r in rows]

# ── Memory 3: Semantic (ChromaDB) ─────────────────────────────────────────────
_chroma_client = _chroma_col = _embedder = None
_chroma_ready  = False

def _init_chroma():
    global _chroma_client, _chroma_col, _embedder, _chroma_ready
    try:
        import chromadb
        from sentence_transformers import SentenceTransformer
        _chroma_client = chromadb.PersistentClient(path=str(CHROMA_DIR))
        _chroma_col    = _chroma_client.get_or_create_collection(
            "banking_knowledge", metadata={"hnsw:space": "cosine"})
        _embedder = SentenceTransformer("all-MiniLM-L6-v2")
        _chroma_ready = True
        print("[Banking] ChromaDB ready")
    except Exception as e:
        print(f"[Banking] ChromaDB init failed: {e}")

def sem_add(text: str, meta: dict | None = None):
    if not _chroma_ready: return
    emb = _embedder.encode([text]).tolist()
    _chroma_col.add(ids=[str(uuid.uuid4())], embeddings=emb,
                    documents=[text], metadatas=[meta or {}])

def sem_query(query: str, top_k: int = 2) -> list[str]:
    if not _chroma_ready or _chroma_col.count() == 0:
        return []
    emb = _embedder.encode([query]).tolist()
    res = _chroma_col.query(query_embeddings=emb,
                            n_results=min(top_k, _chroma_col.count()))
    return res["documents"][0]

# ── Memory 4: Working (Redis / in-process fallback) ───────────────────────────
_redis = None
_store: dict = {}   # in-process fallback

def _init_redis():
    global _redis
    try:
        import redis as rlib
        r = rlib.from_url(os.getenv("REDIS_URL","redis://redis:6379"),
                          socket_connect_timeout=2, socket_timeout=2)
        r.ping()
        _redis = r
        print("[Banking] Redis connected")
    except Exception as e:
        print(f"[Banking] Redis offline, using in-process store: {e}")

def work_set(key: str, value: str, ttl: int = 120):
    if _redis:
        _redis.setex(f"bank:{key}", ttl, value)
    else:
        _store[f"bank:{key}"] = {"v": value, "exp": time.time() + ttl}

def work_get(key: str) -> str | None:
    if _redis:
        v = _redis.get(f"bank:{key}")
        return v.decode() if v else None
    entry = _store.get(f"bank:{key}")
    if entry and time.time() < entry["exp"]:
        return entry["v"]
    _store.pop(f"bank:{key}", None)
    return None

def work_list() -> list[dict]:
    if _redis:
        keys = _redis.keys("bank:*")
        out = []
        for k in keys[:20]:
            v = _redis.get(k)
            if v:
                out.append({"key": k.decode(), "value": v.decode()[:80],
                             "ttl": _redis.ttl(k)})
        return out
    now = time.time()
    return [{"key": k, "value": v["v"][:80], "ttl": int(v["exp"]-now)}
            for k, v in _store.items() if now < v["exp"]]

# ── Banking Dummy Data ────────────────────────────────────────────────────────
CUSTOMERS = [
    {"id":"CUST001","name":"Sarah Mitchell","credit_score":742,"income":85000,
    "account":"ACC-4821","balance":12400,"tx_count":145,"risk":"LOW"},
    {"id":"CUST002","name":"James Okafor","credit_score":618,"income":52000,
    "account":"ACC-3309","balance":3200,"tx_count":89,"risk":"MEDIUM"},
    {"id":"CUST003","name":"Priya Sharma","credit_score":801,"income":120000,
    "account":"ACC-7745","balance":45000,"tx_count":312,"risk":"LOW"},
    {"id":"CUST004","name":"David Chen","credit_score":559,"income":38000,
    "account":"ACC-2201","balance":890,"tx_count":67,"risk":"HIGH"},
    {"id":"CUST005","name":"Emma Williams","credit_score":689,"income":71000,
    "account":"ACC-5563","balance":8700,"tx_count":201,"risk":"MEDIUM"},
]

LOAN_PURPOSES = [
    "Home renovation — kitchen and bathroom upgrade",
    "Debt consolidation — merge 3 credit cards",
    "Vehicle purchase — new electric car",
    "Education — part-time MBA programme",
    "Business expansion — sole trader equipment",
    "Medical expenses — elective surgery",
    "Wedding and honeymoon",
    "Emergency fund top-up",
]

BANKING_RULES = [
    "Debt-to-income ratio must not exceed 43% for conventional loans.",
    "Credit scores below 580 require collateral or a co-signer for loans over £5,000.",
    "Fraud flag: three or more declined transactions in the past 30 days triggers a manual review.",
    "Loans above £25,000 require two forms of income verification and a credit bureau check.",
    "KYC requirements: government-issued photo ID and proof of address dated within 90 days.",
    "Anti-money laundering: cash deposits over £10,000 must be reported to the financial regulator.",
    "Variable-rate loans must include a stress-test at +3% above current rate.",
    "Self-employed applicants must provide 2 years of tax returns.",
    "Minimum loan term is 6 months; maximum is 7 years for personal loans.",
    "Early repayment charges apply within the first 12 months unless waived by the product.",
    "Credit score improvement: reducing utilisation below 30% can raise score by 20-40 points.",
    "Affordability calculation: net monthly income minus fixed outgoings must cover 120% of repayment.",
]

FRAUD_SIGNALS = [
    "Multiple login attempts from different countries within 24 hours.",
    "Loan application submitted within 48 hours of account opening.",
    "Requested amount is more than 10x the average monthly credit.",
    "Address mismatch between application and account records.",
    "Device fingerprint matches a previously flagged fraudulent application.",
]

# ── A2A Agent Definitions ─────────────────────────────────────────────────────
A2A_AGENTS = {
    "intake": {
        "name": "Intake Agent",
        "description": "Collects and validates the initial loan application. Performs KYC and affordability pre-check.",
        "skills": ["loan_intake", "kyc_verification", "affordability_precheck"],
        "system_prompt": (
            "You are a banking intake specialist. You review loan applications concisely. "
            "Given a customer profile, KYC status, and affordability figures, write a 2-sentence "
            "intake summary noting: (1) whether the application is complete and (2) one key concern or positive. "
            "Be professional and factual. Do not make a final decision."
        ),
    },
    "risk": {
        "name": "Risk Assessment Agent",
        "description": "Evaluates credit risk using bureau data, income verification, and debt-to-income ratio.",
        "skills": ["credit_risk", "dti_analysis", "income_verification"],
        "system_prompt": (
            "You are a credit risk analyst at a retail bank. "
            "Given a credit score, DTI ratio, income, and loan amount, write a 2-sentence risk assessment. "
            "State the risk level (LOW/MEDIUM/HIGH) and the single most important factor. "
            "Be concise and data-driven."
        ),
    },
    "fraud": {
        "name": "Fraud Detection Agent",
        "description": "Screens transaction history, device signals, and behavioural patterns for fraud indicators.",
        "skills": ["fraud_screening", "transaction_analysis", "aml_check"],
        "system_prompt": (
            "You are a fraud analyst at a retail bank. "
            "Given transaction data and fraud flags, write a 2-sentence fraud assessment. "
            "State whether the application should proceed, be flagged for review, or be blocked. "
            "Reference specific signals. Be direct."
        ),
    },
    "decision": {
        "name": "Decision Agent",
        "description": "Makes the final credit decision — approve, conditional approval, or decline — with rationale.",
        "skills": ["credit_decision", "offer_generation", "decline_reasoning"],
        "system_prompt": (
            "You are a senior lending manager at a retail bank. "
            "Given intake, risk, and fraud assessments, make a final 2-sentence loan decision. "
            "State clearly: APPROVED, CONDITIONALLY APPROVED, or DECLINED, with the primary reason. "
            "Be definitive and professional."
        ),
    },
}

# ── Mock responses (when LLM is unavailable) ─────────────────────────────────
def _mock_response(agent_id: str, ctx: dict) -> str:
    name  = ctx.get("customer_name", "the applicant")
    score = ctx.get("credit_score", 0)
    dti   = ctx.get("dti_ratio", 0)
    risk  = ctx.get("risk", "MEDIUM")
    fraud = ctx.get("fraud_flags", False)
    amt   = ctx.get("amount", 0)

    if agent_id == "intake":
        kyc = "KYC documents are complete and verified" if not ctx.get("kyc_fail") \
              else "KYC address proof is expired and requires renewal"
        return (f"Application from {name} for £{amt:,.0f} has been received and pre-screened. "
                f"{kyc}; affordability pre-check {'passes' if dti <= 43 else 'fails'} with a DTI of {dti:.1f}%.")
    if agent_id == "risk":
        level = "LOW" if score >= 700 and dti < 35 else "HIGH" if score < 600 or dti > 43 else "MEDIUM"
        factor = "strong credit score" if score >= 700 else "elevated DTI ratio" if dti > 35 else "borderline credit profile"
        return (f"Risk assessment: {level} risk. "
                f"Credit score of {score} is {'above' if score >= 700 else 'below'} threshold; "
                f"the primary factor is the applicant's {factor}.")
    if agent_id == "fraud":
        if fraud:
            return (f"Fraud screening flagged concerns: multiple declined transactions and unusual activity detected. "
                    f"This application requires manual review before proceeding.")
        return (f"No fraud indicators detected for {name}. "
                f"Transaction history is consistent with normal customer behaviour — application may proceed.")
    if agent_id == "decision":
        if fraud:
            verdict = "DECLINED"
            reason  = "fraud screening flagged high-risk transaction patterns requiring further investigation"
        elif score >= 700 and dti <= 35 and not ctx.get("kyc_fail"):
            verdict = "APPROVED"
            reason  = f"strong credit profile (score {score}), manageable DTI ({dti:.1f}%), and clean fraud screen"
        elif score >= 620 and dti <= 43:
            verdict = "CONDITIONALLY APPROVED"
            reason  = "subject to updated proof of address and a two-month bank statement submission"
        else:
            verdict = "DECLINED"
            reason  = f"credit score of {score} falls below minimum threshold or DTI of {dti:.1f}% exceeds policy limit"
        return f"{verdict}: {reason.capitalize()}."
    return f"[{agent_id}] Analysis complete for application #{ctx.get('app_id','N/A')}."

# ── Harness: Session / Progress State ─────────────────────────────────────────
_SESSIONS: dict[str, dict] = {}   # app_id → harness state

def _init_session(app_id: str, customer: dict, loan: dict) -> dict:
    state = {
         "app_id":       app_id,
         "session_num":  0,
         "customer":     customer,
         "loan":         loan,
         "progress": {
             "intake":   "pending",
             "risk":     "pending",
             "fraud":    "pending",
             "decision": "pending",
         },
         "results":      {},
         "context_size": 0,
         "compactions":  0,
         "agent_timings": {
             "intake":   0.0,
             "risk":     0.0,
             "fraud":    0.0,
             "decision": 0.0,
         },
         "pipeline_start": time.perf_counter(),
         "created_at":   datetime.utcnow().isoformat(),
         "updated_at":   datetime.utcnow().isoformat(),
    }
    _SESSIONS[app_id] = state
    return state

# ── SSE helper ────────────────────────────────────────────────────────────────
def _ev(kind: str, **kw) -> str:
    return f"data: {json.dumps({'kind': kind, 'ts': datetime.utcnow().strftime('%H:%M:%S'), **kw})}\n\n"

# ── Main pipeline ──────────────────────────────────────────────────────────────
async def _run_pipeline(app_id: str, customer: dict, loan: dict) -> AsyncGenerator[str, None]:
    PIPELINE_RUNS.inc()
    state = _init_session(app_id, customer, loan)
    c     = customer
    l     = loan

    # ── Harness: Session 1 Initializer ────────────────────────────────────────
    state["session_num"] = 1
    yield _ev("harness_session", session=1, type="INITIALIZER",
              msg=f"Harness initialised for application {app_id}. "
                  f"4 agent stages queued: intake → risk → fraud → decision.")

    app_upsert({
        "id": app_id, "customer_id": c["id"], "customer_name": c["name"],
        "amount": l["amount"], "purpose": l["purpose"], "status": "submitted",
        "credit_score": c["credit_score"], "annual_income": c["income"],
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
    })
    epi_log(app_id, 1, "harness", "application_created",
            f"£{l['amount']:,.0f} for {l['purpose']}", "submitted")
    yield _ev("memory", store="episodic", op="write",
              msg=f"[Episodic] Application {app_id} logged to audit trail (SQLite)")
    await asyncio.sleep(0.3)

    # Store loan rules in semantic memory (first run only)
    rules_needed = sem_query("loan credit score requirement", top_k=1)
    if not rules_needed:
        for rule in BANKING_RULES:
            sem_add(rule, {"source": "regulatory", "added": datetime.utcnow().isoformat()})
        yield _ev("memory", store="semantic", op="write",
                  msg=f"[Semantic] {len(BANKING_RULES)} banking regulations indexed in ChromaDB vector store")
        await asyncio.sleep(0.3)

    # In-context: seed with session start
    ctx_add("system", f"Loan application session for {c['name']} (ID: {app_id}). "
                      f"Requested: £{l['amount']:,.0f} over {l['term_months']} months.")
    ctx_add("user", f"Process loan application. Customer: {c['name']}, "
                    f"Credit score: {c['credit_score']}, Income: £{c['income']:,}/yr.")
    yield _ev("memory", store="context", op="write",
              msg=f"[In-Context] Session seeded — {len(_context)}/{CTX_LIMIT} turns used",
              turns=len(_context), limit=CTX_LIMIT)
    await asyncio.sleep(0.3)

    # ── Harness: Session 2 — Intake Agent (A2A) ───────────────────────────────
    state["session_num"] = 2
    yield _ev("harness_session", session=2, type="CODING_AGENT",
              msg="Harness reading progress file. Next stage: INTAKE. Dispatching via A2A.")

    yield _ev("a2a_discover", agent="intake",
              card={
                  "name": A2A_AGENTS["intake"]["name"],
                  "url":  f"/.well-known/agents/intake",
                  "skills": A2A_AGENTS["intake"]["skills"],
              },
              msg="[A2A] Discovered Intake Agent via Agent Card")
    await asyncio.sleep(0.3)

    # SDK: dispatch tools for intake
    t0 = time.perf_counter()
    
    # Tool: get_customer_profile
    t_tool = time.perf_counter()
    yield _ev("sdk_tool", tool="get_customer_profile", args={"customer_id": c["id"]},
              msg="[SDK] @tool: get_customer_profile()")
    profile = get_customer_profile(c["id"])
    TOOL_CALLS.labels(tool_name="get_customer_profile").inc()
    TOOL_LATENCY.labels(tool_name="get_customer_profile").observe(time.perf_counter() - t_tool)
    yield _ev("sdk_result", tool="get_customer_profile", result=str(profile)[:120])
    await asyncio.sleep(0.25)

    # Tool: verify_kyc_documents
    t_tool = time.perf_counter()
    yield _ev("sdk_tool", tool="verify_kyc_documents", args={"customer_id": c["id"]},
              msg="[SDK] @tool: verify_kyc_documents()")
    kyc = verify_kyc_documents(c["id"])
    TOOL_CALLS.labels(tool_name="verify_kyc_documents").inc()
    TOOL_LATENCY.labels(tool_name="verify_kyc_documents").observe(time.perf_counter() - t_tool)
    yield _ev("sdk_result", tool="verify_kyc_documents",
              result=f"KYC pass={kyc['kyc_pass']} | biometric={kyc['biometric_match']}")
    await asyncio.sleep(0.25)

    # Tool: calculate_affordability
    t_tool = time.perf_counter()
    yield _ev("sdk_tool", tool="calculate_affordability",
              args={"customer_id": c["id"], "loan_amount": l["amount"], "term_months": l["term_months"]},
              msg="[SDK] @tool: calculate_affordability()")
    afford = calculate_affordability(c["id"], l["amount"], l["term_months"])
    TOOL_CALLS.labels(tool_name="calculate_affordability").inc()
    TOOL_LATENCY.labels(tool_name="calculate_affordability").observe(time.perf_counter() - t_tool)
    yield _ev("sdk_result", tool="calculate_affordability",
              result=f"Monthly payment: £{afford['monthly_payment']} | DTI: {afford['dti_ratio']}% | Pass: {afford['dti_pass']}")
    await asyncio.sleep(0.25)

     # A2A task to intake agent
    AGENT_CALLS.labels(agent="intake").inc()
    intake_ctx = {**c, "amount": l["amount"], "purpose": l["purpose"],
                   "kyc_fail": not kyc["kyc_pass"], "dti_ratio": afford["dti_ratio"],
                   "monthly_payment": afford["monthly_payment"], "app_id": app_id}
    user_msg   = (f"Customer {c['name']}, credit {c['credit_score']}, income £{c['income']:,}/yr. "
                   f"Loan: £{l['amount']:,} over {l['term_months']}mo for '{l['purpose']}'. "
                   f"KYC: {'PASS' if kyc['kyc_pass'] else 'FAIL'}. "
                   f"DTI: {afford['dti_ratio']}%. Monthly repayment: £{afford['monthly_payment']}.")
    yield _ev("a2a_request", agent="intake", method="tasks/send",
               msg=f"[A2A] tasks/send → Intake Agent",
               payload=user_msg[:120])
    await asyncio.sleep(0.2)

    llm_txt = await _call_llm(A2A_AGENTS["intake"]["system_prompt"], user_msg, max_tokens=120)
    intake_summary = llm_txt or _mock_response("intake", intake_ctx)
    await asyncio.sleep(0.3)

    ctx_add("assistant", f"[Intake] {intake_summary}")
    state["results"]["intake"] = intake_summary
    state["progress"]["intake"] = "complete"
    intake_duration = time.perf_counter() - t0
    state["agent_timings"]["intake"] = intake_duration
    AGENT_LATENCY.labels(agent="intake").observe(intake_duration)
    MEMORY_OPERATIONS.labels(memory_type="in-context", operation="write").inc()

    epi_log(app_id, 2, "intake", "intake_complete", intake_summary[:120], "complete")
    work_set(f"{app_id}:intake_summary", intake_summary[:200], ttl=600)

    yield _ev("a2a_response", agent="intake", status="completed",
              result=intake_summary)
    yield _ev("memory", store="episodic", op="write",
              msg="[Episodic] Intake decision logged to SQLite audit trail")
    yield _ev("memory", store="working", op="write",
              msg=f"[Working] Intake summary cached in Redis (TTL 600s)")
    yield _ev("memory", store="context", op="write",
              msg=f"[In-Context] {len(_context)}/{CTX_LIMIT} turns", turns=len(_context), limit=CTX_LIMIT)
    await asyncio.sleep(0.4)

    # ── Harness: Session 3 — Risk Agent (A2A) ─────────────────────────────────
    state["session_num"] = 3
    yield _ev("harness_session", session=3, type="CODING_AGENT",
              msg="Harness reads progress: intake=complete. Next: RISK ASSESSMENT.")

    # Query semantic memory for relevant rules
    yield _ev("memory", store="semantic", op="read",
              msg="[Semantic] Querying ChromaDB: 'credit score DTI loan requirements'")
    rules = query_banking_rules(f"credit score {c['credit_score']} DTI {afford['dti_ratio']} loan")
    yield _ev("memory", store="semantic", op="result",
              msg=f"[Semantic] Retrieved {len(rules)} relevant regulation(s): {rules[0][:80]}...")
    await asyncio.sleep(0.3)

    yield _ev("a2a_discover", agent="risk",
              card={"name": A2A_AGENTS["risk"]["name"],
                    "skills": A2A_AGENTS["risk"]["skills"]},
              msg="[A2A] Discovered Risk Assessment Agent")

    AGENT_CALLS.labels(agent="risk").inc()
    t0 = time.perf_counter()
    
    # Tool: check_credit_score
    t_tool = time.perf_counter()
    yield _ev("sdk_tool", tool="check_credit_score", args={"customer_id": c["id"]},
              msg="[SDK] @tool: check_credit_score()")
    credit = check_credit_score(c["id"])
    TOOL_CALLS.labels(tool_name="check_credit_score").inc()
    TOOL_LATENCY.labels(tool_name="check_credit_score").observe(time.perf_counter() - t_tool)
    yield _ev("sdk_result", tool="check_credit_score",
              result=f"Score: {credit['score']} ({credit['band']}) — {credit['bureau']}")
    await asyncio.sleep(0.25)

    risk_msg = (f"Credit score: {credit['score']} ({credit['band']}). "
                f"Annual income: £{c['income']:,}. Loan amount: £{l['amount']:,}. "
                f"DTI ratio: {afford['dti_ratio']}% ({'pass' if afford['dti_pass'] else 'FAIL — exceeds 43%'}). "
                f"Relevant rules: {rules[0][:120] if rules else 'Standard criteria apply'}")
    yield _ev("a2a_request", agent="risk", method="tasks/send",
               msg="[A2A] tasks/send → Risk Assessment Agent",
               payload=risk_msg[:120])
    await asyncio.sleep(0.2)

    llm_txt = await _call_llm(A2A_AGENTS["risk"]["system_prompt"], risk_msg, max_tokens=100)
    risk_summary = llm_txt or _mock_response("risk",
                                              {**c, "dti_ratio": afford["dti_ratio"], "amount": l["amount"]})
    await asyncio.sleep(0.3)

    ctx_add("assistant", f"[Risk] {risk_summary}")
    state["results"]["risk"] = risk_summary
    state["progress"]["risk"] = "complete"
    risk_duration = time.perf_counter() - t0
    state["agent_timings"]["risk"] = risk_duration
    AGENT_LATENCY.labels(agent="risk").observe(risk_duration)

    epi_log(app_id, 3, "risk", "risk_complete", risk_summary[:120], "complete")
    work_set(f"{app_id}:risk_level",
             "HIGH" if c["credit_score"] < 600 or not afford["dti_pass"] else
             "LOW" if c["credit_score"] >= 700 and afford["dti_pass"] else "MEDIUM",
             ttl=600)

    yield _ev("a2a_response", agent="risk", status="completed", result=risk_summary)
    yield _ev("memory", store="working", op="write",
              msg=f"[Working] Risk level cached in Redis for downstream agents")
    await asyncio.sleep(0.4)

    # ── Harness: Session 4 — Fraud Agent (A2A) ────────────────────────────────
    state["session_num"] = 4
    yield _ev("harness_session", session=4, type="CODING_AGENT",
              msg="Harness reads progress: risk=complete. Next: FRAUD SCREENING.")

    yield _ev("a2a_discover", agent="fraud",
              card={"name": A2A_AGENTS["fraud"]["name"],
                    "skills": A2A_AGENTS["fraud"]["skills"]},
              msg="[A2A] Discovered Fraud Detection Agent")

    AGENT_CALLS.labels(agent="fraud").inc()
    t0 = time.perf_counter()
    
    # Tool: scan_transaction_history
    t_tool = time.perf_counter()
    yield _ev("sdk_tool", tool="scan_transaction_history", args={"customer_id": c["id"]},
              msg="[SDK] @tool: scan_transaction_history()")
    tx = scan_transaction_history(c["id"])
    TOOL_CALLS.labels(tool_name="scan_transaction_history").inc()
    TOOL_LATENCY.labels(tool_name="scan_transaction_history").observe(time.perf_counter() - t_tool)
    yield _ev("sdk_result", tool="scan_transaction_history",
              result=f"30-day tx: {tx['transactions_30d']} | Declined: {tx['declined_30d']} | Fraud flags: {tx['fraud_flags']}")
    await asyncio.sleep(0.25)

    # Check working memory — has risk been cached?
    cached_risk = work_get(f"{app_id}:risk_level")
    yield _ev("memory", store="working", op="read",
              msg=f"[Working] Cache lookup: '{app_id}:risk_level' → {cached_risk or 'miss'}")
    await asyncio.sleep(0.2)

    fraud_msg = (f"Transaction history (30 days): {tx['transactions_30d']} total, "
                 f"{tx['declined_30d']} declined, {tx['foreign_transactions']} foreign. "
                 f"Fraud flags: {tx['fraud_flags']}. "
                 f"Specific signals: {'; '.join(tx['flags']) if tx['flags'] else 'none'}. "
                 f"Upstream risk level: {cached_risk or 'MEDIUM'}.")
    yield _ev("a2a_request", agent="fraud", method="tasks/send",
               msg="[A2A] tasks/send → Fraud Detection Agent",
               payload=fraud_msg[:120])
    await asyncio.sleep(0.2)

    llm_txt = await _call_llm(A2A_AGENTS["fraud"]["system_prompt"], fraud_msg, max_tokens=100)
    fraud_summary = llm_txt or _mock_response("fraud",
                                               {**c, "fraud_flags": tx["fraud_flags"], "app_id": app_id})
    await asyncio.sleep(0.3)

    ctx_add("assistant", f"[Fraud] {fraud_summary}")
    state["results"]["fraud"] = fraud_summary
    state["progress"]["fraud"] = "complete"
    fraud_duration = time.perf_counter() - t0
    state["agent_timings"]["fraud"] = fraud_duration
    AGENT_LATENCY.labels(agent="fraud").observe(fraud_duration)

    epi_log(app_id, 4, "fraud", "fraud_complete",
            f"flags={tx['fraud_flags']} signals={len(tx['flags'])}", "complete")

    # Context compaction check
    compaction_event = None
    if len(_context) >= CTX_LIMIT - 1:
        before = len(_context)
        ctx_add("system", "[COMPACTION TRIGGER]")  # triggers auto-compact in ctx_add
        state["compactions"] += 1
        compaction_event = (before, len(_context))

    yield _ev("a2a_response", agent="fraud", status="completed", result=fraud_summary)
    if compaction_event:
        yield _ev("harness_compaction",
                  msg=f"[Harness] Context compacted: {compaction_event[0]} → {compaction_event[1]} turns. "
                      f"Session continuity maintained via progress file.",
                  before=compaction_event[0], after=compaction_event[1])
    await asyncio.sleep(0.4)

    # ── Harness: Session 5 — Decision Agent (A2A) ─────────────────────────────
    state["session_num"] = 5
    yield _ev("harness_session", session=5, type="CODING_AGENT",
              msg="Harness reads progress: fraud=complete. Final stage: CREDIT DECISION.")

    yield _ev("a2a_discover", agent="decision",
              card={"name": A2A_AGENTS["decision"]["name"],
                    "skills": A2A_AGENTS["decision"]["skills"]},
              msg="[A2A] Discovered Decision Agent")

    AGENT_CALLS.labels(agent="decision").inc()
    t0 = time.perf_counter()
    decision_msg = (f"All upstream assessments complete for {c['name']} (ID: {app_id}). "
                    f"Loan: £{l['amount']:,} over {l['term_months']} months. "
                    f"INTAKE: {intake_summary[:100]}. "
                    f"RISK: {risk_summary[:100]}. "
                    f"FRAUD: {fraud_summary[:100]}.")
    yield _ev("a2a_request", agent="decision", method="tasks/send",
              msg="[A2A] tasks/send → Decision Agent (final stage)",
              payload=decision_msg[:140])
    await asyncio.sleep(0.2)

    llm_txt = await _call_llm(A2A_AGENTS["decision"]["system_prompt"], decision_msg, max_tokens=100)
    decision_summary = llm_txt or _mock_response("decision",
        {**c, "amount": l["amount"], "dti_ratio": afford["dti_ratio"],
         "fraud_flags": tx["fraud_flags"], "kyc_fail": not kyc["kyc_pass"], "app_id": app_id})
    await asyncio.sleep(0.3)

    # Determine final status
    decision_upper = decision_summary.upper()
    if "APPROVED" in decision_upper and "CONDITIONAL" not in decision_upper:
         final_status = "approved"
    elif "CONDITIONAL" in decision_upper:
         final_status = "conditional"
    else:
         final_status = "declined"

    ctx_add("assistant", f"[Decision] {decision_summary}")
    state["results"]["decision"] = decision_summary
    state["progress"]["decision"] = "complete"
    decision_duration = time.perf_counter() - t0
    state["agent_timings"]["decision"] = decision_duration
    AGENT_LATENCY.labels(agent="decision").observe(decision_duration)
    
    # ── Record Decision Metrics ────────────────────────────────────────────────
    APPLICATIONS_TOTAL.inc()
    PIPELINE_DECISIONS.labels(outcome=final_status).inc()
    if final_status == "approved":
        APPLICATIONS_APPROVED.inc()
    elif final_status == "conditional":
        APPLICATIONS_CONDITIONAL.inc()
    else:
        APPLICATIONS_DECLINED.inc()
    
    # Record risk level
    risk_level = work_get(f"{app_id}:risk_level") or "MEDIUM"
    RISK_ALERTS.labels(risk_level=risk_level.lower()).inc()
    
    # Record fraud detection if flagged
    if tx.get("fraud_flags", False):
        FRAUD_DETECTIONS.labels(fraud_type="transaction_anomaly").inc()

    # Store decision in semantic memory
    sem_add(f"Application {app_id}: {c['name']} requested £{l['amount']:,}. "
            f"Credit {c['credit_score']}, DTI {afford['dti_ratio']}%. "
            f"Decision: {final_status}. {decision_summary[:100]}",
            {"type": "decision", "app_id": app_id, "customer": c["name"],
             "outcome": final_status})
    yield _ev("memory", store="semantic", op="write",
              msg=f"[Semantic] Decision stored in ChromaDB — future applications can reference this pattern")

    epi_log(app_id, 5, "decision", "decision_complete", decision_summary[:120], final_status)
    app_upsert({
        "id": app_id, "customer_id": c["id"], "customer_name": c["name"],
        "amount": l["amount"], "purpose": l["purpose"], "status": final_status,
        "credit_score": c["credit_score"], "annual_income": c["income"],
        "created_at": state["created_at"],
        "updated_at": datetime.utcnow().isoformat(),
    })
    work_set(f"{app_id}:final_decision", decision_summary[:200], ttl=3600)

    yield _ev("a2a_response", agent="decision", status="completed", result=decision_summary)
    yield _ev("memory", store="episodic", op="write",
              msg=f"[Episodic] Final decision ({final_status.upper()}) persisted to audit log")
    yield _ev("memory", store="working", op="write",
              msg=f"[Working] Decision cached in Redis (TTL 1hr) for notification service")
    await asyncio.sleep(0.3)

     # ── Final harness summary ──────────────────────────────────────────────────
    state["session_num"] = 5
    state["updated_at"]  = datetime.utcnow().isoformat()
    
    # Calculate total pipeline time
    total_pipeline_time = time.perf_counter() - state["pipeline_start"]
    PIPELINE_DURATION.observe(total_pipeline_time)
    
    # Update memory metrics
    MEMORY_ITEMS.labels(memory_type="in-context").set(len(_context))
    MEMORY_ITEMS.labels(memory_type="episodic").set(len(epi_list(app_id)))
    MEMORY_ITEMS.labels(memory_type="working").set(len(work_list()))
    if _chroma_ready and _chroma_col:
        MEMORY_ITEMS.labels(memory_type="semantic").set(_chroma_col.count())
    
    # Record application in health monitor
    health_monitor.record_application(final_status.upper(), total_pipeline_time)
    
    # Post application outcome to Slack
    await post_application_outcome(
         app_id=app_id,
         customer_name=c["name"],
         decision=final_status.upper(),
         reason=decision_summary[:150],
         agent_timings=state["agent_timings"],
         total_time=total_pipeline_time,
         loan_amount=l["amount"],
         loan_term=l["term_months"],
         loan_purpose=l["purpose"],
         credit_score=c["credit_score"],
    )

    yield _ev("done",
               app_id=app_id,
               customer=c["name"],
               decision=final_status.upper(),
               sessions=5,
               compactions=state["compactions"],
               context_turns=len(_context),
               agents_used=4,
               tools_called=5,
               memory_stores=4,
               results=state["results"],
               msg=f"Pipeline complete. Decision: {final_status.upper()}. "
                   f"All 4 memory stores active, 4 A2A agents coordinated, 5 harness sessions.")


# ── REST API ──────────────────────────────────────────────────────────────────
@app.get("/api/status")
def api_status():
    return {"service": "banking-demo", "llm": _llm_backend,
            "model": _llm_model, "mock": _llm_backend == "mock",
            "chroma_ready": _chroma_ready}

@app.get("/api/llm/status")
def api_llm_status():
    return {"backend": _llm_backend, "model": _llm_model, "mock": _llm_backend == "mock"}

@app.get("/api/customers")
def api_customers():
    return {"customers": CUSTOMERS}

@app.get("/api/applications")
def api_applications():
    return {"applications": app_list(20)}

@app.get("/api/events/{app_id}")
def api_events(app_id: str):
    return {"events": epi_list(app_id)}

@app.get("/api/tools")
def api_tools():
    return {"tools": [{k: v for k, v in t.items() if k != "fn"}
                      for t in TOOLS.values()]}

@app.get("/api/agents")
def api_agents():
    return {"agents": [{"id": k, "name": v["name"],
                        "description": v["description"],
                        "skills": v["skills"]}
                       for k, v in A2A_AGENTS.items()]}

@app.get("/api/memory/context")
def api_context():
    return {"items": list(_context), "count": len(_context), "limit": CTX_LIMIT}

@app.get("/api/memory/working")
def api_working():
    return {"items": work_list()}

@app.get("/api/memory/episodic")
def api_episodic_all():
    """Get all episodic memory events (audit trail)."""
    with _db() as c:
        rows = c.execute(
            "SELECT * FROM loan_events ORDER BY ts DESC LIMIT 100"
        ).fetchall()
    return {"items": [dict(r) for r in rows], "count": len(rows)}

@app.get("/api/memory/semantic")
def api_semantic_all():
    """Get all semantic memory entries (knowledge base)."""
    if not _chroma_ready or _chroma_col is None:
        return {"items": [], "count": 0, "status": "not_ready"}
    try:
        results = _chroma_col.get(include=["documents", "metadatas"])
        items = []
        for i, doc_id in enumerate(results.get("ids", [])):
            items.append({
                "id": doc_id,
                "text": results["documents"][i] if i < len(results.get("documents", [])) else "",
                "metadata": results["metadatas"][i] if i < len(results.get("metadatas", [])) else {},
            })
        return {"items": items, "count": len(items), "status": "ready"}
    except Exception as exc:
        return {"items": [], "count": 0, "status": "error", "error": str(exc)}

@app.get("/api/memory/stats")
def api_memory_stats():
    """Get statistics for all memory stores."""
    with _db() as c:
        episodic_count = c.execute("SELECT COUNT(*) FROM loan_events").fetchone()[0]
        app_count = c.execute("SELECT COUNT(*) FROM loan_applications").fetchone()[0]
    
    semantic_count = 0
    if _chroma_ready and _chroma_col is not None:
        try:
            semantic_count = _chroma_col.count()
        except:
            pass
    
    working_items = work_list()
    
    return {
        "context": {"count": len(_context), "limit": CTX_LIMIT},
        "episodic": {"count": episodic_count, "applications": app_count},
        "semantic": {"count": semantic_count, "status": "ready" if _chroma_ready else "not_ready"},
        "working": {"count": len(working_items)},
    }

@app.post("/api/memory/clear/episodic")
def api_clear_episodic():
    """Clear all episodic memory (SQLite audit trail)."""
    try:
        with _db() as c:
            c.execute("DELETE FROM loan_events")
            c.execute("DELETE FROM loan_applications")
            c.commit()
        return {"status": "success", "message": "Episodic memory cleared"}
    except Exception as exc:
        return {"status": "error", "message": str(exc)}, 500

@app.post("/api/memory/clear/semantic")
def api_clear_semantic():
    """Clear all semantic memory (ChromaDB knowledge base)."""
    if not _chroma_ready or _chroma_col is None:
        return {"status": "error", "message": "ChromaDB not ready"}, 500
    try:
        # Delete all documents from the collection
        all_docs = _chroma_col.get()
        if all_docs and all_docs.get("ids"):
            _chroma_col.delete(ids=all_docs["ids"])
        return {"status": "success", "message": "Semantic memory cleared"}
    except Exception as exc:
        return {"status": "error", "message": str(exc)}, 500

@app.get("/api/run")
async def api_run(
    customer_id: str = "CUST001",
    amount: float = 15000,
    term_months: int = 36,
    purpose: str = "Home renovation — kitchen and bathroom upgrade",
):
    customer = next((c for c in CUSTOMERS if c["id"] == customer_id), CUSTOMERS[0])
    loan     = {"amount": amount, "term_months": term_months, "purpose": purpose}
    app_id   = f"LOAN-{datetime.utcnow().strftime('%H%M%S')}-{customer_id[-3:]}"
    ctx_clear()
    return StreamingResponse(
        _run_pipeline(app_id, customer, loan),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )

@app.get("/api/seed")
async def api_seed():
    """Run a quick silent seed to pre-populate applications."""
    ctx_clear()
    for i, cust in enumerate(CUSTOMERS[:3]):
        purpose = LOAN_PURPOSES[i % len(LOAN_PURPOSES)]
        amount  = [10000, 25000, 5000][i]
        loan    = {"amount": amount, "term_months": [24, 48, 12][i], "purpose": purpose}
        app_id  = f"SEED-{i+1:03d}-{cust['id'][-4:]}"
        async for _ in _run_pipeline(app_id, cust, loan):
            pass  # consume silently
    return {"seeded": 3}

@app.get("/api/generate-traffic/{count}")
async def api_generate_traffic(count: int = 20):
    """Generate random loan applications to test performance, metrics, and alerts.
    
    Args:
        count: Number of random transactions to generate (20, 30, or 50)
    
    Returns:
        Summary of generated transactions with timing and decision distribution
    """
    if count not in [20, 30, 50]:
        return {"error": f"Invalid count. Must be 20, 30, or 50. Got {count}"}, 400
    
    import random as rnd
    
    start_time = time.perf_counter()
    results = {
        "approved": 0,
        "declined": 0,
        "conditional": 0,
        "total": count,
        "applications": [],
        "errors": 0,
    }
    
    logger = get_logger(__name__)
    logger.msg(f"Traffic generation started", count=count, timestamp=datetime.utcnow().isoformat())
    
    for i in range(count):
        try:
            # Randomly select customer, loan amount, term, and purpose
            customer = rnd.choice(CUSTOMERS)
            loan_amount = rnd.choice([5000, 10000, 15000, 20000, 25000, 30000, 50000])
            loan_term = rnd.choice([12, 24, 36, 48, 60])
            loan_purpose = rnd.choice(LOAN_PURPOSES)
            
            # Generate unique app ID with timestamp
            app_id = f"TRAFFIC-{datetime.utcnow().strftime('%H%M%S')}-{i+1:03d}-{customer['id'][-3:]}"
            
            # Clear context for fresh session
            ctx_clear()
            
            # Run pipeline silently and collect decision
            decision = None
            async for event in _run_pipeline(app_id, customer, {"amount": loan_amount, "term_months": loan_term, "purpose": loan_purpose}):
                # Parse event to extract decision
                try:
                    event_data = json.loads(event.split("data: ")[1])
                    if event_data.get("kind") == "done":
                        decision = event_data.get("decision", "UNKNOWN")
                except:
                    pass
            
            # Record decision
            if decision:
                if decision == "APPROVED":
                    results["approved"] += 1
                elif decision == "DECLINED":
                    results["declined"] += 1
                elif decision == "CONDITIONALLY APPROVED":
                    results["conditional"] += 1
            
            results["applications"].append({
                "app_id": app_id,
                "customer": customer["name"],
                "amount": loan_amount,
                "term_months": loan_term,
                "decision": decision,
            })
            
            # Small delay to prevent overwhelming the system
            await asyncio.sleep(0.1)
            
        except Exception as e:
            results["errors"] += 1
            logger.msg(f"Error in traffic generation", error=str(e), iteration=i+1)
    
    total_time = time.perf_counter() - start_time
    
    results.update({
        "total_time_seconds": round(total_time, 2),
        "avg_time_per_transaction": round(total_time / count, 2),
        "transactions_per_second": round(count / total_time, 2),
        "approval_rate": round((results["approved"] / count * 100) if count > 0 else 0, 2),
        "decline_rate": round((results["declined"] / count * 100) if count > 0 else 0, 2),
        "conditional_rate": round((results["conditional"] / count * 100) if count > 0 else 0, 2),
    })
    
    logger.msg(
        "Traffic generation completed",
        count=count,
        total_time=total_time,
        approval_rate=results["approval_rate"],
        decline_rate=results["decline_rate"],
    )
    
    return results


@app.on_event("startup")
async def startup():
    # Initialize structured logging
    configure_logging("INFO")
    logger = get_logger(__name__)
    logger.msg("Banking Demo startup", startup_phase="startup_begin")
    
    await _resolve_backend()
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, _init_chroma)
    await loop.run_in_executor(None, _init_redis)
    if _chroma_ready and _chroma_col.count() == 0:
         for rule in BANKING_RULES:
             sem_add(rule, {"source": "regulatory"})
         for signal in FRAUD_SIGNALS:
             sem_add(signal, {"source": "fraud_signals"})
         logger.msg("Knowledge base seeded", status="knowledge_base_ready")
    
    # Start health monitor loop (posts summary every 15 minutes)
    asyncio.create_task(start_health_monitor_loop())
    logger.msg("Health monitor started", interval_minutes=15)
    
    logger.msg("Banking Demo ready", startup_phase="startup_complete", llm_backend=_llm_backend)


# ── Frontend ──────────────────────────────────────────────────────────────────
@app.get("/", response_class=HTMLResponse)
def index():
    with open("frontend/index.html", "r") as f:
        return f.read()

@app.get("/memory", response_class=HTMLResponse)
def memory_inspector():
    with open("frontend/memory.html", "r") as f:
        return f.read()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8005)