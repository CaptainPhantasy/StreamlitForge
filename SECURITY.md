# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | :white_check_mark: |

## Reporting a Vulnerability

Please report security vulnerabilities to security@streamlitforge.com

**IMPORTANT:** Do NOT open a public issue.

**Please include:**
- Vulnerability type (e.g., SQL injection, XSS, information disclosure)
- Affected version
- Steps to reproduce
- Expected vs actual behavior
- Any suggested fixes

## Security Features

### Current Security Measures

1. **API Key Management**
   - API keys stored in user config directory
   - Keys never committed to source code
   - Keys encrypted at rest (future enhancement)

2. **Dependency Security**
   - All dependencies pinned to exact versions
   - Regular security scanning (bandit, safety)
   - Dependency audit (pip-audit)

3. **Code Quality**
   - Pre-commit hooks for code quality
   - Security checks (bandit)
   - Type checking (mypy)

4. **Container Security**
   - Docker non-root user
   - Minimal base images
   - Health checks

### Future Security Enhancements

- [ ] Encrypt API keys at rest
- [ ] Input validation for all user inputs
- [ ] Rate limiting on API calls
- [ ] CSRF protection
- [ ] Security headers in web UI
- [ ] Dependency vulnerability scanning in CI/CD

## Incident Response

### If You Find a Vulnerability

1. Do NOT disclose publicly
2. Contact security@streamlitforge.com
3. Include all relevant details
4. Wait for official disclosure
5. Allow time for patch development

### After Patching

1. Release security advisory
2. Update version to include security fix
3. Update CHANGELOG.md
4. Provide guidance to users
5. Close security issue

## Resources

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [GitHub Security Advisories](https://github.com/CaptainPhantasy/StreamlitForge/security/advisories)
- [Security Guidelines](https://docs.github.com/en/code-security)
