"""E-Commerce order processing pipeline."""

import asyncio
import json
import time
import uuid
from datetime import datetime
from typing import AsyncGenerator

from prometheus_client import Counter, Histogram

from llm import LLMBackend
from memory import MemoryManager
from agents import A2A_AGENTS, get_mock_response
from tools import (
    get_customer,
    check_inventory,
    apply_promotions,
    calculate_shipping,
    run_fraud_check,
    search_policies,
)
from data import PRODUCTS, WAREHOUSES

# Metrics
PIPELINE_RUNS = Counter("ecommerce_pipeline_runs_total", "Total order pipeline runs")
PIPELINE_DURATION = Histogram("ecommerce_pipeline_duration_seconds", "Overall pipeline duration")
AGENT_LATENCY = Histogram("ecommerce_agent_duration_seconds", "Per-agent duration", ["agent"])
STAGE_EXECUTIONS = Counter("ecommerce_pipeline_stage_executions_total", "Pipeline stage executions", ["stage", "status"])
STAGE_DURATION = Histogram("ecommerce_pipeline_stage_duration_seconds", "Pipeline stage duration", ["stage"])
TOOL_CALLS = Counter("ecommerce_agent_tool_calls_total", "Tool calls by agent", ["agent", "tool"])
TOOL_CALL_DURATION = Histogram("ecommerce_agent_tool_call_duration_seconds", "Tool call duration", ["agent", "tool"])

# Timing tracking
_agent_timings = {}
_tool_timings = {}


def _ev(kind: str, **kw) -> str:
    """Create SSE event."""
    return f"data: {json.dumps({'kind': kind, 'ts': datetime.utcnow().strftime('%H:%M:%S'), **kw})}\n\n"


