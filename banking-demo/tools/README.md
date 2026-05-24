# Tools Module — Banking Demo

Dedicated module for tool definitions and registration. Enables scalable tool development with clear separation of concerns.

## Structure

```
tools/
├── __init__.py              # Module exports and registry initialization
├── registry.py              # Tool registry and @register_tool decorator
├── README.md                # This file
│
├── customer/                # Customer operations
│   ├── __init__.py
│   ├── get_profile.py       # get_customer_profile() tool
│   └── verify_kyc.py        # verify_kyc_documents() tool
│
├── credit/                  # Credit operations
│   ├── __init__.py
│   ├── check_score.py       # check_credit_score() tool
│   └── calculate_affordability.py  # calculate_affordability() tool
│
├── fraud/                   # Fraud detection
│   ├── __init__.py
│   └── scan_transactions.py # scan_transaction_history() tool
│
└── compliance/              # Regulatory compliance
    ├── __init__.py
    └── query_rules.py       # query_banking_rules() tool
```

## Current Tools

### Customer Tools
- **`get_customer_profile(customer_id: str)`** — Retrieve full customer profile including credit score and risk rating
- **`verify_kyc_documents(customer_id: str)`** — Check KYC document status against identity verification service

### Credit Tools
- **`check_credit_score(customer_id: str)`** — Run soft credit bureau enquiry and return score plus band
- **`calculate_affordability(customer_id, loan_amount, term_months)`** — Calculate monthly repayment and debt-to-income ratio

### Fraud Tools
- **`scan_transaction_history(customer_id: str)`** — Scan recent transactions for suspicious patterns

### Compliance Tools
- **`query_banking_rules(topic: str)`** — Search regulatory knowledge base for relevant rules

## Adding a New Tool

### 1. Create Tool File

Create a new file in the appropriate category folder:

```python
# tools/customer/new_tool.py
"""
Tool description.

One-line summary of what this tool does.
"""

from tools.registry import register_tool


# Import dependencies from main module if needed
def _get_customers():
    """Get customers list from main module."""
    from main import CUSTOMERS
    return CUSTOMERS


@register_tool
def my_new_tool(param1: str, param2: int) -> dict:
    """Tool description for discovery and documentation."""
    # Implementation here
    return {"result": "value"}
```

### 2. Export in Category `__init__.py`

```python
# tools/customer/__init__.py
from tools.customer.new_tool import my_new_tool

__all__ = [
    "get_customer_profile",
    "verify_kyc_documents",
    "my_new_tool",  # Add here
]
```

### 3. Export in Main `tools/__init__.py`

```python
# tools/__init__.py
from tools.customer import my_new_tool

__all__ = [
    # ... existing exports ...
    "my_new_tool",  # Add here
]
```

### 4. Tool is Automatically Registered

When `tools/__init__.py` is imported, the `@register_tool` decorator automatically:
- Registers the tool in the `TOOLS` registry
- Extracts function name, docstring, and parameters
- Makes it discoverable via `/api/tools` endpoint

## Tool Best Practices

### 1. Pure Functions
Tools should be pure functions with no side effects:
```python
# ✓ Good: Pure function
@register_tool
def calculate_value(amount: float) -> dict:
    return {"result": amount * 1.1}

# ✗ Bad: Side effects (modifies global state)
@register_tool
def calculate_value(amount: float) -> dict:
    global total
    total += amount  # Side effect!
    return {"result": total}
```

### 2. Clear Docstrings
Docstrings become tool descriptions in discovery:
```python
@register_tool
def check_credit_score(customer_id: str) -> dict:
    """Run a soft credit bureau enquiry and return score plus band."""
    # The docstring above is used as the tool description
```

### 3. Type Hints
Always include type hints for parameters and return values:
```python
@register_tool
def calculate_affordability(
    customer_id: str,
    loan_amount: float,
    term_months: int
) -> dict:
    """Calculate monthly repayment and debt-to-income ratio."""
```

### 4. Error Handling
Return structured error responses:
```python
@register_tool
def get_customer_profile(customer_id: str) -> dict:
    """Retrieve full customer profile including credit score and risk rating."""
    customers = _get_customers()
    c = next((x for x in customers if x["id"] == customer_id), None)
    if not c:
        return {"error": "Customer not found", "customer_id": customer_id}
    return c
```

