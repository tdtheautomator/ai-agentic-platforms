# Agents Module — Banking Demo

Dedicated module for agent implementations and definitions. Enables scalable agent development with clear separation of concerns.

## Structure

```
agents/
├── __init__.py              # Module exports and registry initialization
├── base.py                  # Agent base class
├── context.py               # AgentContext dataclass
├── registry.py              # Agent registry and @register_agent decorator
├── README.md                # This file
│
├── intake/                  # Intake agent
│   ├── __init__.py
│   ├── agent.py             # IntakeAgent class
│   ├── definition.py        # Agent definition
│   ├── prompts.py           # System prompts and message builders
│   └── README.md            # Intake-specific docs
│
├── risk/                    # Risk assessment agent
│   ├── __init__.py
│   ├── agent.py             # RiskAgent class
│   ├── definition.py        # Agent definition
│   ├── prompts.py           # System prompts and message builders
│   └── README.md
│
├── fraud/                   # Fraud detection agent
│   ├── __init__.py
│   ├── agent.py             # FraudAgent class
│   ├── definition.py        # Agent definition
│   ├── prompts.py           # System prompts and message builders
│   └── README.md
│
└── decision/                # Decision agent
    ├── __init__.py
    ├── agent.py             # DecisionAgent class
    ├── definition.py        # Agent definition
    ├── prompts.py           # System prompts and message builders
    └── README.md
```

## Current Agents

### Intake Agent
- **Location**: `agents/intake/`
- **Class**: `IntakeAgent`
- **Purpose**: Collects and validates the initial loan application
- **Skills**: loan_intake, kyc_verification, affordability_precheck
- **Responsibilities**:
  - Retrieve customer profile
  - Verify KYC documents
  - Calculate affordability
  - Call LLM for intake assessment
  - Log to episodic memory

### Risk Agent
- **Location**: `agents/risk/`
- **Class**: `RiskAgent`
- **Purpose**: Evaluates credit risk using bureau data
- **Skills**: credit_risk, dti_analysis, income_verification
- **Responsibilities**:
  - Query semantic memory for banking rules
  - Analyze credit score and DTI
  - Call LLM for risk assessment
  - Log to episodic memory
  - Cache risk level in working memory

### Fraud Agent
- **Location**: `agents/fraud/`
- **Class**: `FraudAgent`
- **Purpose**: Screens for fraud indicators
- **Skills**: fraud_screening, transaction_analysis, aml_check
- **Responsibilities**:
  - Scan transaction history
  - Check working memory for upstream risk level
  - Call LLM for fraud assessment
  - Log to episodic memory

### Decision Agent
- **Location**: `agents/decision/`
- **Class**: `DecisionAgent`
- **Purpose**: Makes the final credit decision
- **Skills**: credit_decision, offer_generation, decline_reasoning
- **Responsibilities**:
  - Combine all upstream assessments
  - Call LLM for final decision
  - Determine final status (approved, conditional, declined)
  - Store decision in semantic memory
  - Log to episodic memory

## Agent Registry

The `A2A_AGENTS` dictionary is automatically populated when agents are imported:

```python
from agents import A2A_AGENTS

# A2A_AGENTS structure:
# {
#     "intake": {
#         "name": "Intake Agent",
#         "description": "...",
#         "skills": [...],
#         "system_prompt": "..."
#     },
#     "risk": {...},
#     "fraud": {...},
#     "decision": {...}
# }
```

## Adding a New Agent

### 1. Create Agent Folder

```bash
mkdir agents/new_agent
```

### 2. Create Agent Files

**agents/new_agent/definition.py**:
```python
from agents.registry import register_agent

@register_agent("new_agent")
def new_agent_definition() -> dict:
    """New agent definition."""
    return {
        "name": "New Agent",
        "description": "Agent description",
        "skills": ["skill1", "skill2"],
        "system_prompt": "System prompt for the LLM",
    }
```

**agents/new_agent/prompts.py**:
```python
SYSTEM_PROMPT = "System prompt for the LLM"

def build_user_message(customer: dict, loan: dict) -> str:
    """Build the user message for the agent."""
    return f"Message for {customer['name']}..."
```

**agents/new_agent/agent.py**:
```python
from agents.base import Agent
from agents.context import AgentContext
from agents.new_agent.prompts import SYSTEM_PROMPT, build_user_message

class NewAgent(Agent):
    """New agent implementation."""
    
    def __init__(self):
        super().__init__("new_agent", SYSTEM_PROMPT)
    
    async def run(self, context: AgentContext) -> str:
        """Execute the agent."""
        # Implementation here
        return "Result"
```

**agents/new_agent/__init__.py**:
```python
from agents.new_agent.agent import NewAgent
from agents.new_agent.definition import new_agent_definition

__all__ = [
    "NewAgent",
    "new_agent_definition",
]
```

