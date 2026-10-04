# Contributing to NASA Python SDK

Thank you for your interest in contributing to the **NASA Python SDK**! We welcome bug fixes, documentation improvements, new endpoint additions, and performance enhancements.

---

## 🛠️ Development Setup

### 1. Prerequisites
- Python 3.10+
- Git

### 2. Fork and Clone
```bash
git clone https://github.com/your-username/nasa-sdk.git
cd nasa-sdk
```

### 3. Create a Virtual Environment
```bash
python -m venv .venv

# On Linux/macOS:
source .venv/bin/activate

# On Windows:
.\.venv\Scripts\activate
```

### 4. Install Dependencies
Install the package in editable mode along with development dependencies:
```bash
pip install -e ".[dev]"
```

---

## 🧪 Testing and Quality Standards

We maintain **100% test coverage** and strict typing standards. Before submitting a Pull Request, run the following verification steps:

### Run Unit Tests & Coverage
```bash
pytest
```

### Run Linter & Formatter (Ruff)
```bash
ruff check src tests
ruff format --check src tests
```

To auto-format code:
```bash
ruff format src tests
```

### Run Type Checker (Mypy)
```bash
mypy src
```

---

## 📝 Commit Guidelines

We recommend using [Conventional Commits](https://www.conventionalcommits.org/):
- `feat:` A new feature or endpoint
- `fix:` A bug fix
- `docs:` Documentation changes
- `test:` Adding or refactoring tests
- `refactor:` Code change that neither fixes a bug nor adds a feature
- `chore:` Maintenance tasks or dependency updates

---

## 🚀 Submitting a Pull Request

1. Create a feature branch: `git checkout -b feat/your-feature-name`
2. Commit your changes: `git commit -m "feat(apod): add thumbnail support"`
3. Push to your fork: `git push origin feat/your-feature-name`
4. Open a Pull Request on GitHub against the `main` branch.
