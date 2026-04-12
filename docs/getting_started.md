# Getting Started with StreamlitForge

## Introduction

StreamlitForge is an AI-powered CLI tool for building Streamlit applications. It provides deterministic port management, template scaffolding, LLM integration, and comprehensive testing.

---

## Installation

### Prerequisites

- Python 3.8 or higher
- pip (Python package installer)
- (Optional) Docker for containerized deployment

### Install StreamlitForge

```bash
# Clone the repository
git clone https://github.com/CaptainPhantasy/StreamlitForge.git
cd StreamlitForge

# Install in editable mode
pip install -e .

# Verify installation
streamlitforge --version
```

---

## Quick Start

### Create Your First Project

```bash
# Basic project creation
streamlitforge create my-first-app

# With dependencies
streamlitforge create my-app --dependencies pandas matplotlib

# Using a template
streamlitforge create my-dashboard --template dashboard

# Skip virtual environment creation
streamlitforge create my-app --no-venv --no-git
```

### Start the Application

```bash
# Navigate to your project
cd my-first-app/src

# Run the Streamlit app
streamlit run streamlit_app.py

# Or use the deterministic port manager
streamlit run streamlit_app.py --server.port 8501
```

---

## Available Templates

StreamlitForge comes with 5 built-in templates:

| Template | Description | Use Case |
|----------|-------------|----------|
| **dashboard** | Data visualization dashboard | Analytics and metrics |
| **chat** | LLM-powered chat interface | Conversational AI |
| **crud** | Create, Read, Update, Delete app | Database-backed apps |
| **analysis** | Data analysis tool | EDA and insights |
| **admin** | Admin panel dashboard | Management interfaces |

### List Available Templates

```bash
streamlitforge list-templates
```

### Using a Template

```bash
streamlitforge create my-dashboard --template dashboard
```

---

## LLM Integration

### Ollama (Local - Free)

```bash
# 1. Install Ollama
# https://ollama.ai/

# 2. Run Ollama
ollama run llama3

# 3. Configure StreamlitForge
streamlitforge configure --provider ollama --model llama3
```

### OpenAI (Paid)

```bash
streamlitforge configure --provider openai --api-key sk-...
```

### Groq (Free Tier)

```bash
streamlitforge configure --provider groq --api-key ...
```

---

## Project Structure

After creating a project:

```
my-project/
├── .streamlit/              # Streamlit configuration
├── src/                     # Source code
│   └── streamlit_app.py    # Main application file
├── tests/                   # Test files
├── data/                    # Data files
├── requirements.txt         # Python dependencies
├── README.md               # Project documentation
└── streamlitforge_config.yaml  # Configuration
```

---

## Common Commands

### Project Management

```bash
# Create project
streamlitforge create my-app

# List templates
streamlitforge list-templates

# Get project info
streamlitforge info my-app

# Delete project
streamlitforge delete my-app
```

### Configuration

```bash
# Configure LLM provider
streamlitforge configure --provider ollama --model llama3

# Initialize configuration
streamlitforge init
```

### Knowledge Base

```bash
# Search knowledge base
streamlitforge knowledge search "chat interface"

# View all patterns
streamlitforge knowledge list
```

---

## Development

### Run Tests

```bash
# Run all tests
python -m pytest streamlitforge/tests/ -v

# Run with coverage
python -m pytest streamlitforge/tests/ -v --cov=streamlitforge

# Run integration tests
python -m pytest streamlitforge/tests/integration/ -v
```

### Code Quality

```bash
# Format code
black streamlitforge/ app/

# Lint code
flake8 streamlitforge/ app/

# Type checking
mypy streamlitforge/
```

### Security

```bash
# Security scan
./scripts/security_scan.sh
```

---

## Docker Deployment

### Build Docker Image

```bash
docker build -t streamlitforge:test .
```

### Run with Docker Compose

```bash
# Start production service
docker-compose up -d streamlitforge

# Start development service
docker-compose up -d streamlitforge-dev

# Run tests in container
docker-compose up -d streamlitforge-test
```

---

## Troubleshooting

### Port Already in Use

```bash
# Find process using port
lsof -i :8501

# Kill process or use different port
streamlitforge create myapp --port 8502
```

### Virtual Environment Issues

```bash
# Skip venv creation
streamlitforge create my-app --no-venv
```

### Dependency Conflicts

```bash
# Install in clean environment
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

---

## Best Practices

### 1. Use Deterministic Port Management

StreamlitForge automatically assigns ports using path hashing. No conflicts!

### 2. Pin Dependencies

Use pinned versions for production:
```txt
# requirements.txt
streamlit==1.32.0
pandas==2.0.3
```

### 3. Use Templates

Start with a template to avoid boilerplate code.

### 4. Write Tests

Always test your applications:
```bash
python -m pytest tests/ -v
```

### 5. Security Scanning

Run security scans regularly:
```bash
./scripts/security_scan.sh
```

---

## Next Steps

1. **Explore Templates**: Try different templates to see what's possible
2. **Configure LLM**: Set up your preferred LLM provider
3. **Build Your App**: Use StreamlitForge to scaffold your application
4. **Add Features**: Extend your app with additional components
5. **Test Thoroughly**: Write tests for all your code
6. **Deploy**: Use Docker for containerized deployment

---

## Resources

- **Documentation:** [GitHub README](https://github.com/CaptainPhantasy/StreamlitForge)
- **Issues:** [GitHub Issues](https://github.com/CaptainPhantasy/StreamlitForge/issues)
- **Changelog:** [CHANGELOG.md](https://github.com/CaptainPhantasy/StreamlitForge/blob/main/CHANGELOG.md)
- **Security Policy:** [SECURITY.md](https://github.com/CaptainPhantasy/StreamlitForge/blob/main/SECURITY.md)

---

## Need Help?

If you need assistance:
1. Check the troubleshooting section above
2. Review the runbook: [docs/runbook.md](https://github.com/CaptainPhantasy/StreamlitForge/blob/main/docs/runbook.md)
3. Open an issue on GitHub
4. Contact security@streamlitforge.com for vulnerabilities

---

**Version:** 1.0.0
**Last Updated:** 2026-03-04
