"""Senior Developer Persona for expert guidance."""

from typing import Any, Dict, List, Optional

SENIOR_DEVELOPER_PROMPT = """
You are a Senior Streamlit Developer with 15+ years of experience in:
- Python web development (Flask, Django, FastAPI)
- Data visualization (Plotly, Altair, Matplotlib)
- Frontend development (React, Vue, modern CSS)
- Database design (SQL, NoSQL, ORMs)
- Cloud deployment (AWS, GCP, Azure)
- Performance optimization and scaling
- Security best practices

Your expertise in Streamlit specifically includes:
- All versions from 0.x through 1.x
- Session state management patterns
- Caching strategies for performance
- Multi-page app architecture
- Custom component development
- Enterprise deployment patterns
- Common pitfalls and anti-patterns

When answering:
1. Provide architectural context, not just code
2. Explain trade-offs and alternatives considered
3. Warn about potential issues before they occur
4. Suggest production-ready patterns over quick hacks
5. Reference specific Streamlit versions when relevant
6. Include error handling and edge cases

Tone: Professional, direct, and educational. You're a mentor, not just an answer bot.
"""


class SeniorDeveloperPersona:
    """Encapsulates senior developer expertise for Streamlit."""

    DOMAINS = {
        "architecture": [
            "Multi-page app structure",
            "State management patterns",
            "Component composition",
            "API integration patterns",
            "Authentication flows",
        ],
        "performance": [
            "Caching strategies",
            "Lazy loading",
            "Async operations",
            "Memory management",
            "Query optimization",
        ],
        "security": [
            "Input validation",
            "Secrets management",
            "Authentication/Authorization",
            "SQL injection prevention",
            "XSS protection",
        ],
        "deployment": [
            "Streamlit Cloud",
            "Docker containerization",
            "Kubernetes scaling",
            "CI/CD pipelines",
            "Environment configuration",
        ],
        "patterns": [
            "Repository pattern",
            "Factory pattern",
            "Observer pattern",
            "State machine",
            "Middleware chains",
        ],
    }

    DOMAIN_KEYWORDS = {
        "architecture": ["structure", "architect", "design", "multipage", "multi-page", "organize"],
        "performance": ["slow", "fast", "cache", "speed", "optimize", "memory", "performance"],
        "security": ["secure", "auth", "password", "secret", "sql injection", "xss", "token"],
        "deployment": ["deploy", "docker", "cloud", "kubernetes", "k8s", "heroku", "render"],
        "patterns": ["pattern", "repository", "factory", "observer", "state machine", "middleware"],
    }

    def detect_domain(self, question: str) -> str:
        question_lower = question.lower()
        scores: Dict[str, int] = {}
        for domain, keywords in self.DOMAIN_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw in question_lower)
            scores[domain] = score
        best = max(scores, key=scores.get) if scores else "architecture"
        return best if scores.get(best, 0) > 0 else "architecture"

    def get_system_prompt(self, domain: str = None) -> str:
        prompt = SENIOR_DEVELOPER_PROMPT
        if domain and domain in self.DOMAINS:
            patterns = ", ".join(self.DOMAINS[domain])
            prompt += f"\n\nFocus on: {domain}\nRelevant patterns: {patterns}"
        return prompt

    def get_review_prompt(self, code: str) -> str:
        return f"""Review this Streamlit code from a senior developer perspective:

```python
{code}
```

Provide:
1. Overall assessment (1-10)
2. Strengths
3. Areas for improvement
4. Security concerns
5. Performance suggestions
6. Best practice violations
7. Refactoring recommendations
"""
