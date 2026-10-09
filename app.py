"""
Main FastAPI Application for Fact-Checker & Daily News Digest.
Provides REST API endpoints and an interactive web dashboard.
"""

import os
from typing import Optional, Dict, Any, List
from fastapi import FastAPI, Query, HTTPException, Request, Response
from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field

from config import settings
from core.graph import (
    run_fact_check,
    run_news_digest,
    get_fact_check_mermaid,
    get_news_digest_mermaid
)
from core.state import FactCheckVerdict, NewsDigestResult
from tools.credibility import get_domain_credibility
from tools.clickbait import analyze_clickbait
from rag.vector_store import vector_store
from mcp_server import MCP_TOOLS, MCP_RESOURCES, handle_tool_call, handle_resource_read

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    description="Agentic AI Fact-Checking and Daily News Digest platform powered by LangGraph, MCP, RAG, and ReAct."
)

# In-memory history for session inspection
HISTORY_FACT_CHECKS: List[Dict[str, Any]] = []
HISTORY_DIGESTS: List[Dict[str, Any]] = []

# Mount static files and templates
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
static_dir = os.path.join(BASE_DIR, "web", "static")
templates_dir = os.path.join(BASE_DIR, "web", "templates")
os.makedirs(static_dir, exist_ok=True)
os.makedirs(templates_dir, exist_ok=True)

app.mount("/static", StaticFiles(directory=static_dir), name="static")
templates = Jinja2Templates(directory=templates_dir)


# -------------------------------------------------------------------------
# Request Models
# -------------------------------------------------------------------------

class FactCheckRequest(BaseModel):
    claim: str = Field(..., min_length=3, max_length=4000, description="The claim or headline to verify")


class CredibilityRequest(BaseModel):
    domain: str = Field(..., description="Domain or URL to rate")


class ClickbaitRequest(BaseModel):
    text: str = Field(..., description="Headline or text to analyze")


# -------------------------------------------------------------------------
# Web UI Routes
# -------------------------------------------------------------------------

@app.get("/", response_class=HTMLResponse)
async def home_page(request: Request):
    """Renders the interactive Agentic AI Dashboard."""
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "app_name": settings.APP_NAME,
            "version": settings.VERSION,
            "llm_provider": settings.LLM_PROVIDER
        }
    )


# -------------------------------------------------------------------------
# REST API Endpoints
# -------------------------------------------------------------------------

@app.post("/api/fact-check", response_model=FactCheckVerdict)
async def api_fact_check(req: FactCheckRequest):
    """
    Executes the full LangGraph Fact-Checking multi-agent workflow:
    Input Guardrail -> Clickbait Analyzer -> RAG Retrieval -> ReAct Web Search -> Evidence Evaluator -> Verdict Synthesizer.
    """
    try:
        verdict = run_fact_check(req.claim)
        HISTORY_FACT_CHECKS.insert(0, verdict.model_dump())
        if len(HISTORY_FACT_CHECKS) > 50:
            HISTORY_FACT_CHECKS.pop()
        return verdict
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/digest", response_model=NewsDigestResult)
async def api_get_digest(
    category: str = Query("World", enum=["World", "Technology", "India", "Science", "Business", "Sports"]),
    limit: int = Query(5, ge=1, le=15)
):
    """
    Executes the LangGraph News Digest workflow:
    Fetch RSS -> Filter & Rank by Credibility -> Summarize -> Compile Digest.
    """
    try:
        digest = run_news_digest(category=category, limit=limit)
        HISTORY_DIGESTS.insert(0, digest.model_dump())
        if len(HISTORY_DIGESTS) > 30:
            HISTORY_DIGESTS.pop()
        return digest
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/digest/export")
async def api_export_digest(
    category: str = Query("World"),
    format: str = Query("markdown", enum=["markdown", "json"])
):
    """Exports compiled daily digest as downloadable Markdown or JSON."""
    digest = run_news_digest(category=category, limit=6)
    if format == "markdown":
        return Response(
            content=digest.markdown_content,
            media_type="text/markdown",
            headers={"Content-Disposition": f"attachment; filename=digest_{category.lower()}.md"}
        )
    return JSONResponse(content=digest.model_dump())


@app.post("/api/tools/credibility")
async def api_check_credibility(req: CredibilityRequest):
    """Direct tool endpoint: evaluates domain credibility rating (0-100)."""
    return get_domain_credibility(req.domain)


@app.post("/api/tools/clickbait")
async def api_check_clickbait(req: ClickbaitRequest):
    """Direct tool endpoint: analyzes headline sensationalism and clickbait score."""
    return analyze_clickbait(req.text)


@app.get("/api/rag/search")
async def api_rag_search(query: str = Query(...), top_k: int = Query(3, ge=1, le=10)):
    """Direct tool endpoint: queries RAG vector store for verified facts."""
    return vector_store.similarity_search(query, top_k=top_k)


@app.get("/api/history")
async def api_get_history():
    """Returns past fact-checks and news digests generated in current session."""
    return {
        "fact_checks": HISTORY_FACT_CHECKS[:20],
        "digests": HISTORY_DIGESTS[:10]
    }


@app.get("/api/graph/mermaid")
async def api_get_mermaid():
    """Returns Mermaid architecture diagram representations of the LangGraph workflows."""
    return {
        "fact_check_graph": get_fact_check_mermaid(),
        "news_digest_graph": get_news_digest_mermaid()
    }


# -------------------------------------------------------------------------
# MCP Protocol REST Interoperability Endpoints
# -------------------------------------------------------------------------

@app.get("/api/mcp/manifest")
async def api_mcp_manifest():
    """Returns Model Context Protocol (MCP) server manifest and tools schema."""
    return {
        "server": {
            "name": settings.MCP_SERVER_NAME,
            "version": settings.VERSION,
            "protocolVersion": "2024-11-05"
        },
        "tools": MCP_TOOLS,
        "resources": MCP_RESOURCES
    }


@app.post("/api/mcp/tool/call")
async def api_mcp_call_tool(payload: Dict[str, Any]):
    """Invokes an MCP tool via JSON-RPC compatible payload."""
    name = payload.get("name")
    arguments = payload.get("arguments", {})
    if not name:
        raise HTTPException(status_code=400, detail="Missing tool 'name'")
    try:
        return handle_tool_call(name, arguments)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/health")
async def health_check():
    """System health check and diagnostic information."""
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": settings.VERSION,
        "llm_provider": settings.LLM_PROVIDER,
        "rag_indexed_docs": len(vector_store.documents),
        "environment": settings.ENVIRONMENT
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host=settings.HOST, port=settings.PORT, reload=settings.DEBUG)
