"""
E-Commerce Order Fulfilment Pipeline (Refactored)
===================================================
Scenario: A customer places an order on an online retailer. The platform
processes it end-to-end using four AI agents.

Architecture:
- SDK Layer    — @tool functions: get_customer, check_inventory, calculate_shipping, etc.
- Harness      — S1 Initialiser → S2 Validation → S3 Fulfilment → S4 Pricing → S5 Dispatch
- A2A Protocol — Four specialist agents via JSON-RPC 2.0
- Memory       — In-context, Episodic (SQLite), Semantic (ChromaDB), Working (Redis)

Port: 8007
"""

from __future__ import annotations

import asyncio
import json
import os
import uuid
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, StreamingResponse
from prometheus_fastapi_instrumentator import Instrumentator

from llm import LLMFactory
from memory import MemoryManager
from tools import TOOLS
from agents import A2A_AGENTS
from data import CUSTOMERS, PRODUCTS
from harness import run_pipeline, PIPELINE_DURATION, STAGE_EXECUTIONS, STAGE_DURATION, TOOL_CALLS, TOOL_CALL_DURATION
from transaction_summary import TransactionSummary

# ── App ───────────────────────────────────────────────────────────────────────
app = FastAPI(title="E-Commerce Agent Demo")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
Instrumentator().instrument(app).expose(app)

# ── Global state ──────────────────────────────────────────────────────────────
_llm_backend = None
_memory_manager = None
_transaction_summary = None
_SERVICE_NAME = "E-Commerce Demo"

# ── Initialization ────────────────────────────────────────────────────────────
@app.on_event("startup")
async def startup():
    """Initialize LLM backend and memory manager."""
    print("[STARTUP] Starting initialization...")
    global _llm_backend, _memory_manager, _transaction_summary

    # Initialize LLM backend
    _llm_backend = await LLMFactory.create()
    print(f"[{_SERVICE_NAME}] LLM: {_llm_backend.get_name()}/{_llm_backend.get_model()}")

    # Initialize memory manager
    data_dir = Path(os.getenv("DATA_DIR", "/data"))
    _memory_manager = MemoryManager(data_dir)
    print(f"[{_SERVICE_NAME}] Memory manager initialized")
    
    # Initialize transaction summary service
    try:
        _transaction_summary = TransactionSummary()
        print(f"[{_SERVICE_NAME}] Transaction summary service initialized")
    except Exception as e:
        print(f"[{_SERVICE_NAME}] ERROR initializing transaction summary: {e}")
        _transaction_summary = None


# ── REST endpoints ────────────────────────────────────────────────────────────
@app.get("/api/status")
def api_status():
    """Get service status."""
    return {
        "service": "ecommerce-demo",
        "llm": _llm_backend.get_name() if _llm_backend else "unknown",
        "model": _llm_backend.get_model() if _llm_backend else "unknown",
        "mock": _llm_backend.get_name() == "mock" if _llm_backend else True,
        "chroma_ready": _memory_manager.semantic.is_ready() if _memory_manager else False,
    }


@app.get("/api/llm/status")
def api_llm_status():
    """Get LLM status."""
    return {
        "backend": _llm_backend.get_name() if _llm_backend else "unknown",
        "model": _llm_backend.get_model() if _llm_backend else "unknown",
        "mock": _llm_backend.get_name() == "mock" if _llm_backend else True,
    }


@app.get("/api/customers")
def api_customers():
    """Get list of customers."""
    return {"customers": CUSTOMERS}


@app.get("/api/products")
def api_products():
    """Get list of products."""
    return {"products": PRODUCTS}


@app.get("/api/orders")
def api_orders():
    """Get recent orders."""
    if not _memory_manager:
        return {"orders": []}
    return {"orders": _memory_manager.episodic.get_orders(20)}


@app.get("/api/events/{order_id}")
def api_events(order_id: str):
    """Get events for an order."""
    if not _memory_manager:
        return {"events": []}
    return {"events": _memory_manager.episodic.get_events(order_id)}


@app.get("/api/tools")
def api_tools():
    """Get registered tools."""
    return {
        "tools": [
            {k: v for k, v in t.items() if k != "fn"}
            for t in TOOLS.values()
        ]
    }


@app.get("/api/agents")
def api_agents():
    """Get agent definitions."""
    return {
        "agents": [
            {
                "id": k,
                "name": v["name"],
                "description": v["description"],
                "skills": v["skills"],
            }
            for k, v in A2A_AGENTS.items()
        ]
    }


@app.get("/api/memory/context")
def api_context():
    """Get in-context memory."""
    if not _memory_manager:
        return {"items": [], "count": 0, "limit": 10}
    return {
        "items": _memory_manager.context.get_all(),
        "count": _memory_manager.context.count(),
        "limit": _memory_manager.context.limit,
    }


@app.get("/api/memory/working")
def api_working():
    """Get working memory."""
    if not _memory_manager:
        return {"items": []}
    return {"items": _memory_manager.working.list_all()}


