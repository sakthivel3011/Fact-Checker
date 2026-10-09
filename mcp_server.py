"""
Model Context Protocol (MCP) Server for Fact-Checker & Daily News Digest.
Exposes Fact-Checking and News-Digest tools and resources over the standard MCP protocol.
Compatible with Claude Desktop, Cursor, Antigravity, and MCP Clients.
"""

import json
import sys
from typing import Dict, Any, List

from core.graph import run_fact_check, run_news_digest
from tools.credibility import get_domain_credibility
from tools.clickbait import analyze_clickbait
from rag.vector_store import vector_store
from config import settings

# MCP Server Metadata
MCP_SERVER_INFO = {
    "name": settings.MCP_SERVER_NAME,
    "version": settings.VERSION,
    "protocolVersion": "2024-11-05"
}

# MCP Tools Manifest
MCP_TOOLS = [
    {
        "name": "fact_check_claim",
        "description": "Verify the veracity of a news claim using multi-agent LangGraph workflow with Tavily search and RAG.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "claim": {
                    "type": "string",
                    "description": "The statement, headline, or claim to fact-check"
                }
            },
            "required": ["claim"]
        }
    },
    {
        "name": "get_daily_digest",
        "description": "Fetch and compile a categorized news digest with executive summary and key points from trusted RSS feeds.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "category": {
                    "type": "string",
                    "enum": ["World", "Technology", "India", "Science", "Business", "Sports"],
                    "description": "News category to fetch and summarize",
                    "default": "World"
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of articles to include",
                    "default": 5
                }
            }
        }
    },
    {
        "name": "verify_source_credibility",
        "description": "Evaluates the credibility rating (0-100) and trustworthiness tier of a news domain or URL.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "domain_or_url": {
                    "type": "string",
                    "description": "Domain name or URL (e.g. 'reuters.com' or 'https://bbc.com/news/...')"
                }
            },
            "required": ["domain_or_url"]
        }
    },
    {
        "name": "analyze_headline_clickbait",
        "description": "Detects emotional sensationalism, exaggerated claims, and clickbait patterns in a headline.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "headline": {
                    "type": "string",
                    "description": "The headline or claim to analyze for clickbait"
                }
            },
            "required": ["headline"]
        }
    },
    {
        "name": "search_rag_knowledge_base",
        "description": "Searches the local RAG vector store for verified benchmark claims and debunks.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Semantic search query"
                },
                "top_k": {
                    "type": "integer",
                    "default": 3
                }
            },
            "required": ["query"]
        }
    }
]

# MCP Resources Manifest
MCP_RESOURCES = [
    {
        "uri": "factchecker://digest/today",
        "name": "Today's Global News Digest",
        "description": "Live intelligence briefing of top global stories",
        "mimeType": "text/markdown"
    },
    {
        "uri": "factchecker://sources/credibility",
        "name": "Domain Credibility Index",
        "description": "Reference catalog of news domain credibility scores",
        "mimeType": "application/json"
    },
    {
        "uri": "factchecker://claims/benchmarks",
        "name": "Verified Fact-Check Benchmarks",
        "description": "Curated benchmark database of verified and debunked claims",
        "mimeType": "application/json"
    }
]


