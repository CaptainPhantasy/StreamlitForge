# User Acceptance Testing Checklist

## Installation

- [ ] pip install works
  ```bash
  pip install -e .
  ```
  **Expected:** Successfully installs streamlitforge-0.1.0

- [ ] No dependency conflicts
  ```bash
  pip list | grep streamlitforge
  ```

- [ ] CLI command available
  ```bash
  streamlitforge --help
  ```
  **Expected:** Shows StreamlitForge help text

## Basic Operations

- [ ] Create project
  ```bash
  streamlitforge create test-project --no-venv --no-git
  ```
  **Expected:** Project directory created with streamlit_app.py

- [ ] List templates
  ```bash
  streamlitforge list-templates
  ```
  **Expected:** Lists 5 templates (dashboard, chat, crud, analysis, admin)

- [ ] Get project info
  ```bash
  streamlitforge info test-project
  ```
  **Expected:** Shows project details

- [ ] Delete project
  ```bash
  streamlitforge delete test-project
  ```
  **Expected:** Project directory removed

## Templates

- [ ] Dashboard template works
  ```bash
  streamlitforge create dashboard --template dashboard --no-venv --no-git
  ```
  **Expected:** Project created with dashboard layout

- [ ] Chat template works
  ```bash
  streamlitforge create chat --template chat --no-venv --no-git
  ```
  **Expected:** Project created with chat interface

- [ ] CRUD template works
  ```bash
  streamlitforge create crud --template crud --no-venv --no-git
  ```
  **Expected:** Project created with CRUD operations

- [ ] Analysis template works
  ```bash
  streamlitforge create analysis --template analysis --no-venv --no-git
  ```
  **Expected:** Project created with analysis tools

- [ ] Admin template works
  ```bash
  streamlitforge create admin --template admin --no-venv --no-git
  ```
  **Expected:** Project created with admin panel

## LLM Integration

- [ ] Ollama works (if installed)
  ```bash
  ollama run llama3
  ```
  ```bash
  streamlitforge configure --provider ollama --model llama3
  ```
  **Expected:** LLM provider configured

- [ ] OpenAI works (if key provided)
  ```bash
  streamlitforge configure --provider openai --api-key sk-...
  ```
  **Expected:** LLM provider configured

- [ ] Fallback works when offline
  **Expected:** Pattern library used when LLM unavailable

## Security & Quality

- [ ] Dependencies pinned
  ```bash
  cat requirements.txt
  ```
  **Expected:** All versions use `==` (no ranges like `>=`)

- [ ] Security scan passes
  ```bash
  ./scripts/security_scan.sh
  ```
  **Expected:** No HIGH severity issues

- [ ] Pre-commit hooks configured
  ```bash
  pip install pre-commit
  pre-commit install
  ```
  **Expected:** Hooks installed successfully

## Edge Cases

- [ ] Special characters in project name
  ```bash
  streamlitforge create "test-project-123" --no-venv --no-git
  ```
  **Expected:** Project created successfully

- [ ] Long project names
  ```bash
  streamlitforge create "this-is-a-very-long-project-name-for-testing" --no-venv --no-git
  ```
  **Expected:** Project created successfully

- [ ] Existing project overwrite
  ```bash
  streamlitforge create test-project --no-venv --no-git
  streamlitforge create test-project --no-venv --no-git --force
  ```
  **Expected:** Second command succeeds (or warns)

- [ ] Invalid template name
  ```bash
  streamlitforge create test --template invalid_template
  ```
  **Expected:** Error message about invalid template

## Documentation

- [ ] README accurate
  ```bash
  cat README.md
  ```
  **Expected:** Installation, usage, and features are current

- [ ] Help text clear
  ```bash
  streamlitforge --help
  ```
  **Expected:** Clear command descriptions

- [ ] Error messages helpful
  ```bash
  streamlitforge create --invalid-option
  ```
  **Expected:** Clear error message

## Performance

- [ ] Project creation is fast
  ```bash
  time streamlitforge create perf-test --no-venv --no-git
  ```
  **Expected:** < 5 seconds for project creation

- [ ] Port lookup is fast
  ```bash
  time streamlitforge create test --no-venv --no-git
  ```
  **Expected:** < 1 second

## Integration Tests

- [ ] Integration tests pass
  ```bash
  python -m pytest streamlitforge/tests/integration/ -v
  ```
  **Expected:** All integration tests pass

- [ ] Performance tests pass
  ```bash
  python -m pytest streamlitforge/tests/performance/ -v
  ```
  **Expected:** All performance tests pass

## Docker

- [ ] Docker builds
  ```bash
  docker build -t streamlitforge:test .
  ```
  **Expected:** Build successful, image size < 500MB

- [ ] Docker runs CLI
  ```bash
  docker run --rm streamlitforge:test streamlitforge --help
  ```
  **Expected:** Shows help text

## Common Issues (Should Not Occur)

- [ ] No port conflicts
  **Expected:** Multiple projects can coexist

- [ ] No dependency conflicts
  **Expected:** Dependencies don't conflict

- [ ] No security vulnerabilities
  **Expected:** Security scan clean

---

## UAT Sign-off

**Tested By:** __________________

**Date:** ______________

**Status:** [ ] PASS [ ] FAIL [ ] PARTIAL

**Comments:** _________________________________________________________
_____________________________________________________________

---

## If Issues Found

1. Document the issue in this checklist
2. Categorize as Critical / High / Medium / Low
3. Provide reproduction steps
4. Create issue in GitHub with severity tag
5. Fix and re-test
6. Sign off after fix
