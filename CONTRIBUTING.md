# Contributing to StreamlitForge

Thank you for considering contributing to StreamlitForge! This document outlines the process for contributing to the project.

## Development Setup

1. Clone the repository:
```bash
git clone https://github.com/yourusername/streamlitforge.git
cd streamlitforge
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -e .
pip install -r requirements-dev.txt
```

## Running Tests

```bash
pytest streamlitforge/tests/ -v
```

## Code Style

We use:
- **Black** for code formatting
- **Flake8** for linting
- **MyPy** for type checking

Run before committing:
```bash
black streamlitforge/
flake8 streamlitforge/
mypy streamlitforge/
```

## Pull Request Process

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Format code with Black
7. Commit your changes (`git commit -m 'Add amazing feature'`)
8. Push to your branch (`git push origin feature/amazing-feature`)
9. Open a Pull Request

## Commit Messages

Use clear, descriptive commit messages:
- `feat: Add new feature`
- `fix: Fix bug in X`
- `docs: Update documentation`
- `test: Add tests for Y`
- `refactor: Refactor Z`

## Code Review Process

All submissions require review. We use GitHub pull requests for this purpose.

## Community Guidelines

- Be respectful and inclusive
- Follow the code of conduct
- Help others learn and grow

## Questions?

Open an issue or reach out to the maintainers.

Thank you for contributing! 🎉
