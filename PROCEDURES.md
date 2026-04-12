# StreamlitForge Production Roadmap Procedures

**Created:** 2026-03-04
**Status:** Active
**Constraint:** No CI/CD until all tests pass locally

---

## Pre-Phase Requirements

Before starting Phase 1, complete these prerequisites:

```bash
# PREREQ-1: Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# PREREQ-2: Install all dependencies
pip install -e ".[dev]"
pip install -r requirements.txt
pip install -r requirements-dev.txt

# PREREQ-3: Verify installation
pip list | grep -E "pytest|streamlit|click|jinja"

# Expected output should include:
# pytest, streamlit, click, jinja2, black, flake8, mypy
```

---

## Phase 1: Foundation (Week 1-2)

### 1.1 Verify All Tests Pass

**Objective:** Ensure test suite runs successfully before any CI/CD setup.

#### Procedure

```bash
# STEP 1.1.1: Activate virtual environment
source .venv/bin/activate

# STEP 1.1.2: Run full test suite with verbose output
python -m pytest streamlitforge/tests/ -v --tb=short

# STEP 1.1.3: Run with coverage report
python -m pytest streamlitforge/tests/ -v --cov=streamlitforge --cov-report=term-missing

# STEP 1.1.4: Save test results
python -m pytest streamlitforge/tests/ -v --tb=short > test_results_baseline.txt 2>&1
```

#### Verification

```bash
# VERIFY 1.1.1: Check exit code
echo $?  # Should be 0

# VERIFY 1.1.2: Count passed vs failed
grep -E "passed|failed|error" test_results_baseline.txt
```

#### If Tests Fail

```bash
# ROLLBACK 1.1.1: Document failures
python -m pytest streamlitforge/tests/ -v --tb=long > test_failures_detail.txt 2>&1

# ROLLBACK 1.1.2: Fix failing tests BEFORE proceeding
# Do NOT continue to next step until all tests pass
```

#### Success Criteria

- [ ] All tests pass (exit code 0)
- [ ] No skipped tests (unless intentionally skipped)
- [ ] Coverage report generated
- [ ] Baseline results saved

---

### 1.2 Replace Print Statements with Logging

**Objective:** Implement proper logging throughout the codebase.

#### Procedure

```bash
# STEP 1.2.1: Find all print statements
grep -rn "print(" --include="*.py" . > print_statements.txt

# STEP 1.2.2: Review each file
cat print_statements.txt
```

#### Files to Modify

Based on assessment, these files contain print statements:

| File | Print Count | Action |
|------|-------------|--------|
| `streamlitforge/cli.py` | ~3 | Replace with click.echo() or logging |
| `streamlitforge/core/*.py` | ~2 | Add logging |
| `app/pages/*.py` | ~2 | Use st.write() for Streamlit |

#### Implementation Pattern

```python
# BEFORE
print(f"Processing {file}")

# AFTER (for CLI modules)
import logging
logger = logging.getLogger(__name__)
logger.info(f"Processing {file}")

# AFTER (for Streamlit pages - keep as st.write)
st.write(f"Processing {file}")  # This is correct for Streamlit
```

#### Create Logging Configuration

Create `streamlitforge/utils/logging_config.py`:

```python
"""Logging configuration for StreamlitForge."""
import logging
import sys
from pathlib import Path

def setup_logging(level: str = "INFO", log_file: str = None):
    """Setup logging configuration.
    
    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional log file path
    """
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    handlers = [logging.StreamHandler(sys.stdout)]
    
    if log_file:
        Path(log_file).parent.mkdir(parents=True, exist_ok=True)
        handlers.append(logging.FileHandler(log_file))
    
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format=log_format,
        handlers=handlers,
    )
    
    # Reduce noise from third-party libraries
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)
```

#### Update CLI Entry Point

In `streamlitforge/cli.py`, add at the top of main():

```python
from streamlitforge.utils.logging_config import setup_logging

@click.group()
@click.option("--debug", is_flag=True, help="Enable debug logging")
@click.pass_context
def cli(ctx, debug):
    """StreamlitForge — AI-Powered Streamlit Application Builder CLI."""
    level = "DEBUG" if debug else "INFO"
    setup_logging(level=level)
    ctx.ensure_object(dict)
```

#### Verification

```bash
# VERIFY 1.2.1: Run CLI with debug
python -m streamlitforge.cli --debug --help

# VERIFY 1.2.2: Check no print statements remain in core modules
grep -rn "print(" --include="*.py" streamlitforge/core/ streamlitforge/cli.py || echo "Clean"

# VERIFY 1.2.3: Run tests again
python -m pytest streamlitforge/tests/ -v --tb=short
```

#### Success Criteria

