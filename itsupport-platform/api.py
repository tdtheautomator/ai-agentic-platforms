"""
REST API routes for IT Support demo.

Parameterized route setup for service-agnostic API endpoints.
"""

from fastapi import FastAPI
from fastapi.responses import StreamingResponse

from config import Config
import llm
from memory import _context, CTX_LIMIT, work_list, epi_list, ticket_list, ctx_clear


def setup_routes(
    app: FastAPI,
    config: Config,
    tools_dict: dict,
    agents_dict: dict,
    run_pipeline_fn,
    mock_fn,
    agents_sequence: list[str],
    users_list: list[dict] = None,
    ticket_templates: list[dict] = None,
    kb_articles: list[str] = None,
) -> None:
    """Register all API routes on the FastAPI app."""

    @app.get("/api/status")
    def api_status():
        """Service status and LLM backend info."""
        from memory import _chroma_ready
        return {
            "service": "itsupport-demo",
            "llm": llm._llm_backend,
            "model": llm._llm_model,
            "mock": llm._llm_backend == "mock",
            "chroma_ready": _chroma_ready
        }

    @app.get("/api/llm/status")
    def api_llm_status():
        """LLM backend details."""
        return {
            "backend": llm._llm_backend,
            "model": llm._llm_model,
            "mock": llm._llm_backend == "mock"
        }

    @app.get("/api/users")
    def api_users():
        """List all users."""
        return {"users": users_list or []}

    @app.get("/api/tickets")
    def api_tickets():
        """List recent tickets."""
        return {"tickets": ticket_list(20)}

    @app.get("/api/events/{ticket_id}")
    def api_events(ticket_id: str):
        """Get audit log for a ticket."""
        return {"events": epi_list(ticket_id)}

    @app.get("/api/tools")
    def api_tools():
        """List all available tools with schemas."""
        return {
            "tools": [
                {k: v for k, v in t.items() if k != "fn"}
                for t in tools_dict.values()
            ]
        }

    @app.get("/api/agents")
    def api_agents():
        """List all agents with descriptions."""
        return {
            "agents": [
                {
                    "id": k,
                    "name": v.get("name", k),
                    "description": v.get("description", ""),
                    "skills": v.get("skills", [])
                }
                for k, v in agents_dict.items()
            ]
        }

    @app.get("/api/memory/context")
    def api_context():
        """Get current in-context memory."""
        return {
            "items": list(_context),
            "count": len(_context),
            "limit": CTX_LIMIT
        }

    @app.get("/api/memory/working")
    def api_working():
        """Get current working cache (Redis/in-process)."""
        return {"items": work_list()}

    @app.get("/api/run")
    async def api_run(
        user_id: str = "USR001",
        category: str = "Network / VPN",
        priority: str = "HIGH",
        description: str = "Cannot connect to VPN — error 800 timeout. Working from home.",
    ):
        """Run pipeline for a ticket (streaming SSE)."""
        from datetime import datetime
        
        user = next((u for u in users_list if u["id"] == user_id), users_list[0]) if users_list else {}
        
        # Normalize priority to uppercase
        priority = priority.upper()
        
        # Normalize category: find matching category from known list (case-insensitive)
        if ticket_templates:
            known_categories = list(set(t["category"] for t in ticket_templates))
            category = next(
                (cat for cat in known_categories if cat.lower() == category.lower()),
                category  # fallback to original if no match
            )
        
        ticket = {"category": category, "priority": priority, "description": description}
        ticket_id = f"INC-{datetime.utcnow().strftime('%H%M%S')}-{user_id[-3:]}"
        ctx_clear()
        
        return StreamingResponse(
            run_pipeline_fn(
                ticket_id,
                user,
                ticket,
                agents_sequence,
                tools_dict,
                agents_dict,
                mock_fn,
                config=config,
            ),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
        )

    @app.get("/api/seed")
    async def api_seed():
        """Pre-populate demo data (silent run)."""
        ctx_clear()
        if not users_list or not ticket_templates:
            return {"seeded": 0}
        
        for i, u in enumerate(users_list[:3]):
            tmpl = ticket_templates[i % len(ticket_templates)]
            ticket_id = f"SEED-{i+1:03d}-{u['id'][-4:]}"
            async for _ in run_pipeline_fn(
                ticket_id,
                u,
                tmpl,
                agents_sequence,
                tools_dict,
                agents_dict,
                mock_fn,
                config=config,
            ):
                pass
        return {"seeded": min(3, len(users_list))}
