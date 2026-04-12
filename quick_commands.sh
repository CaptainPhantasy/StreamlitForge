#!/bin/bash
# Quick command reference for StreamlitForge production roadmap
# Run this script to see all key commands organized by phase

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}═══════════════════════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}  STREAMLITFORGE: PRODUCTION ROADMAP - QUICK REFERENCE${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════════════════════${NC}"
echo ""

# Phase 1: Foundation
echo -e "${GREEN}═══════════════════════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}  PHASE 1: FOUNDATION (Week 1-2)${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════════════════════════════${NC}"
echo ""

# 1.1 Tests
echo -e "${YELLOW}1.1 - Verify Tests Pass${NC}"
echo -e "  Create venv:     python3 -m venv .venv"
echo -e "  Activate:        source .venv/bin/activate"
echo -e "  Install deps:    pip install -e \".[dev]\""
echo -e "  Run tests:       python -m pytest streamlitforge/tests/ -v"
echo -e "  With coverage:   python -m pytest streamlitforge/tests/ -v --cov=streamlitforge"
echo -e "  Save baseline:   python -m pytest streamlitforge/tests/ -v --tb=short > test_baseline.txt"
echo ""

# 1.2 Logging
echo -e "${YELLOW}1.2 - Replace Print with Logging${NC}"
echo -e "  Find prints:     grep -rn \"print(\" --include=\"*.py\" streamlitforge/"
echo -e "  Review each file and replace with logging"
echo ""

# 1.3 Security
echo -e "${YELLOW}1.3 - Add Security Scanning${NC}"
echo -e "  Install tools:   pip install bandit safety pip-audit"
echo -e "  Run bandit:      bandit -r streamlitforge/ -f txt"
echo -e "  Run safety:      safety check"
echo -e "  Run pip-audit:   pip-audit"
echo ""

# 1.4 Docker
echo -e "${YELLOW}1.4 - Add Dockerfile${NC}"
echo -e "  Build image:     docker build -t streamlitforge:test ."
echo -e "  Run CLI:         docker run --rm streamlitforge:test streamlitforge --help"
echo -e "  Test in container:"
echo -e "    docker run --rm streamlitforge:test python -m pytest streamlitforge/tests/ -v"
echo ""

# 1.5 CI/CD (AFTER all tests pass)
echo -e "${YELLOW}1.5 - Set Up CI/CD${NC}"
echo -e "  Create workflow: .github/workflows/ci.yml"
echo -e "  Test locally:    gh pr create --title \"Test\" --body \"Test\""
echo -e "  Check CI:        gh pr checks"
echo ""

# Phase 2: Hardening
echo ""
echo -e "${BLUE}═══════════════════════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}  PHASE 2: HARDENING (Week 3-4)${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════════════════════${NC}"
echo ""

# 2.1 HANDOFF
echo -e "${YELLOW}2.1 - Complete HANDOFF.md${NC}"
echo -e "  Gather data:     Check project state, metrics, decisions"
echo -e "  Fill sections:   Quick State, Active Work, Completed Items"
echo -e "  Commit:          git add HANDOFF.md && git commit -m \"docs: Complete HANDOFF.md\""
echo ""

# 2.2 Integration Tests
echo -e "${YELLOW}2.2 - Add Integration Tests${NC}"
echo -e "  Create file:     streamlitforge/tests/integration/test_integration.py"
echo -e "  Run tests:       python -m pytest streamlitforge/tests/integration/ -v"
echo -e "  In CI:           Add to .github/workflows/ci.yml"
echo ""

# 2.3 Dependencies
echo -e "${YELLOW}2.3 - Pin Dependency Versions${NC}"
echo -e "  Generate lock:   pip freeze > requirements-lock.txt"
echo -e "  Verify:          grep -E \">|<|~=\" requirements-lock.txt"
echo -e "  Update pyproject: Replace version ranges with exact versions"
echo ""

# 2.4 Release Workflow
echo -e "${YELLOW}2.4 - Create Release Workflow${NC}"
echo -e "  Create file:     .github/workflows/release.yml"
echo -e "  Bump version:    ./scripts/bump_version.sh 0.2.0-beta.1"
echo ""

# 2.5 Pre-commit
echo -e "${YELLOW}2.5 - Add Pre-commit Hooks${NC}"
echo -e "  Install:         pip install pre-commit"
echo -e "  Install hooks:   pre-commit install"
echo -e "  Run on all:      pre-commit run --all-files"
echo -e "  In CI:           Add pre-commit job to workflows/ci.yml"
echo ""

# Phase 3: Polish
echo ""
echo -e "${BLUE}═══════════════════════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}  PHASE 3: POLISH (Week 5-6)${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════════════════════${NC}"
echo ""

# 3.1 Performance
echo -e "${YELLOW}3.1 - Performance Testing${NC}"
echo -e "  Install tools:   pip install pytest-benchmark"
echo -e "  Run benchmarks:  python -m pytest streamlitforge/tests/performance/ -v --benchmark-only"
echo -e "  Save results:    ./scripts/run_benchmarks.sh"
echo ""

# 3.2 Security Audit
echo -e "${YELLOW}3.2 - Security Audit${NC}"
echo -e "  Full scan:       ./scripts/security_scan.sh > security_audit.txt"
echo -e "  Manual review:   Check API key storage, input validation"
echo -e "  Create policy:   SECURITY.md"
echo ""

# 3.3 Documentation
echo -e "${YELLOW}3.3 - Documentation Review${NC}"
echo -e "  Review README:   Check for accuracy, broken links"
echo -e "  Update CHANGELOG: Document beta release"
echo -e "  Verify examples: Test all commands in README"
echo ""

# 3.4 UAT
echo -e "${YELLOW}3.4 - User Acceptance Testing${NC}"
echo -e "  Test install:    pip install -e ."
echo -e "  Test commands:   streamlitforge --help, streamlitforge create, etc."
echo -e "  Test templates:  Test all 5 templates"
echo ""

# 3.5 Beta Release
echo -e "${YELLOW}3.5 - Beta Release${NC}"
echo -e "  Bump version:    ./scripts/bump_version.sh 0.2.0-beta.1"
echo -e "  Create tag:      git tag -a v0.2.0-beta.1 -m \"Beta release\""
echo -e "  Push tag:        git push origin v0.2.0-beta.1"
echo -e "  Create release:  gh release create v0.2.0-beta.1 --title \"v0.2.0-beta.1\""
echo ""

# Phase 4: Production
echo ""
echo -e "${BLUE}═══════════════════════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}  PHASE 4: PRODUCTION (Week 7+)${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════════════════════${NC}"
echo ""

# 4.1 Deployment
echo -e "${YELLOW}4.1 - Production Deployment${NC}"
echo -e "  Bump version:    ./scripts/bump_version.sh 1.0.0"
echo -e "  Create tag:      git tag -a v1.0.0 -m \"Production release\""
echo -e "  Push tag:        git push origin v1.0.0"
echo -e "  Create release:  gh release create v1.0.0 --title \"v1.0.0\""
echo ""

# 4.2 Monitoring
echo -e "${YELLOW}4.2 - Monitoring Setup${NC}"
echo -e "  Health checks:   Configure /health endpoint"
echo -e "  Alerting:        Set up alerts for failures"
echo ""

# 4.3 Runbook
echo -e "${YELLOW}4.3 - Runbook Creation${NC}"
echo -e "  Create file:     docs/runbook.md"
echo -e "  Document issues: Common problems and solutions"
echo -e "  Document rollback: Rollback procedure"
echo ""

# 4.4 Training
echo -e "${YELLOW}4.4 - User Training${NC}"
echo -e "  Create guide:    docs/getting_started.md"
echo -e "  Record video:    Tutorial recording"
echo -e "  Create FAQ:      docs/faq.md"
echo ""

# 4.5 Release
echo -e "${YELLOW}4.5 - v1.0.0 Release${NC}"
echo -e "  Verify:          All docs complete, all tests pass"
echo -e "  Deploy:          Release to PyPI (automatic via CI)"
echo -e "  Announce:        Create blog post / social media"
echo ""

# Common Commands
echo ""
echo -e "${BLUE}═══════════════════════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}  COMMON COMMANDS${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════════════════════${NC}"
echo ""

echo "Test commands:"
echo "  python -m pytest streamlitforge/tests/ -v"
echo "  python -m pytest streamlitforge/tests/ --cov=streamlitforge"
echo "  python -m pytest streamlitforge/tests/ -v --tb=long"

echo ""
echo "Security commands:"
echo "  bandit -r streamlitforge/"
echo "  safety check"
echo "  pip-audit"

echo ""
echo "Docker commands:"
echo "  docker build -t streamlitforge:test ."
echo "  docker run --rm streamlitforge:test streamlitforge --help"
echo "  docker-compose up -d streamlitforge"

echo ""
echo "Git commands:"
echo "  git status"
echo "  git add ."
echo "  git commit -m \"message\""
echo "  git push origin main"
echo "  git checkout -b feature-name"

echo ""
echo "GitHub commands:"
echo "  gh pr create --title \"Title\" --body \"Body\""
echo "  gh pr checks"
echo "  gh release create <tag> --title \"Title\""

echo ""
echo -e "${BLUE}═══════════════════════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}  START HERE: Phase 1.1 - Verify All Tests Pass${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "${RED}⚠️  CRITICAL: Do not proceed to Phase 1.5 (CI/CD) until all tests pass!${NC}"
echo ""
echo -e "Run these commands to start Phase 1.1:"
echo -e "  ${GREEN}python3 -m venv .venv${NC}"
echo -e "  ${GREEN}source .venv/bin/activate${NC}"
echo -e "  ${GREEN}pip install -e \".[dev]\"${NC}"
echo -e "  ${GREEN}python -m pytest streamlitforge/tests/ -v${NC}"
echo ""
echo -e "${BLUE}──────────────────────────────────────────────────────────────────────────────${NC}"
echo ""
