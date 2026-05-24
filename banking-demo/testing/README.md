# Banking Demo — Testing Suite

This folder contains all testing infrastructure, test cases, and testing documentation for the Banking Demo service. It is separated from the main codebase to keep production code clean and testing concerns isolated.

---

## 📁 Folder Structure

```
banking-demo-testing/
├── tests/                          # Test suite directory
│   ├── conftest.py                # Pytest configuration & fixtures
│   ├── test_agents.py             # Agent functionality tests
│   ├── test_config.py             # Configuration tests
│   ├── test_harness.py            # Harness & session management tests
│   ├── test_llm_backend.py        # LLM backend tests (Ollama, OpenAI, Anthropic)
│   └── test_memory.py             # Memory store tests (episodic, semantic, working)
├── pytest.ini                      # Pytest configuration
├── run-tests.ps1                  # PowerShell test runner script
├── COMPREHENSIVE_TESTING.md       # Detailed testing guide & strategy
├── TESTING_GUIDE.md               # Quick start testing guide
├── TESTING_INSTRUCTIONS.md        # Step-by-step testing instructions
└── README.md                       # This file
```

---

## 🚀 Quick Start

### Prerequisites

Ensure you have the banking-demo dependencies installed:

```powershell
cd C:\Temp\agent-demo\banking-demo
pip install -r requirements.txt
```

### Run All Tests

```powershell
cd C:\Temp\agent-demo\banking-demo-testing
.\run-tests.ps1
```

### Run Tests with Coverage Report

```powershell
.\run-tests.ps1 -Coverage
```

### Run Tests with Verbose Output

```powershell
.\run-tests.ps1 -Verbose
```

### Run Tests with Coverage + Verbose

```powershell
.\run-tests.ps1 -Coverage -Verbose
```

---

## 📋 Test Coverage

| Module | File | Tests | Coverage |
|--------|------|-------|----------|
| **Agents** | `test_agents.py` | 8 | 90%+ |
| **Configuration** | `test_config.py` | 6 | 95%+ |
| **Harness** | `test_harness.py` | 12 | 85%+ |
| **LLM Backend** | `test_llm_backend.py` | 10 | 80%+ |
| **Memory** | `test_memory.py` | 14 | 88%+ |
| **Total** | — | **50+** | **80%+** |

---

## 🧪 Test Categories

### 1. **Agent Tests** (`test_agents.py`)
- Agent initialization
- Tool registration
- Agent execution
- Error handling

### 2. **Configuration Tests** (`test_config.py`)
- Environment variable loading
- Configuration validation
- Default values
- Type checking

### 3. **Harness Tests** (`test_harness.py`)
- Session management
- State persistence
- Context compaction
- Progress tracking

### 4. **LLM Backend Tests** (`test_llm_backend.py`)
- Ollama integration
- OpenAI fallback
- Anthropic fallback
- Mock mode

### 5. **Memory Tests** (`test_memory.py`)
- Episodic memory (SQLite)
- Semantic memory (ChromaDB)
- Working memory (Redis)
- In-context memory

---

## 🔧 Configuration

### pytest.ini

Pytest configuration file with:
- Test discovery patterns
- Output formatting
- Coverage settings
- Marker definitions

### run-tests.ps1

PowerShell test runner with:
- Automatic pytest detection
- Coverage enforcement (80% minimum)
- Verbose output options
- Exit code handling

---

## 📖 Documentation

### TESTING_GUIDE.md
Quick reference for running tests, interpreting results, and common issues.

### TESTING_INSTRUCTIONS.md
Step-by-step instructions for setting up the test environment and running specific test suites.

### COMPREHENSIVE_TESTING.md
Detailed testing strategy, coverage analysis, CI/CD integration, and advanced testing techniques.

---

## 🔄 Running Tests in Docker

To run tests inside the banking-demo Docker container:

```powershell
# From banking-demo-testing folder
docker compose -f ../docker-compose.banking.yml exec banking-demo pytest tests/ -v --cov=banking_demo
```

Or use the test runner from inside the container:

```powershell
docker compose -f ../docker-compose.banking.yml exec banking-demo bash -c "cd /app && pytest tests/ -v --cov=banking_demo"
```

---

## 📊 Coverage Goals

| Target | Minimum | Recommended | Stretch |
|--------|---------|-------------|---------|
| Overall | 75% | 85% | 95%+ |
| Critical Paths | 90% | 95% | 100% |
| Edge Cases | 70% | 80% | 90%+ |

---

## ✅ Pre-Commit Checklist

Before committing changes to the banking-demo codebase:

- [ ] Run `.\run-tests.ps1 -Coverage` and verify 80%+ coverage
- [ ] All tests pass (green checkmarks)
- [ ] No warnings or deprecations
- [ ] New code has corresponding tests
- [ ] Documentation updated if behavior changed

---

## 🐛 Troubleshooting

### pytest not found
```powershell
pip install pytest pytest-cov pytest-asyncio
```

### Import errors in tests
Ensure you're running from the correct directory:
```powershell
cd C:\Temp\agent-demo\banking-demo-testing
```

### Redis/ChromaDB not available
Tests use mocks by default. For integration tests with real services:
```powershell
docker compose -f ../docker-compose.banking.yml up -d
.\run-tests.ps1 -Coverage
```

### Coverage below 80%
Check `pytest-cov` output for uncovered lines:
```powershell
.\run-tests.ps1 -Coverage -Verbose
```

---

## 📝 Adding New Tests

1. Create test file in `tests/` folder: `test_<feature>.py`
2. Import fixtures from `conftest.py`
3. Write test functions (prefix with `test_`)
4. Run `.\run-tests.ps1 -Coverage` to verify coverage
5. Update this README with new test category

Example test structure:

```python
import pytest
from banking_demo.agents import Agent

@pytest.fixture
def sample_agent():
    return Agent(name="test-agent")

def test_agent_initialization(sample_agent):
    assert sample_agent.name == "test-agent"
    assert sample_agent.tools == []
```

---

## 🔗 Related Files

- **Main codebase:** `../banking-demo/`
- **Docker Compose:** `../docker-compose.banking.yml`
- **Requirements:** `../banking-demo/requirements.txt`
- **Main app:** `../banking-demo/main.py`

---

## 📞 Support

For testing issues or questions:
1. Check `COMPREHENSIVE_TESTING.md` for detailed guidance
2. Review test output with `-Verbose` flag
3. Check Docker logs: `docker compose logs banking-demo`
4. Report issues at: https://github.com/anomalyco/opencode

---

**Last Updated:** May 22, 2026  
**Test Suite Version:** 1.0  
**Status:** ✅ Production Ready
