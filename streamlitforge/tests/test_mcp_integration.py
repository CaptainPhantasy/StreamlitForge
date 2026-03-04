"""Tests for MCP Integration Layer — no mocks, real functional calls."""

import unittest

from streamlitforge.mcp_integration import (
    MCPLabClient,
    MCPToolError,
    SupercacheIntegration,
    SafeOpsIntegration,
    DevToolsIntegration,
    ContextIntegration,
    PatternIntegration,
    StreamlitForgeMCPIntegration,
)


class TestMCPLabClient(unittest.TestCase):
    def test_default_endpoint(self):
        client = MCPLabClient()
        self.assertEqual(client.endpoint, "http://localhost:8108/mcp")

    def test_custom_endpoint(self):
        client = MCPLabClient(endpoint="http://myserver:9000/mcp")
        self.assertEqual(client.endpoint, "http://myserver:9000/mcp")

    def test_initial_request_id(self):
        client = MCPLabClient()
        self.assertEqual(client.request_id, 0)

    def test_timeout_default(self):
        client = MCPLabClient()
        self.assertEqual(client.timeout, 30.0)

    def test_is_available_returns_false_when_no_server(self):
        client = MCPLabClient(endpoint="http://localhost:1/mcp")
        self.assertFalse(client.is_available())

    def test_call_tool_raises_on_connection_error(self):
        client = MCPLabClient(endpoint="http://localhost:1/mcp")
        client.timeout = 1.0
        with self.assertRaises(MCPToolError):
            client.call_tool("server", "tool", {})


class TestMCPToolError(unittest.TestCase):
    def test_is_exception(self):
        self.assertTrue(issubclass(MCPToolError, Exception))

    def test_message(self):
        err = MCPToolError("something failed")
        self.assertEqual(str(err), "something failed")


class TestSupercacheIntegration(unittest.TestCase):
    def setUp(self):
        self.client = MCPLabClient(endpoint="http://localhost:1/mcp")
        self.client.timeout = 1.0
        self.sc = SupercacheIntegration(self.client)

    def test_has_mcp_reference(self):
        self.assertIs(self.sc.mcp, self.client)

    def test_store_pattern_raises_on_no_server(self):
        with self.assertRaises(MCPToolError):
            self.sc.store_pattern("test", {"code": "x"}, ["tag"])

    def test_search_raises_on_no_server(self):
        with self.assertRaises(MCPToolError):
            self.sc.search("query")

    def test_store_reasoning_raises_on_no_server(self):
        with self.assertRaises(MCPToolError):
            self.sc.store_reasoning("ctx", "reason", "conclusion")


class TestSafeOpsIntegration(unittest.TestCase):
    def setUp(self):
        self.client = MCPLabClient(endpoint="http://localhost:1/mcp")
        self.client.timeout = 1.0
        self.so = SafeOpsIntegration(self.client)

    def test_has_mcp_reference(self):
        self.assertIs(self.so.mcp, self.client)

    def test_refactor_raises_on_no_server(self):
        with self.assertRaises(MCPToolError):
            self.so.refactor([{"type": "edit", "path": "/tmp/x"}], "pytest")

    def test_simulate_impact_raises_on_no_server(self):
        with self.assertRaises(MCPToolError):
            self.so.simulate_impact([{"type": "edit", "path": "/tmp/x"}], "/tmp")


class TestDevToolsIntegration(unittest.TestCase):
    def setUp(self):
        self.client = MCPLabClient(endpoint="http://localhost:1/mcp")
        self.client.timeout = 1.0
        self.dt = DevToolsIntegration(self.client)

    def test_has_mcp_reference(self):
        self.assertIs(self.dt.mcp, self.client)

    def test_analyze_dependencies_raises_on_no_server(self):
        with self.assertRaises(MCPToolError):
            self.dt.analyze_dependencies("/tmp/project")

    def test_generate_tests_raises_on_no_server(self):
        with self.assertRaises(MCPToolError):
            self.dt.generate_tests("def foo(): pass")


class TestContextIntegration(unittest.TestCase):
    def setUp(self):
        self.client = MCPLabClient(endpoint="http://localhost:1/mcp")
        self.client.timeout = 1.0
        self.ctx = ContextIntegration(self.client)

    def test_has_mcp_reference(self):
        self.assertIs(self.ctx.mcp, self.client)

    def test_ingest_raises_on_no_server(self):
        with self.assertRaises(MCPToolError):
            self.ctx.ingest("/tmp/project")

    def test_search_raises_on_no_server(self):
        with self.assertRaises(MCPToolError):
            self.ctx.search("query")


class TestPatternIntegration(unittest.TestCase):
    def setUp(self):
        self.client = MCPLabClient(endpoint="http://localhost:1/mcp")
        self.client.timeout = 1.0
        self.pi = PatternIntegration(self.client)

    def test_has_mcp_reference(self):
        self.assertIs(self.pi.mcp, self.client)

    def test_detect_and_crystallize_raises_on_no_server(self):
        with self.assertRaises(MCPToolError):
            self.pi.detect_and_crystallize("code", "context", ["tag"])

    def test_adapt_pattern_raises_on_no_server(self):
        with self.assertRaises(MCPToolError):
            self.pi.adapt_pattern("query", "context")

    def test_store_episode_raises_on_no_server(self):
        with self.assertRaises(MCPToolError):
            self.pi.store_episode("trigger", "reasoning", "solution", "success")


class TestStreamlitForgeMCPIntegration(unittest.TestCase):
    def test_default_init(self):
        mcp = StreamlitForgeMCPIntegration()
        self.assertIsInstance(mcp.mcp, MCPLabClient)
        self.assertIsInstance(mcp.supercache, SupercacheIntegration)
        self.assertIsInstance(mcp.safe_ops, SafeOpsIntegration)
        self.assertIsInstance(mcp.devtools, DevToolsIntegration)
        self.assertIsInstance(mcp.context, ContextIntegration)
        self.assertIsInstance(mcp.patterns, PatternIntegration)

    def test_custom_endpoint(self):
        mcp = StreamlitForgeMCPIntegration(endpoint="http://custom:9000/mcp")
        self.assertEqual(mcp.mcp.endpoint, "http://custom:9000/mcp")

    def test_is_available_returns_false_no_server(self):
        mcp = StreamlitForgeMCPIntegration(endpoint="http://localhost:1/mcp")
        self.assertFalse(mcp.is_available())

    def test_all_integrations_share_client(self):
        mcp = StreamlitForgeMCPIntegration()
        self.assertIs(mcp.supercache.mcp, mcp.mcp)
        self.assertIs(mcp.safe_ops.mcp, mcp.mcp)
        self.assertIs(mcp.devtools.mcp, mcp.mcp)
        self.assertIs(mcp.context.mcp, mcp.mcp)
        self.assertIs(mcp.patterns.mcp, mcp.mcp)


if __name__ == "__main__":
    unittest.main()
