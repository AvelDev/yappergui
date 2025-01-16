# Contributing to YapperGUI

Thank you for your interest in contributing to YapperGUI! This document provides guidelines and instructions for contributing to the project.

## Development Setup

1. Fork and clone the repository
2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Install development dependencies:
```bash
pip install pytest pytest-cov black mypy
```

## Code Style

- Follow PEP 8 guidelines
- Use type hints for all function parameters and return values
- Add docstrings to all modules, classes, and functions
- Use black for code formatting
- Use meaningful variable and function names

## Testing

- Write unit tests for new features
- Ensure all tests pass before submitting a PR
- Maintain or improve code coverage

Run tests:
```bash
pytest tests/
```

## Pull Request Process

1. Create a feature branch from `main`
2. Make your changes
3. Add or update tests
4. Update documentation
5. Run tests and ensure they pass
6. Submit a Pull Request

## Commit Messages

Follow the conventional commits specification:
- feat: New feature
- fix: Bug fix
- docs: Documentation changes
- style: Code style changes
- refactor: Code refactoring
- test: Test updates
- chore: Maintenance tasks

## Code Review

- All submissions require review
- Address review comments
- Keep discussions focused and professional
- Be patient and respectful

## Documentation

- Update README.md if needed
- Add docstrings for new code
- Update API documentation
- Include examples for new features

## License

By contributing, you agree that your contributions will be licensed under the project's MIT License.
