"""Project Manager for StreamlitForge project scaffolding.

Creates the project structure defined in PLANNING.md with:
- .streamlit/config.toml with assigned port
- src/ with app.py, pages/, components/, utils/
- tests/, assets/, data/, docs/
- requirements.txt, .gitignore, .env.example, run.sh, README.md
"""

import os
import stat
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional

from .port_manager import get_port_manager
from ..templates import BuiltInTemplates


class ProjectManager:
    """Creates and manages StreamlitForge projects."""

    PROJECTS_REGISTRY = Path.home() / ".streamlitforge" / "projects.json"

    def _load_registry(self) -> Dict:
        """Load the projects registry."""
        if self.PROJECTS_REGISTRY.exists():
            import json
            return json.loads(self.PROJECTS_REGISTRY.read_text())
        return {}

    def _save_registry(self, registry: Dict) -> None:
        """Save the projects registry."""
        import json
        self.PROJECTS_REGISTRY.parent.mkdir(parents=True, exist_ok=True)
        self.PROJECTS_REGISTRY.write_text(json.dumps(registry, indent=2))

    def list_projects(self) -> List[Dict]:
        """List all registered projects."""
        registry = self._load_registry()
        projects = []
        for path, info in registry.items():
            if Path(path).exists():
                projects.append({
                    "name": Path(path).name,
                    "path": path,
                    "port": info.get("port"),
                    "created": info.get("created", ""),
                })
        return projects

    def _register_project(self, project_dir: Path, port: int) -> None:
        """Register a project in the registry."""
        from datetime import datetime
        registry = self._load_registry()
        registry[str(project_dir)] = {
            "port": port,
            "created": datetime.now().isoformat(),
        }
        self._save_registry(registry)

    def create_project(
        self,
        project_name: str,
        parent_dir: Optional[str] = None,
        template: Optional[str] = None,
        dependencies: Optional[List[str]] = None,
        create_venv: bool = True,
        force: bool = False,
    ) -> Path:
        """Create a new Streamlit project.

        Returns the Path to the created project directory.
        """
        parent = Path(parent_dir).resolve() if parent_dir else Path.cwd().resolve()
        project_dir = parent / project_name

        if project_dir.exists() and not force:
            raise FileExistsError(
                f"Project already exists: {project_dir}. Use force=True to overwrite."
            )

        if project_dir.exists() and force:
            import shutil
            shutil.rmtree(project_dir)

        # Get a deterministic port
        pm = get_port_manager()
        port = pm.get_port(str(project_dir))

        # Build directory tree
        self._create_dirs(project_dir)

        # Render files
        self._write_streamlit_config(project_dir, port)
        self._write_app(project_dir, project_name, template)
        self._write_requirements(project_dir, dependencies)
        self._write_gitignore(project_dir)
        self._write_env_example(project_dir)
        self._write_run_sh(project_dir)
        self._write_readme(project_dir, project_name, port)
        self._write_init_files(project_dir)
        self._write_helpers(project_dir)
        self._write_app_config(project_dir, project_name)
        self._write_test_stub(project_dir, project_name)

        # Virtual environment (optional — callers may skip for speed)
        if create_venv:
            self._create_venv(project_dir)

        # Register the project
        self._register_project(project_dir, port)

        return project_dir

    def get_project_info(self, project_path: str) -> Dict:
        """Return info dict about an existing project."""
        p = Path(project_path).resolve()
        if not p.exists():
            raise FileNotFoundError(f"Project not found: {project_path}")

        pm = get_port_manager()
        port = pm.lookup(str(p))
        file_count = sum(1 for _ in p.rglob("*") if _.is_file())

        info: Dict = {
            "name": p.name,
            "path": str(p),
            "port": port,
            "files": file_count,
        }

        config_toml = p / ".streamlit" / "config.toml"
        if config_toml.exists():
            info["streamlit_config"] = config_toml.read_text()

        return info

    def delete_project(self, project_path: str) -> None:
        """Delete project directory and release its port."""
        import shutil
        p = Path(project_path).resolve()
        if not p.exists():
            raise FileNotFoundError(f"Project not found: {project_path}")
        get_port_manager().release_port(str(p))
        shutil.rmtree(p)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _create_dirs(root: Path) -> None:
        for d in [
            ".streamlit",
            "src/pages",
            "src/components",
            "src/utils",
            "tests",
            "assets",
            "data",
            "docs",
        ]:
            (root / d).mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _write_streamlit_config(root: Path, port: int) -> None:
        (root / ".streamlit" / "config.toml").write_text(
            f"""[server]
port = {port}
headless = true
runOnSave = true

[theme]
primaryColor = "#00D4FF"
backgroundColor = "#0D0D0D"
secondaryBackgroundColor = "#1A0A1F"
textColor = "#F8F8F8"

[client]
showErrorDetails = false
toolbarMode = "minimal"
""",
            encoding="utf-8",
        )

    @staticmethod
    def _write_app(root: Path, project_name: str, template: Optional[str]) -> None:
        if template:
            try:
                content = BuiltInTemplates.get_template(template)
            except Exception:
                content = _default_app(project_name)
        else:
            content = _default_app(project_name)
        (root / "src" / "app.py").write_text(content, encoding="utf-8")

    @staticmethod
    def _write_requirements(root: Path, extra: Optional[List[str]]) -> None:
        base = ["streamlit>=1.28.0"]
        all_deps = base + (extra or [])
        (root / "requirements.txt").write_text(
            "\n".join(all_deps) + "\n", encoding="utf-8"
        )

    @staticmethod
    def _write_gitignore(root: Path) -> None:
        (root / ".gitignore").write_text(
            """__pycache__/
*.py[cod]
.venv/
venv/
.env
.DS_Store
*.egg-info/
dist/
build/
""",
            encoding="utf-8",
        )

    @staticmethod
    def _write_env_example(root: Path) -> None:
        (root / ".env.example").write_text(
            """# LLM provider keys (optional)
# OPENROUTER_API_KEY=sk-or-...
# OPENAI_API_KEY=sk-...
# GROQ_API_KEY=gsk_...
""",
            encoding="utf-8",
        )

    @staticmethod
    def _write_run_sh(root: Path) -> None:
        run_sh = root / "run.sh"
        run_sh.write_text(
            """#!/bin/bash
source .venv/bin/activate 2>/dev/null || source venv/bin/activate 2>/dev/null || true
streamlit run src/app.py
""",
            encoding="utf-8",
        )
        run_sh.chmod(run_sh.stat().st_mode | stat.S_IEXEC)

    @staticmethod
    def _write_readme(root: Path, name: str, port: int) -> None:
        (root / "README.md").write_text(
            f"""# {name}

Streamlit application created with **StreamlitForge**.

## Quick Start

```bash
source .venv/bin/activate
pip install -r requirements.txt
streamlit run src/app.py          # opens on port {port}
```

## Project Layout

| Directory | Purpose |
|-----------|---------|
| `src/` | Application source code |
| `src/pages/` | Multi-page Streamlit pages |
| `src/components/` | Reusable UI components |
| `tests/` | Test suite |
| `assets/` | Static assets (images, CSS) |
| `data/` | Sample / user data |
| `docs/` | Documentation |
""",
            encoding="utf-8",
        )

    @staticmethod
    def _write_init_files(root: Path) -> None:
        for d in ["src", "src/pages", "src/components", "src/utils", "tests"]:
            init = root / d / "__init__.py"
            if not init.exists():
                init.write_text("", encoding="utf-8")

    @staticmethod
    def _write_helpers(root: Path) -> None:
        (root / "src" / "utils" / "helpers.py").write_text(
            '''"""Shared helpers."""


def format_number(n: float, decimals: int = 2) -> str:
    """Return a human-friendly number string."""
    if abs(n) >= 1_000_000:
        return f"{n / 1_000_000:.{decimals}f}M"
    if abs(n) >= 1_000:
        return f"{n / 1_000:.{decimals}f}K"
    return f"{n:.{decimals}f}"
''',
            encoding="utf-8",
        )

    @staticmethod
    def _write_app_config(root: Path, project_name: str) -> None:
        (root / "src" / "config.py").write_text(
            f'''"""Application configuration."""

APP_NAME = "{project_name}"
APP_ICON = "🚀"
LAYOUT = "wide"
''',
            encoding="utf-8",
        )

    @staticmethod
    def _write_test_stub(root: Path, name: str) -> None:
        (root / "tests" / "test_app.py").write_text(
            f'''"""Smoke tests for {name}."""


def test_import():
    """Ensure the src package is importable."""
    import src  # noqa: F401
''',
            encoding="utf-8",
        )

    @staticmethod
    def _create_venv(root: Path) -> None:
        venv_dir = root / ".venv"
        if venv_dir.exists():
            return
        try:
            subprocess.run(
                [sys.executable, "-m", "venv", str(venv_dir)],
                check=True,
                capture_output=True,
                timeout=120,
            )
        except subprocess.TimeoutExpired:
            pass  # non-fatal: user can create venv manually
        except subprocess.CalledProcessError:
            pass  # non-fatal


# ------------------------------------------------------------------
# Default app template (when no --template is given)
# ------------------------------------------------------------------

def _default_app(project_name: str) -> str:
    return f'''"""Streamlit application — {project_name}."""

import streamlit as st

st.set_page_config(
    page_title="{project_name}",
    page_icon="🚀",
    layout="wide",
)

st.title("{project_name}")

st.markdown("""
Welcome to **{project_name}**, built with StreamlitForge.
""")

with st.sidebar:
    st.header("Settings")
    user_input = st.text_input("Enter something")
    if user_input:
        st.success(f"You entered: {{user_input}}")

st.header("Main Content")

import pandas as pd, numpy as np

df = pd.DataFrame(np.random.randn(50, 3), columns=["A", "B", "C"])
st.dataframe(df)
st.line_chart(df)
'''
