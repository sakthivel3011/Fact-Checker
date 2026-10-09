"""Unit tests for the Model Context Protocol (MCP) Server implementation."""

import json
import pytest
from mcp_server import process_jsonrpc_message, MCP_TOOLS, MCP_RESOURCES


def test_mcp_initialize():
    msg = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {}
    }
    res = process_jsonrpc_message(msg)
    assert res["id"] == 1
    assert "serverInfo" in res["result"]
    assert res["result"]["serverInfo"]["name"] == "fact-checker-mcp"


def test_mcp_tools_list():
    msg = {
        "jsonrpc": "2.0",
        "id": 2,
        "method": "tools/list",
        "params": {}
    }
    res = process_jsonrpc_message(msg)
    assert res["id"] == 2
    tools = res["result"]["tools"]
    tool_names = [t["name"] for t in tools]
    assert "fact_check_claim" in tool_names
    assert "get_daily_digest" in tool_names
    assert "verify_source_credibility" in tool_names


def test_mcp_resources_list():
    msg = {
        "jsonrpc": "2.0",
        "id": 3,
        "method": "resources/list",
        "params": {}
    }
    res = process_jsonrpc_message(msg)
    assert res["id"] == 3
    resources = res["result"]["resources"]
    uris = [r["uri"] for r in resources]
    assert "factchecker://digest/today" in uris
    assert "factchecker://sources/credibility" in uris


def test_mcp_tool_call_credibility():
    msg = {
        "jsonrpc": "2.0",
        "id": 4,
        "method": "tools/call",
        "params": {
            "name": "verify_source_credibility",
            "arguments": {"domain_or_url": "reuters.com"}
        }
    }
    res = process_jsonrpc_message(msg)
    assert res["id"] == 4
    content = res["result"]["content"][0]["text"]
    parsed = json.loads(content)
    assert parsed["domain"] == "reuters.com"
    assert parsed["score"] >= 90
