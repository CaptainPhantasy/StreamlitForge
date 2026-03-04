# Quick Start Guide

This guide will help you get started with StreamlitForge quickly.

## Installation

```bash
pip install streamlitforge
```

## Create Your First Project

```bash
streamlitforge create my-app
```

This creates a new Streamlit project with:
- Project directory structure
- Virtual environment
- Basic Streamlit app
- Configuration file
- Dependencies file

## Project Structure

```
my-app/
├── venv/                    # Virtual environment
├── src/
│   └── streamlit_app.py    # Main application
├── tests/                  # Test files
├── data/                   # Data files
├── docs/                   # Documentation
├── requirements.txt        # Dependencies
├── README.md              # Project README
└── streamlitforge_config.yaml  # Configuration
```

## Using Templates

StreamlitForge includes built-in templates:

### Dashboard Template
```bash
streamlitforge create my-dashboard --template dashboard
```

Creates a data visualization dashboard with:
- Metrics display
- Interactive charts
- Data upload
- Multiple chart types

### Chat Template
```bash
streamlitforge create my-chat --template chat
```

Creates an LLM-powered chat interface with:
- Message history
- Streaming responses
- Session state management

### CRUD Template
```bash
streamlitforge create my-crud --template crud
```

Creates a data management application with:
- Create, Read, Update, Delete operations
- Form inputs
- Data table display

### Analysis Template
```bash
streamlitforge create my-analysis --template analysis
```

Creates a data analysis tool with:
- File upload
- Statistical analysis
- Correlation matrices
- Distribution plots

### Admin Template
```bash
streamlitforge create my-admin --template admin
```

Creates an admin dashboard with:
- User metrics
- Activity monitoring
- Quick actions
- Reports

## Running Your App

```bash
cd my-app
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
streamlit run src/streamlit_app.py
```

## Configuration

Edit `streamlitforge_config.yaml`:

```yaml
project_name: my-app
port: 8501
dependencies:
  - pandas
  - numpy

llm:
  provider: openrouter
  api_key: your-api-key
  model: llama3-70b-8192
```

## LLM Integration

### OpenRouter (Cloud)

```yaml
llm:
  provider: openrouter
  api_key: sk-or-your-key
  model: llama3-70b-8192
```

### Ollama (Local)

```bash
# Install Ollama
# https://ollama.ai/

# Run model
ollama run llama3

# Configure
llm:
  provider: ollama
  model: llama3
```

## Adding Dependencies

```bash
# Add to requirements.txt
echo "plotly" >> requirements.txt

# Install
pip install -r requirements.txt
```

## CLI Commands

```bash
# List templates
streamlitforge list-templates

# Get project info
streamlitforge info my-app

# Initialize config
streamlitforge init

# Search knowledge base
streamlitforge knowledge search "chat interface"

# Delete project
streamlitforge delete my-app
```

## Next Steps

- Explore the [Templates Guide](templates.md)
- Learn about [LLM Integration](llm-integration.md)
- Read the [Configuration Guide](configuration.md)
- Check out [Best Practices](best-practices.md)

## Getting Help

- Documentation: https://streamlitforge.readthedocs.io
- Issues: https://github.com/yourusername/streamlitforge/issues
- Discussions: https://github.com/yourusername/streamlitforge/discussions