- [ ] No print() statements in core modules (cli.py, core/*.py)
- [ ] Logging configuration module created
- [ ] CLI supports --debug flag
- [ ] All tests still pass

---

### 1.3 Add Security Scanning

**Objective:** Integrate security scanning tools.

#### Procedure

```bash
# STEP 1.3.1: Install security tools
pip install bandit safety pip-audit

# STEP 1.3.2: Run bandit scan
bandit -r streamlitforge/ -f json -o security_bandit.json
bandit -r streamlitforge/ -f txt

# STEP 1.3.3: Run safety check
safety check --json > security_safety.json 2>&1 || true
safety check

# STEP 1.3.4: Run pip-audit
pip-audit --format json > security_pip_audit.json 2>&1 || true
pip-audit
```

#### Create Security Scan Script

Create `scripts/security_scan.sh`:

```bash
#!/bin/bash
# Security scanning script for StreamlitForge

set -e

echo "=== Running Security Scans ==="

echo ""
echo "1. Bandit (code security)"
bandit -r streamlitforge/ -f txt || true

echo ""
echo "2. Safety (dependency vulnerabilities)"
safety check || true

echo ""
echo "3. pip-audit (dependency audit)"
pip-audit || true

echo ""
echo "=== Security Scan Complete ==="
```

```bash
chmod +x scripts/security_scan.sh
```

#### Create Security Configuration

Create `bandit.yaml`:

```yaml
# Bandit security scanner configuration
targets:
  - streamlitforge

exclude_dirs:
  - streamlitforge/tests
  - .venv
  - venv

skips:
  - B101  # assert_used (OK in tests)
```

#### Verification

```bash
# VERIFY 1.3.1: Run security scan script
./scripts/security_scan.sh

# VERIFY 1.3.2: Check for HIGH severity issues
cat security_bandit.json | python -m json.tool | grep -i "HIGH" || echo "No high severity issues"
```

#### Success Criteria

- [ ] Bandit scan runs without errors
- [ ] Safety check runs
- [ ] No HIGH severity issues (or documented exceptions)
- [ ] Security scan script created

---

### 1.4 Add Dockerfile and docker-compose

**Objective:** Containerize the application.

#### Create Dockerfile

Create `Dockerfile`:

```dockerfile
# StreamlitForge Docker Image
# Multi-stage build for optimized image size

# ============================================
# Stage 1: Builder
# ============================================
FROM python:3.11-slim as builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Install the package
COPY . .
RUN pip install --no-cache-dir -e ".[dev]"

# ============================================
# Stage 2: Runtime
# ============================================
FROM python:3.11-slim as runtime

WORKDIR /app

# Create non-root user
RUN useradd --create-home --shell /bin/bash appuser

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy application code
COPY --chown=appuser:appuser . /app

# Switch to non-root user
USER appuser

# Expose default Streamlit port
EXPOSE 8501

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import streamlitforge; print('healthy')" || exit 1

# Default command
CMD ["streamlitforge", "--help"]
```

#### Create docker-compose.yml

Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  streamlitforge:
    build:
      context: .
      dockerfile: Dockerfile
    image: streamlitforge:latest
    container_name: streamlitforge
    ports:
      - "8501:8501"
    volumes:
      - ./projects:/app/projects
      - streamlitforge-data:/home/appuser/.streamlitforge
    environment:
      - STREAMLITFORGE_LOG_LEVEL=INFO
    command: streamlitforge --help

  # Development service with hot reload
  streamlitforge-dev:
    build:
      context: .
      dockerfile: Dockerfile
    image: streamlitforge:dev
    container_name: streamlitforge-dev
    ports:
      - "8502:8501"
    volumes:
      - .:/app
      - streamlitforge-data:/home/appuser/.streamlitforge
    environment:
      - STREAMLITFORGE_LOG_LEVEL=DEBUG
    command: python -m streamlitforge.cli --debug --help

  # Test runner service
  streamlitforge-test:
    build:
      context: .
      dockerfile: Dockerfile
    image: streamlitforge:test
    container_name: streamlitforge-test
    volumes:
      - .:/app
    command: python -m pytest streamlitforge/tests/ -v

volumes:
  streamlitforge-data:
```

#### Create .dockerignore

Create `.dockerignore`:

```
# Git
.git
.gitignore

# Python
__pycache__
*.py[cod]
*$py.class
*.so
.Python
.venv
venv/
ENV/

# Testing
.pytest_cache
.coverage
htmlcov/
.tox/
.hypothesis/

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Build artifacts
dist/
build/
*.egg-info/

# Security files (should not be in image)
.env
*.pem
*.key
secrets.toml

# Documentation
docs/
*.md
!README.md

# Test results
test_results*.txt
security_*.json
```

#### Verification

```bash
# VERIFY 1.4.1: Build Docker image
docker build -t streamlitforge:test .

# VERIFY 1.4.2: Run container
docker run --rm streamlitforge:test streamlitforge --version

# VERIFY 1.4.3: Run tests in container
docker run --rm streamlitforge:test python -m pytest streamlitforge/tests/ -v

# VERIFY 1.4.4: Test docker-compose
docker-compose up -d streamlitforge
docker-compose ps
docker-compose down
```

#### Success Criteria

- [ ] Dockerfile builds successfully
- [ ] Container runs streamlitforge CLI
- [ ] Tests pass in container
- [ ] docker-compose works
- [ ] Image size < 500MB

---

### 1.5 Set Up CI/CD Pipeline (ONLY AFTER TESTS PASS)

**CRITICAL:** This step is ONLY executed after 1.1-1.4 are complete and all tests pass.

#### Create GitHub Actions Workflow

Create `.github/workflows/ci.yml`:

```yaml
name: CI/CD Pipeline

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main, develop ]

# Cancel in-progress runs for the same branch
concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true

jobs:
  # ==========================================
  # Job 1: Code Quality
  # ==========================================
  lint:
    name: Code Quality
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
          cache: 'pip'
      
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install black flake8 mypy
          pip install -e ".[dev]"
      
      - name: Run Black
        run: black --check streamlitforge/ app/
      
      - name: Run Flake8
        run: flake8 streamlitforge/ app/ --count --select=E9,F63,F7,F82 --show-source --statistics
      
      - name: Run MyPy
        run: mypy streamlitforge/ --ignore-missing-imports || true

  # ==========================================
  # Job 2: Security Scan
  # ==========================================
  security:
    name: Security Scan
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
          cache: 'pip'
      
      - name: Install security tools
        run: |
          python -m pip install --upgrade pip
          pip install bandit safety pip-audit
          pip install -e "."
      
      - name: Run Bandit
        run: bandit -r streamlitforge/ -f json -o bandit-report.json || true
        continue-on-error: true
      
      - name: Run Safety
        run: safety check --json || true
        continue-on-error: true
      
      - name: Run pip-audit
        run: pip-audit --format json || true
        continue-on-error: true
      
      - name: Upload security reports
        uses: actions/upload-artifact@v4
        with:
          name: security-reports
          path: |
            bandit-report.json
          retention-days: 30

  # ==========================================
  # Job 3: Test Suite
  # ==========================================
  test:
    name: Test Suite (Python ${{ matrix.python-version }})
    runs-on: ubuntu-latest
    needs: [lint]  # Only run if lint passes
    strategy:
      matrix:
        python-version: ['3.8', '3.9', '3.10', '3.11', '3.12']
      fail-fast: false
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python ${{ matrix.python-version }}
        uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
          cache: 'pip'
      
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -e ".[dev]"
          pip install pytest-cov
      
      - name: Run tests
        run: |
          python -m pytest streamlitforge/tests/ -v \
            --cov=streamlitforge \
            --cov-report=xml \
            --cov-report=term-missing \
            --junitxml=test-results.xml
      
      - name: Upload coverage
        uses: codecov/codecov-action@v4
        if: matrix.python-version == '3.11'
        with:
          files: ./coverage.xml
          fail_ci_if_error: false
      
      - name: Upload test results
        uses: actions/upload-artifact@v4
        if: always()
        with:
          name: test-results-${{ matrix.python-version }}
          path: test-results.xml
          retention-days: 30

  # ==========================================
  # Job 4: Docker Build
  # ==========================================
  docker:
    name: Docker Build
    runs-on: ubuntu-latest
    needs: [test]  # Only run if tests pass
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3
      
      - name: Build Docker image
        uses: docker/build-push-action@v5
        with:
          context: .
          push: false
          tags: streamlitforge:${{ github.sha }}
          cache-from: type=gha
          cache-to: type=gha,mode=max
      
      - name: Run tests in container
        run: |
          docker build -t streamlitforge:test .
          docker run --rm streamlitforge:test python -m pytest streamlitforge/tests/ -v

  # ==========================================
  # Job 5: Integration Check
  # ==========================================
  integration:
    name: Integration Check
    runs-on: ubuntu-latest
    needs: [test, docker]
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      
      - name: Install package
        run: |
          pip install -e ".[dev]"
      
      - name: Test CLI commands
        run: |
          streamlitforge --version
          streamlitforge --help
          streamlitforge list-templates
      
      - name: Test project creation
        run: |
          streamlitforge create test-project --no-venv --no-git
          ls -la test-project/
```

#### Create Branch Protection Rules

After CI is working, configure GitHub branch protection:

1. Go to Settings → Branches → Add rule
2. Branch name pattern: `main`
3. Check:
   - [x] Require status checks to pass before merging
   - [x] Require branches to be up to date before merging
   - [x] Status checks: `lint`, `test (3.11)`, `security`
   - [x] Require pull request reviews before merging

#### Verification

```bash
# VERIFY 1.5.1: Commit workflow file
git add .github/workflows/ci.yml
git commit -m "ci: Add GitHub Actions CI/CD pipeline"

# VERIFY 1.5.2: Push to feature branch first
git checkout -b ci/setup-github-actions
git push -u origin ci/setup-github-actions

# VERIFY 1.5.3: Create PR and verify CI runs
gh pr create --title "ci: Add GitHub Actions CI/CD pipeline" --body "Implements Phase 1.5"

# VERIFY 1.5.4: Check all jobs pass
gh pr checks
```

#### Success Criteria

- [ ] All CI jobs pass on PR
- [ ] No failing tests in CI
- [ ] Coverage report uploaded
- [ ] Docker builds in CI
- [ ] Branch protection configured

---

## Phase 1 Completion Checklist

Before proceeding to Phase 2, verify ALL items:

### Phase 1.1: Tests Pass
- [ ] Virtual environment created
- [ ] All dependencies installed
- [ ] All tests pass locally
- [ ] Coverage report generated
- [ ] Baseline saved

### Phase 1.2: Logging
- [ ] No print() in core modules
- [ ] Logging config module created
- [ ] CLI --debug flag works
- [ ] Tests still pass

### Phase 1.3: Security
- [ ] Bandit runs successfully
- [ ] Safety check runs
- [ ] No HIGH severity issues
- [ ] Security script created

### Phase 1.4: Docker
- [ ] Dockerfile builds
- [ ] Container runs CLI
- [ ] Tests pass in container
- [ ] docker-compose works

### Phase 1.5: CI/CD
- [ ] GitHub Actions workflow created
- [ ] All jobs pass on PR
- [ ] Branch protection configured

---

## Phase 2: Hardening (Week 3-4)

### 2.1 Complete HANDOFF.md

**Objective:** Fill HANDOFF.md with actual project data.

#### Procedure

1. Gather current state:

```bash
# Gather project metrics
echo "## Project Metrics" > handoff_data.txt
echo "- Lines of code: $(find . -name '*.py' ! -path './.venv/*' | xargs wc -l | tail -1)" >> handoff_data.txt
echo "- Test files: $(find . -name 'test_*.py' | wc -l)" >> handoff_data.txt
echo "- Python files: $(find . -name '*.py' ! -path './.venv/*' | wc -l)" >> handoff_data.txt
```

2. Update HANDOFF.md sections:

| Section | Content to Add |
|---------|----------------|
| QUICK STATE | Current working directory, branch, build status, test status |
| ACTIVE WORK | Current phase, next steps |
| COMPLETED THIS SESSION | Features implemented |
| LOST CONTEXT INSURANCE | All decisions made, rejected approaches |
| FEATURE INVENTORY | All features with status |
| VERIFICATION PROCEDURES | Exact commands to verify |
| ARCHITECTURE NOTES | System diagram, data flow |
| SESSION METADATA | Duration, files modified |

3. Create commit:

```bash
git add HANDOFF.md
git commit -m "docs: Complete HANDOFF.md with current project state"
```

#### Success Criteria

- [ ] All HANDOFF.md sections filled
- [ ] Quick State reflects current reality
- [ ] Verification procedures tested
- [ ] Committed to repository

---

### 2.2 Add Integration Tests

**Objective:** Create end-to-end integration tests.

#### Create Integration Test File

Create `streamlitforge/tests/integration/test_integration.py`:

```python
"""Integration tests for StreamlitForge CLI."""
import os
import subprocess
import tempfile
from pathlib import Path
import pytest

@pytest.fixture
def temp_project_dir():
    """Create a temporary directory for test projects."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

class TestCLIIntegration:
    """Integration tests for CLI commands."""
    
    def test_create_project_basic(self, temp_project_dir):
        """Test basic project creation."""
        result = subprocess.run(
            ["streamlitforge", "create", "test-project", "--path", str(temp_project_dir)],
            capture_output=True,
            text=True,
        )
        
        assert result.returncode == 0
        assert (temp_project_dir / "test-project").exists()
        assert (temp_project_dir / "test-project" / "src" / "streamlit_app.py").exists()
    
    def test_create_project_with_template(self, temp_project_dir):
        """Test project creation with template."""
        result = subprocess.run(
            ["streamlitforge", "create", "test-dashboard", 
             "--path", str(temp_project_dir),
             "--template", "dashboard"],
            capture_output=True,
            text=True,
        )
        
        assert result.returncode == 0
        assert (temp_project_dir / "test-dashboard").exists()
    
    def test_list_templates(self):
        """Test list-templates command."""
        result = subprocess.run(
            ["streamlitforge", "list-templates"],
            capture_output=True,
            text=True,
        )
        
        assert result.returncode == 0
        assert "dashboard" in result.stdout
        assert "chat" in result.stdout
    
    def test_create_and_delete_project(self, temp_project_dir):
        """Test project lifecycle."""
        # Create
        subprocess.run(
            ["streamlitforge", "create", "lifecycle-test", "--path", str(temp_project_dir)],
            capture_output=True,
        )
        
        assert (temp_project_dir / "lifecycle-test").exists()
        
        # Delete
        result = subprocess.run(
            ["streamlitforge", "delete", "lifecycle-test", "--path", str(temp_project_dir)],
            capture_output=True,
            text=True,
        )
        
        assert result.returncode == 0
        assert not (temp_project_dir / "lifecycle-test").exists()

class TestPortManagerIntegration:
    """Integration tests for port management."""
    
    def test_deterministic_port(self, temp_project_dir):
        """Test that same path gets same port."""
        from streamlitforge.core.port_manager import PortManager
        
        pm = PortManager()
        path = str(temp_project_dir / "test-project")
        
        port1 = pm.lookup(path)
        port2 = pm.lookup(path)
        
        assert port1 == port2
        assert 8501 <= port1 <= 8999

class TestLLMIntegration:
    """Integration tests for LLM providers."""
    
    def test_ollama_connection(self):
        """Test Ollama provider connection (if available)."""
        pytest.skip("Requires Ollama to be running")
    
    def test_provider_fallback(self):
        """Test that provider fallback works."""
        from streamlitforge.llm.router import EnhancedLLMRouter
        
        router = EnhancedLLMRouter()
        # Test fallback mechanism
        assert router is not None
```

#### Create Integration Test Configuration

Create `streamlitforge/tests/integration/__init__.py`:

```python
"""Integration tests for StreamlitForge."""
import pytest

def pytest_configure(config):
    """Configure integration test markers."""
    config.addinivalue_line(
        "markers", "integration: mark test as integration test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
```

#### Update pyproject.toml

Add to `pyproject.toml`:

```toml
[tool.pytest.ini_options]
testpaths = ["streamlitforge/tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
addopts = "-v --tb=short -m 'not slow'"
markers = [
    "integration: Integration tests",
    "slow: Slow running tests",
]
```

#### Run Integration Tests

```bash
# Run all tests including integration
python -m pytest streamlitforge/tests/ -v -m "not slow"

# Run only integration tests
python -m pytest streamlitforge/tests/integration/ -v

# Run with coverage
python -m pytest streamlitforge/tests/ -v --cov=streamlitforge --cov-report=term-missing
```

#### Success Criteria

- [ ] Integration test file created
- [ ] All integration tests pass
- [ ] Tests run in CI pipeline
- [ ] Coverage includes integration paths

---

### 2.3 Pin Dependency Versions

**Objective:** Lock all dependencies to specific versions.

#### Create requirements-lock.txt

```bash
# Generate locked requirements
pip freeze > requirements-lock.txt

# Verify no version ranges
grep -E ">|<|~=" requirements-lock.txt && echo "WARNING: Version ranges found" || echo "All versions pinned"
```

#### Update requirements.txt

Replace `requirements.txt` with exact versions:

```txt
click==8.3.1
jinja2==3.1.3
pyyaml==6.0.1
requests==2.31.0
numpy==1.26.4
streamlit==1.32.0
```

#### Update pyproject.toml

```toml
dependencies = [
    "click==8.3.1",
    "jinja2==3.1.3",
    "pyyaml==6.0.1",
    "requests==2.31.0",
    "numpy==1.26.4",
    "streamlit==1.32.0",
]
```

#### Create Dependency Update Script

Create `scripts/update_dependencies.sh`:

```bash
#!/bin/bash
# Update dependencies and create lock file

set -e

echo "=== Updating Dependencies ==="

# Update pip
pip install --upgrade pip

# Install current requirements
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Generate lock file
pip freeze > requirements-lock.txt

# Verify
echo ""
echo "=== Verification ==="
echo "Total packages: $(wc -l < requirements-lock.txt)"
echo "Version ranges: $(grep -c -E '>|<|~=' requirements-lock.txt || echo 0)"

echo ""
echo "=== Done ==="
echo "Review requirements-lock.txt and commit if correct"
```

```bash
chmod +x scripts/update_dependencies.sh
```

#### Verification

```bash
# VERIFY 2.3.1: Clean install from lock
python -m venv test_venv
source test_venv/bin/activate
pip install -r requirements-lock.txt

# VERIFY 2.3.2: Run tests
python -m pytest streamlitforge/tests/ -v

# VERIFY 2.3.3: Cleanup
deactivate
rm -rf test_venv
```

#### Success Criteria

- [ ] requirements-lock.txt generated
- [ ] All versions pinned (no ranges)
- [ ] Clean install works
- [ ] Tests pass with locked versions

---

### 2.4 Create Release Workflow

**Objective:** Automate version releases.

#### Create Release Workflow

Create `.github/workflows/release.yml`:

```yaml
name: Release

on:
  release:
    types: [published]
  workflow_dispatch:
    inputs:
      version:
        description: 'Version to release (e.g., 0.2.0)'
        required: true

jobs:
  build-and-publish:
    name: Build and Publish
    runs-on: ubuntu-latest
    permissions:
      contents: write
      id-token: write  # For PyPI trusted publishing
    
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
          cache: 'pip'
      
      - name: Install build tools
        run: |
          python -m pip install --upgrade pip
          pip install build twine
      
      - name: Build package
        run: |
          python -m build
          twine check dist/*
      
      - name: Publish to PyPI
        uses: pypa/gh-action-pypi-publish@release/v1
        if: github.event_name == 'release'
      
      - name: Build Docker image
        uses: docker/build-push-action@v5
        with:
          context: .
          push: true
          tags: |
            ghcr.io/${{ github.repository }}:${{ github.event.release.tag_name }}
            ghcr.io/${{ github.repository }}:latest
      
      - name: Update CHANGELOG
        run: |
          # Extract release notes and update CHANGELOG
          echo "Release published: ${{ github.event.release.tag_name }}"
```

#### Create Version Bump Script

Create `scripts/bump_version.sh`:

```bash
#!/bin/bash
# Bump version across the project

set -e

if [ -z "$1" ]; then
    echo "Usage: ./scripts/bump_version.sh <version>"
    echo "Example: ./scripts/bump_version.sh 0.2.0"
    exit 1
fi

VERSION=$1
echo "Bumping version to $VERSION"

# Update pyproject.toml
sed -i.bak "s/version = \".*\"/version = \"$VERSION\"/" pyproject.toml
rm pyproject.toml.bak

# Update CLI
sed -i.bak "s/version_option(version=\".*\")/version_option(version=\"$VERSION\")/" streamlitforge/cli.py
rm streamlitforge/cli.py.bak

# Update __init__.py
echo "__version__ = \"$VERSION\"" > streamlitforge/__init__.py

echo "Version bumped to $VERSION"
echo "Commit with: git commit -am 'chore: Bump version to $VERSION'"
```

```bash
chmod +x scripts/bump_version.sh
```

#### Success Criteria

- [ ] Release workflow created
- [ ] Version bump script works
- [ ] Docker images tagged correctly
- [ ] PyPI publishing configured

---

### 2.5 Add Pre-commit Hooks

**Objective:** Enforce code quality before commits.

#### Create .pre-commit-config.yaml

```yaml
# Pre-commit hooks for StreamlitForge
repos:
  # General file checks
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-json
      - id: check-added-large-files
        args: ['--maxkb=500']
      - id: check-merge-conflict
      - id: debug-statements
  
  # Python formatting
  - repo: https://github.com/psf/black
    rev: 24.2.0
    hooks:
      - id: black
        language_version: python3.11
  
  # Import sorting
  - repo: https://github.com/pycqa/isort
    rev: 5.13.2
    hooks:
      - id: isort
        args: ["--profile", "black"]
  
  # Linting
  - repo: https://github.com/pycqa/flake8
    rev: 7.0.0
    hooks:
      - id: flake8
        args: ['--max-line-length=100', '--extend-ignore=E203']
  
  # Type checking (optional, non-blocking)
  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.8.0
    hooks:
      - id: mypy
        additional_dependencies: [types-all]
        args: [--ignore-missing-imports]
        pass_filenames: false
  
  # Security
  - repo: https://github.com/PyCQA/bandit
    rev: 1.7.8
    hooks:
      - id: bandit
        args: ['-r', 'streamlitforge/', '-ll']
        pass_filenames: false
```

#### Install Pre-commit

```bash
# Install pre-commit
pip install pre-commit

# Install hooks
pre-commit install

# Run on all files (first time)
pre-commit run --all-files

# Run on staged files only
pre-commit
```

#### Create Pre-commit CI

Add to `.github/workflows/ci.yml`:

```yaml
  # Add after lint job
  pre-commit:
    name: Pre-commit
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      
      - name: Run pre-commit
        uses: pre-commit/action@v3.0.1
```

#### Success Criteria

- [ ] Pre-commit installed
- [ ] Hooks run on all files
- [ ] CI includes pre-commit check
- [ ] Commits blocked on failure

---

## Phase 2 Completion Checklist

### Phase 2.1: HANDOFF.md
- [ ] All sections filled
- [ ] Committed to repo

### Phase 2.2: Integration Tests
- [ ] Test file created
- [ ] Tests pass
- [ ] CI includes integration

### Phase 2.3: Pinned Dependencies
- [ ] Lock file generated
- [ ] Clean install works
- [ ] Tests pass

### Phase 2.4: Release Workflow
- [ ] Workflow created
- [ ] Version bump script works

### Phase 2.5: Pre-commit Hooks
- [ ] Hooks installed
- [ ] CI includes check

---

## Phase 3: Polish (Week 5-6)

### 3.1 Performance Testing

#### Create Performance Test Suite

Create `streamlitforge/tests/performance/test_performance.py`:

```python
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

# Run with: pytest -v --benchmark-only streamlitforge/tests/performance/
```

#### Install pytest-benchmark

```bash
pip install pytest-benchmark
```

#### Create Performance Benchmark Script

Create `scripts/run_benchmarks.sh`:

```bash
#!/bin/bash
# Run performance benchmarks

set -e

echo "=== Running Performance Benchmarks ==="

python -m pytest streamlitforge/tests/performance/ \
    --benchmark-only \
    --benchmark-sort=mean \
    --benchmark-cols=mean,stddev,rounds \
    -v

echo ""
echo "=== Benchmarks Complete ==="
```

```bash
chmod +x scripts/run_benchmarks.sh
```

#### Success Criteria

- [ ] Performance tests created
- [ ] Benchmarks run successfully
- [ ] Baseline metrics captured
- [ ] No performance regressions

---

### 3.2 Security Audit

#### Run Comprehensive Security Scan

```bash
# Full security suite
./scripts/security_scan.sh > security_audit_full.txt 2>&1

# Manual review items
echo "=== Manual Security Review Checklist ===" > security_review.md
echo "" >> security_review.md
echo "- [ ] API key storage reviewed" >> security_review.md
echo "- [ ] Input sanitization verified" >> security_review.md
echo "- [ ] Rate limiting implemented" >> security_review.md
echo "- [ ] Secrets not in git history" >> security_review.md
echo "- [ ] Dependencies checked for vulnerabilities" >> security_review.md
```

#### Create Security Policy

Create `SECURITY.md`:

```markdown
# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | :white_check_mark: |

## Reporting a Vulnerability

Please report security vulnerabilities to security@streamlitforge.com

Do NOT open a public issue.

## Security Features

- API keys stored in user config directory
- No credentials in source code
- Dependencies pinned to known-good versions
- Security scanning in CI pipeline
```

#### Success Criteria

- [ ] Full security scan run
- [ ] Manual review completed
- [ ] Security policy created
- [ ] No HIGH severity issues

---

### 3.3 Documentation Review

#### Create Documentation Checklist

```bash
# Check documentation completeness
cat > docs_review.md << 'EOF'
# Documentation Review

## README.md
- [ ] Installation instructions accurate
- [ ] Usage examples work
- [ ] Links are valid
- [ ] Badges updated

## CHANGELOG.md
- [ ] All versions documented
- [ ] Breaking changes noted
- [ ] Migration guides provided

## CONTRIBUTING.md
- [ ] Setup instructions clear
- [ ] PR process documented
- [ ] Code style guidelines

## API Documentation
- [ ] All public APIs documented
- [ ] Examples provided
- [ ] Type hints present
EOF
```

#### Update README

Ensure README.md includes:
- [x] Installation instructions
- [x] Quick start guide
- [x] Feature list
- [x] Configuration examples
- [x] Contributing link

#### Success Criteria

- [ ] All docs reviewed
- [ ] Broken links fixed
- [ ] Examples verified
- [ ] API docs complete

---

### 3.4 User Acceptance Testing

#### Create UAT Checklist

Create `docs/uat_checklist.md`:

```markdown
# User Acceptance Testing Checklist

## Installation
- [ ] pip install works
- [ ] No dependency conflicts
- [ ] CLI command available

## Basic Operations
- [ ] Create project
- [ ] List templates
- [ ] Delete project
- [ ] Get project info

## Templates
- [ ] Dashboard template works
- [ ] Chat template works
- [ ] CRUD template works
- [ ] Analysis template works
- [ ] Admin template works

## LLM Integration
- [ ] Ollama works (if installed)
- [ ] OpenAI works (if key provided)
- [ ] Fallback works when offline

## Edge Cases
- [ ] Special characters in project name
- [ ] Long project names
- [ ] Existing project overwrite
- [ ] Invalid template name

## Documentation
- [ ] README accurate
- [ ] Help text clear
- [ ] Error messages helpful
```

#### Conduct UAT

```bash
# Run through all UAT items manually
# Document any issues found
```

#### Success Criteria

- [ ] All UAT items pass
- [ ] Issues documented
- [ ] Critical issues fixed
- [ ] UAT signed off

---

### 3.5 Beta Release

#### Prepare Beta Release

```bash
# 1. Ensure all Phase 3 items complete
# 2. Run full test suite
python -m pytest streamlitforge/tests/ -v

# 3. Run security scan
./scripts/security_scan.sh

# 4. Update version
./scripts/bump_version.sh 0.2.0-beta.1

# 5. Update CHANGELOG
# Add beta release notes

# 6. Create tag
git tag -a v0.2.0-beta.1 -m "Beta release 0.2.0-beta.1"
git push origin v0.2.0-beta.1

# 7. Create GitHub release
gh release create v0.2.0-beta.1 \
    --title "v0.2.0-beta.1 - Beta Release" \
    --notes "Beta release for testing"
```

#### Success Criteria

- [ ] Beta tag created
- [ ] Release published
- [ ] Beta testers recruited
- [ ] Feedback collected

---

## Phase 3 Completion Checklist

### Phase 3.1: Performance
- [ ] Benchmarks created
- [ ] Baseline captured

### Phase 3.2: Security Audit
- [ ] Full scan run
- [ ] Manual review done
- [ ] Policy created

### Phase 3.3: Documentation
- [ ] All docs reviewed
- [ ] Examples verified

### Phase 3.4: UAT
- [ ] All tests pass
- [ ] Issues fixed

### Phase 3.5: Beta
- [ ] Beta released
- [ ] Feedback collected

---

## Phase 4: Production (Week 7+)

### 4.1 Production Deployment

#### Pre-deployment Checklist

```bash
# Final verification
echo "=== Pre-deployment Verification ==="

# 1. All tests pass
python -m pytest streamlitforge/tests/ -v

# 2. Security scan clean
./scripts/security_scan.sh

# 3. Docker builds
docker build -t streamlitforge:prod .

# 4. Version correct
grep "version =" pyproject.toml
```

#### Deployment Steps

```bash
# 1. Create production release
./scripts/bump_version.sh 1.0.0
git tag -a v1.0.0 -m "Production release 1.0.0"
git push origin v1.0.0

# 2. GitHub release
gh release create v1.0.0 \
    --title "v1.0.0 - Production Release" \
    --notes "First production release"

# 3. Verify PyPI publish (automatic via CI)

# 4. Verify Docker publish (automatic via CI)

# 5. Update documentation site
```

#### Success Criteria

- [ ] v1.0.0 released
- [ ] Published to PyPI
- [ ] Docker image published
- [ ] Documentation updated

---

### 4.2 Monitoring Setup

#### Create Monitoring Configuration

Create `monitoring/prometheus.yml`:

```yaml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'streamlitforge'
    static_configs:
      - targets: ['localhost:8501']
```

#### Add Health Endpoint

In future version, add health check endpoint to CLI.

#### Success Criteria

- [ ] Health checks configured
- [ ] Alerts set up
- [ ] Dashboards created

---

### 4.3 Runbook Creation

Create `docs/runbook.md`:

```markdown
# StreamlitForge Operations Runbook

## Common Issues

### Issue: Port Already in Use
**Symptom:** Error "Port 8501 already in use"
**Solution:**
```bash
# Find process using port
lsof -i :8501

# Kill process or use different port
streamlitforge create myapp --port 8502
```

### Issue: Virtual Environment Creation Fails
**Symptom:** Error during `streamlitforge create`
**Solution:**
```bash
# Use --no-venv flag
streamlitforge create myapp --no-venv

# Create venv manually
python -m venv myapp/.venv
```

### Issue: Tests Failing
**Symptom:** Test suite failures
**Solution:**
```bash
# Run with verbose output
python -m pytest streamlitforge/tests/ -v --tb=long

# Check dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

## Deployment Checklist

1. [ ] All tests pass
2. [ ] Security scan clean
3. [ ] Version bumped
4. [ ] CHANGELOG updated
5. [ ] Tag created
6. [ ] Release published

## Rollback Procedure

1. Identify previous stable version
2. Revert to previous tag: `git checkout v0.9.0`
3. Rebuild and redeploy
4. Document issue for post-mortem
```

#### Success Criteria

- [ ] Runbook created
- [ ] Common issues documented
- [ ] Rollback procedure tested

---

### 4.4 User Training

#### Create Training Materials

1. **Getting Started Guide** - `docs/getting_started.md`
2. **Video Tutorial** - Record 10-minute intro
3. **FAQ** - `docs/faq.md`
4. **Examples Repository** - Sample projects

#### Success Criteria

- [ ] Training docs created
- [ ] Video recorded
- [ ] FAQ populated
- [ ] Examples available

---

### 4.5 v1.0.0 Release

#### Final Release Checklist

```markdown
# v1.0.0 Release Checklist

## Code Quality
- [ ] All tests pass (100%)
- [ ] Code coverage > 80%
- [ ] No security vulnerabilities
- [ ] Documentation complete

## Release Process
- [ ] Version bumped to 1.0.0
- [ ] CHANGELOG updated
- [ ] Tag created
- [ ] Release notes written

## Distribution
- [ ] Published to PyPI
- [ ] Docker image published
- [ ] GitHub release created
- [ ] Announcement posted

## Post-release
- [ ] Monitor for issues
- [ ] Respond to feedback
- [ ] Plan v1.1.0 features
```

#### Success Criteria

- [ ] v1.0.0 released
- [ ] Available on PyPI
- [ ] Docker image pulled successfully
- [ ] Users installing successfully

---

## Phase 4 Completion Checklist

### Phase 4.1: Deployment
- [ ] v1.0.0 released
- [ ] PyPI published
- [ ] Docker published

### Phase 4.2: Monitoring
- [ ] Health checks configured
- [ ] Alerts active

### Phase 4.3: Runbook
- [ ] Runbook created
- [ ] Team trained

### Phase 4.4: Training
- [ ] Docs created
- [ ] Video recorded

### Phase 4.5: Release
- [ ] v1.0.0 live
- [ ] Users successful

---

## Quick Reference Commands

### Phase 1 Commands
```bash
# Setup
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"

# Test
python -m pytest streamlitforge/tests/ -v

# Security
bandit -r streamlitforge/

# Docker
docker build -t streamlitforge:test .
docker run --rm streamlitforge:test streamlitforge --help
```

### Phase 2 Commands
```bash
# Integration tests
python -m pytest streamlitforge/tests/integration/ -v

# Dependencies
pip freeze > requirements-lock.txt

# Pre-commit
pre-commit run --all-files
```

### Phase 3 Commands
```bash
# Benchmarks
./scripts/run_benchmarks.sh

# Security audit
./scripts/security_scan.sh > security_audit.txt

# Beta release
./scripts/bump_version.sh 0.2.0-beta.1
```

### Phase 4 Commands
```bash
# Production release
./scripts/bump_version.sh 1.0.0
git tag -a v1.0.0 -m "Production release"
git push origin v1.0.0
gh release create v1.0.0
```

---

## Summary

**Total Estimated Time:** 6-8 weeks

**Critical Path:**
1. Tests must pass before CI/CD (Phase 1.1 → 1.5)
2. Security must be clean before beta (Phase 2.3 → 3.5)
3. All phases must complete before production (Phase 1-3 → 4)

**Risk Mitigation:**
- Each phase has verification steps
- Rollback procedures documented
- No step proceeds without previous success

**Success Metrics:**
- Test coverage > 80%
- No HIGH security vulnerabilities
- CI/CD pipeline passing
- v1.0.0 released to PyPI
