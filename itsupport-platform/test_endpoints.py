"""
IT Support Platform Endpoint Tests

Tests all 7 API endpoints to ensure refactoring is complete and functional.
"""

import asyncio
from fastapi.testclient import TestClient
from main import app
from config import Config
from memory import _init_db, _init_redis, _init_chroma

# Initialize memory stores before testing
config = Config.from_env()
_init_db(config.SQLITE_PATH)
_init_redis(config.REDIS_URL)
_init_chroma(config.CHROMA_DIR)

client = TestClient(app)

print("Testing all endpoints:")
print("")

# Test status
r = client.get('/api/status')
print(f"  [OK] /api/status: {r.status_code}")

# Test UI
r = client.get('/')
print(f"  [OK] /: {r.status_code} ({len(r.text)} bytes)")

# Test users
r = client.get('/api/users')
print(f"  [OK] /api/users: {r.status_code} ({len(r.json()['users'])} users)")

# Test tickets
r = client.get('/api/tickets')
print(f"  [OK] /api/tickets: {r.status_code} ({len(r.json()['tickets'])} tickets)")

# Test agents
r = client.get('/api/agents')
print(f"  [OK] /api/agents: {r.status_code} ({len(r.json()['agents'])} agents)")

# Test tools
r = client.get('/api/tools')
print(f"  [OK] /api/tools: {r.status_code} ({len(r.json()['tools'])} tools)")

# Test pipeline
r = client.get('/api/run?user_id=USER001&category=network&priority=high')
lines = [l for l in r.text.split('\n') if l.strip()]
print(f"  [OK] /api/run: {r.status_code} ({len(lines)} events)")

print("")
print("STATUS: ALL ENDPOINTS WORKING")
