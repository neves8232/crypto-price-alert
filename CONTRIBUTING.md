# Contributing to Crypto Price Alert System

First off, thank you for considering contributing to the Crypto Price Alert System! It's people like you that make this project better.

## Table of Contents

1. [Code of Conduct](#code-of-conduct)
2. [How Can I Contribute?](#how-can-i-contribute)
3. [Development Workflow](#development-workflow)
4. [Coding Standards](#coding-standards)
5. [Testing Requirements](#testing-requirements)
6. [Documentation Requirements](#documentation-requirements)
7. [Commit Message Conventions](#commit-message-conventions)
8. [Pull Request Process](#pull-request-process)
9. [Review Process](#review-process)
10. [Community](#community)

---

## Code of Conduct

### Our Pledge

We pledge to make participation in our project a harassment-free experience for everyone, regardless of age, body size, disability, ethnicity, sex characteristics, gender identity and expression, level of experience, education, socio-economic status, nationality, personal appearance, race, religion, or sexual identity and orientation.

### Our Standards

**Positive behavior includes**:
- Using welcoming and inclusive language
- Being respectful of differing viewpoints and experiences
- Gracefully accepting constructive criticism
- Focusing on what is best for the community
- Showing empathy towards other community members

**Unacceptable behavior includes**:
- Trolling, insulting/derogatory comments, and personal attacks
- Public or private harassment
- Publishing others' private information without permission
- Other conduct which could reasonably be considered inappropriate

### Enforcement

Report unacceptable behavior to support@crypto-price-alert.com. All complaints will be reviewed and investigated promptly and fairly.

---

## How Can I Contribute?

### Reporting Bugs

**Before submitting a bug report**:
- Check the [Troubleshooting Guide](docs/TROUBLESHOOTING.md)
- Search [existing issues](https://github.com/yourusername/crypto-price-alert/issues)
- Collect relevant information (logs, environment details)

**Submitting a bug report**:

1. Use the [bug report template](.github/ISSUE_TEMPLATE/bug_report.md)
2. Provide a clear, descriptive title
3. Include detailed steps to reproduce
4. Describe the expected vs actual behavior
5. Add logs, screenshots, or error messages
6. Specify your environment (OS, Docker version, etc.)

**Example**:
```markdown
## Bug Description
Telegram alerts not being delivered

## Steps to Reproduce
1. Create alert with valid chat_id
2. Trigger alert condition
3. No message received

## Expected Behavior
Receive Telegram notification

## Actual Behavior
No notification received

## Logs
```
make logs-telegram
# Paste relevant logs here
```

## Environment
- OS: Ubuntu 22.04
- Docker: 20.10.21
- Docker Compose: 2.12.0
```

### Suggesting Features

**Before suggesting a feature**:
- Check if it's already in the [roadmap](README.md#roadmap)
- Search [existing feature requests](https://github.com/yourusername/crypto-price-alert/issues?q=is%3Aissue+label%3Aenhancement)

**Submitting a feature request**:

1. Use the [feature request template](.github/ISSUE_TEMPLATE/feature_request.md)
2. Provide a clear, descriptive title
3. Explain the problem this feature solves
4. Describe your proposed solution
5. Consider alternative solutions
6. Add mockups or examples if applicable

### Contributing Code

We love code contributions! Here's how to get started:

1. **Find or create an issue** to work on
2. **Comment on the issue** to let others know you're working on it
3. **Fork the repository**
4. **Create a branch** from `main`
5. **Make your changes**
6. **Write tests**
7. **Update documentation**
8. **Submit a pull request**

---

## Development Workflow

### Setting Up Your Development Environment

```bash
# 1. Fork and clone the repository
git clone https://github.com/YOUR_USERNAME/crypto-price-alert.git
cd crypto-price-alert

# 2. Add upstream remote
git remote add upstream https://github.com/yourusername/crypto-price-alert.git

# 3. Create virtual environment (for local development)
python3.11 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 4. Install dependencies
pip install -r requirements-dev.txt

# 5. Copy environment template
cp .env.example .env

# 6. Edit .env with your values
nano .env

# 7. Start development environment
make dev
```

### Creating a Feature Branch

```bash
# Update main branch
git checkout main
git pull upstream main

# Create feature branch
git checkout -b feature/amazing-feature

# Or for bug fixes
git checkout -b fix/bug-description
```

### Making Changes

1. **Write code** following our [coding standards](#coding-standards)
2. **Write tests** for new functionality
3. **Run tests locally**:
   ```bash
   pytest
   pytest --cov=src --cov-report=html
   ```
4. **Update documentation** if needed
5. **Run linters**:
   ```bash
   make lint
   # Or manually:
   ruff src/ tests/
   black src/ tests/
   mypy src/
   ```

### Committing Changes

```bash
# Stage changes
git add .

# Commit with descriptive message
git commit -m "feat: add email notification support"

# Push to your fork
git push origin feature/amazing-feature
```

See [Commit Message Conventions](#commit-message-conventions) for guidelines.

### Submitting a Pull Request

1. **Update your branch** with latest main:
   ```bash
   git fetch upstream
   git rebase upstream/main
   ```

2. **Push to your fork**:
   ```bash
   git push origin feature/amazing-feature --force-with-lease
   ```

3. **Create Pull Request** on GitHub:
   - Use the [pull request template](.github/PULL_REQUEST_TEMPLATE.md)
   - Reference related issues (#123)
   - Provide clear description of changes
   - Add screenshots for UI changes
   - List breaking changes if any

---

## Coding Standards

### Python Style Guide

We follow **PEP 8** with some modifications:

```python
# Good: Clear, descriptive names
def calculate_price_change_percentage(old_price: Decimal, new_price: Decimal) -> Decimal:
    """Calculate percentage change between two prices."""
    return ((new_price - old_price) / old_price) * 100

# Bad: Unclear names, no types
def calc(a, b):
    return ((b - a) / a) * 100
```

### Code Formatting

**Use black** for automatic formatting:
```bash
black src/ tests/
```

**Settings** (pyproject.toml):
```toml
[tool.black]
line-length = 100
target-version = ['py311']
```

### Linting

**Use ruff** for linting:
```bash
ruff src/ tests/
```

**Common rules**:
- No unused imports
- No undefined variables
- No mutable default arguments
- Use f-strings for formatting
- Use type hints

### Type Hints

**Always use type hints**:
```python
# Good
def create_alert(
    user_id: str,
    crypto_id: str,
    threshold: Decimal
) -> Alert:
    ...

# Bad
def create_alert(user_id, crypto_id, threshold):
    ...
```

**Check types with mypy**:
```bash
mypy src/
```

### Async/Await

**Use async/await** for I/O operations:
```python
# Good
async def fetch_price(crypto_id: str) -> Decimal:
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        return parse_price(response)

# Bad
def fetch_price(crypto_id: str) -> Decimal:
    response = requests.get(url)  # Blocking I/O
    return parse_price(response)
```

### Error Handling

**Use specific exceptions**:
```python
# Good
try:
    alert = await db.get_alert(alert_id)
except AlertNotFoundError:
    raise HTTPException(status_code=404, detail="Alert not found")

# Bad
try:
    alert = await db.get_alert(alert_id)
except Exception:
    raise HTTPException(status_code=500, detail="Error")
```

### Logging

**Use structured logging**:
```python
# Good
logger.info(
    "alert_triggered",
    alert_id=alert.id,
    crypto_id=alert.crypto_id,
    price=current_price
)

# Bad
logger.info(f"Alert {alert.id} triggered for {alert.crypto_id}")
```

---

## Testing Requirements

### Test Coverage

**Minimum coverage**: 80% overall, 90% for critical paths

```bash
# Run tests with coverage
pytest --cov=src --cov-report=html --cov-report=term

# View coverage report
open htmlcov/index.html
```

### Writing Tests

**Use pytest** with async support:
```python
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_create_alert(client: AsyncClient, db: AsyncSession):
    """Test creating a new alert."""
    # Arrange
    alert_data = {
        "user_id": "test_user",
        "crypto_id": "bitcoin",
        "alert_type": "PRICE_ABOVE",
        "threshold": 50000.00,
        "telegram_chat_id": "123456789"
    }

    # Act
    response = await client.post("/api/alerts", json=alert_data)

    # Assert
    assert response.status_code == 201
    result = response.json()
    assert result["user_id"] == "test_user"
    assert result["threshold"] == 50000.00
```

### Test Organization

```
tests/
├── unit/
│   ├── test_alert_engine.py
│   ├── test_price_collector.py
│   └── test_rate_limiter.py
├── integration/
│   ├── test_api_alerts.py
│   ├── test_api_cryptocurrencies.py
│   └── test_telegram_service.py
└── conftest.py  # Shared fixtures
```

### Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/unit/test_alert_engine.py

# Run specific test
pytest tests/unit/test_alert_engine.py::test_price_above_alert

# Run with verbose output
pytest -v

# Run with coverage
pytest --cov=src

# Run integration tests only
pytest tests/integration/
```

---

## Documentation Requirements

### Code Documentation

**Document all public functions**:
```python
def evaluate_alert(alert: Alert, current_price: Decimal) -> bool:
    """
    Evaluate if an alert should trigger based on current price.

    Args:
        alert: The alert configuration to evaluate
        current_price: Current cryptocurrency price

    Returns:
        True if alert should trigger, False otherwise

    Raises:
        ValueError: If alert type is not supported

    Example:
        >>> alert = Alert(alert_type="PRICE_ABOVE", threshold=50000)
        >>> evaluate_alert(alert, Decimal("51000"))
        True
    """
    ...
```

### API Documentation

**Document all endpoints** with OpenAPI annotations:
```python
@router.post("/alerts", response_model=AlertResponse, status_code=201)
async def create_alert(
    alert_data: AlertCreate,
    db: AsyncSession = Depends(get_db),
) -> AlertResponse:
    """
    Create a new price alert.

    Args:
        alert_data: Alert configuration

    Returns:
        Created alert with ID

    Raises:
        HTTPException: 404 if cryptocurrency not found

    Example:
        ```json
        {
          "user_id": "user123",
          "crypto_id": "bitcoin",
          "alert_type": "PRICE_ABOVE",
          "threshold": 50000.00,
          "telegram_chat_id": "123456789"
        }
        ```
    """
    ...
```

### README Updates

**Update README.md** if you:
- Add new features
- Change API endpoints
- Modify configuration options
- Add new dependencies

### Changelog Updates

**Update CHANGELOG.md** for all notable changes:
```markdown
## [Unreleased]

### Added
- Email notification support (#123)

### Changed
- Improved alert evaluation performance (#124)

### Fixed
- Fixed Telegram rate limiting issue (#125)
```

---

## Commit Message Conventions

We follow **Conventional Commits** specification:

### Format

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Types

- **feat**: New feature
- **fix**: Bug fix
- **docs**: Documentation changes
- **style**: Code style changes (formatting, no logic change)
- **refactor**: Code refactoring
- **test**: Adding or updating tests
- **chore**: Maintenance tasks (dependencies, config)
- **perf**: Performance improvements

### Examples

**Feature**:
```
feat(alerts): add email notification support

- Implemented email service client
- Added email templates
- Updated alert dispatcher to support multiple channels

Closes #123
```

**Bug fix**:
```
fix(telegram): handle rate limit errors correctly

Fixed issue where rate limit errors crashed the service.
Now properly retries with exponential backoff.

Fixes #124
```

**Documentation**:
```
docs(api): add examples for all endpoints

Added curl and Python examples for:
- Cryptocurrency endpoints
- Alert endpoints
- Price endpoints
```

**Breaking change**:
```
feat(api): redesign alert creation endpoint

BREAKING CHANGE: The alert creation endpoint now requires
a `notification_config` object instead of direct `telegram_chat_id`.

Migration guide added to docs/MIGRATION.md

Closes #125
```

---

## Pull Request Process

### Before Submitting

1. **Update your branch**:
   ```bash
   git fetch upstream
   git rebase upstream/main
   ```

2. **Run all checks**:
   ```bash
   make lint
   pytest
   pytest --cov=src
   ```

3. **Update documentation**:
   - Update README.md if needed
   - Update CHANGELOG.md
   - Add/update docstrings

4. **Squash commits** if needed:
   ```bash
   git rebase -i HEAD~3  # Squash last 3 commits
   ```

### PR Checklist

- [ ] Tests pass locally
- [ ] Code is linted and formatted
- [ ] Documentation updated
- [ ] CHANGELOG.md updated
- [ ] Commit messages follow conventions
- [ ] PR description is clear and complete
- [ ] Related issues are referenced

### PR Template

```markdown
## Description
Brief description of changes

## Related Issues
Closes #123
Fixes #124

## Changes
- Added email notification support
- Updated alert dispatcher
- Added email templates

## Breaking Changes
None

## Testing
- Added unit tests for email service
- Added integration tests for alert dispatcher
- All tests passing

## Screenshots
(if applicable)

## Checklist
- [x] Tests pass
- [x] Code linted
- [x] Documentation updated
- [x] CHANGELOG updated
```

---

## Review Process

### What We Look For

**Code Quality**:
- Follows coding standards
- Well-structured and readable
- Properly documented
- Includes tests

**Functionality**:
- Solves the problem
- No obvious bugs
- Handles edge cases
- Performance considerations

**Testing**:
- Adequate test coverage
- Tests are meaningful
- Edge cases covered

**Documentation**:
- README updated if needed
- API documentation complete
- Code comments where needed

### Review Timeline

- **Initial review**: Within 48 hours
- **Follow-up reviews**: Within 24 hours
- **Merge**: After approval from 2 maintainers

### Addressing Review Comments

```bash
# Make requested changes
git add .
git commit -m "fix: address review comments"
git push origin feature/amazing-feature
```

**Be responsive**:
- Address all comments
- Explain your reasoning if you disagree
- Ask for clarification if needed
- Be patient and respectful

---

## Community

### Communication Channels

- **GitHub Issues**: Bug reports, feature requests
- **GitHub Discussions**: Questions, ideas, announcements
- **Email**: support@crypto-price-alert.com

### Getting Help

**Stuck?** Here's how to get help:

1. Check the [documentation](docs/)
2. Search [existing issues](https://github.com/yourusername/crypto-price-alert/issues)
3. Ask in [GitHub Discussions](https://github.com/yourusername/crypto-price-alert/discussions)
4. Email support@crypto-price-alert.com

### Recognition

Contributors are recognized in:
- CHANGELOG.md for each release
- README.md contributors section
- GitHub Contributors page

---

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

## Questions?

Have questions about contributing? Feel free to:
- Open a [GitHub Discussion](https://github.com/yourusername/crypto-price-alert/discussions)
- Email us at support@crypto-price-alert.com

Thank you for contributing! 🎉