### 3. Update agents/__init__.py

Add the new agent to the imports:

```python
from agents.new_agent import NewAgent, new_agent_definition
```

### 4. Agent is Auto-Registered

When `agents/__init__.py` is imported, the `@register_agent` decorator automatically registers the new agent in `A2A_AGENTS`.

## Base Agent Class

All agents inherit from `Agent` (agents/base.py):

```python
class Agent:
    def __init__(self, name: str, system_prompt: str):
        """Initialize an agent."""
        self.name = name
        self.system_prompt = system_prompt
    
    async def run(self, context: AgentContext) -> str:
        """Execute the agent."""
        raise NotImplementedError()
    
    async def _log_execution(self, context, duration_ms, status):
        """Log agent execution metrics."""
        # Logging implementation
```

## Agent Context

All agents receive an `AgentContext` with:
- `app_id`: Unique application ID
- `customer`: Customer profile dictionary
- `loan`: Loan details dictionary
- `session_num`: Current harness session number
- `memory_manager`: Memory manager for all 4 stores
- `llm_client`: LLM backend client
- `results`: Dictionary of results from previous agents
- `request_id`: Correlation ID for request tracing

## Best Practices

### 1. Separation of Concerns
- **agent.py**: Only agent class logic
- **definition.py**: Only agent definition
- **prompts.py**: Only prompts and message builders

### 2. Prompts Management
Keep all prompts in `prompts.py`:
- `SYSTEM_PROMPT`: System prompt for the LLM
- `build_user_message()`: Build user message from context
- `parse_result()`: Parse LLM result (if needed)

### 3. Error Handling
Always wrap agent logic in try-except:
```python
try:
    # Agent logic
    result = await context.llm_client.call(...)
    await self._log_execution(context, duration_ms, "success")
    return result
except Exception as exc:
    await self._log_execution(context, duration_ms, "error")
    await logger.aerror("agent_error", agent=self.name, error=str(exc))
    raise
```

### 4. Memory Integration
Use all 4 memory types:
- **In-Context**: `context.memory_manager.add_to_context()`
- **Episodic**: `context.memory_manager.add_to_episodic()`
- **Semantic**: `context.memory_manager.add_to_semantic()` or `search_semantic()`
- **Working**: `context.memory_manager.add_to_working()` or `get_working()`

### 5. Logging
Use structlog for structured logging:
```python
await logger.ainfo("agent_start", agent=self.name, app_id=context.app_id)
await logger.aerror("agent_error", agent=self.name, error=str(exc))
```

## Testing Agents

### Unit Test Example

```python
# tests/agents/intake/test_agent.py
import pytest
from agents.intake import IntakeAgent

@pytest.mark.asyncio
async def test_intake_agent_initialization():
    """Test intake agent initialization."""
    agent = IntakeAgent()
    assert agent.name == "intake"
    assert "banking intake specialist" in agent.system_prompt.lower()
```

### Integration Test Example

```python
# tests/agents/test_registry.py
from agents import A2A_AGENTS

def test_all_agents_registered():
    """Verify all agents are registered."""
    expected = ["intake", "risk", "fraud", "decision"]
    assert set(A2A_AGENTS.keys()) == set(expected)
```

## Metrics

All agent execution is tracked via Prometheus metrics:

- `banking_agent_calls_total` — Counter of agent calls by agent name
- `banking_agent_duration_seconds` — Histogram of agent execution duration by agent name
- `banking_agent_errors_total` — Counter of agent errors by agent name and error type

Example:
```python
banking_agent_calls_total{agent="intake"} 42
banking_agent_duration_seconds_bucket{agent="intake",le="0.5"} 38
banking_agent_errors_total{agent="intake",error_type="llm_timeout"} 2
```

## Future Enhancements

Possible improvements as the agent ecosystem grows:

1. **Agent Versioning** — Track agent versions and support multiple versions
2. **Agent Dependencies** — Declare dependencies between agents
3. **Agent Metadata** — Add tags, categories, cost estimates
4. **Agent Validation** — Validate agent inputs/outputs
5. **Agent Caching** — Cache agent results for deterministic agents
6. **Agent Monitoring** — Enhanced observability and alerting
7. **Agent Composition** — Combine agents into higher-level operations
8. **Agent Permissions** — Control which agents can call which tools

## Questions?

Refer to:
- **Agent Base Class**: `agents/base.py`
- **Agent Registry**: `agents/registry.py`
- **Agent Imports**: `agents/__init__.py`
- **Pipeline Usage**: `main.py` (search for `_run_pipeline`)
- **API Endpoint**: `main.py` (search for `@app.get("/api/agents")`)