### 5. Dependency Injection
Import dependencies from main module using helper functions:
```python
def _get_customers():
    """Get customers list from main module."""
    from main import CUSTOMERS
    return CUSTOMERS

@register_tool
def my_tool(customer_id: str) -> dict:
    customers = _get_customers()
    # Use customers here
```

## Tool Registry

The `TOOLS` dictionary is automatically populated when tools are imported:

```python
from tools import TOOLS

# TOOLS structure:
# {
#     "tool_name": {
#         "name": "tool_name",
#         "description": "Tool docstring",
#         "params": ["param1", "param2"],
#         "fn": <function object>
#     },
#     ...
# }
```

## API Endpoint

Tools are exposed via REST API:

```bash
# Get all tools (without function references)
GET /api/tools

# Response:
{
  "tools": [
    {
      "name": "get_customer_profile",
      "description": "Retrieve full customer profile...",
      "params": ["customer_id"]
    },
    ...
  ]
}
```

## Testing Tools

### Unit Test Example

```python
# tests/tools/test_customer.py
import pytest
from tools.customer import get_customer_profile


def test_get_customer_profile_found():
    """Test retrieving an existing customer."""
    result = get_customer_profile("CUST001")
    assert "error" not in result
    assert result["id"] == "CUST001"


def test_get_customer_profile_not_found():
    """Test retrieving a non-existent customer."""
    result = get_customer_profile("INVALID")
    assert result["error"] == "Customer not found"
```

### Integration Test Example

```python
# tests/tools/test_integration.py
from tools import TOOLS


def test_all_tools_registered():
    """Verify all tools are registered."""
    expected = [
        "get_customer_profile",
        "verify_kyc_documents",
        "check_credit_score",
        "calculate_affordability",
        "scan_transaction_history",
        "query_banking_rules",
    ]
    assert set(TOOLS.keys()) == set(expected)


def test_tool_schema():
    """Verify tool schema is correct."""
    tool = TOOLS["get_customer_profile"]
    assert "name" in tool
    assert "description" in tool
    assert "params" in tool
    assert "fn" in tool
```

## Metrics

All tool execution is tracked via Prometheus metrics:

- `banking_tool_calls_total` — Counter of tool execution calls by tool name
- `banking_tool_duration_seconds` — Histogram of tool execution duration by tool name
- `banking_tool_errors_total` — Counter of tool execution errors by tool name and error type

Example:
```python
# Metrics are automatically recorded when tools are called in the pipeline
banking_tool_calls_total{tool_name="check_credit_score"} 42
banking_tool_duration_seconds_bucket{tool_name="check_credit_score",le="0.1"} 38
banking_tool_errors_total{tool_name="check_credit_score",error_type="not_found"} 2
```

## Migration from Old Structure

The tools have been refactored from inline definitions in `main.py` to this dedicated module. The migration is transparent:

- **Before**: Tools defined as decorated functions in `main.py`
- **After**: Tools defined in `tools/` module, imported in `main.py`
- **Behavior**: Identical — all tools work the same way, just better organized

## Future Enhancements

Possible improvements as the tool ecosystem grows:

1. **Tool Versioning** — Track tool versions and support multiple versions
2. **Tool Dependencies** — Declare dependencies between tools
3. **Tool Metadata** — Add tags, categories, cost estimates
4. **Tool Validation** — JSON Schema validation for tool inputs/outputs
5. **Tool Caching** — Cache tool results for deterministic tools
6. **Tool Monitoring** — Enhanced observability and alerting
7. **Tool Composition** — Combine tools into higher-level operations
8. **Tool Permissions** — Control which agents can call which tools

## Questions?

Refer to:
- **Tool Registry**: `tools/registry.py`
- **Tool Imports**: `tools/__init__.py`
- **Pipeline Usage**: `main.py` (search for `TOOL_CALLS` or `_run_pipeline`)
- **API Endpoint**: `main.py` (search for `@app.get("/api/tools")`)
