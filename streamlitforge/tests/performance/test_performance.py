"""Performance tests for StreamlitForge.

Uses simple timing instead of pytest-benchmark to avoid extra dependencies.
"""
import time

from streamlitforge.core.port_manager import PortManager
from streamlitforge.core.project_manager import ProjectManager


class TestPerformance:
    """Performance checks with plain timing."""

    def test_port_lookup_speed(self):
        """Port lookup should complete quickly."""
        pm = PortManager()
        test_path = "/tmp/streamlitforge_perf_test"

        start = time.perf_counter()
        port = pm.get_port(test_path)
        elapsed = time.perf_counter() - start

        assert 8501 <= port <= 8999
        assert elapsed < 1.0, f"Port lookup took {elapsed:.3f}s"
        pm.release_port(test_path)

    def test_project_creation_speed(self, tmp_path):
        """Project creation should complete quickly."""
        pm = ProjectManager()

        start = time.perf_counter()
        result = pm.create_project(
            project_name="perf-test",
            parent_dir=str(tmp_path),
            create_venv=False,
        )
        elapsed = time.perf_counter() - start

        assert result.exists()
        assert elapsed < 5.0, f"Project creation took {elapsed:.3f}s"

    def test_large_project_list(self):
        """Listing projects should return a list quickly."""
        pm = ProjectManager()

        start = time.perf_counter()
        result = pm.list_projects()
        elapsed = time.perf_counter() - start

        assert isinstance(result, list)
        assert elapsed < 2.0, f"List took {elapsed:.3f}s"

    def test_knowledge_base_search_speed(self):
        """Knowledge base search should complete quickly."""
        from streamlitforge.knowledge.streamlit_kb import StreamlitKnowledgeBase

        kb = StreamlitKnowledgeBase()

        start = time.perf_counter()
        result = kb.search_examples("chat interface")
        elapsed = time.perf_counter() - start

        assert isinstance(result, list)
        assert elapsed < 2.0, f"Search took {elapsed:.3f}s"

    def test_pattern_learner_load_speed(self):
        """Pattern learner initialization should complete quickly."""
        from streamlitforge.patterns.learner import PatternLearner

        start = time.perf_counter()
        result = PatternLearner()
        elapsed = time.perf_counter() - start

        assert result is not None
        assert result.get_builtin_pattern_count() > 0
        assert elapsed < 2.0, f"Init took {elapsed:.3f}s"
