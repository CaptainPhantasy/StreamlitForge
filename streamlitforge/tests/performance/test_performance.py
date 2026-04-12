"""Performance tests for StreamlitForge."""
import time
import tempfile
from pathlib import Path
import pytest

from streamlitforge.core.port_manager import PortManager
from streamlitforge.core.project_manager import ProjectManager


class TestPerformance:
    """Performance benchmarks."""

    def test_port_lookup_speed(self, benchmark):
        """Benchmark port lookup speed."""
        pm = PortManager()

        result = benchmark(pm.lookup, "/tmp/test-project")

        assert 8501 <= result <= 8999

    def test_project_creation_speed(self, benchmark, tmp_path):
        """Benchmark project creation speed."""
        pm = ProjectManager()

        def create_project():
            return pm.create_project(
                project_name="perf-test",
                parent_dir=str(tmp_path),
                create_venv=False,  # Skip venv for speed
            )

        result = benchmark(create_project)
        assert result.exists()

    def test_large_project_list(self, benchmark):
        """Benchmark listing many projects."""
        pm = ProjectManager()

        result = benchmark(pm.list_projects)
        assert isinstance(result, list)

    def test_knowledge_base_search_speed(self, benchmark):
        """Benchmark knowledge base search speed."""
        from streamlitforge.knowledge import StreamlitKnowledgeBase

        kb = StreamlitKnowledgeBase()

        def search_knowledge():
            return kb.search("chat interface")

        result = benchmark(search_knowledge)
        assert isinstance(result, list)

    def test_pattern_learner_load_speed(self, benchmark):
        """Benchmark pattern learner initialization."""
        from streamlitforge.patterns.learner import PatternLearner

        result = benchmark(PatternLearner)
        assert result is not None
        assert result.get_builtin_pattern_count() > 0
