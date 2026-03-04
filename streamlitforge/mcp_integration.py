"""MCP Integration Layer for Floyd Labs MCP ecosystem."""

import json
import requests
from typing import Any, Dict, List, Optional


class MCPToolError(Exception):
    pass


class MCPLabClient:
    """HTTP JSON-RPC 2.0 client for Floyd Labs MCP servers."""

    def __init__(self, endpoint: str = "http://localhost:8108/mcp"):
        self.endpoint = endpoint
        self.request_id = 0
        self.timeout = 30.0

    def call_tool(self, server: str, tool: str, arguments: dict) -> dict:
        self.request_id += 1
        payload = {
            "jsonrpc": "2.0",
            "id": self.request_id,
            "method": f"mcp_{server}_{tool}",
            "params": arguments,
        }
        try:
            resp = requests.post(
                self.endpoint, json=payload, timeout=self.timeout
            )
            resp.raise_for_status()
            result = resp.json()
        except requests.RequestException as exc:
            raise MCPToolError(f"MCP request failed: {exc}") from exc

        if "error" in result:
            raise MCPToolError(f"MCP tool error: {result['error']}")
        return result.get("result", {})

    def is_available(self) -> bool:
        try:
            resp = requests.get(self.endpoint.rsplit("/", 1)[0], timeout=2)
            return resp.status_code < 500
        except Exception:
            return False


class SupercacheIntegration:
    """Integration with floyd-supercache for pattern storage."""

    def __init__(self, mcp: MCPLabClient):
        self.mcp = mcp

    def store_pattern(self, name: str, pattern: dict, tags: List[str]) -> str:
        result = self.mcp.call_tool(
            "floyd-supercache", "cache_store_pattern",
            {"name": name, "pattern": pattern, "tags": tags, "category": "streamlit"},
        )
        return result.get("key", "")

    def search(self, query: str, tier: str = "all") -> List[dict]:
        result = self.mcp.call_tool(
            "floyd-supercache", "cache_search",
            {"query": query, "tier": tier, "limit": 20},
        )
        return result.get("results", [])

    def store_reasoning(self, context: str, reasoning: str, conclusion: str) -> str:
        result = self.mcp.call_tool(
            "floyd-supercache", "cache_store_reasoning",
            {"context": context, "reasoning": reasoning, "conclusion": conclusion},
        )
        return result.get("id", "")


class SafeOpsIntegration:
    """Integration with floyd-safe-ops for safe code modifications."""

    def __init__(self, mcp: MCPLabClient):
        self.mcp = mcp

    def refactor(self, operations: List[dict], verify_command: str, git_commit: bool = False) -> dict:
        return self.mcp.call_tool(
            "floyd-safe-ops", "safe_refactor",
            {"operations": operations, "verifyCommand": verify_command, "gitCommit": git_commit},
        )

    def simulate_impact(self, operations: List[dict], project_path: str) -> dict:
        return self.mcp.call_tool(
            "floyd-safe-ops", "impact_simulate",
            {"operations": operations, "resolvedProjectPath": project_path},
        )


class DevToolsIntegration:
    """Integration with floyd-devtools for code analysis."""

    def __init__(self, mcp: MCPLabClient):
        self.mcp = mcp

    def analyze_dependencies(self, project_path: str) -> dict:
        return self.mcp.call_tool(
            "floyd-devtools", "dependency_analyzer",
            {"action": "analyze", "project_path": project_path, "language": "python"},
        )

    def generate_tests(self, source_code: str, framework: str = "pytest") -> str:
        result = self.mcp.call_tool(
            "floyd-devtools", "test_generator",
            {"action": "generate", "source_code": source_code, "framework": framework},
        )
        return result.get("tests", "")


class ContextIntegration:
    """Integration with context-singularity for code indexing."""

    def __init__(self, mcp: MCPLabClient):
        self.mcp = mcp

    def ingest(self, root_path: str, pattern: str = "**/*.py") -> dict:
        return self.mcp.call_tool(
            "context-singularity", "ingest_codebase",
            {"root_path": root_path, "pattern": pattern},
        )

    def search(self, query: str, limit: int = 10) -> List[dict]:
        result = self.mcp.call_tool(
            "context-singularity", "ask",
            {"query": query, "limit": limit},
        )
        return result.get("results", [])


class PatternIntegration:
    """Integration with pattern-crystallizer for pattern learning."""

    def __init__(self, mcp: MCPLabClient):
        self.mcp = mcp

    def detect_and_crystallize(self, code: str, context: str, tags: List[str]) -> dict:
        return self.mcp.call_tool(
            "pattern-crystallizer", "detect_and_crystallize",
            {"code": code, "context": context, "language": "python", "tags": tags},
        )

    def adapt_pattern(self, query: str, current_context: str) -> List[dict]:
        result = self.mcp.call_tool(
            "pattern-crystallizer", "adapt_pattern",
            {"query": query, "current_context": current_context, "max_results": 5},
        )
        return result.get("patterns", [])

    def store_episode(self, trigger: str, reasoning: str, solution: str, outcome: str) -> str:
        result = self.mcp.call_tool(
            "pattern-crystallizer", "store_episode",
            {"trigger": trigger, "reasoning": reasoning, "solution": solution, "outcome": outcome},
        )
        return result.get("id", "")


class StreamlitForgeMCPIntegration:
    """Main integration class for all MCP services."""

    def __init__(self, endpoint: str = "http://localhost:8108/mcp"):
        self.mcp = MCPLabClient(endpoint)
        self.supercache = SupercacheIntegration(self.mcp)
        self.safe_ops = SafeOpsIntegration(self.mcp)
        self.devtools = DevToolsIntegration(self.mcp)
        self.context = ContextIntegration(self.mcp)
        self.patterns = PatternIntegration(self.mcp)

    def is_available(self) -> bool:
        return self.mcp.is_available()
