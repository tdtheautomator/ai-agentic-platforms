# Developer Guide — Banking Demo

A comprehensive guide for extending and maintaining the Banking Demo platform. This document covers adding new tools, agents, updating existing components, and managing observability.

---

## Table of Contents

- [Adding New Tools](#adding-new-tools)
- [Adding New Agents](#adding-new-agents)
- [Updating Existing Tools](#updating-existing-tools)
- [Updating Existing Agents](#updating-existing-agents)
- [Updating Harness (Orchestrator)](#updating-harness-orchestrator)
- [Adding New Grafana Dashboards](#adding-new-grafana-dashboards)
- [Adding New Alerts](#adding-new-alerts)
- [Alembic — Database Migrations](#alembic--database-migrations)

---

## Adding New Tools

Tools are the SDK layer that agents use to interact with external systems. They follow a decorator-based registration pattern.

### Step 1: Create a New Tool Module

Create a new file in the appropriate category under `tools/`:

```bash
# Example: Adding a new customer verification tool
touch tools/customer/document_verification.py
```

### Step 2: Implement the Tool Function

```python
# tools/customer/document_verification.py
"""
Document Verification Tool

Verifies customer documents (passport, driver's license, etc.)
"""

from tools.registry import register_tool
from typing import Dict, Any


@register_tool(
    name="verify_customer_documents",
    description="Verify customer identity documents (passport, driver's license, national ID)",
    args_schema={
        "customer_id": {
            "type": "string",
            "description": "Customer ID to verify documents for"
        },
        "document_type": {
            "type": "string",
            "enum": ["passport", "driver_license", "national_id"],
            "description": "Type of document to verify"
        }
    }
)
def verify_customer_documents(customer_id: str, document_type: str) -> Dict[str, Any]:
    """
    Verify customer identity documents.
    
    Args:
        customer_id: Customer ID to verify
        document_type: Type of document (passport, driver_license, national_id)
    
    Returns:
        Dictionary with verification results:
        {
            "verified": bool,
            "document_type": str,
            "expiry_date": str,
            "confidence_score": float,
            "notes": str
        }
    """
    # Dummy implementation — replace with actual verification logic
    import random
    from datetime import datetime, timedelta
    
    verified = random.choice([True, True, False])  # 66% success rate
    expiry = datetime.now() + timedelta(days=random.randint(30, 3650))
    
    return {
        "verified": verified,
        "document_type": document_type,
        "expiry_date": expiry.isoformat(),
        "confidence_score": round(random.uniform(0.7, 1.0), 2),
        "notes": "Document verified successfully" if verified else "Document expired or invalid"
    }
```

### Step 3: Export the Tool

Update `tools/__init__.py` to include your new tool:

```python
# tools/__init__.py
from tools.registry import TOOLS, register_tool

# Import all tools to trigger registration
from tools.customer import get_customer_profile, verify_kyc_documents, verify_customer_documents
from tools.credit import check_credit_score, calculate_affordability
from tools.fraud import scan_transaction_history
from tools.compliance import query_banking_rules

__all__ = [
    # Registry
    "TOOLS",
    "register_tool",
    # Customer tools
    "get_customer_profile",
    "verify_kyc_documents",
    "verify_customer_documents",  # NEW
    # Credit tools
    "check_credit_score",
    "calculate_affordability",
    # Fraud tools
    "scan_transaction_history",
    # Compliance tools
    "query_banking_rules",
]
```

### Step 4: Use the Tool in an Agent

In your agent code, call the tool:

```python
# agents/intake.py
from tools import verify_customer_documents

async def run(self, context: AgentContext) -> str:
    # Call the new tool
    doc_result = verify_customer_documents(
        customer_id=context.customer_id,
        document_type="passport"
    )
    
    if not doc_result["verified"]:
        return f"Document verification failed: {doc_result['notes']}"
    
    # Continue with other logic...
```

### Step 5: Test the Tool

```python
# tests/test_tools.py
import pytest
from tools import verify_customer_documents

def test_verify_customer_documents():
    result = verify_customer_documents(
        customer_id="CUST001",
        document_type="passport"
    )
    
    assert "verified" in result
    assert "document_type" in result
    assert result["document_type"] == "passport"
    assert 0 <= result["confidence_score"] <= 1.0

@pytest.mark.asyncio
async def test_tool_in_pipeline():
    # Test tool execution in the full pipeline
    pass
```

### Step 6: Add Tool Metrics

Update `main.py` to track metrics for your new tool:

```python
# In main.py, add to the tool dispatch section:
t_tool = time.perf_counter()
yield _ev("sdk_tool", tool="verify_customer_documents", 
          args={"customer_id": c["id"], "document_type": "passport"},
          msg="[SDK] @tool: verify_customer_documents()")

doc_result = verify_customer_documents(c["id"], "passport")

TOOL_CALLS.labels(tool_name="verify_customer_documents").inc()
TOOL_LATENCY.labels(tool_name="verify_customer_documents").observe(
    time.perf_counter() - t_tool
)
```

### Tool Registry Reference

The `@register_tool` decorator accepts:

```python
@register_tool(
    name="tool_name",                    # Unique tool identifier
    description="Tool description",      # Human-readable description
    args_schema={                        # JSON Schema for arguments
        "arg_name": {
            "type": "string|number|boolean|array|object",
            "description": "Argument description",
            "enum": ["option1", "option2"],  # Optional: restrict values
            "required": True/False           # Optional: mark as required
        }
    }
)
def my_tool(arg1: str, arg2: int) -> dict:
    pass
```

---

## Adding New Agents

Agents are specialist decision-makers that process context and produce assessments. They follow the A2A (Agent-to-Agent) protocol.

### Step 1: Create Agent Module

```bash
# Create agent directory
mkdir -p agents/compliance
touch agents/compliance/__init__.py
touch agents/compliance/agent.py
```

### Step 2: Implement the Agent

```python
# agents/compliance/agent.py
"""
Compliance Agent

Evaluates regulatory compliance requirements for loan applications.
"""

from __future__ import annotations

import time
from typing import TYPE_CHECKING

import structlog

from agents.base import Agent
from tools import query_banking_rules

if TYPE_CHECKING:
    from agents.context import AgentContext

logger = structlog.get_logger(__name__)


class ComplianceAgent(Agent):
    """
    Compliance Agent for evaluating regulatory requirements.
    
    Checks if loan applications meet regulatory standards:
    - Anti-money laundering (AML) requirements
    - Know-your-customer (KYC) requirements
    - Debt-to-income ratio limits
    - Loan amount thresholds
    """

    def __init__(self):
        super().__init__(
            name="compliance",
            system_prompt=(
                "You are a compliance officer at a retail bank. "
                "Given loan application details and regulatory rules, "
                "write a 2-sentence compliance assessment. "
                "State whether the application meets all regulatory requirements "
                "and flag any compliance concerns. Be direct and factual."
            )
        )

    async def run(self, context: AgentContext) -> str:
        """
        Execute compliance assessment.
        
        Args:
            context: Agent execution context with application data
            
        Returns:
            Compliance assessment as a string
        """
        t0 = time.perf_counter()
        
        try:
            # Query banking rules
            rules = query_banking_rules(
                f"compliance AML KYC loan amount {context.loan_amount}"
            )
            
            # Build compliance message
            compliance_msg = (
                f"Loan: £{context.loan_amount:,} over {context.term_months} months. "
                f"Customer: {context.customer_name}, Income: £{context.annual_income:,}/yr. "
                f"Relevant rules: {rules[0][:120] if rules else 'Standard criteria apply'}. "
                f"DTI: {context.dti_ratio}%. KYC: {'PASS' if context.kyc_pass else 'FAIL'}."
            )
            
            # Call LLM for assessment
            from llm import get_llm_backend
            llm = get_llm_backend()
            
            assessment = await llm.call(
                system=self.system_prompt,
                user=compliance_msg,
                max_tokens=100
            )
            
            duration_ms = (time.perf_counter() - t0) * 1000
            await self._log_execution(context, duration_ms, "success")
            
            return assessment or "Compliance check complete."
            
        except Exception as exc:
            duration_ms = (time.perf_counter() - t0) * 1000
            await self._log_execution(context, duration_ms, "error")
            raise


# Agent definition for A2A discovery
compliance_definition = {
    "id": "compliance",
    "name": "Compliance Agent",
    "description": "Evaluates regulatory compliance requirements for loan applications",
    "skills": ["aml_check", "kyc_verification", "regulatory_compliance"],
    "system_prompt": ComplianceAgent().system_prompt,
}
```

### Step 3: Register the Agent

Update `agents/registry.py`:

```python
# agents/registry.py
from agents.compliance import ComplianceAgent, compliance_definition

# Add to A2A_AGENTS registry
A2A_AGENTS = {
    "intake": {...},
    "risk": {...},
    "fraud": {...},
    "decision": {...},
    "compliance": compliance_definition,  # NEW
}
```

### Step 4: Export the Agent

Update `agents/__init__.py`:

```python
# agents/__init__.py
from agents.compliance import ComplianceAgent, compliance_definition

__all__ = [
    "Agent",
    "AgentContext",
    "A2A_AGENTS",
    "IntakeAgent",
    "RiskAgent",
    "FraudAgent",
    "DecisionAgent",
    "ComplianceAgent",  # NEW
]
```

### Step 5: Integrate into Pipeline

Update `main.py` to include the new agent in the harness:

```python
# In main.py, add to the pipeline after fraud agent:

# ── Harness: Session 5 — Compliance Agent (A2A) ─────────────────
state["session_num"] = 5
yield _ev("harness_session", session=5, type="CODING_AGENT",
          msg="Harness reads progress: fraud=complete. Next: COMPLIANCE CHECK.")

yield _ev("a2a_discover", agent="compliance",
          card={"name": A2A_AGENTS["compliance"]["name"],
                "skills": A2A_AGENTS["compliance"]["skills"]},
          msg="[A2A] Discovered Compliance Agent")

AGENT_CALLS.labels(agent="compliance").inc()
t0 = time.perf_counter()

compliance_msg = (f"Application for {c['name']} (ID: {app_id}). "
                  f"Loan: £{l['amount']:,} over {l['term_months']} months. "
                  f"DTI: {afford['dti_ratio']}%. KYC: {'PASS' if kyc['kyc_pass'] else 'FAIL'}.")

llm_txt = await _call_llm(A2A_AGENTS["compliance"]["system_prompt"], 
                          compliance_msg, max_tokens=100)
compliance_summary = llm_txt or _mock_response("compliance", {...})

ctx_add("assistant", f"[Compliance] {compliance_summary}")
state["results"]["compliance"] = compliance_summary
state["progress"]["compliance"] = "complete"
compliance_duration = time.perf_counter() - t0
state["agent_timings"]["compliance"] = compliance_duration
AGENT_LATENCY.labels(agent="compliance").observe(compliance_duration)

yield _ev("a2a_response", agent="compliance", status="completed", 
          result=compliance_summary)
```

### Step 6: Test the Agent

```python
# tests/test_agents.py
import pytest
from agents import ComplianceAgent
from agents.context import AgentContext

@pytest.mark.asyncio
async def test_compliance_agent():
    agent = ComplianceAgent()
    
    context = AgentContext(
        app_id="TEST-001",
        customer_name="John Doe",
        loan_amount=25000,
        term_months=36,
        annual_income=75000,
        dti_ratio=35.0,
        kyc_pass=True
    )
    
    result = await agent.run(context)
    
    assert isinstance(result, str)
    assert len(result) > 0
```

---

## Updating Existing Tools

### Modifying Tool Logic

```python
# tools/credit/calculate_affordability.py

@register_tool(
    name="calculate_affordability",
    description="Calculate monthly payment and debt-to-income ratio for a loan",
    args_schema={
        "customer_id": {"type": "string"},
        "loan_amount": {"type": "number"},
        "term_months": {"type": "number"}
    }
)
def calculate_affordability(customer_id: str, loan_amount: float, term_months: int) -> dict:
    """
    Updated: Now includes stress-test calculation at +3% interest rate.
    """
    from main import CUSTOMERS
    
    customer = next((c for c in CUSTOMERS if c["id"] == customer_id), None)
    if not customer:
        return {"error": f"Customer {customer_id} not found"}
    
    annual_income = customer["income"]
    monthly_income = annual_income / 12
    
    # Calculate base monthly payment (assume 5% interest rate)
    base_rate = 0.05
    monthly_rate = base_rate / 12
    n_payments = term_months
    
    if monthly_rate == 0:
        monthly_payment = loan_amount / n_payments
    else:
        monthly_payment = loan_amount * (monthly_rate * (1 + monthly_rate) ** n_payments) / \
                         ((1 + monthly_rate) ** n_payments - 1)
    
    # Calculate DTI
    dti_ratio = (monthly_payment / monthly_income) * 100
    
    # NEW: Stress test at +3%
    stress_rate = base_rate + 0.03
    stress_monthly_rate = stress_rate / 12
    stress_payment = loan_amount * (stress_monthly_rate * (1 + stress_monthly_rate) ** n_payments) / \
                    ((1 + stress_monthly_rate) ** n_payments - 1)
    stress_dti = (stress_payment / monthly_income) * 100
    
    return {
        "monthly_payment": round(monthly_payment, 2),
        "dti_ratio": round(dti_ratio, 1),
        "dti_pass": dti_ratio <= 43,
        "stress_payment": round(stress_payment, 2),  # NEW
        "stress_dti": round(stress_dti, 1),          # NEW
        "stress_pass": stress_dti <= 43,              # NEW
    }
```

### Updating Tool Arguments

```python
# Before:
@register_tool(
    name="scan_transaction_history",
    description="Scan customer transaction history for fraud indicators",
    args_schema={
        "customer_id": {"type": "string"}
    }
)

# After: Add date range parameter
@register_tool(
    name="scan_transaction_history",
    description="Scan customer transaction history for fraud indicators",
    args_schema={
        "customer_id": {"type": "string"},
        "days_back": {
            "type": "number",
            "description": "Number of days to look back (default: 30)",
            "default": 30
        },
        "min_amount": {
            "type": "number",
            "description": "Minimum transaction amount to consider",
            "default": 0
        }
    }
)
def scan_transaction_history(customer_id: str, days_back: int = 30, min_amount: float = 0) -> dict:
    # Updated implementation
    pass
```

### Deprecating a Tool

```python
# Mark tool as deprecated
@register_tool(
    name="old_tool",
    description="[DEPRECATED] Use new_tool instead",
    args_schema={...}
)
def old_tool(...):
    """
    DEPRECATED: This tool is no longer maintained.
    Use new_tool() instead.
    """
    import warnings
    warnings.warn("old_tool is deprecated, use new_tool instead", DeprecationWarning)
    # Redirect to new tool
    return new_tool(...)
```

---

## Updating Existing Agents

### Modifying Agent System Prompt

```python
# agents/risk.py

class RiskAgent(Agent):
    def __init__(self):
        super().__init__(
            name="risk",
            system_prompt=(
                "You are a senior credit risk analyst at a retail bank. "
                "Given a credit score, DTI ratio, income, loan amount, and stress-test results, "
                "write a 3-sentence risk assessment (increased from 2 sentences). "  # UPDATED
                "State the risk level (LOW/MEDIUM/HIGH), the primary factor, "
                "and whether stress-test results warrant additional scrutiny. "  # UPDATED
                "Be concise, data-driven, and consider macro-economic factors. "  # UPDATED
                "Do not make a final decision."
            )
        )
```

### Adding New Skills to an Agent

```python
# agents/intake.py

intake_definition = {
    "id": "intake",
    "name": "Intake Agent",
    "description": "Collects and validates the initial loan application",
    "skills": [
        "loan_intake",
        "kyc_verification",
        "affordability_precheck",
        "document_verification",  # NEW
        "income_verification",     # NEW
    ],
    "system_prompt": IntakeAgent().system_prompt,
}
```

### Updating Agent Execution Logic

```python
# agents/fraud.py

class FraudAgent(Agent):
    async def run(self, context: AgentContext) -> str:
        t0 = time.perf_counter()
        
        try:
            # Scan transactions
            tx = scan_transaction_history(
                context.customer_id,
                days_back=90  # UPDATED: increased from 30
            )
            
            # NEW: Check for velocity fraud
            velocity_score = self._calculate_velocity_score(tx)
            
            # NEW: Check device fingerprint
            device_risk = self._check_device_fingerprint(context)
            
            # Build fraud message with new signals
            fraud_msg = (
                f"Transaction history (90 days): {tx['transactions_90d']} total, "
                f"{tx['declined_90d']} declined. "
                f"Velocity score: {velocity_score}/100. "
                f"Device risk: {device_risk}. "
                f"Fraud flags: {tx['fraud_flags']}."
            )
            
            # Call LLM
            llm = get_llm_backend()
            assessment = await llm.call(
                system=self.system_prompt,
                user=fraud_msg,
                max_tokens=100
            )
            
            duration_ms = (time.perf_counter() - t0) * 1000
            await self._log_execution(context, duration_ms, "success")
            
            return assessment
            
        except Exception as exc:
            duration_ms = (time.perf_counter() - t0) * 1000
            await self._log_execution(context, duration_ms, "error")
            raise
    
    def _calculate_velocity_score(self, tx: dict) -> int:
        """Calculate velocity fraud score (0-100)."""
        # NEW METHOD
        declined_rate = (tx['declined_90d'] / max(tx['transactions_90d'], 1)) * 100
        if declined_rate > 30:
            return 85
        elif declined_rate > 15:
            return 60
        else:
            return 30
    
    def _check_device_fingerprint(self, context: AgentContext) -> str:
        """Check device fingerprint against known fraud patterns."""
        # NEW METHOD
        return "LOW" if context.device_id not in context.flagged_devices else "HIGH"
```

---

## Updating Harness (Orchestrator)

The harness manages multi-session workflows. Updates typically involve adding new sessions or modifying session logic.

### Adding a New Session

```python
# main.py

async def _run_pipeline(app_id: str, customer: dict, loan: dict) -> AsyncGenerator[str, None]:
    PIPELINE_RUNS.inc()
    state = _init_session(app_id, customer, loan)
    c = customer
    l = loan
    
    # ... existing sessions 1-5 ...
    
    # ── NEW: Harness: Session 6 — Pricing Agent (A2A) ─────────────────
    state["session_num"] = 6
    yield _ev("harness_session", session=6, type="CODING_AGENT",
              msg="Harness reads progress: decision=complete. Final stage: PRICING.")
    
    yield _ev("a2a_discover", agent="pricing",
              card={"name": A2A_AGENTS["pricing"]["name"],
                    "skills": A2A_AGENTS["pricing"]["skills"]},
              msg="[A2A] Discovered Pricing Agent")
    
    AGENT_CALLS.labels(agent="pricing").inc()
    t0 = time.perf_counter()
    
    pricing_msg = (f"Approved loan for {c['name']}: £{l['amount']:,} over {l['term_months']} months. "
                   f"Credit score: {c['credit_score']}. DTI: {afford['dti_ratio']}%. "
                   f"Calculate appropriate interest rate and offer terms.")
    
    llm_txt = await _call_llm(A2A_AGENTS["pricing"]["system_prompt"], 
                              pricing_msg, max_tokens=150)
    pricing_summary = llm_txt or _mock_response("pricing", {...})
    
    ctx_add("assistant", f"[Pricing] {pricing_summary}")
    state["results"]["pricing"] = pricing_summary
    state["progress"]["pricing"] = "complete"
    pricing_duration = time.perf_counter() - t0
    state["agent_timings"]["pricing"] = pricing_duration
    AGENT_LATENCY.labels(agent="pricing").observe(pricing_duration)
    
    yield _ev("a2a_response", agent="pricing", status="completed", 
              result=pricing_summary)
    
    # ... continue with final summary ...
```

### Modifying Session Logic

```python
# main.py - Update intake session to include new verification

# ── Harness: Session 2 — Intake Agent (A2A) ───────────────────────────
state["session_num"] = 2

# NEW: Add document verification before KYC
t_tool = time.perf_counter()
yield _ev("sdk_tool", tool="verify_customer_documents",
          args={"customer_id": c["id"], "document_type": "passport"},
          msg="[SDK] @tool: verify_customer_documents()")

doc_result = verify_customer_documents(c["id"], "passport")
TOOL_CALLS.labels(tool_name="verify_customer_documents").inc()
TOOL_LATENCY.labels(tool_name="verify_customer_documents").observe(
    time.perf_counter() - t_tool
)

if not doc_result["verified"]:
    yield _ev("sdk_result", tool="verify_customer_documents",
              result=f"Document verification FAILED: {doc_result['notes']}")
    # Could fail the application here
else:
    yield _ev("sdk_result", tool="verify_customer_documents",
              result=f"Document verified with {doc_result['confidence_score']*100:.0f}% confidence")

# ... continue with existing tools ...
```

### Adding Conditional Logic

```python
# main.py - Add conditional session based on risk level

# After fraud session, check if high-risk
risk_level = work_get(f"{app_id}:risk_level") or "MEDIUM"

if risk_level == "HIGH":
    # ── Harness: Session 5A — Manual Review (Conditional) ───────────────
    state["session_num"] = 5
    yield _ev("harness_session", session=5, type="MANUAL_REVIEW",
              msg="HIGH risk detected. Routing to manual review queue.")
    
    # Store for manual review
    work_set(f"{app_id}:manual_review_required", "true", ttl=86400)
    
    yield _ev("done",
              app_id=app_id,
              customer=c["name"],
              decision="MANUAL_REVIEW",
              reason="High-risk application requires manual review",
              msg="Application routed to manual review queue")
else:
    # Continue with normal decision flow
    pass
```

### Updating Session Progress Tracking

```python
# main.py - Update session initialization

def _init_session(app_id: str, customer: dict, loan: dict) -> dict:
    state = {
        "app_id": app_id,
        "session_num": 0,
        "customer": customer,
        "loan": loan,
        "progress": {
            "intake": "pending",
            "risk": "pending",
            "fraud": "pending",
            "compliance": "pending",  # NEW
            "decision": "pending",
        },
        "results": {},
        "context_size": 0,
        "compactions": 0,
        "agent_timings": {
            "intake": 0.0,
            "risk": 0.0,
            "fraud": 0.0,
            "compliance": 0.0,  # NEW
            "decision": 0.0,
        },
        "pipeline_start": time.perf_counter(),
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
    }
    _SESSIONS[app_id] = state
    return state
```

---

## Adding New Grafana Dashboards

Grafana dashboards visualize metrics collected by Prometheus.

### Step 1: Create Dashboard JSON

```bash
# Create dashboard file
touch monitoring/grafana/dashboards/compliance_dashboard.json
```

### Step 2: Define Dashboard Structure

```json
{
  "dashboard": {
    "title": "Compliance Monitoring",
    "description": "Monitor compliance assessments and regulatory requirements",
    "tags": ["banking", "compliance"],
    "timezone": "browser",
    "panels": [
      {
        "id": 1,
        "title": "Compliance Checks by Status",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(banking_compliance_checks_total[5m])",
            "legendFormat": "{{status}}",
            "refId": "A"
          }
        ],
        "yaxes": [
          {
            "format": "short",
            "label": "Checks/sec"
          }
        ]
      },
      {
        "id": 2,
        "title": "Compliance Failures",
        "type": "stat",
        "targets": [
          {
            "expr": "increase(banking_compliance_failures_total[1h])",
            "refId": "A"
          }
        ],
        "thresholds": {
          "mode": "absolute",
          "steps": [
            {
              "color": "green",
              "value": null
            },
            {
              "color": "red",
              "value": 5
            }
          ]
        }
      },
      {
        "id": 3,
        "title": "Compliance Agent Latency",
        "type": "graph",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, banking_agent_duration_seconds_bucket{agent=\"compliance\"})",
            "legendFormat": "p95",
            "refId": "A"
          }
        ],
        "yaxes": [
          {
            "format": "s",
            "label": "Latency"
          }
        ]
      },
      {
        "id": 4,
        "title": "Compliance Issues by Type",
        "type": "piechart",
        "targets": [
          {
            "expr": "banking_compliance_issues_total",
            "legendFormat": "{{issue_type}}",
            "refId": "A"
          }
        ]
      }
    ]
  }
}
```

### Step 3: Register Dashboard in Provisioning

Update `monitoring/grafana/provisioning/dashboards/dashboards.yaml`:

```yaml
apiVersion: 1

providers:
  - name: 'Banking Dashboards'
    orgId: 1
    folder: ''
    type: file
    disableDeletion: false
    editable: true
    options:
      path: /var/lib/grafana/dashboards

dashboards:
  - name: 'Pipeline Metrics'
    path: /var/lib/grafana/dashboards/pipeline_dashboard.json
  - name: 'Agent Performance'
    path: /var/lib/grafana/dashboards/agent_dashboard.json
  - name: 'Memory Usage'
    path: /var/lib/grafana/dashboards/memory_dashboard.json
  - name: 'Compliance Monitoring'  # NEW
    path: /var/lib/grafana/dashboards/compliance_dashboard.json
```

### Step 4: Add Metrics to Prometheus

First, ensure your metrics are exposed in `main.py`:

```python
# main.py - Add new metrics

from prometheus_client import Counter, Histogram

# Compliance Metrics
COMPLIANCE_CHECKS = Counter(
    "banking_compliance_checks_total",
    "Total compliance checks",
    ["status"]
)
COMPLIANCE_FAILURES = Counter(
    "banking_compliance_failures_total",
    "Total compliance failures by type",
    ["failure_type"]
)
COMPLIANCE_LATENCY = Histogram(
    "banking_compliance_latency_seconds",
    "Compliance check latency"
)
```

### Step 5: Populate Metrics in Code

```python
# main.py - Record compliance metrics

t0 = time.perf_counter()

try:
    compliance_result = await compliance_agent.run(context)
    COMPLIANCE_CHECKS.labels(status="success").inc()
except Exception as exc:
    COMPLIANCE_CHECKS.labels(status="failure").inc()
    COMPLIANCE_FAILURES.labels(failure_type=type(exc).__name__).inc()
finally:
    COMPLIANCE_LATENCY.observe(time.perf_counter() - t0)
```

### Step 6: Reload Grafana

```bash
# Grafana automatically reloads provisioned dashboards
# Or manually reload via API:
curl -X POST http://localhost:3000/api/admin/provisioning/dashboards/reload \
  -H "Authorization: Bearer $GRAFANA_API_TOKEN"
```

---

## Adding New Alerts

Alerts notify operators when metrics exceed thresholds.

### Step 1: Define Alert Rules

Update `monitoring/alert_rules.yml`:

```yaml
groups:
  - name: banking_alerts
    interval: 30s
    rules:
      # Existing alerts...
      
      # NEW: Compliance Alert
      - alert: HighComplianceFailureRate
        expr: |
          (
            increase(banking_compliance_failures_total[5m])
            /
            increase(banking_compliance_checks_total[5m])
          ) > 0.1
        for: 5m
        labels:
          severity: warning
          component: compliance
        annotations:
          summary: "High compliance failure rate ({{ $value | humanizePercentage }})"
          description: |
            Compliance checks are failing at a high rate.
            More than 10% of checks failed in the last 5 minutes.
            
            Current failure rate: {{ $value | humanizePercentage }}
            Dashboard: http://localhost:3000/d/compliance
      
      # NEW: Compliance Agent Timeout
      - alert: ComplianceAgentTimeout
        expr: |
          histogram_quantile(0.95, banking_agent_duration_seconds_bucket{agent="compliance"}) > 30
        for: 5m
        labels:
          severity: critical
          component: compliance
        annotations:
          summary: "Compliance Agent p95 latency exceeds 30s"
          description: |
            The Compliance Agent is experiencing high latency.
            95th percentile latency: {{ $value }}s
            
            This may indicate performance issues or external API delays.
      
      # NEW: Compliance Errors
      - alert: ComplianceAgentErrors
        expr: |
          increase(banking_agent_errors_total{agent="compliance"}[5m]) > 5
        for: 5m
        labels:
          severity: warning
          component: compliance
        annotations:
          summary: "Compliance Agent errors detected"
          description: |
            The Compliance Agent has encountered {{ $value }} errors in the last 5 minutes.
            
            Check logs for details: docker logs agent-banking-demo
```

### Step 2: Add Recording Rules (Optional)

Recording rules pre-compute frequently used expressions:

```yaml
# monitoring/recording_rules.yml

groups:
  - name: banking_recording_rules
    interval: 30s
    rules:
      # Existing rules...
      
      # NEW: Compliance failure rate
      - record: compliance:failure_rate:5m
        expr: |
          (
            increase(banking_compliance_failures_total[5m])
            /
            increase(banking_compliance_checks_total[5m])
          )
      
      # NEW: Compliance agent latency p95
      - record: compliance:agent_latency_p95:5m
        expr: |
          histogram_quantile(0.95, banking_agent_duration_seconds_bucket{agent="compliance"})
```

### Step 3: Configure AlertManager Routing

Update `monitoring/alertmanager.yml`:

```yaml
global:
  resolve_timeout: 5m
  slack_api_url: '${SLACK_WEBHOOK_URL}'

route:
  receiver: 'default'
  group_by: ['alertname', 'cluster', 'service']
  group_wait: 10s
  group_interval: 10s
  repeat_interval: 12h
  
  routes:
    # Route compliance alerts to compliance team
    - match:
        component: compliance
      receiver: 'compliance-team'
      group_wait: 5s
      group_interval: 5s
      repeat_interval: 1h
    
    # Route critical alerts immediately
    - match:
        severity: critical
      receiver: 'pagerduty'
      group_wait: 0s
      repeat_interval: 5m

receivers:
  - name: 'default'
    slack_configs:
      - channel: '#alerts'
        title: 'Banking Alert'
        text: '{{ range .Alerts }}{{ .Annotations.description }}{{ end }}'
  
  - name: 'compliance-team'
    slack_configs:
      - channel: '#compliance-alerts'
        title: 'Compliance Alert'
        text: '{{ range .Alerts }}{{ .Annotations.description }}{{ end }}'
  
  - name: 'pagerduty'
    pagerduty_configs:
      - service_key: '${PAGERDUTY_SERVICE_KEY}'
        description: '{{ .GroupLabels.alertname }}'
```

### Step 4: Test Alerts

```bash
# Manually trigger an alert for testing
docker exec agent-prometheus-banking promtool check rules /etc/prometheus/alert_rules.yml

# View active alerts
curl http://localhost:9090/api/v1/alerts

# Simulate high failure rate
# Run load test with intentionally failing tools
curl http://localhost:8005/api/generate-traffic/50
```

### Step 5: Monitor Alerts

Access AlertManager dashboard: http://localhost:9093

---

## Alembic — Database Migrations

Alembic manages database schema changes in a version-controlled way.

### What is Alembic?

Alembic is a lightweight database migration tool for SQLAlchemy. It allows you to:

- **Version control** your database schema
- **Track changes** over time
- **Rollback** to previous versions if needed
- **Collaborate** on schema changes without conflicts
- **Automate** schema updates in CI/CD pipelines

### Project Structure

```
alembic/
├── alembic.ini                  # Configuration file
├── env.py                       # Migration environment setup
├── script.py.mako               # Template for new migrations
└── versions/                    # Migration scripts
    ├── 001_initial_schema.py
    ├── 002_add_compliance_table.py
    └── ...
```

### Step 1: Configure Alembic

The `alembic.ini` file contains database connection settings:

```ini
# alembic.ini

[alembic]
# path to migration scripts
script_location = alembic

# template used to generate migration file names
file_template = %%(rev)s_%%(slug)s

# sys.path path, will be prepended to sys.path if present
prepend_sys_path = .

# timezone to use when rendering the date
# within the migration file as well as the filename.
# string value is passed to zoneinfo.ZoneInfo()
# leave blank for localtime
# timezone =

# max length of characters to apply to the
# "slug" field when generating a new migration
# set to 0 to disable, None to read the value from the
# environment variable ALEMBIC_SLUG_SZ
truncate_slug_length = 40

# set to 'true' to run the environment during
# the 'revision' command, regardless of autogenerate
# this is useful for determining just what has changed,
# running "alembic revision --autogenerate" and
# then reviewing and tweaking the newly generated revision
# before applying it to the database; when False, this only
# happens when there are no changes
# always_version = false

# Database connection string
sqlalchemy.url = sqlite:////data/sqlite/banking.db

[loggers]
keys = root,sqlalchemy

[handlers]
keys = console

[formatters]
keys = generic

[logger_root]
level = WARN
handlers = console
qualname =

[logger_sqlalchemy]
level = WARN
handlers =
qualname = sqlalchemy.engine

[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic

[formatter_generic]
format = %(levelname)-5.5s [%(name)s] %(message)s
datefmt = %H:%M:%S
```

### Step 2: Create a New Migration

```bash
# Auto-generate migration based on model changes
alembic revision --autogenerate -m "Add compliance table"

# Or create an empty migration for manual editing
alembic revision -m "Add compliance table"
```

### Step 3: Write Migration Script

```python
# alembic/versions/003_add_compliance_table.py
"""Add compliance table

Revision ID: 003
Revises: 002
Create Date: 2026-05-24 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Upgrade: Create compliance_checks table
    """
    op.create_table(
        'compliance_checks',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('application_id', sa.String(36), nullable=False),
        sa.Column('customer_id', sa.String(36), nullable=False),
        sa.Column('check_type', sa.String(50), nullable=False),
        sa.Column('status', sa.String(20), nullable=False),  # PASS, FAIL, PENDING
        sa.Column('details', sa.Text),
        sa.Column('created_at', sa.DateTime, nullable=False),
        sa.Column('updated_at', sa.DateTime, nullable=False),
    )
    
    # Add indexes
    op.create_index('idx_compliance_app_id', 'compliance_checks', ['application_id'])
    op.create_index('idx_compliance_customer_id', 'compliance_checks', ['customer_id'])
    op.create_index('idx_compliance_status', 'compliance_checks', ['status'])


def downgrade() -> None:
    """
    Downgrade: Drop compliance_checks table
    """
    op.drop_index('idx_compliance_status')
    op.drop_index('idx_compliance_customer_id')
    op.drop_index('idx_compliance_app_id')
    op.drop_table('compliance_checks')
```

### Step 4: Apply Migrations

```bash
# Apply all pending migrations
alembic upgrade head

# Apply specific number of migrations
alembic upgrade +2

# Apply to specific revision
alembic upgrade 003

# Rollback to previous revision
alembic downgrade -1

# Rollback to specific revision
alembic downgrade 002

# View current revision
alembic current

# View migration history
alembic history --verbose
```

### Step 5: Common Migration Patterns

#### Add a Column

```python
def upgrade() -> None:
    op.add_column('loan_applications', 
                  sa.Column('compliance_status', sa.String(20)))

def downgrade() -> None:
    op.drop_column('loan_applications', 'compliance_status')
```

#### Rename a Column

```python
def upgrade() -> None:
    op.alter_column('loan_applications', 'old_name', new_column_name='new_name')

def downgrade() -> None:
    op.alter_column('loan_applications', 'new_name', new_column_name='old_name')
```

#### Add a Constraint

```python
def upgrade() -> None:
    op.create_unique_constraint('uq_app_customer', 'loan_applications', 
                               ['application_id', 'customer_id'])

def downgrade() -> None:
    op.drop_constraint('uq_app_customer', 'loan_applications')
```

#### Add a Foreign Key

```python
def upgrade() -> None:
    op.create_foreign_key('fk_compliance_app', 'compliance_checks', 
                         'loan_applications', ['application_id'], ['id'])

def downgrade() -> None:
    op.drop_constraint('fk_compliance_app', 'compliance_checks')
```

#### Create an Index

```python
def upgrade() -> None:
    op.create_index('idx_loan_status', 'loan_applications', ['status'])

def downgrade() -> None:
    op.drop_index('idx_loan_status')
```

### Step 6: Best Practices

1. **One change per migration** — Keep migrations focused and atomic
2. **Test both directions** — Always test upgrade and downgrade
3. **Write descriptive messages** — Use clear revision messages
4. **Handle data migrations** — Use data() function for complex migrations
5. **Version control** — Commit migrations with your code
6. **Review before applying** — Check migration script before running on production

```python
# Example: Data migration with validation
def upgrade() -> None:
    # Create new column
    op.add_column('loan_applications', sa.Column('new_status', sa.String(20)))
    
    # Migrate data
    connection = op.get_bind()
    connection.execute(
        sa.text(
            "UPDATE loan_applications SET new_status = CASE "
            "  WHEN status = 'approved' THEN 'APPROVED' "
            "  WHEN status = 'declined' THEN 'DECLINED' "
            "  ELSE 'PENDING' "
            "END"
        )
    )
    
    # Drop old column
    op.drop_column('loan_applications', 'status')
    
    # Rename new column
    op.alter_column('loan_applications', 'new_status', new_column_name='status')
```

### Step 7: CI/CD Integration

Run migrations automatically in Docker:

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

# Run migrations before starting app
CMD ["sh", "-c", "alembic upgrade head && uvicorn main:app --host 0.0.0.0 --port 8005"]
```

Or in docker-compose:

```yaml
# docker-compose.yml
services:
  banking-demo:
    build: .
    environment:
      DATABASE_URL: sqlite:////data/sqlite/banking.db
    volumes:
      - banking_sqlite:/data/sqlite
    command: >
      sh -c "alembic upgrade head &&
             uvicorn main:app --host 0.0.0.0 --port 8005"
```

---

## Summary

This developer guide covers the main extension points:

| Task | File | Pattern |
|------|------|---------|
| Add Tool | `tools/{category}/{name}.py` | `@register_tool` decorator |
| Add Agent | `agents/{name}/agent.py` | Inherit from `Agent` base class |
| Update Tool | Modify function in `tools/` | Update args_schema or logic |
| Update Agent | Modify class in `agents/` | Update system_prompt or run() method |
| Update Harness | Edit `main.py` | Add/modify session logic |
| Add Dashboard | `monitoring/grafana/dashboards/` | JSON dashboard definition |
| Add Alert | `monitoring/alert_rules.yml` | Prometheus alert rule |
| Database Change | `alembic/versions/` | Alembic migration script |

For questions or issues, refer to:
- Main README: `README.md`
- Tool documentation: `tools/README.md`
- Monitoring setup: `monitoring/` directory
- Database schema: `alembic/versions/`
