# Contributing

Contributions are welcome. You can report bugs, request features, or submit pull requests.

## Development Setup

1. Requirements: Python 3.10 or newer and Git.
2. Clone the repository:
   ```bash
   git clone https://github.com/Arthur-911/SDK-Software-development-Kit-.git
   cd SDK-Software-development-Kit-
   ```
3. Set up a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .\.venv\Scripts\activate
   ```
4. Install editable package and development dependencies:
   ```bash
   pip install -e ".[dev]"
   ```

## Checks and Testing

Before opening a pull request, make sure tests and formatting pass:

```bash
# Run tests with coverage
pytest

# Check linting and formatting
ruff check src tests
ruff format --check src tests

# Run type checker
mypy src
```

## Pull Requests

1. Create a branch: `git checkout -b feature-or-fix-name`
2. Commit your work with clear commit messages.
3. Push to your branch and open a pull request on GitHub.