def handle_tool_call(name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Executes requested tool and returns MCP tool response."""
    if name == "fact_check_claim":
        claim = arguments.get("claim", "")
        verdict = run_fact_check(claim)
        return {
            "content": [
                {
                    "type": "text",
                    "text": json.dumps(verdict.model_dump(), indent=2)
                }
            ]
        }

    elif name == "get_daily_digest":
        category = arguments.get("category", "World")
        limit = arguments.get("limit", 5)
        digest = run_news_digest(category=category, limit=limit)
        return {
            "content": [
                {
                    "type": "text",
                    "text": json.dumps(digest.model_dump(), indent=2)
                }
            ]
        }

    elif name == "verify_source_credibility":
        domain = arguments.get("domain_or_url", "")
        info = get_domain_credibility(domain)
        return {
            "content": [
                {
                    "type": "text",
                    "text": json.dumps(info, indent=2)
                }
            ]
        }

    elif name == "analyze_headline_clickbait":
        headline = arguments.get("headline", "")
        res = analyze_clickbait(headline)
        return {
            "content": [
                {
                    "type": "text",
                    "text": json.dumps(res, indent=2)
                }
            ]
        }

    elif name == "search_rag_knowledge_base":
        query = arguments.get("query", "")
        top_k = arguments.get("top_k", 3)
        hits = vector_store.similarity_search(query, top_k=top_k)
        return {
            "content": [
                {
                    "type": "text",
                    "text": json.dumps(hits, indent=2)
                }
            ]
        }

    else:
        raise ValueError(f"Unknown tool: {name}")


def handle_resource_read(uri: str) -> Dict[str, Any]:
    """Reads requested MCP resource by URI."""
    if uri == "factchecker://digest/today":
        digest = run_news_digest(category="World", limit=3)
        return {
            "contents": [
                {
                    "uri": uri,
                    "mimeType": "text/markdown",
                    "text": digest.markdown_content
                }
            ]
        }
    elif uri == "factchecker://sources/credibility":
        return {
            "contents": [
                {
                    "uri": uri,
                    "mimeType": "application/json",
                    "text": json.dumps(settings.DOMAIN_CREDIBILITY_SCORES, indent=2)
                }
            ]
        }
    elif uri == "factchecker://claims/benchmarks":
        return {
            "contents": [
                {
                    "uri": uri,
                    "mimeType": "application/json",
                    "text": json.dumps(vector_store.documents, indent=2)
                }
            ]
        }
    else:
        raise ValueError(f"Unknown resource URI: {uri}")


def process_jsonrpc_message(msg: Dict[str, Any]) -> Dict[str, Any]:
    """Dispatches JSON-RPC 2.0 MCP protocol requests."""
    msg_id = msg.get("id")
    method = msg.get("method")
    params = msg.get("params", {})

    if method == "initialize":
        return {
            "jsonrpc": "2.0",
            "id": msg_id,
            "result": {
                "protocolVersion": MCP_SERVER_INFO["protocolVersion"],
                "serverInfo": MCP_SERVER_INFO,
                "capabilities": {
                    "tools": {"listChanged": False},
                    "resources": {"subscribe": False, "listChanged": False}
                }
            }
        }

    elif method == "tools/list":
        return {
            "jsonrpc": "2.0",
            "id": msg_id,
            "result": {"tools": MCP_TOOLS}
        }

    elif method == "tools/call":
        name = params.get("name")
        arguments = params.get("arguments", {})
        try:
            tool_res = handle_tool_call(name, arguments)
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": tool_res
            }
        except Exception as e:
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "error": {"code": -32000, "message": str(e)}
            }

    elif method == "resources/list":
        return {
            "jsonrpc": "2.0",
            "id": msg_id,
            "result": {"resources": MCP_RESOURCES}
        }

    elif method == "resources/read":
        uri = params.get("uri")
        try:
            res_content = handle_resource_read(uri)
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": res_content
            }
        except Exception as e:
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "error": {"code": -32000, "message": str(e)}
            }

    elif method == "notifications/initialized":
        # Client acknowledgement, no response required
        return {}

    else:
        return {
            "jsonrpc": "2.0",
            "id": msg_id,
            "error": {"code": -32601, "message": f"Method not found: {method}"}
        }


def run_stdio_server():
    """Runs MCP server listening on stdin and responding on stdout."""
    for line in sys.stdin:
        if not line.strip():
            continue
        try:
            req = json.loads(line)
            res = process_jsonrpc_message(req)
            if res:
                sys.stdout.write(json.dumps(res) + "\n")
                sys.stdout.flush()
        except Exception as e:
            err_resp = {
                "jsonrpc": "2.0",
                "id": None,
                "error": {"code": -32700, "message": f"Parse error: {e}"}
            }
            sys.stdout.write(json.dumps(err_resp) + "\n")
            sys.stdout.flush()


if __name__ == "__main__":
    run_stdio_server()
