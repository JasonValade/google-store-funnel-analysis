# Contributing to Google Store Funnel Analysis

Thank you for your interest in contributing! This document provides guidelines for contributing to this project.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Workflow](#development-workflow)
- [Code Style and Quality](#code-style-and-quality)
- [Testing](#testing)
- [Submitting Changes](#submitting-changes)
- [Reporting Issues](#reporting-issues)

## Code of Conduct

This project adheres to a code of conduct. By participating, you are expected to uphold this standard. Please be respectful, inclusive, and collaborative.

## Getting Started

### Prerequisites

- Python 3.11 or newer
- Git
- Docker (optional, for containerized development)

### Setup

1. Fork the repository on GitHub
2. Clone your fork locally:
   ```bash
   git clone https://github.com/YOUR_USERNAME/google-store-funnel-analysis.git
   cd google-store-funnel-analysis
   ```
3. Create a virtual environment:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```
4. Install development dependencies:
   ```bash
   make install-dev
   ```
5. Install pre-commit hooks:
   ```bash
   make pre-commit-install
   ```

## Development Workflow

### Branching Strategy

- `main` - Production-ready code
- `develop` - Integration branch for features
- Feature branches - `feature/your-feature-name`
- Bugfix branches - `bugfix/your-bugfix-name`

### Creating a Feature Branch

```bash
git checkout -b feature/your-feature-name
```

### Making Changes

1. Make your changes following the [Code Style and Quality](#code-style-and-quality) guidelines
2. Write tests for new functionality
3. Ensure all tests pass: `make test`
4. Run code quality checks: `make check`

### Committing Changes

Pre-commit hooks will automatically run before each commit. If they fail, fix the issues and try again.

Commit messages should follow conventional commits format:

```
type(scope): subject

body

footer
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

Example:
```
feat(dashboard): add product category filter to funnel page

Add a dropdown filter allowing users to filter funnel metrics by
product category. This helps identify category-specific conversion
patterns.

Closes #42
```

## Code Style and Quality

This project uses automated tools to ensure code quality:

### Tools

- **Black** - Code formatting
- **Ruff** - Linting and import sorting
- **MyPy** - Static type checking
- **Bandit** - Security linting

### Running Checks

```bash
make lint          # Run linters
make format        # Format code
make check         # Run all quality checks
make security      # Run security audit
```

### Guidelines

- Follow PEP 8 style guide
- Write docstrings for all functions and classes
- Keep functions focused and small
- Use type hints where appropriate
- Add comments for complex logic

## Testing

### Running Tests

```bash
make test          # Run all tests
make test-cov      # Run tests with coverage report
```

### Writing Tests

- Write unit tests for new functionality in the `tests/` directory
- Test both happy paths and edge cases
- Mock external dependencies (BigQuery, file I/O)
- Aim for high test coverage on critical paths

### Test Structure

```python
def test_function_name():
    """Test description."""
    # Arrange
    input_data = ...

    # Act
    result = function_under_test(input_data)

    # Assert
    assert result == expected
```

## Submitting Changes

### Pull Request Process

1. Update documentation if needed
2. Ensure all tests pass: `make test`
3. Ensure code quality checks pass: `make check`
4. Push your branch to GitHub:
   ```bash
   git push origin feature/your-feature-name
   ```
5. Create a pull request on GitHub
6. Fill in the PR template
7. Wait for CI checks to pass
8. Address review feedback

### Pull Request Checklist

- [ ] Tests pass locally
- [ ] Code follows style guidelines
- [ ] Documentation is updated
- [ ] Commit messages are clear
- [ ] PR description explains the change

## Reporting Issues

### Bug Reports

When reporting a bug, include:

- Description of the bug
- Steps to reproduce
- Expected behavior
- Actual behavior
- Environment (OS, Python version)
- Screenshots if applicable

### Feature Requests

When requesting a feature, include:

- Description of the feature
- Use case and motivation
- Possible implementation approach
- Alternatives considered

## Questions?

If you have questions that aren't covered here, please open an issue with the `question` label.

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
