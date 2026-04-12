# RC Completion Plan — StreamlitForge
Generated: 2026-03-08
Current Stage: ALPHA
Target Stage: Release Candidate
Verdict: GO-WITH-RISKS

## Summary
StreamlitForge has solid foundations: Docker, pre-commit hooks, PyPI release workflow, integration 
tests, deterministic port management, LLM abstraction layer. The pyproject.toml classifier says 
"Development Status :: 3 - Alpha" — honest. Missing: full CI (only release workflow exists), 
coverage enforcement, several roadmap items that should land before RC, and a proper test run 
confirmation. The PyPI publish workflow is the strongest asset here.

---

## BLOCKING ITEMS

### CI/CD
- [ ] **Add full CI workflow (separate from release)**
  - File: `.github/workflows/ci.yml` (create new)
  - Content:
    ```yaml
    name: CI
    on: [push, pull_request]
    jobs:
      test:
        runs-on: ubuntu-latest
        steps:
          - uses: actions/checkout@v4
          - uses: actions/setup-python@v5
            with: { python-version: '3.11' }
          - run: pip install -e ".[dev]"
          - run: pytest streamlitforge/tests/ --cov=streamlitforge --cov-fail-under=70
          - run: ruff check streamlitforge/
          - run: bandit -r streamlitforge/ -ll
    ```
  - Validation: CI runs on every push, exits 0
  - Effort: 2 hours

- [ ] **Verify all tests currently pass**
  - Command: `cd /Volumes/Storage/StreamlitForge && pip install -e ".[dev]" && pytest streamlitforge/tests/ -v`
  - Validation: 0 failures
  - Effort: 1 hour (fix any failures found)

### Documentation
- [ ] **Update pyproject.toml classifier from Alpha to Beta**
  - File: `pyproject.toml`
  - Change: `"Development Status :: 3 - Alpha"` → `"Development Status :: 4 - Beta"`
  - Validation: `pip show streamlitforge` shows Beta status
  - Effort: 5 min

- [ ] **Create `.env.example`**
  - File: `.env.example`
  - Content: `OPENROUTER_API_KEY=`, `OLLAMA_HOST=http://localhost:11434`, `GROQ_API_KEY=`
  - Validation: File exists, no real keys present
  - Effort: 15 min

- [ ] **Create `docs/DEPLOYMENT.md`**
  - Content: pip install steps, Docker build and run commands, env var list, PyPI publish steps
  - Validation: Deployable from scratch using only this doc
  - Effort: 1.5 hours

### Security
- [ ] **Run `pip-audit` and `safety check`**
  - Command: `pip-audit -r requirements.txt`
  - Validation: No CRITICAL findings
  - Effort: 1 hour

- [ ] **Verify no API keys hardcoded in source**
  - Command: `grep -r "sk-or-\|sk-\|gsk_" streamlitforge/ --include="*.py" | grep -v test`
  - Validation: Zero results
  - Effort: 30 min

### Roadmap Items (RC-blocking)
- [ ] **Add auth template**
  - File: `streamlitforge/templates/auth.py` (create)
  - Content: Basic username/password pattern using `streamlit-authenticator`
  - Why: Security template is a hard requirement before shipping a "production-ready" builder
  - Effort: 4 hours

---

## STRONGLY RECOMMENDED

- [ ] **Add database integration template**
  - File: `streamlitforge/templates/database.py`
  - Content: SQLite + pandas read pattern, SQLAlchemy connection template
  - Effort: 3 hours

- [ ] **Add streaming support to LLM abstraction**
  - File: `streamlitforge/llm/base.py`
  - Add `stream=True` parameter to LLM client interface
  - Effort: 3 hours

- [ ] **Docker multi-stage build**
  - File: `Dockerfile`
  - Separate build and runtime stages to reduce image size
  - Effort: 1 hour

- [ ] **Add CHANGELOG RC entry**
  - File: `CHANGELOG.md`
  - Effort: 30 min

---

## NICE TO HAVE

- [ ] Web UI for configuration (listed in roadmap)
- [ ] Multi-language support
- [ ] More template variety (admin panel, analytics)

---

## ORDERED EXECUTION SEQUENCE

1. Run tests — confirm all passing: `pytest streamlitforge/tests/ -v`
2. Create `.env.example`
3. Run `pip-audit` — fix any HIGH/CRITICAL
4. Verify no hardcoded keys
5. Create `.github/workflows/ci.yml`
6. Add auth template
7. Update pyproject.toml classifier to Beta
8. Write `docs/DEPLOYMENT.md`
9. Update CHANGELOG
10. Tag: `git tag -a v1.0.0-rc1 -m "Release Candidate 1"`

---

## RISK REGISTER

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| No auth template ships with "production-ready" tool | High | Certain | Build auth template before RC |
| Only 1 CI workflow (release) — no continuous testing | High | Confirmed | Add ci.yml immediately |
| LLM API keys in config YAML could be committed | High | Possible | Add `streamlitforge_config.yaml` to `.gitignore` |

---

## VALIDATION GATE

- [ ] `pytest streamlitforge/tests/ --cov=streamlitforge --cov-fail-under=70` passes
- [ ] `ruff check streamlitforge/` clean
- [ ] `bandit -r streamlitforge/ -ll` no HIGH findings
- [ ] `pip-audit` no CRITICAL CVEs
- [ ] `docker build -t streamlitforge:latest .` succeeds
- [ ] `streamlitforge create test-app` creates valid project
- [ ] Auth template exists and documented
- [ ] `.env.example` at repo root
- [ ] `docs/DEPLOYMENT.md` complete
- [ ] CI workflow runs on push