async def _pipeline_with_summary(order_id, customer, cart, llm, memory):
    """Wrapper that sends transaction summary to Slack after pipeline completion."""
    print(f"[DEBUG] _pipeline_with_summary called for order {order_id}", flush=True)
    async for event in run_pipeline(order_id, customer, cart, llm, memory):
        yield event
        
        # Parse the event to check if it's the "done" event
        if event.startswith("data: "):
            try:
                data = json.loads(event[6:-2])  # Remove "data: " prefix and "\n\n" suffix
                if data.get("kind") == "done":
                    # Send transaction summary to Slack directly (synchronously, before stream closes)
                    try:
                        # Parse items if it's a JSON string
                        items = data.get("items", "[]")
                        if isinstance(items, str):
                            try:
                                items = json.loads(items)
                            except:
                                items = []
                        
                        # Create summary directly
                        summary = _transaction_summary.capture(
                            order_id=data.get("order_id", ""),
                            customer={
                                "id": data.get("customer_id", ""),
                                "name": data.get("customer", ""),
                                "tier": data.get("customer_tier", ""),
                            },
                            cart=items,
                            subtotal=float(data.get("subtotal", 0)),
                            final_total=float(data.get("final_total", 0)),
                            discount=float(data.get("discount", 0)),
                            shipping=float(data.get("shipping", 0)),
                            final_status=data.get("outcome", "UNKNOWN").lower().replace(" ", "_"),
                            warehouse=data.get("warehouse", ""),
                            agent_timings={},
                            tool_timings={},
                            fraud_check={
                                "score": float(data.get("fraud_score", 0)),
                                "requires_review": bool(data.get("fraud_requires_review", False)),
                                "reason": str(data.get("fraud_reason", "")),
                            },
                            promo={
                                "promo_code": str(data.get("promo_code", "NONE")),
                                "saving": float(data.get("promo_saving", 0)),
                            },
                            dispatch_reasoning=str(data.get("dispatch_reasoning", ""))[:200],
                            validation_reasoning=str(data.get("validation_reasoning", ""))[:200],
                            fulfilment_reasoning=str(data.get("fulfilment_reasoning", ""))[:200],
                            pricing_reasoning=str(data.get("pricing_reasoning", ""))[:200],
                        )
                        
                        # Send to Slack synchronously
                        if _transaction_summary:
                            sent = _transaction_summary.send_to_slack(summary)
                            print(f"[TransactionSummary] Sent to Slack: {sent}")
                        
                    except Exception as e:
                        print(f"[TransactionSummary] Error sending summary: {e}", flush=True)
            except json.JSONDecodeError:
                pass  # Silently ignore non-JSON events


