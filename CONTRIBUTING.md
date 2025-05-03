# Contributing to PesaLink Bulk Account Validator

Thank you for considering contributing to the PesaLink Bulk Account Validator! This document provides guidelines and instructions for contributing.

## Code of Conduct

By participating in this project, you agree to maintain a respectful and inclusive environment for everyone.

## How Can I Contribute?

### Reporting Bugs

Before creating a bug report:
- Check the issue tracker to see if the problem has already been reported
- Gather information about your environment (OS, Python version, etc.)

When reporting a bug:
- Use a clear and descriptive title
- Describe the exact steps to reproduce the problem
- Explain what behavior you expected and what you actually observed
- Include relevant logs, screenshots, or other information that might help

### Suggesting Enhancements

Before suggesting an enhancement:
- Check if the feature has already been suggested or implemented
- Consider whether it aligns with the project's goals

When suggesting an enhancement:
- Use a clear and descriptive title
- Provide a detailed description of the proposed functionality
- Explain why it would be useful to most users
- Include examples of how the feature would be used

### Pull Requests

1. Fork the repository
2. Create a new branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests to ensure they pass
5. Commit your changes (`git commit -m 'Add some amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

## Development Environment

### Setup

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/pesalink-validator.git
   cd pesalink-validator
   ```

2. Create and activate a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Install development dependencies:
   ```
   pip install pytest pytest-cov black flake8 isort
   ```

### Testing

Run the test suite:
```
./test_scripts/run_tests.sh
```

Run specific tests:
```
python -m pytest test_scripts/test_file.py::test_function
```

### Code Style

We follow the PEP 8 style guide with these specifications:
- Line length: 100 characters
- Docstrings: Google style
- Import order: standard library, third-party, local

Format your code before submitting:
```
black app scripts test_scripts
isort app scripts test_scripts
flake8 app scripts test_scripts
```

## Documentation

When adding new features, please update the relevant documentation:
- Update docstrings for all functions, classes, and modules
- Update README.md if appropriate
- Update user and developer guides if needed

## Commit Messages

Follow these guidelines for commit messages:
- Use the present tense ("Add feature" not "Added feature")
- Use the imperative mood ("Move cursor to..." not "Moves cursor to...")
- Limit the first line to 72 characters or less
- Reference issues and pull requests after the first line

## Release Process

1. Update version number in relevant files
2. Update CHANGELOG.md with list of changes
3. Create a new release on GitHub with release notes
4. Tag the release according to semantic versioning

## Questions?

If you have any questions or need help with contributing, please open an issue with the "question" label.

Thank you for contributing to the PesaLink Bulk Account Validator!