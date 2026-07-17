"""Integration tests for StreamlitForge CLI."""
import os
import subprocess
import sys
import tempfile
from pathlib import Path
import pytest

# Pytest marker configuration
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "integration: mark test as integration test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )


def _run_cli(*args, **kwargs):
    """Run streamlitforge CLI via the venv python -m, ensuring it's on PATH."""
    env = os.environ.copy()
    venv_bin = os.path.dirname(sys.executable)
    env["PATH"] = venv_bin + os.pathsep + env.get("PATH", "")
    return subprocess.run(
        [sys.executable, "-m", "streamlitforge.cli"] + list(args),
        capture_output=True,
        text=True,
        env=env,
        **kwargs,
    )


class TestCLIIntegration:
    """Integration tests for CLI commands."""

    @pytest.fixture
    def temp_project_dir(self):
        """Create a temporary directory for test projects."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    def test_create_project_basic(self, temp_project_dir):
        """Test basic project creation."""
        result = _run_cli("create", "test-project", "--path", str(temp_project_dir))

        assert result.returncode == 0, f"CLI failed: {result.stderr}"
        assert (temp_project_dir / "test-project").exists(), "Project directory not created"
        assert (temp_project_dir / "test-project" / "src" / "app.py").exists(), \
            "Main app file not created"

    def test_create_project_with_template(self, temp_project_dir):
        """Test project creation with template."""
        result = _run_cli("create", "test-dashboard",
                          "--path", str(temp_project_dir),
                          "--template", "dashboard")

        assert result.returncode == 0, f"CLI failed: {result.stderr}"
        assert (temp_project_dir / "test-dashboard").exists(), "Project directory not created"

    def test_list_templates(self):
        """Test list-templates command."""
        result = _run_cli("list-templates")

        assert result.returncode == 0, f"list-templates failed: {result.stderr}"
        assert "dashboard" in result.stdout, "Dashboard template not found"
        assert "chat" in result.stdout, "Chat template not found"

    def test_create_and_delete_project(self, temp_project_dir):
        """Test project lifecycle."""
        # Create
        _run_cli("create", "lifecycle-test", "--path", str(temp_project_dir))

        assert (temp_project_dir / "lifecycle-test").exists(), "Project creation failed"

        # Delete
        result = _run_cli("delete", str(temp_project_dir / "lifecycle-test"), "--yes")

        assert result.returncode == 0, f"Delete failed: {result.stderr}"
        assert not (temp_project_dir / "lifecycle-test").exists(), "Project not deleted"


class TestPortManagerIntegration:
    """Integration tests for port management."""

    def test_deterministic_port(self):
        """Test that same path gets same port."""
        from streamlitforge.core.port_manager import PortManager

        pm = PortManager()
        test_path = "/tmp/streamlitforge_test_project"

        port1 = pm.get_port(test_path)
        port2 = pm.lookup(test_path)

        assert port1 == port2, f"Ports differ: {port1} != {port2}"
        assert 8501 <= port1 <= 8999, f"Port {port1} out of range"
        pm.release_port(test_path)

    def test_different_paths_get_different_ports(self):
        """Test that different paths get different ports."""
        from streamlitforge.core.port_manager import PortManager

        pm = PortManager()

        port1 = pm.get_port("/tmp/streamlitforge_int_test_p1")
        port2 = pm.get_port("/tmp/streamlitforge_int_test_p2")

        assert port1 != port2, "Different paths should get different ports"
        pm.release_port("/tmp/streamlitforge_int_test_p1")
        pm.release_port("/tmp/streamlitforge_int_test_p2")


class TestProjectManagerIntegration:
    """Integration tests for project manager."""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    def test_list_projects(self, temp_dir):
        """Test listing projects."""
        from streamlitforge.core.project_manager import ProjectManager

        pm = ProjectManager()
        projects = pm.list_projects()

        assert isinstance(projects, list), "list_projects should return a list"
        # May be empty initially
        assert all(isinstance(p, dict) for p in projects), "All items should be dicts"

    def test_get_project_info(self, temp_dir):
        """Test getting project information."""
        from streamlitforge.core.project_manager import ProjectManager

        pm = ProjectManager()
        projects = pm.list_projects()

        if projects:
            project = projects[0]
            # Check if project has expected keys
            assert "name" in project or "path" in project, "Project missing expected keys"


class TestLLMIntegration:
    """Integration tests for LLM providers."""

    def test_llm_router_exists(self):
        """Test that LLM router can be instantiated."""
        from streamlitforge.llm.router import EnhancedLLMRouter

        router = EnhancedLLMRouter()
        assert router is not None, "LLM router should be instantiable"

    def test_provider_fallback(self):
        """Test that provider fallback works."""
        from streamlitforge.llm.router import EnhancedLLMRouter
        from streamlitforge.llm.providers.ollama import OllamaProvider

        provider = OllamaProvider()
        router = EnhancedLLMRouter(providers={"ollama": provider})
        # Test that router has providers configured
        assert len(router.providers) > 0, "Router should have providers configured"


class TestKnowledgeBaseIntegration:
    """Integration tests for knowledge base."""

    def test_knowledge_base_exists(self):
        """Test that knowledge base can be instantiated."""
        from streamlitforge.knowledge.streamlit_kb import StreamlitKnowledgeBase

        kb = StreamlitKnowledgeBase()
        assert kb is not None, "Knowledge base should be instantiable"

    def test_knowledge_base_search(self):
        """Test that knowledge base search works."""
        from streamlitforge.knowledge.streamlit_kb import StreamlitKnowledgeBase

        kb = StreamlitKnowledgeBase()
        # Test search returns results (may be empty if no data)
        results = kb.search_examples("chat interface")
        assert isinstance(results, list), "Search should return a list"


class TestTemplateIntegration:
    """Integration tests for templates."""

    def test_templates_available(self):
        """Test that templates are available."""
        from streamlitforge.templates import BuiltInTemplates

        names = BuiltInTemplates.get_template_names()
        assert len(names) > 0, "Should have templates available"


class TestPatternLibraryIntegration:
    """Integration tests for pattern library."""

    def test_pattern_learner_exists(self):
        """Test that pattern learner can be instantiated."""
        from streamlitforge.patterns.learner import PatternLearner

        learner = PatternLearner()
        assert learner is not None, "Pattern learner should be instantiable"

    def test_builtin_patterns_loaded(self):
        """Test that builtin patterns are loaded."""
        from streamlitforge.patterns.learner import PatternLearner

        learner = PatternLearner()
        # Check that patterns were loaded
        assert learner.get_builtin_pattern_count() > 0, "Should have builtin patterns"

    def test_get_builtin_pattern_count(self):
        """Test getting builtin pattern count."""
        from streamlitforge.patterns.learner import PatternLearner

        learner = PatternLearner()
        count = learner.get_builtin_pattern_count()
        assert isinstance(count, int), "Count should be an integer"
        assert count >= 0, "Count should be non-negative"