@app.get("/api/run")
async def api_run(
    customer_id: str = "C001",
    sku1: str = "SKU-001",
    qty1: int = 1,
    sku2: str = "",
    qty2: int = 1,
):
    """Run the order processing pipeline."""
    if not _llm_backend or not _memory_manager:
        return {"error": "Service not initialized"}

    customer = next((c for c in CUSTOMERS if c["id"] == customer_id), CUSTOMERS[0])
    cart = [{"sku": sku1, "qty": qty1}]
    if sku2:
        cart.append({"sku": sku2, "qty": qty2})

    order_id = f"ORD-{datetime.utcnow().strftime('%H%M%S')}-{customer_id[-3:]}"
    _memory_manager.context.clear()

    return StreamingResponse(
        _pipeline_with_summary(order_id, customer, cart, _llm_backend, _memory_manager),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@app.get("/api/seed")
async def api_seed():
    """Seed sample orders."""
    if not _llm_backend or not _memory_manager:
        return {"error": "Service not initialized"}

    _memory_manager.context.clear()
    seed_orders = [
        ("C001", "SKU-001", 1, "", 1),
        ("C002", "SKU-003", 2, "SKU-006", 1),
        ("C004", "SKU-007", 1, "", 1),
    ]
    for cid, s1, q1, s2, q2 in seed_orders:
        cust = next((c for c in CUSTOMERS if c["id"] == cid), CUSTOMERS[0])
        cart = [{"sku": s1, "qty": q1}]
        if s2:
            cart.append({"sku": s2, "qty": int(q2)})
        oid = f"SEED-{cid[-3:]}-{uuid.uuid4().hex[:4].upper()}"
        async for _ in run_pipeline(oid, cust, cart, _llm_backend, _memory_manager):
            pass
    return {"seeded": 3}


@app.post("/api/transaction/summary")
def api_transaction_summary(
    order_id: str,
    customer_id: str,
    customer_name: str,
    tier: str,
    items: str,
    subtotal: float,
    discount: float,
    shipping: float,
    final_total: float,
    final_status: str,
    warehouse: str,
    agent_timings: str,
    tool_timings: str,
    fraud_score: float = 0,
    fraud_requires_review: bool = False,
    fraud_reason: str = "",
    promo_code: str = "NONE",
    promo_saving: float = 0,
    dispatch_reasoning: str = "",
    validation_reasoning: str = "",
    fulfilment_reasoning: str = "",
    pricing_reasoning: str = "",
):
    """Send transaction summary to Slack.
    
    This endpoint is called after pipeline completion to send a detailed
    summary of the transaction to Slack.
    """
    print(f"[TransactionSummary] Endpoint called for order {order_id}")
    if not _transaction_summary:
        print(f"[TransactionSummary] Service not initialized!")
        return {"error": "Transaction summary service not initialized"}
    
    try:
        # Parse JSON strings
        items_list = json.loads(items) if isinstance(items, str) else items
        agent_timings_dict = json.loads(agent_timings) if isinstance(agent_timings, str) else agent_timings
        tool_timings_dict = json.loads(tool_timings) if isinstance(tool_timings, str) else tool_timings
        
        # Capture summary
        summary = _transaction_summary.capture(
            order_id=order_id,
            customer={"id": customer_id, "name": customer_name, "tier": tier},
            cart=items_list,
            subtotal=subtotal,
            final_total=final_total,
            discount=discount,
            shipping=shipping,
            final_status=final_status,
            warehouse=warehouse,
            agent_timings=agent_timings_dict,
            tool_timings=tool_timings_dict,
            fraud_check={
                "score": fraud_score,
                "requires_review": fraud_requires_review,
                "reason": fraud_reason,
            },
            promo={
                "promo_code": promo_code,
                "saving": promo_saving,
            },
            dispatch_reasoning=dispatch_reasoning,
            validation_reasoning=validation_reasoning,
            fulfilment_reasoning=fulfilment_reasoning,
            pricing_reasoning=pricing_reasoning,
        )
        
        # Send to Slack
        sent = _transaction_summary.send_to_slack(summary)
        
        return {
            "order_id": order_id,
            "status": final_status,
            "slack_sent": sent,
            "summary": summary,
        }
    except Exception as e:
        return {"error": str(e)}


@app.get("/", response_class=HTMLResponse)
def api_root():
    """Serve HTML UI."""
    return _HTML


# ── HTML UI ───────────────────────────────────────────────────────────────────
_HTML = """<!DOCTYPE html>
<html lang="en" data-theme="light">
<head>
<meta charset="UTF-8"/><meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>E-Commerce Order Pipeline</title>
<style>
:root{
  --bg:#f4f4f5;--surface:#fff;--card:#fff;--border:#d1d5db;--border2:#e5e7eb;
  --accent:#2563eb;--a2:#007a63;--a3:#dc4e2a;--a4:#b45309;--p:#7c3aed;
  --g:#007a63;--b:#2563eb;--o:#dc4e2a;--y:#b45309;
  --text:#111827;--m:#6b7280;--code-bg:#f0f2f5;
  --mono:Consolas,'Courier New',monospace;
  --sans:Calibri,Arial,Helvetica,sans-serif;
  color-scheme:light}
[data-theme=dark]{
  --bg:#06080f;--surface:#0d1117;--card:#111827;--border:#1f2d3d;--border2:#253348;
  --accent:#5b8cff;--a2:#00d4aa;--a3:#ff7c5c;--a4:#f0c040;--p:#b57bee;
  --g:#00d4aa;--b:#5b8cff;--o:#ff7c5c;--y:#f0c040;
  --text:#e2e8f0;--m:#64748b;--code-bg:#080c14;
  color-scheme:dark}
*{box-sizing:border-box;margin:0;padding:0}
html,body{background:var(--bg);color:var(--text);font-family:var(--sans);min-height:100vh;font-size:15px}
.llm-banner{display:flex;align-items:center;gap:.6rem;padding:.35rem 1rem;
  font-family:var(--mono);font-size:.72rem;border-bottom:1px solid var(--border);
  background:var(--surface);flex-wrap:wrap}
.llm-dot{width:8px;height:8px;border-radius:50%;flex-shrink:0;animation:blink 2.5s infinite}
@keyframes blink{0%,100%{opacity:1}50%{opacity:.35}}
.llm-mock{background:#dc4e2a}.llm-ollama{background:#007a63}
.llm-openai{background:#2563eb}.llm-anthropic{background:#7c3aed}
.llm-name{font-weight:700;color:var(--text)}.llm-model{color:var(--m)}
.llm-tag{font-size:.64rem;padding:.1rem .45rem;border-radius:3px;
  border:1px solid var(--border);color:var(--m);margin-left:auto}
header{background:var(--surface);border-bottom:1px solid var(--border);
  padding:.85rem 1.5rem;display:flex;align-items:center;
  justify-content:space-between;flex-wrap:wrap;gap:.5rem}
.logo{font-family:var(--mono);font-size:.82rem;font-weight:700;color:var(--accent);letter-spacing:.1em}
.logo span{color:var(--text)}
.badges{display:flex;gap:.4rem;flex-wrap:wrap}
.badge{font-family:var(--mono);font-size:.62rem;padding:.18rem .6rem;
  border-radius:100px;border:1px solid;letter-spacing:.06em}
main{max-width:1440px;margin:0 auto;padding:1rem;display:grid;
  grid-template-columns:290px 1fr 250px;gap:.85rem}
@media(max-width:1150px){main{grid-template-columns:260px 1fr}}
@media(max-width:750px){main{grid-template-columns:1fr}}
.full-row{grid-column:1/-1}
.panel{background:var(--card);border:1px solid var(--border);border-radius:10px;overflow:hidden}
.phdr{padding:.6rem .9rem;border-bottom:1px solid var(--border);font-family:var(--mono);
  font-size:.68rem;letter-spacing:.1em;display:flex;align-items:center;
  justify-content:space-between;gap:.4rem;background:var(--surface)}
.pbody{padding:.85rem}
.section-lbl{font-family:var(--mono);font-size:.6rem;color:var(--m);
  letter-spacing:.14em;text-transform:uppercase;margin:.7rem 0 .3rem}
.section-lbl:first-child{margin-top:0}
.cust-item{border:1px solid var(--border);border-radius:7px;padding:.5rem .7rem;
  cursor:pointer;background:var(--surface);margin-bottom:.35rem;transition:border-color .15s}
.cust-item:hover,.cust-item.active{border-color:var(--accent);background:var(--bg)}
.cust-name{font-weight:600;font-size:.82rem;margin-bottom:.18rem}
.cust-meta{font-family:var(--mono);font-size:.64rem;color:var(--m);
  display:flex;gap:.4rem;flex-wrap:wrap}
.tier-gold{color:var(--y)}.tier-silver{color:var(--m)}.tier-bronze{color:var(--a4)}
.cart-row{display:flex;gap:.4rem;align-items:center;margin-bottom:.4rem}
select,input[type=number]{background:var(--bg);border:1px solid var(--border);
  border-radius:6px;padding:.42rem .7rem;color:var(--text);font-family:var(--mono);
  font-size:.72rem;outline:none}
select:focus,input:focus{border-color:var(--accent)}
.form-label{font-family:var(--mono);font-size:.62rem;color:var(--m);margin-bottom:.12rem}
button{border:none;border-radius:7px;padding:.45rem 1rem;font-family:var(--mono);
  font-size:.72rem;font-weight:700;cursor:pointer;transition:opacity .15s;width:100%}
button:hover{opacity:.82}button:disabled{opacity:.35;cursor:not-allowed}
.btn-run{background:var(--accent);color:#fff;margin-top:.3rem}
.btn-seed{background:var(--surface);border:1px solid var(--border);color:var(--m);
  font-size:.65rem;padding:.32rem .65rem}
.agent-flow{display:flex;align-items:center;gap:.35rem;flex-wrap:wrap;
  padding:.5rem .7rem;background:var(--bg);border-radius:8px;
  border:1px solid var(--border);margin-bottom:.6rem}
.af-agent{border-radius:5px;padding:.28rem .6rem;font-family:var(--mono);
  font-size:.65rem;border:1px solid;transition:all .25s}
.af-arrow{color:var(--m);font-size:.8rem}
.af-pending {background:var(--bg);border-color:var(--border);color:var(--m)}
.af-active  {background:rgba(37,99,235,.15);border-color:var(--b);color:var(--b);animation:pulse-b 1s infinite}
@keyframes pulse-b{0%,100%{opacity:1}50%{opacity:.55}}
.af-complete{background:rgba(0,122,99,.12);border-color:var(--g);color:var(--g)}
#stream{min-height:180px;max-height:calc(100vh - 14rem);overflow-y:auto;
  font-family:var(--mono);font-size:.69rem;line-height:1.82}
#stream::-webkit-scrollbar{width:4px}
#stream::-webkit-scrollbar-thumb{background:var(--border);border-radius:2px}
.ev{padding:.28rem .45rem;border-radius:5px;margin-bottom:.22rem;
  display:flex;gap:.45rem;align-items:flex-start;border-left:2px solid transparent;flex-wrap:nowrap}
.ev-harness_session  {background:rgba(37,99,235,.06); border-left-color:var(--b)}
.ev-a2a_discover     {background:rgba(124,58,237,.06);border-left-color:var(--p)}
.ev-a2a_request      {background:rgba(0,122,99,.06);  border-left-color:var(--g)}
.ev-a2a_response     {background:rgba(0,122,99,.1);   border-left-color:var(--g)}
.ev-sdk_tool         {background:rgba(180,83,9,.06);  border-left-color:var(--y)}
.ev-sdk_result       {background:rgba(180,83,9,.04);  border-left-color:var(--y)}
.ev-memory           {background:rgba(100,116,139,.05);border-left-color:var(--m)}
.ev-harness_compaction{background:rgba(220,78,42,.07);border-left-color:var(--o)}
.ev-done             {background:rgba(0,122,99,.11);  border-left-color:var(--g);border-left-width:3px}
.ev-ts  {color:var(--m);min-width:3.8rem;font-size:.63rem;flex-shrink:0}
.ev-kind{min-width:8rem;font-size:.61rem;opacity:.65;flex-shrink:0}
.ev-msg {word-break:break-word}
.ev-result{margin-top:.15rem;font-size:.65rem;color:var(--m);
  border-top:1px dashed var(--border2);padding-top:.12rem;word-break:break-word}
.mem-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:.65rem}
@media(max-width:900px){.mem-grid{grid-template-columns:repeat(2,1fr)}}
@media(max-width:500px){.mem-grid{grid-template-columns:1fr}}
.mem-box{background:var(--surface);border:1px solid var(--border);border-radius:7px;
  padding:.65rem .8rem;border-top-width:2px;min-height:130px}
.mem-box.ctx{border-top-color:var(--b)}.mem-box.epi{border-top-color:var(--g)}
.mem-box.sem{border-top-color:var(--p)}.mem-box.wrk{border-top-color:var(--y)}
.mem-lbl{font-family:var(--mono);font-size:.6rem;color:var(--m);letter-spacing:.1em;margin-bottom:.3rem}
.mem-val{font-size:1.3rem;font-weight:700;line-height:1}
.mem-sub{font-family:var(--mono);font-size:.62rem;color:var(--m);margin-top:.12rem}
.mem-list{max-height:70px;overflow-y:auto;font-family:var(--mono);font-size:.64rem;
  color:var(--m);line-height:1.7;margin-top:.3rem}
.outcome-badge{font-family:var(--mono);font-size:.78rem;font-weight:700;
  padding:.32rem .85rem;border-radius:6px;border:1px solid;display:inline-block;margin-bottom:.4rem}
.oc-confirmed      {background:rgba(0,122,99,.1);border-color:var(--g);color:var(--g)}
.oc-held_for_review{background:rgba(180,83,9,.1);border-color:var(--y);color:var(--y)}
.oc-cancelled      {background:rgba(220,78,42,.1);border-color:var(--o);color:var(--o)}
.tool-item{background:var(--bg);border:1px solid var(--border);border-radius:6px;
  padding:.5rem .65rem;margin-bottom:.32rem}
.tool-name{color:var(--y);font-family:var(--mono);font-size:.68rem;font-weight:700;margin-bottom:.15rem}
.tool-desc{font-size:.7rem;color:var(--m);line-height:1.5}
.ord-table{width:100%;border-collapse:collapse;font-size:.74rem}
.ord-table th{font-family:var(--mono);font-size:.6rem;letter-spacing:.08em;text-align:left;
  padding:.38rem .5rem;border-bottom:1px solid var(--border);color:var(--m);background:var(--surface)}
.ord-table td{padding:.38rem .5rem;border-bottom:1px solid var(--border2);
  font-family:var(--mono);font-size:.67rem;color:var(--m)}
.ord-table tbody tr:hover td{background:var(--bg)}
.st-confirmed{color:var(--g)}.st-held_for_review{color:var(--y)}
.st-cancelled{color:var(--o)}.st-pending{color:var(--b)}
.prod-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(120px,1fr));gap:.4rem}
.prod-item{background:var(--bg);border:1px solid var(--border);border-radius:6px;
  padding:.45rem .55rem;cursor:pointer;transition:border-color .15s}
.prod-item:hover{border-color:var(--accent)}
.prod-item.selected{border-color:var(--accent);background:rgba(37,99,235,.05)}
.prod-name{font-size:.72rem;font-weight:600;line-height:1.3;margin-bottom:.15rem}
.prod-price{font-family:var(--mono);font-size:.68rem;color:var(--g)}
.prod-stock{font-family:var(--mono);font-size:.62rem}
.stock-ok{color:var(--g)}.stock-low{color:var(--y)}.stock-out{color:var(--o)}
#theme-toggle{position:fixed;bottom:18px;left:18px;z-index:9999;
  width:34px;height:34px;border-radius:50%;background:var(--card);
  border:1px solid var(--border);font-size:16px;cursor:pointer;
  display:flex;align-items:center;justify-content:center;
  box-shadow:0 2px 6px rgba(0,0,0,.12);transition:border-color .15s}
#theme-toggle:hover{border-color:var(--accent)}
</style>
</head>
<body>
<button id="theme-toggle" onclick="toggleTheme()" title="Toggle light / dark theme">
  <span id="theme-icon">🌙</span>
</button>
<div id="llm-banner" class="llm-banner">
  <span class="llm-dot llm-mock"></span><span class="llm-name">Loading...</span>
</div>
<header>
  <div>
    <div class="logo">E-Commerce Agent Platform <span>— Order Pipeline</span></div>
    <div style="font-family:var(--mono);font-size:.65rem;color:var(--m);margin-top:.18rem">
      SDK tools + Harness sessions + A2A protocol + 4 memory stores — end-to-end order fulfilment
    </div>
  </div>
  <div class="badges">
    <span class="badge" style="border-color:var(--b);color:var(--b)">SDK</span>
    <span class="badge" style="border-color:var(--g);color:var(--g)">Harness</span>
    <span class="badge" style="border-color:var(--p);color:var(--p)">A2A</span>
    <span class="badge" style="border-color:var(--y);color:var(--y)">Memory</span>
    <span class="badge" style="border-color:var(--m);color:var(--m)">port 8007</span>
  </div>
</header>

<main>
<!-- LEFT -->
<div>
  <div class="panel" style="margin-bottom:.75rem">
    <div class="phdr" style="color:var(--text)">ORDER BUILDER</div>
    <div class="pbody">
      <div class="section-lbl">Customer</div>
      <div id="cust-list"></div>
      <div class="section-lbl" style="margin-top:.75rem">Products — click to add to cart</div>
      <div class="prod-grid" id="prod-grid"></div>
      <div class="section-lbl" style="margin-top:.65rem">Cart</div>
      <div id="cart-display" style="font-family:var(--mono);font-size:.7rem;color:var(--m);
        min-height:32px;background:var(--bg);border:1px solid var(--border);
        border-radius:6px;padding:.4rem .6rem">Empty — click products above</div>
      <button class="btn-run" id="run-btn" onclick="runPipeline()" style="margin-top:.5rem">Run Order Pipeline</button>
      <button class="btn-seed" onclick="seedData()" style="margin-top:.4rem">Seed 3 Sample Orders</button>
    </div>
  </div>
  <div class="panel">
    <div class="phdr" style="color:var(--y)">SDK TOOL REGISTRY</div>
    <div class="pbody" id="tool-list"></div>
  </div>
</div>

<!-- CENTRE -->
<div>
  <div class="panel" style="margin-bottom:.75rem">
    <div class="phdr" style="color:var(--p)">A2A AGENT PIPELINE
      <span id="pipeline-status" style="font-size:.65rem;color:var(--m)">idle</span>
    </div>
    <div class="pbody">
      <div class="agent-flow">
        <div class="af-agent af-pending" id="af-validation">Validation</div>
        <span class="af-arrow">→</span>
        <div class="af-agent af-pending" id="af-fulfilment">Fulfilment</div>
        <span class="af-arrow">→</span>
        <div class="af-agent af-pending" id="af-pricing">Pricing</div>
        <span class="af-arrow">→</span>
        <div class="af-agent af-pending" id="af-dispatch">Dispatch</div>
        <span id="session-tag" style="margin-left:auto;font-family:var(--mono);font-size:.62rem;color:var(--m)"></span>
      </div>
      <div id="outcome-result"></div>
      <div id="stream"></div>
    </div>
  </div>
  <div class="panel">
    <div class="phdr" style="color:var(--p)">A2A AGENT CARDS</div>
    <div class="pbody" id="agent-cards"></div>
  </div>
</div>

<!-- RIGHT -->
<div>
  <div class="panel">
    <div class="phdr" style="color:var(--g)">ORDER HISTORY</div>
    <div class="pbody" style="padding:.5rem;overflow-x:auto">
      <table class="ord-table">
        <thead><tr><th>ID</th><th>Customer</th><th>Total</th><th>Status</th></tr></thead>
        <tbody id="ord-tbody">
          <tr><td colspan="4" style="text-align:center;color:var(--m);padding:.5rem">No orders yet</td></tr>
        </tbody>
      </table>
    </div>
  </div>
</div>

<!-- MEMORY STORES — full width -->
<div class="panel full-row">
  <div class="phdr" style="color:var(--g)">MEMORY STORES — LIVE ACTIVITY</div>
  <div class="pbody">
    <div class="mem-grid">
      <div class="mem-box ctx">
        <div class="mem-lbl">IN-CONTEXT</div>
        <div class="mem-val" id="ctx-turns" style="color:var(--b)">0</div>
        <div class="mem-sub" id="ctx-sub">/ 10 turns</div>
        <div class="mem-list" id="ctx-list"></div>
      </div>
      <div class="mem-box epi">
        <div class="mem-lbl">EPISODIC (SQLite)</div>
        <div class="mem-val" id="epi-count" style="color:var(--g)">0</div>
        <div class="mem-sub">order events</div>
        <div class="mem-list" id="epi-list"></div>
      </div>
      <div class="mem-box sem">
        <div class="mem-lbl">SEMANTIC (ChromaDB)</div>
        <div class="mem-val" id="sem-count" style="color:var(--p)">0</div>
        <div class="mem-sub">policies + products</div>
        <div class="mem-list" id="sem-list">Policy KB + product catalogue</div>
      </div>
      <div class="mem-box wrk">
        <div class="mem-lbl">WORKING (Redis)</div>
        <div class="mem-val" id="wrk-count" style="color:var(--y)">0</div>
        <div class="mem-sub">active cache keys</div>
        <div class="mem-list" id="wrk-list"></div>
      </div>
    </div>
  </div>
</div>
</main>

<script>
// Theme
(function(){
  var s=localStorage.getItem('theme')||'light';
  document.documentElement.setAttribute('data-theme',s);
  var ic=document.getElementById('theme-icon');
  if(ic)ic.innerHTML=s==='dark'?'&#9728;':'🌙';
})();
function toggleTheme(){
  var c=document.documentElement.getAttribute('data-theme')||'light';
  var n=c==='dark'?'light':'dark';
  document.documentElement.setAttribute('data-theme',n);
  localStorage.setItem('theme',n);
  var ic=document.getElementById('theme-icon');
  if(ic)ic.innerHTML=n==='dark'?'&#9728;':'🌙';
}

// LLM Banner
async function loadBanner(){
  try{
    var d=await fetch('/api/llm/status').then(r=>r.json());
    var b=document.getElementById('llm-banner');
    var cls=d.mock?'llm-mock':'llm-'+d.backend;
    b.innerHTML='<span class="llm-dot '+cls+'"></span>'
      +'<span class="llm-name">'+(d.mock?'MOCK MODE':d.backend.toUpperCase())+'</span>'
      +(d.model&&!d.mock?'<span class="llm-model">/ '+d.model+'</span>':'')
      +'<span class="llm-tag">'+(d.mock?'No Ollama / API key':'Live')+'</span>'
      +'<span style="margin-left:.5rem;font-family:var(--mono);font-size:.63rem;color:var(--m)">E-Commerce Order Pipeline</span>';
  }catch(e){}
}
loadBanner();setInterval(loadBanner,30000);

// Customers
let selectedCust='C001';
async function loadCustomers(){
  var d=await fetch('/api/customers').then(r=>r.json());
  document.getElementById('cust-list').innerHTML=d.customers.map(c=>`
    <div class="cust-item${c.id===selectedCust?' active':''}" onclick="selectCust('${c.id}',this)">
      <div class="cust-name">${c.name}${c.flagged?' [FLAGGED]':''}</div>
      <div class="cust-meta">
        <span class="tier-${c.tier}">${c.tier.toUpperCase()}</span>
        <span>${c.orders_ytd} orders</span>
        <span>${c.loyalty_pts} pts</span>
      </div>
    </div>`).join('');
}
function selectCust(id,el){
  selectedCust=id;
  document.querySelectorAll('.cust-item').forEach(x=>x.classList.remove('active'));
  el.classList.add('active');
}
loadCustomers();

// Products & cart
let cart=[];
async function loadProducts(){
  var d=await fetch('/api/products').then(r=>r.json());
  document.getElementById('prod-grid').innerHTML=d.products.map(p=>`
    <div class="prod-item" id="prod-${p.sku}" onclick="toggleProduct('${p.sku}')">
      <div class="prod-name">${p.name.split(' ').slice(0,3).join(' ')}</div>
      <div class="prod-price">£${p.price.toFixed(2)}</div>
      <div class="prod-stock ${p.stock===0?'stock-out':p.stock<5?'stock-low':'stock-ok'}">
        ${p.stock===0?'Out of stock':p.stock<5?'Low stock '+p.stock:p.stock+' in stock'}
      </div>
    </div>`).join('');
}
function toggleProduct(sku){
  var idx=cart.findIndex(i=>i.sku===sku);
  if(idx>=0){ cart.splice(idx,1); document.getElementById('prod-'+sku).classList.remove('selected'); }
  else if(cart.length<3){ cart.push({sku,qty:1}); document.getElementById('prod-'+sku).classList.add('selected'); }
  renderCart();
}
function renderCart(){
  var el=document.getElementById('cart-display');
  if(!cart.length){ el.textContent='Empty — click products above'; return; }
  el.innerHTML=cart.map(i=>
    `<span style="color:var(--text)">${i.sku}</span> x${i.qty} &nbsp;`).join(' | ');
}
loadProducts();

// Tools & agents
async function loadTools(){
  var d=await fetch('/api/tools').then(r=>r.json());
  document.getElementById('tool-list').innerHTML=d.tools.map(t=>`
    <div class="tool-item">
      <div class="tool-name">@tool ${t.name}()</div>
      <div class="tool-desc">${t.description}</div>
    </div>`).join('');
}
loadTools();
async function loadAgents(){
  var d=await fetch('/api/agents').then(r=>r.json());
  document.getElementById('agent-cards').innerHTML=d.agents.map(a=>`
    <div style="margin-bottom:.45rem;background:var(--bg);border:1px solid var(--border);border-radius:7px;padding:.5rem .7rem">
      <div style="font-family:var(--mono);font-size:.68rem;font-weight:700;color:var(--p);margin-bottom:.18rem">${a.name}</div>
      <div style="font-size:.7rem;color:var(--m);line-height:1.5">${a.description}</div>
      <div style="margin-top:.25rem;display:flex;flex-wrap:wrap;gap:.22rem">
        ${a.skills.map(s=>`<span style="font-family:var(--mono);font-size:.58rem;padding:.1rem .38rem;border-radius:3px;border:1px solid var(--border);color:var(--m)">${s}</span>`).join('')}
      </div>
    </div>`).join('');
}
loadAgents();

// Orders
async function loadOrders(){
  var d=await fetch('/api/orders').then(r=>r.json());
  var tb=document.getElementById('ord-tbody');
  if(!d.orders.length){
    tb.innerHTML='<tr><td colspan="4" style="color:var(--m);text-align:center;padding:.5rem">No orders yet</td></tr>';
    return;
  }
  tb.innerHTML=d.orders.map(o=>`<tr>
    <td>${o.id}</td>
    <td>${o.customer_name.split(' ')[0]}</td>
    <td>£${o.total.toFixed(2)}</td>
    <td class="st-${o.status}">${o.status.replace(/_/g,' ').toUpperCase()}</td>
  </tr>`).join('');
}

// Memory
let currentOrder=null;
async function refreshMemory(){
  var ctx=await fetch('/api/memory/context').then(r=>r.json());
  document.getElementById('ctx-turns').textContent=ctx.count;
  document.getElementById('ctx-sub').textContent='/ '+ctx.limit+' turns';
  document.getElementById('ctx-list').innerHTML=
    ctx.items.slice(-3).map(m=>`<div>${m.role}: ${m.content.slice(0,50)}...</div>`).join('')||'empty';
  if(currentOrder){
    var ev=await fetch('/api/events/'+currentOrder).then(r=>r.json());
    document.getElementById('epi-count').textContent=ev.events.length;
    document.getElementById('epi-list').innerHTML=
      ev.events.slice(-3).map(e=>`<div>${e.agent}: ${e.event}</div>`).join('');
  }
  var wk=await fetch('/api/memory/working').then(r=>r.json());
  document.getElementById('wrk-count').textContent=wk.items.length;
  document.getElementById('wrk-list').innerHTML=
    wk.items.slice(0,4).map(i=>`
      <div style="display:flex;justify-content:space-between">
        <span>${i.key.replace('ec:','')}</span>
        <span style="color:var(--y)">${i.ttl}s</span>
      </div>`).join('')||'empty';
}

function setAgent(id,cls){
  var el=document.getElementById('af-'+id);
  if(el)el.className='af-agent '+cls;
}

function addEv(d){
  var stream=document.getElementById('stream');
  var div=document.createElement('div');
  div.className='ev ev-'+d.kind;
  var label=d.msg||(d.result?String(d.result).slice(0,100):'');
  var detail=(d.msg&&d.result)
    ?'<div class="ev-result">'+String(d.result).slice(0,180)+'</div>':'';
  div.innerHTML='<span class="ev-ts">'+(d.ts||'')+'</span>'
    +'<span class="ev-kind">['+d.kind.replace(/_/g,' ')+']</span>'
    +'<div style="flex:1"><span class="ev-msg">'+label+'</span>'+detail+'</div>';
  stream.appendChild(div);
  stream.scrollTop=stream.scrollHeight;
  if(d.kind==='a2a_request'&&d.agent)
    ['validation','fulfilment','pricing','dispatch'].forEach(a=>{
      if(a===d.agent)setAgent(a,'af-agent af-active');
    });
  if(d.kind==='a2a_response'&&d.agent)setAgent(d.agent,'af-agent af-complete');
  if(d.kind==='harness_session')
    document.getElementById('session-tag').textContent='Session '+d.session;
  if(d.kind==='memory')setTimeout(refreshMemory,300);
}

async function runPipeline(){
  if(!cart.length){alert('Add at least one product to the cart.');return;}
  var btn=document.getElementById('run-btn');
  var stream=document.getElementById('stream');
  btn.disabled=true;stream.innerHTML='';
  document.getElementById('outcome-result').innerHTML='';
  ['validation','fulfilment','pricing','dispatch'].forEach(a=>setAgent(a,'af-agent af-pending'));
  document.getElementById('pipeline-status').textContent='running...';
  document.getElementById('session-tag').textContent='';
  currentOrder=null;
  var url='/api/run?customer_id='+selectedCust
    +'&sku1='+cart[0].sku+'&qty1='+cart[0].qty
    +(cart[1]?'&sku2='+cart[1].sku+'&qty2='+cart[1].qty:'');
  var es=new EventSource(url);
  es.onmessage=e=>{
    var d=JSON.parse(e.data);
    addEv(d);
    if(d.kind==='memory'&&d.store==='semantic')
      document.getElementById('sem-count').textContent=
        (parseInt(document.getElementById('sem-count').textContent)||0)+1;
    if(d.kind==='done'){
      currentOrder=d.order_id;
      es.close();btn.disabled=false;
      document.getElementById('pipeline-status').textContent='complete';
      var oc=d.outcome.toLowerCase().replace(/ /g,'_');
      document.getElementById('outcome-result').innerHTML=
        '<div style="margin-bottom:.55rem">'
        +'<span class="outcome-badge oc-'+oc+'">'+d.outcome+'</span>'
        +'<div style="font-size:.78rem;color:var(--m);line-height:1.65;margin-top:.28rem">'+d.results.dispatch+'</div>'
        +'<div style="font-family:var(--mono);font-size:.62rem;color:var(--m);margin-top:.25rem">'
        +'£'+d.final_total.toFixed(2)+' total &nbsp;|&nbsp; £'+d.saving.toFixed(2)+' saved'
        +' &nbsp;|&nbsp; '+d.agents_used+' agents &nbsp;|&nbsp; '+d.tools_called+' tools'
        +' &nbsp;|&nbsp; '+d.memory_stores+' memory stores'
        +'</div></div>';
      refreshMemory();loadOrders();
    }
  };
  es.onerror=()=>{es.close();btn.disabled=false;
    document.getElementById('pipeline-status').textContent='error';};
}

async function seedData(){
  var btn=event.target;btn.disabled=true;btn.textContent='Seeding...';
  await fetch('/api/seed');
  btn.textContent='Seed 3 Sample Orders';btn.disabled=false;
  loadOrders();
}

setInterval(refreshMemory,8000);
loadOrders();
</script>
</body>
</html>"""
