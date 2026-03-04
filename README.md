# StreamlitForge

AI-Powered Streamlit Application Builder CLI

StreamlitForge is a robust CLI tool for building Streamlit applications with AI assistance. It provides deterministic port management, template scaffolding, LLM integration, and knowledge base for Streamlit best practices.

## Features

- **Deterministic Port Management**: Same project always gets the same port via path hashing
- **Project Scaffolding**: Create projects with one command
- **LLM Integration**: Support for multiple providers (OpenRouter, Ollama, Groq)
- **Knowledge Base**: Built-in Streamlit examples and patterns
- **Template System**: Ready-to-use templates for common use cases
- **Offline Support**: Works without API keys (Ollama, etc.)

## Installation

```bash
pip install -e .
```

## Quick Start

Create a new project:

```bash
streamlitforge create my-app
```

This will:
1. Create a project directory
2. Set up a virtual environment
3. Install dependencies
4. Generate a basic Streamlit app
5. Create a requirements.txt file

## Usage

### Create a Project

```bash
# Basic creation
streamlitforge create my-app

# With custom path
streamlitforge create my-app --path /path/to/projects

# With dependencies
streamlitforge create my-app --dependencies pandas matplotlib

# Using a template
streamlitforge create my-app --template dashboard
```

### List Available Templates

```bash
streamlitforge list-templates
```

Templates available:
- `dashboard` - Data visualization dashboard
- `chat` - LLM-powered chat interface
- `crud` - Create, Read, Update, Delete application
- `analysis` - Data analysis tool
- `admin` - Admin panel dashboard

### Get Project Info

```bash
streamlitforge info my-app
```

### Delete a Project

```bash
streamlitforge delete my-app
```

### Initialize Configuration

```bash
streamlitforge init
```

## Project Structure

After creating a project:

```
my-app/
├── venv/                    # Virtual environment
├── src/
│   └── streamlit_app.py    # Main application file
├── tests/                  # Test files
├── data/                   # Data files
├── docs/                   # Documentation
├── requirements.txt        # Python dependencies
├── README.md              # Project README
├── .gitignore             # Git ignore file
└── streamlitforge_config.yaml  # Configuration
```

## Configuration

Create or edit `streamlitforge_config.yaml`:

```yaml
project_name: my-app
port: 8501
dependencies: []
templates: []

llm:
  provider: openrouter
  api_key: your-api-key
  model: llama3-70b-8192
  temperature: 0.7
  max_tokens: 2048

knowledge:
  max_examples: 10

patterns:
  storage_dir: .streamlitforge/patterns
```

### LLM Providers

#### OpenRouter (Recommended)

```yaml
llm:
  provider: openrouter
  api_key: sk-or-...
  model: llama3-70b-8192
```

#### Ollama (Local - Free)

```bash
# Install Ollama
# https://ollama.ai/

# Run Ollama
ollama run llama3

# Configure StreamlitForge
llm:
  provider: ollama
  model: llama3
```

## Project Lifecycle

### Running the Application

```bash
# Activate virtual environment
source venv/bin/activate  # macOS/Linux
# or
venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Run the app
streamlit run src/streamlit_app.py --server.port 8501
```

### Adding Features

StreamlitForge includes a built-in knowledge base with common patterns:

```bash
streamlitforge knowledge search "chat interface"
```

## Architecture

### Core Components

1. **Port Manager**: Deterministic port assignment using path hashing
2. **Configuration System**: YAML/JSON configuration with validation
3. **Project Manager**: Project scaffolding and lifecycle management
4. **LLM Abstraction Layer**: Unified interface for multiple providers
5. **Knowledge Base**: Streamlit examples and patterns
6. **Template Engine**: Jinja2-based templating system
7. **CLI Interface**: Command-line interface for all operations

### Port Assignment Algorithm

StreamlitForge uses SHA-256 hashing of project paths to determine ports:

1. Normalize project path (remove spaces, expand ~)
2. Generate SHA-256 hash
3. Take first 16 hex characters
4. Map to port range [base_port, max_port]
5. Cache result for consistency

This ensures:
- Same project always gets same port
- Different projects get different ports
- No port conflicts
- No manual configuration needed

## Testing

Run tests:

```bash
streamlitforge test
```

## Roadmap

- [x] Core infrastructure (Port Manager, Config, Project Manager)
- [x] LLM Integration (OpenRouter, Ollama)
- [x] Knowledge Base (examples, patterns)
- [x] Template System (Jinja2)
- [x] CLI Interface
- [ ] Enhanced templates (more components, layouts)
- [ ] Database integration patterns
- [ ] Authentication templates
- [ ] Streaming support
- [ ] Multi-language support
- [ ] Web UI for configuration

## Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## License

MIT License - see LICENSE file for details

## Support

For issues and questions:
- GitHub Issues: https://github.com/yourusername/streamlitforge/issues
- Documentation: https://streamlitforge.com/docs

## Acknowledgments

- Streamlit team for the amazing framework
- OpenRouter for the LLM provider
- Ollama for local LLM support

---

Built with ❤️ using StreamlitForge
