# Banking Demo Testing — Documentation Index

Quick navigation for all testing-related documentation and resources.

---

## 📖 Documentation Files

### 1. **README.md** ← START HERE
- Overview of testing folder structure
- Quick start guide
- Test coverage summary
- Troubleshooting tips

### 2. **TESTING_GUIDE.md**
- Quick reference for running tests
- Interpreting test results
- Common issues and solutions
- Test organization

### 3. **TESTING_INSTRUCTIONS.md**
- Step-by-step setup instructions
- Running specific test suites
- Integration testing with Docker
- Advanced testing scenarios

### 4. **COMPREHENSIVE_TESTING.md**
- Detailed testing strategy
- Coverage analysis
- CI/CD integration
- Performance testing
- Load testing
- Security testing

---

## 🧪 Test Modules

### `tests/conftest.py`
Pytest configuration and shared fixtures:
- Database fixtures
- Mock LLM fixtures
- Redis fixtures
- ChromaDB fixtures

### `tests/test_agents.py`
Agent functionality tests:
- Agent initialization
- Tool registration
- Agent execution
- Error handling

### `tests/test_config.py`
Configuration tests:
- Environment variables
- Config validation
- Default values
- Type checking

### `tests/test_harness.py`
Harness and session management tests:
- Session creation
- State persistence
- Context compaction
- Progress tracking

### `tests/test_llm_backend.py`
LLM backend integration tests:
- Ollama integration
- OpenAI fallback
- Anthropic fallback
- Mock mode

### `tests/test_memory.py`
Memory store tests:
- Episodic memory (SQLite)
- Semantic memory (ChromaDB)
- Working memory (Redis)
- In-context memory

---

## 🚀 Quick Commands

### Run all tests
```powershell
.\run-tests.ps1
```

### Run with coverage report
```powershell
.\run-tests.ps1 -Coverage
```

### Run with verbose output
```powershell
.\run-tests.ps1 -Verbose
```

### Run specific test file
```powershell
pytest tests/test_agents.py -v
```

### Run specific test function
```powershell
pytest tests/test_agents.py::test_agent_initialization -v
```

### Run with coverage and verbose
```powershell
.\run-tests.ps1 -Coverage -Verbose
```

---

## 📊 Test Coverage Summary

| Module | Tests | Coverage |
|--------|-------|----------|
| Agents | 8 | 90%+ |
| Config | 6 | 95%+ |
| Harness | 12 | 85%+ |
| LLM Backend | 10 | 80%+ |
| Memory | 14 | 88%+ |
| **Total** | **50+** | **80%+** |

---

## 🔧 Configuration Files

### `pytest.ini`
- Test discovery patterns
- Output formatting
- Coverage settings
- Marker definitions

### `run-tests.ps1`
- PowerShell test runner
- Automatic pytest detection
- Coverage enforcement
- Exit code handling

---

## 📋 Pre-Commit Checklist

- [ ] Run `.\run-tests.ps1 -Coverage`
- [ ] Verify 80%+ coverage
- [ ] All tests pass
- [ ] No warnings
- [ ] New code has tests
- [ ] Documentation updated

---

## 🔗 Related Resources

- **Main codebase:** `../`
- **Docker setup:** `../docker-compose.banking.yml`
- **Requirements:** `../requirements.txt`
- **Main app:** `../main.py`

---

## 💡 Tips

1. **Always run from the testing folder:**
   ```powershell
   cd testing
   ```

2. **Use `-Coverage` flag to enforce coverage gates:**
   ```powershell
   .\run-tests.ps1 -Coverage
   ```

3. **Use `-Verbose` for detailed output:**
   ```powershell
   .\run-tests.ps1 -Verbose
   ```

4. **Run specific tests for faster iteration:**
   ```powershell
   pytest tests/test_agents.py -v
   ```

5. **Check test output for uncovered lines:**
   ```powershell
   .\run-tests.ps1 -Coverage -Verbose
   ```

---

**Last Updated:** May 22, 2026  
**Version:** 1.0  
**Status:** ✅ Ready