async def run_pipeline(
    order_id: str,
    customer: dict,
    cart: list[dict],
    llm: LLMBackend,
    memory: MemoryManager,
) -> AsyncGenerator[str, None]:
    """
    Run the e-commerce order processing pipeline.
    
    Args:
        order_id: Order ID
        customer: Customer data
        cart: Cart items
        llm: LLM backend
        memory: Memory manager
        
    Yields:
        SSE events
    """
    pipeline_start = time.perf_counter()
    PIPELINE_RUNS.inc()
    c = customer
    
    # Track stage timings
    stage_timings = {}

    # Compute totals from cart
    subtotal = sum(
        i["qty"] * next((p["price"] for p in PRODUCTS if p["sku"] == i["sku"]), 0)
        for i in cart
    )
    primary_warehouse = next(
        (p["warehouse"] for p in PRODUCTS if p["sku"] == cart[0]["sku"]),
        "LDN-EAST",
    )

    # ── S1 Initialiser ────────────────────────────────────────────────────────
    s1_start = time.perf_counter()
    yield _ev(
        "harness_session",
        session=1,
        type="INITIALIZER",
        msg=f"Harness initialised. Order {order_id}: {len(cart)} item(s), subtotal £{subtotal:.2f}.",
    )

    order_data = {
        "id": order_id,
        "customer_id": c["id"],
        "customer_name": c["name"],
        "items": json.dumps(cart),
        "subtotal": subtotal,
        "discount": 0,
        "shipping": 0,
        "total": subtotal,
        "status": "pending",
        "warehouse": primary_warehouse,
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
    }
    memory.episodic.upsert_order(order_data)
    memory.episodic.log_event(
        order_id, 1, "harness", "order_created", f"£{subtotal:.2f} | {len(cart)} items", "pending"
    )
    yield _ev(
        "memory",
        store="episodic",
        op="write",
        msg=f"[Episodic] Order {order_id} logged to SQLite audit trail",
    )
    await asyncio.sleep(0.3)

    # Seed KB on first run
    if memory.semantic.is_ready() and memory.semantic.count() == 0:
        from data import POLICIES
        for policy in POLICIES:
            memory.semantic.add(policy, {"source": "policy"})
        for p in PRODUCTS:
            memory.semantic.add(
                f"{p['name']} — {p['category']}, £{p['price']}, SKU {p['sku']}",
                {"source": "catalogue", "sku": p["sku"]},
            )
        yield _ev(
            "memory",
            store="semantic",
            op="write",
            msg=f"[Semantic] {len(POLICIES)} policies + {len(PRODUCTS)} products indexed in ChromaDB",
        )
        await asyncio.sleep(0.3)

    memory.context.add("system", f"Order {order_id} for {c['name']} ({c['tier']} tier). Cart: {cart}.")
    memory.context.add("user", f"Process order. Items: {[i['sku'] for i in cart]}. Subtotal: £{subtotal:.2f}.")
    yield _ev(
        "memory",
        store="context",
        op="write",
        msg=f"[In-Context] Session started — {memory.context.count()}/{memory.context.limit} turns",
        turns=memory.context.count(),
        limit=memory.context.limit,
    )
    await asyncio.sleep(0.3)
    
    # Record S1 completion
    s1_duration = time.perf_counter() - s1_start
    stage_timings["initialiser"] = s1_duration
    STAGE_DURATION.labels(stage="initialiser").observe(s1_duration)
    STAGE_EXECUTIONS.labels(stage="initialiser", status="completed").inc()

    # ── S2 Validation Agent ───────────────────────────────────────────────────
    s2_start = time.perf_counter()
    yield _ev(
        "harness_session",
        session=2,
        type="CODING_AGENT",
        msg="Progress: stage=validation. Dispatching via A2A.",
    )
    yield _ev(
        "a2a_discover",
        agent="validation",
        card={
            "name": A2A_AGENTS["validation"]["name"],
            "skills": A2A_AGENTS["validation"]["skills"],
        },
        msg="[A2A] Discovered Validation Agent Card",
    )
    await asyncio.sleep(0.2)

    t0 = time.perf_counter()

    # SDK tools
    yield _ev("sdk_tool", tool="get_customer", args={"customer_id": c["id"]}, msg="[SDK] @tool: get_customer()")
    tool_start = time.perf_counter()
    profile = get_customer(c["id"])
    tool_duration = time.perf_counter() - tool_start
    TOOL_CALLS.labels(agent="validation", tool="get_customer").inc()
    TOOL_CALL_DURATION.labels(agent="validation", tool="get_customer").observe(tool_duration)
    yield _ev(
        "sdk_result",
        tool="get_customer",
        result=f"Tier: {profile.get('tier')} | Orders YTD: {profile.get('orders_ytd')} | Flagged: {profile.get('flagged')}",
    )
    await asyncio.sleep(0.2)

    inventory_results = []
    all_available = True
    for item in cart:
        yield _ev(
            "sdk_tool",
            tool="check_inventory",
            args={"sku": item["sku"], "qty": item["qty"]},
            msg=f"[SDK] @tool: check_inventory({item['sku']} x{item['qty']})",
        )
        tool_start = time.perf_counter()
        inv = check_inventory(item["sku"], item["qty"])
        tool_duration = time.perf_counter() - tool_start
        TOOL_CALLS.labels(agent="validation", tool="check_inventory").inc()
        TOOL_CALL_DURATION.labels(agent="validation", tool="check_inventory").observe(tool_duration)
        inventory_results.append(inv)
        if not inv.get("available", False):
            all_available = False
        yield _ev(
            "sdk_result",
            tool="check_inventory",
            result=f"{inv.get('name', '?')} — stock:{inv.get('stock', 0)} available:{inv.get('available')}",
        )
        await asyncio.sleep(0.15)

    yield _ev(
        "sdk_tool",
        tool="run_fraud_check",
        args={"customer_id": c["id"], "order_total": subtotal},
        msg="[SDK] @tool: run_fraud_check()",
    )
    tool_start = time.perf_counter()
    fraud = run_fraud_check(c["id"], subtotal)
    tool_duration = time.perf_counter() - tool_start
    TOOL_CALLS.labels(agent="validation", tool="run_fraud_check").inc()
    TOOL_CALL_DURATION.labels(agent="validation", tool="run_fraud_check").observe(tool_duration)
    yield _ev(
        "sdk_result",
        tool="run_fraud_check",
        result=f"Score:{fraud['fraud_score']} Flags:{len(fraud['flags'])} AutoApprove:{fraud['auto_approve']}",
    )
    await asyncio.sleep(0.2)

    val_msg = (
        f"Customer {c['name']} (tier:{c['tier']}, flagged:{c['flagged']}, "
        f"orders_ytd:{c['orders_ytd']}). "
        f"Cart: {len(cart)} items, all_available:{all_available}. "
        f"Fraud score:{fraud['fraud_score']}, flags:{fraud['flags'][:2]}."
    )
    yield _ev(
        "a2a_request",
        agent="validation",
        method="tasks/send",
        msg="[A2A] tasks/send → Validation Agent",
        payload=val_msg[:130],
    )
    await asyncio.sleep(0.2)

    llm_response = await llm.call(A2A_AGENTS["validation"]["system_prompt"], val_msg, 120)
    val_out = llm_response or get_mock_response(
        "validation",
        {
            "customer_name": c["name"],
            "tier": c["tier"],
            "fraud_requires_review": fraud["requires_review"],
            "fraud_flags": len(fraud["flags"]),
            "fraud_flag_detail": fraud["flags"][0] if fraud["flags"] else "",
            "all_available": all_available,
            "item_count": len(cart),
        },
    )
    await asyncio.sleep(0.3)

    memory.context.add("assistant", f"[Validation] {val_out}")
    AGENT_LATENCY.labels(agent="validation").observe(time.perf_counter() - t0)
    memory.episodic.log_event(order_id, 2, "validation", "validation_complete", val_out[:120], "complete")
    memory.working.set(f"{order_id}:fraud_score", str(fraud["fraud_score"]), ttl=600)
    memory.working.set(f"{order_id}:all_available", str(all_available), ttl=600)

    yield _ev("a2a_response", agent="validation", status="completed", result=val_out)
    yield _ev(
        "memory",
        store="working",
        op="write",
        msg="[Working] Fraud score + stock availability cached in Redis (TTL 600s)",
    )
    yield _ev(
        "memory",
        store="context",
        op="write",
        msg=f"[In-Context] {memory.context.count()}/{memory.context.limit} turns",
        turns=memory.context.count(),
        limit=memory.context.limit,
    )
    await asyncio.sleep(0.4)
    
    # Record S2 completion
    s2_duration = time.perf_counter() - s2_start
    stage_timings["validation"] = s2_duration
    STAGE_DURATION.labels(stage="validation").observe(s2_duration)
    STAGE_EXECUTIONS.labels(stage="validation", status="completed").inc()

    # ── S3 Fulfilment Agent ───────────────────────────────────────────────────
    s3_start = time.perf_counter()
    yield _ev(
        "harness_session",
        session=3,
        type="CODING_AGENT",
        msg="Progress: validation=complete. Next: FULFILMENT.",
    )
    yield _ev(
        "a2a_discover",
        agent="fulfilment",
        card={
            "name": A2A_AGENTS["fulfilment"]["name"],
            "skills": A2A_AGENTS["fulfilment"]["skills"],
        },
        msg="[A2A] Discovered Fulfilment Agent Card",
    )
    await asyncio.sleep(0.2)

    t0 = time.perf_counter()

    # KB lookup
    yield _ev(
        "memory",
        store="semantic",
        op="read",
        msg=f"[Semantic] Querying ChromaDB: 'shipping policy gold tier fulfilment'",
    )
    policies = search_policies(f"shipping fulfilment {c['tier']} tier warehouse")
    yield _ev(
        "memory",
        store="semantic",
        op="result",
        result=policies[0][:90] if policies else "No policy found",
        msg=f"[Semantic] {len(policies)} policy article(s) retrieved",
    )
    await asyncio.sleep(0.2)

    # Cached fraud score
    cached_fraud = memory.working.get(f"{order_id}:fraud_score")
    yield _ev(
        "memory",
        store="working",
        op="read",
        msg=f"[Working] Cache read: '{order_id}:fraud_score' → {cached_fraud or 'miss'}",
    )
    await asyncio.sleep(0.15)

    total_weight = sum(
        next((p["weight_kg"] for p in PRODUCTS if p["sku"] == i["sku"]), 0) * i["qty"]
        for i in cart
    )
    tool_start = time.perf_counter()
    ship = calculate_shipping(primary_warehouse, c["address"][-3:], total_weight, subtotal)
    tool_duration = time.perf_counter() - tool_start
    TOOL_CALLS.labels(agent="fulfilment", tool="calculate_shipping").inc()
    TOOL_CALL_DURATION.labels(agent="fulfilment", tool="calculate_shipping").observe(tool_duration)
    yield _ev(
        "sdk_tool",
        tool="calculate_shipping",
        args={"warehouse": primary_warehouse, "weight_kg": total_weight},
        msg="[SDK] @tool: calculate_shipping()",
    )
    yield _ev(
        "sdk_result",
        tool="calculate_shipping",
        result=f"Standard: £{ship['standard_cost']} | Free: {ship['free_shipping']} | ETA: {ship['estimated_days']}d",
    )
    await asyncio.sleep(0.2)

    ful_msg = (
        f"Warehouse {primary_warehouse} (cap:{ship['capacity_pct']}%, "
        f"cutoff:{ship['dispatch_cutoff']}, nextday:{ship.get('estimated_days', 2) == 1}). "
        f"Weight:{total_weight:.1f}kg. Shipping: £{ship['standard_cost']}. "
        f"Policy: {policies[0][:80] if policies else 'standard'}"
    )
    yield _ev(
        "a2a_request",
        agent="fulfilment",
        method="tasks/send",
        msg="[A2A] tasks/send → Fulfilment Agent",
        payload=ful_msg[:130],
    )
    await asyncio.sleep(0.2)

    llm_response = await llm.call(A2A_AGENTS["fulfilment"]["system_prompt"], ful_msg, 120)
    ful_out = llm_response or get_mock_response(
        "fulfilment",
        {
            "customer_name": c["name"],
            "tier": c["tier"],
            "warehouse": primary_warehouse,
        },
    )
    await asyncio.sleep(0.3)

    memory.context.add("assistant", f"[Fulfilment] {ful_out}")
    AGENT_LATENCY.labels(agent="fulfilment").observe(time.perf_counter() - t0)
    memory.episodic.log_event(order_id, 3, "fulfilment", "fulfilment_complete", ful_out[:120], "complete")
    memory.working.set(f"{order_id}:warehouse", primary_warehouse, ttl=600)
    memory.working.set(f"{order_id}:shipping_cost", str(ship["standard_cost"]), ttl=600)

    yield _ev("a2a_response", agent="fulfilment", status="completed", result=ful_out)
    yield _ev(
        "memory",
        store="working",
        op="write",
        msg="[Working] Warehouse assignment + shipping cost cached",
    )
    await asyncio.sleep(0.4)
    
    # Record S3 completion
    s3_duration = time.perf_counter() - s3_start
    stage_timings["fulfilment"] = s3_duration
    STAGE_DURATION.labels(stage="fulfilment").observe(s3_duration)
    STAGE_EXECUTIONS.labels(stage="fulfilment", status="completed").inc()

    # ── S4 Pricing Agent ──────────────────────────────────────────────────────
    s4_start = time.perf_counter()
    yield _ev(
        "harness_session",
        session=4,
        type="CODING_AGENT",
        msg="Progress: fulfilment=complete. Next: PRICING.",
    )
    yield _ev(
        "a2a_discover",
        agent="pricing",
        card={
            "name": A2A_AGENTS["pricing"]["name"],
            "skills": A2A_AGENTS["pricing"]["skills"],
        },
        msg="[A2A] Discovered Pricing Agent Card",
    )
    await asyncio.sleep(0.2)

    t0 = time.perf_counter()
    primary_category = next((p["category"] for p in PRODUCTS if p["sku"] == cart[0]["sku"]), "General")

    yield _ev(
        "sdk_tool",
        tool="apply_promotions",
        args={"customer_id": c["id"], "subtotal": subtotal, "category": primary_category},
        msg="[SDK] @tool: apply_promotions()",
    )
    tool_start = time.perf_counter()
    promo = apply_promotions(c["id"], subtotal, primary_category)
    tool_duration = time.perf_counter() - tool_start
    TOOL_CALLS.labels(agent="pricing", tool="apply_promotions").inc()
    TOOL_CALL_DURATION.labels(agent="pricing", tool="apply_promotions").observe(tool_duration)
    yield _ev(
        "sdk_result",
        tool="apply_promotions",
        result=f"Code:{promo['promo_code']} Saving:£{promo['saving']} Net:£{promo['final_subtotal']}",
    )
    await asyncio.sleep(0.2)

    ship_cost = float(memory.working.get(f"{order_id}:shipping_cost") or ship["standard_cost"])
    final_total = round(promo["final_subtotal"] + ship_cost, 2)

    price_msg = (
        f"Subtotal £{subtotal:.2f}, promo {promo['promo_code']} saves £{promo['saving']:.2f}. "
        f"After discount: £{promo['final_subtotal']:.2f}. "
        f"Shipping: £{ship_cost:.2f}. "
        f"Customer tier: {c['tier']}. Final total: £{final_total:.2f}."
    )
    yield _ev(
        "a2a_request",
        agent="pricing",
        method="tasks/send",
        msg="[A2A] tasks/send → Pricing Agent",
        payload=price_msg[:130],
    )
    await asyncio.sleep(0.2)

    llm_response = await llm.call(A2A_AGENTS["pricing"]["system_prompt"], price_msg, 120)
    price_out = llm_response or get_mock_response(
        "pricing",
        {
            "customer_name": c["name"],
            "order_total": subtotal,
            "saving": promo["saving"],
            "promo_code": promo["promo_code"],
            "final_total": final_total,
        },
    )
    await asyncio.sleep(0.3)

    memory.context.add("assistant", f"[Pricing] {price_out}")
    AGENT_LATENCY.labels(agent="pricing").observe(time.perf_counter() - t0)
    memory.episodic.log_event(order_id, 4, "pricing", "pricing_complete", price_out[:120], "complete")

    # Context compaction check
    compaction_event = None
    if memory.context.count() >= memory.context.limit - 1:
        before = memory.context.count()
        memory.context.add("system", "[COMPACTION]")
        compaction_event = (before, memory.context.count())

    yield _ev("a2a_response", agent="pricing", status="completed", result=price_out)
    if compaction_event:
        yield _ev(
            "harness_compaction",
            msg=f"[Harness] Context compacted: {compaction_event[0]} → {compaction_event[1]} turns. Session continuity maintained.",
            before=compaction_event[0],
            after=compaction_event[1],
        )
    await asyncio.sleep(0.4)
    
    # Record S4 completion
    s4_duration = time.perf_counter() - s4_start
    stage_timings["pricing"] = s4_duration
    STAGE_DURATION.labels(stage="pricing").observe(s4_duration)
    STAGE_EXECUTIONS.labels(stage="pricing", status="completed").inc()

    # ── S5 Dispatch Agent ─────────────────────────────────────────────────────
    s5_start = time.perf_counter()
    yield _ev(
        "harness_session",
        session=5,
        type="CODING_AGENT",
        msg="Progress: pricing=complete. Final stage: DISPATCH DECISION.",
    )
    yield _ev(
        "a2a_discover",
        agent="dispatch",
        card={
            "name": A2A_AGENTS["dispatch"]["name"],
            "skills": A2A_AGENTS["dispatch"]["skills"],
        },
        msg="[A2A] Discovered Dispatch Agent Card",
    )
    await asyncio.sleep(0.2)

    t0 = time.perf_counter()
    dispatch_msg = (
        f"Order {order_id} for {c['name']} ({c['tier']} tier). "
        f"Validation: {val_out[:80]}. "
        f"Fulfilment: warehouse {primary_warehouse}. "
        f"Final total: £{final_total:.2f} (saved £{promo['saving']:.2f}). "
        f"Fraud score: {cached_fraud or fraud['fraud_score']}. "
        f"All items available: {all_available}."
    )
    yield _ev(
        "a2a_request",
        agent="dispatch",
        method="tasks/send",
        msg="[A2A] tasks/send → Dispatch Agent (final decision)",
        payload=dispatch_msg[:140],
    )
    await asyncio.sleep(0.2)

    llm_response = await llm.call(A2A_AGENTS["dispatch"]["system_prompt"], dispatch_msg, 100)
    dispatch_out = llm_response or get_mock_response(
        "dispatch",
        {
            "customer_name": c["name"],
            "tier": c["tier"],
            "warehouse": primary_warehouse,
            "fraud_requires_review": fraud["requires_review"],
            "all_available": all_available,
            "final_total": final_total,
            "order_id": order_id,
            "saving": promo["saving"],
            "promo_code": promo["promo_code"],
        },
    )
    await asyncio.sleep(0.3)

    # Determine final status
    up = dispatch_out.upper()
    if "CONFIRMED" in up:
        final_status = "confirmed"
    elif "HOLD" in up or "REVIEW" in up:
        final_status = "held_for_review"
    else:
        final_status = "cancelled"

    memory.context.add("assistant", f"[Dispatch] {dispatch_out}")
    AGENT_LATENCY.labels(agent="dispatch").observe(time.perf_counter() - t0)
    memory.episodic.log_event(order_id, 5, "dispatch", "dispatch_complete", dispatch_out[:120], final_status)

    # Store decision in semantic memory
    memory.semantic.add(
        f"Order {order_id}: {c['name']} ({c['tier']}) placed £{final_total:.2f} order. "
        f"Outcome: {final_status}. {dispatch_out[:80]}",
        {"type": "decision", "order_id": order_id, "outcome": final_status},
    )
    yield _ev(
        "memory",
        store="semantic",
        op="write",
        msg="[Semantic] Order outcome stored in ChromaDB for future pattern matching",
    )

    order_data["discount"] = promo["saving"]
    order_data["shipping"] = ship_cost
    order_data["total"] = final_total
    order_data["status"] = final_status
    order_data["updated_at"] = datetime.utcnow().isoformat()
    memory.episodic.upsert_order(order_data)
    memory.working.set(f"{order_id}:final_status", final_status, ttl=3600)

    yield _ev("a2a_response", agent="dispatch", status="completed", result=dispatch_out)
    yield _ev(
        "memory",
        store="episodic",
        op="write",
        msg=f"[Episodic] Final status ({final_status.upper()}) persisted to SQLite",
    )
    yield _ev(
        "memory",
        store="working",
        op="write",
        msg="[Working] Final status cached in Redis (TTL 1hr) for notification service",
    )
    await asyncio.sleep(0.3)
    
    # Record S5 completion
    s5_duration = time.perf_counter() - s5_start
    stage_timings["dispatch"] = s5_duration
    STAGE_DURATION.labels(stage="dispatch").observe(s5_duration)
    STAGE_EXECUTIONS.labels(stage="dispatch", status=final_status).inc()
    
    # Record overall pipeline duration
    pipeline_duration = time.perf_counter() - pipeline_start
    PIPELINE_DURATION.observe(pipeline_duration)

    yield _ev(
        "done",
        order_id=order_id,
        customer=c["name"],
        customer_id=c["id"],
        customer_tier=c["tier"],
        items=json.dumps(cart),
        subtotal=subtotal,
        discount=promo["saving"],
        shipping=ship_cost,
        final_total=final_total,
        outcome=final_status.upper().replace("_", " "),
        warehouse=primary_warehouse,
        fraud_score=fraud.get("fraud_score", 0),
        fraud_requires_review=fraud.get("requires_review", False),
        fraud_reason=", ".join(fraud.get("flags", [])),
        promo_code=promo["promo_code"],
        promo_saving=promo["saving"],
        validation_reasoning=val_out[:200],
        fulfilment_reasoning=ful_out[:200],
        pricing_reasoning=price_out[:200],
        dispatch_reasoning=dispatch_out[:200],
        sessions=5,
        compactions=1 if compaction_event else 0,
        context_turns=memory.context.count(),
        agents_used=4,
        tools_called=5,
        memory_stores=4,
        results={
            "validation": val_out,
            "fulfilment": ful_out,
            "pricing": price_out,
            "dispatch": dispatch_out,
        },
        msg=f"Pipeline complete. Outcome: {final_status.upper().replace('_', ' ')}.",
    )
