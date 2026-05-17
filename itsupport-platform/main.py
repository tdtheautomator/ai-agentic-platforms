"""
IT Support Agent Pipeline — Main Entry Point

Orchestrates all components: config, LLM, memory, harness, API, and UI.
"""

import asyncio

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from prometheus_fastapi_instrumentator import Instrumentator
from prometheus_client import Counter, Histogram

from config import Config
from llm import _resolve_backend
from memory import _init_db, _init_chroma, _init_redis
from api import setup_routes
from ui import get_html
from agents import A2A_AGENTS
from tools import TOOLS
from mock import _mock_response
from harness import _run_pipeline
from data import USERS, TICKET_TEMPLATES, KB_ARTICLES

# Load configuration
config = Config.from_env()

# FastAPI app
app = FastAPI(title=config.SERVICE_NAME)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
Instrumentator().instrument(app).expose(app)

# Prometheus metrics
PIPELINE_RUNS = Counter("itsupport_pipeline_runs_total", "Total IT support pipeline runs")
AGENT_LATENCY = Histogram("itsupport_agent_duration_seconds", "Per-agent duration", ["agent"])

# Setup routes
setup_routes(
    app,
    config,
    TOOLS,
    A2A_AGENTS,
    _run_pipeline,
    _mock_response,
    agents_sequence=["triage", "diagnostic", "resolution", "escalation"],
    users_list=USERS,
    ticket_templates=TICKET_TEMPLATES,
    kb_articles=KB_ARTICLES,
)

# Frontend
@app.get("/", response_class=HTMLResponse)
def index():
    """Serve frontend HTML."""
    return get_html(config)


# Startup
@app.on_event("startup")
async def startup():
    """Initialize all services on startup."""
    await _resolve_backend(config)
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, _init_db, config.SQLITE_PATH)
    await loop.run_in_executor(None, _init_chroma, config.CHROMA_DIR)
    await loop.run_in_executor(None, _init_redis, config.REDIS_URL)
    
    # Seed knowledge base
    from datetime import datetime
    from memory import sem_add, _chroma_ready
    import memory.semantic as sem_module
    
    if _chroma_ready and sem_module._chroma_col is not None:
        try:
            if sem_module._chroma_col.count() == 0:
                for article in KB_ARTICLES:
                    sem_add(article, {"source": "kb", "added": datetime.utcnow().isoformat()})
                print("[IT Support] Knowledge base seeded.")
        except Exception as e:
            print(f"[IT Support] Knowledge base seeding failed: {e}")
