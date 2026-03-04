# Changelog

All notable changes to StreamlitForge will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2024-01-01

### Added
- Core infrastructure (Port Manager, Config, Project Manager)
- Deterministic port assignment using SHA-256 path hashing
- Configuration system with YAML/JSON support
- Project scaffolding and lifecycle management
- LLM abstraction layer with multiple provider support
  - OpenRouter provider
  - Ollama provider (local, free)
  - LLM Router with fallback support
- Streamlit Knowledge Base
  - Built-in examples and patterns
  - Semantic search capability
  - Pattern storage and retrieval
- Template Engine with Jinja2
  - Built-in templates (dashboard, chat, CRUD, analysis, admin)
  - Component templates
- CLI interface with Click
  - `create` - Create new projects
  - `list-templates` - List available templates
  - `info` - Get project information
  - `delete` - Delete projects
  - `init` - Initialize configuration
  - `knowledge search` - Search knowledge base
- Comprehensive test suite
- Documentation (README, CONTRIBUTING)

### Features
- Vendor-agnostic LLM integration
- Offline support (Ollama)
- No port conflicts (deterministic assignment)
- Virtual environment setup
- Dependency management
- Template-based scaffolding

### Infrastructure
- Python 3.8+ support
- PyPI package configuration
- MIT License
- Git repository setup

## [Unreleased]

### Planned
- Enhanced templates with more components
- Database integration patterns
- Authentication templates
- Streaming support
- Multi-language support
- Web UI for configuration
- Pattern discovery and sharing
- CI/CD templates
- Docker support
- More LLM providers (Anthropic, Azure OpenAI)
