# StreamlitForge Operations Runbook

## Overview

This runbook provides operational procedures for managing StreamlitForge, including common issues, troubleshooting, and rollback procedures.

---

## Common Issues

### Issue 1: Port Already in Use

**Symptom:**
```
OSError: [Errno 48] Address already in use
```

**Solution 1:** Kill the process using the port
```bash
# Find process using port
lsof -i :8501

# Kill the process
kill -9 <PID>

# Or use the port manager to get a different port
streamlitforge create myapp --port <alternative_port>
```

**Solution 2:** Use StreamlitForge's deterministic port management
```bash
# StreamlitForge will automatically handle port conflicts
streamlitforge create myapp
```

### Issue 2: Virtual Environment Creation Fails

**Symptom:**
```
PermissionError: [Errno 13] Permission denied
```

**Solution:**
```bash
# Use --no-venv flag to skip venv creation
streamlitforge create myapp --no-venv

# Or create venv manually
python3 -m venv myapp/.venv
source myapp/.venv/bin/activate
```

### Issue 3: Tests Failing

**Symptom:**
```
pytest errors during test run
```

**Solution 1:** Install dependencies
```bash
pip install -e ".[dev]"
pip install pytest pytest-cov
```

**Solution 2:** Check for Python version compatibility
```bash
python3 --version  # Should be 3.8+
```

**Solution 3:** Clean and reinstall
```bash
pip uninstall streamlitforge -y
pip install -e ".[dev]"
```

### Issue 4: Docker Build Fails

**Symptom:**
```
Docker build failed
```

**Solution 1:** Check Docker installation
```bash
docker --version  # Should be >= 20.10
docker ps  # Should list running containers
```

**Solution 2:** Clean up and rebuild
```bash
docker system prune -a
docker build -t streamlitforge:test .
```

### Issue 5: Security Scan Fails

**Symptom:**
```
Security scan found HIGH severity issues
```

**Solution:**
```bash
# Review bandit report
cat security_results/bandit.txt

# Fix the issues and run again
./scripts/security_scan.sh
```

---

## Deployment Checklist

### Pre-Deployment

- [ ] All tests pass locally
- [ ] Security scan clean (no HIGH severity)
- [ ] Documentation complete
- [ ] Version bumped to release version
- [ ] CHANGELOG updated
- [ ] Tag created
- [ ] Release notes written

### Deployment Steps

1. **Update version**
   ```bash
   ./scripts/bump_version.sh 1.0.0
   ```

2. **Update CHANGELOG**
   ```bash
   # Document release notes in CHANGELOG.md
   ```

3. **Create tag**
   ```bash
   git tag -a v1.0.0 -m "Release 1.0.0 - Production Release"
   ```

4. **Push tag**
   ```bash
   git push origin v1.0.0
   ```

5. **Create GitHub release**
   ```bash
   gh release create v1.0.0 \
       --title "v1.0.0 - Production Release" \
       --notes "First production release"
   ```

6. **Verify PyPI publish** (automatic via GitHub Actions)

7. **Verify Docker publish** (automatic via GitHub Actions)

---

## Rollback Procedure

### Rollback to Previous Version

1. **Identify previous stable version**
   ```bash
   git log --oneline -10
   ```

2. **Checkout previous tag**
   ```bash
   git checkout v0.9.0
   ```

3. **Rebuild and redeploy**
   ```bash
   docker build -t streamlitforge:0.9.0 .
   docker-compose up -d streamlitforge
   ```

4. **Document issue**
   - Create GitHub issue for post-mortem
   - Analyze what went wrong
   - Plan fix for next release

---

## Monitoring

### Health Checks

```bash
# Check if StreamlitForge CLI works
streamlitforge --version

# Check if Docker image builds
docker build -t streamlitforge:test .

# Check if tests pass
python -m pytest streamlitforge/tests/ -v
```

### Logs

```bash
# View streamlitforge logs (if configured)
cat streamlitforge.log

# View Docker logs
docker logs streamlitforge

# View test results
cat test_results_baseline.txt
```

---

## Maintenance Tasks

### Weekly

- [ ] Review security scan results
- [ ] Check for dependency updates
- [ ] Review test coverage
- [ ] Update documentation if needed

### Monthly

- [ ] Review and update dependencies
- [ ] Performance benchmarking
- [ ] Security vulnerability scanning
- [ ] Backup configuration files

### Quarterly

- [ ] Full security audit
- [ ] Performance review
- [ ] User feedback review
- [ ] Version planning

---

## API Key Management

### Configuring API Keys

```bash
# Configure for specific provider
streamlitforge configure --provider openai --api-key sk-...
streamlitforge configure --provider ollama --model llama3
```

### Viewing Configured Keys

```bash
# List configured providers
streamlitforge info
```

### Securing API Keys

- Keys stored in `~/.streamlitforge/secrets.toml`
- Never commit to git (ignored in .dockerignore)
- Rotate keys regularly
- Use environment variables for production

---

## Troubleshooting by Component

### Port Manager

```python
from streamlitforge.core.port_manager import PortManager

pm = PortManager()
port = pm.lookup("/path/to/project")
print(f"Port assigned: {port}")
```

### Project Manager

```python
from streamlitforge.core.project_manager import ProjectManager

pm = ProjectManager()
projects = pm.list_projects()
for project in projects:
    print(f"Name: {project['name']}, Path: {project['path']}")
```

### LLM Router

```python
from streamlitforge.llm.router import EnhancedLLMRouter

router = EnhancedLLMRouter()
print(f"Available providers: {list(router.providers.keys())}")
```

### Pattern Library

```python
from streamlitforge.patterns.learner import PatternLearner

learner = PatternLearner()
patterns = learner.get_builtin_pattern_count()
print(f"Patterns loaded: {patterns}")
```

---

## Support

### Getting Help

- **GitHub Issues:** https://github.com/CaptainPhantasy/StreamlitForge/issues
- **Documentation:** https://github.com/CaptainPhantasy/StreamlitForge/blob/main/README.md
- **Security:** security@streamlitforge.com (for vulnerabilities)

### Escalation

1. Check this runbook for solutions
2. Review documentation
3. Search GitHub Issues
4. Open new issue with details
5. If critical, contact security@streamlitforge.com

---

**Last Updated:** 2026-03-04
**Version:** 1.0.0
