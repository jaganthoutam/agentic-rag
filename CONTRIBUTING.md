# Contributing to Agentic RAG

Thank you for your interest in contributing to Agentic RAG! This document provides guidelines and instructions for contributing.

## Code of Conduct

By participating in this project, you agree to abide by our [Code of Conduct](CODE_OF_CONDUCT.md).

## How to Contribute

### Reporting Bugs

If you find a bug, please create an issue with the following information:

- A clear, descriptive title
- A detailed description of the bug
- Steps to reproduce the issue
- Expected behavior
- Actual behavior
- Screenshots (if applicable)
- Environment information (OS, Python version, package versions)

### Suggesting Enhancements

We welcome suggestions for new features or improvements. Please create an issue with:

- A clear, descriptive title
- A detailed description of the proposed enhancement
- The rationale for the enhancement
- Possible implementation approaches (if you have ideas)

### Pull Requests

We welcome pull requests! Please follow these steps:

1. Fork the repository
2. Create a new branch for your feature or bug fix
3. Make your changes
4. Add or update tests for your changes
5. Run the test suite to ensure all tests pass
6. Update documentation as needed
7. Submit a pull request with a clear description of your changes

### Development Workflow

1. Install development dependencies:
   ```bash
   pip install -r requirements-dev.txt
   ```

2. Make your changes

3. Run tests:
   ```bash
   pytest tests/
   ```

4. Check code style:
   ```bash
   flake8 .
   ```

5. Format code:
   ```bash
   black .
   ```

## Code Style Guidelines

- Follow PEP 8 style guidelines
- Use meaningful variable and function names
- Write clear docstrings in the Google Python Style format
- Include type annotations
- Keep functions and methods focused on a single responsibility
- Write unit tests for new features

## Testing

- All new features should include unit tests
- All bug fixes should include a test that reproduces the bug
- Tests should be focused and test one aspect of functionality
- Integration tests should be included for complex interactions

## Documentation

- Update the README.md if your changes impact how users interact with the system
- Update or add docstrings for new or modified functions, classes, and methods
- Update or add documentation in the docs/ directory as needed

## Commit Guidelines

- Use clear, descriptive commit messages
- Use the present tense ("Add feature" not "Added feature")
- Use the imperative mood ("Move cursor to..." not "Moves cursor to...")
- Reference issues and pull requests in commit messages where appropriate

## Versioning

We follow [Semantic Versioning](https://semver.org/). Please consider the version impact of your changes.

## License

By contributing to Agentic RAG, you agree that your contributions will be licensed under the project's [MIT License](LICENSE).

## Questions

If you have any questions about contributing, please create an issue with your question.

Thank you for your contributions!