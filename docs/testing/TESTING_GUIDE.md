# Testing Guide

Complete guide for running and writing tests for the Crypto Price Alert system.

## Table of Contents

- [Quick Start](#quick-start)
- [Test Structure](#test-structure)
- [Running Tests](#running-tests)
- [Test Markers](#test-markers)
- [Writing Tests](#writing-tests)
- [CI/CD Integration](#cicd-integration)
- [Load Testing](#load-testing)
- [Troubleshooting](#troubleshooting)

## Quick Start

### Install Test Dependencies

```bash
cd /home/user/crypto-price-alert
pip install -r tests/requirements.txt
```

### Run All Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html
```

### Run Specific Test Categories

```bash
# Unit tests only (fast)
pytest -m unit

# Integration tests only
pytest -m integration

# E2E tests only
pytest -m e2e
```

## Test Structure

```
tests/
├── unit/                           # Unit tests (mocked dependencies)
│   ├── test_telegram_service/
│   │   ├── test_auth.py           # Authentication tests
│   │   ├── test_rate_limiter.py   # Rate limiter logic tests
│   │   ├── test_telegram_client.py # Telegram client tests
│   │   └── test_models.py         # Pydantic model tests
│   └── test_crypto_service/
│       ├── test_alert_engine.py   # Alert evaluation tests
│       ├── test_price_collector.py # Price collection tests
│       └── test_models.py         # Schema validation tests
├── integration/                    # Integration tests (real APIs)
│   ├── test_coingecko_api.py     # CoinGecko API integration
│   └── test_database.py          # Database CRUD tests
├── e2e/                           # End-to-end tests
│   └── test_full_alert_flow.py   # Complete alert flow tests
├── load/                          # Load testing
│   └── locustfile.py             # Locust load test scenarios
├── utils/                         # Test utilities
│   └── test_helpers.py           # Helper functions
├── conftest.py                    # Pytest fixtures
└── pytest.ini                     # Pytest configuration
```

## Running Tests

### Basic Commands

```bash
# Run all tests with verbose output
pytest -v

# Run specific test file
pytest tests/unit/test_telegram_service/test_rate_limiter.py

# Run specific test function
pytest tests/unit/test_alert_engine.py::TestAlertEngine::test_price_above_alert_triggers

# Run tests matching pattern
pytest -k "alert"

# Stop on first failure
pytest -x

# Run last failed tests
pytest --lf
```

### With Coverage

```bash
# Generate coverage report
pytest --cov=src --cov-report=html --cov-report=term

# View HTML coverage report
open htmlcov/index.html
```

### Parallel Execution

```bash
# Install pytest-xdist
pip install pytest-xdist

# Run tests in parallel (4 workers)
pytest -n 4
```

## Test Markers

Tests are organized using pytest markers:

### Available Markers

- `unit` - Fast unit tests with mocked dependencies
- `integration` - Integration tests with real API calls
- `e2e` - End-to-end tests (slowest)
- `requires_telegram` - Requires Telegram bot token
- `requires_api_key` - Requires CoinGecko API key
- `requires_db` - Requires database connection
- `slow` - Slow running tests

### Using Markers

```bash
# Run only unit tests
pytest -m unit

# Run integration tests excluding those needing Telegram
pytest -m "integration and not requires_telegram"

# Run all tests except slow ones
pytest -m "not slow"

# Combine markers
pytest -m "unit or integration"
```

## Writing Tests

### Unit Test Example

```python
import pytest
from crypto_service.services.alert_engine import AlertEngine

@pytest.mark.unit
async def test_price_above_alert_triggers(test_db):
    """Test that PRICE_ABOVE alert triggers when price exceeds threshold."""
    engine = AlertEngine(test_db)

    alert = Alert(
        alert_type="PRICE_ABOVE",
        threshold=Decimal("50000.00"),
        # ... other fields
    )

    crypto = Cryptocurrency(
        current_price=Decimal("51000.00"),
        # ... other fields
    )

    should_trigger, message = await engine._evaluate_condition(alert, crypto)

    assert should_trigger is True
    assert "above" in message.lower()
```

### Integration Test Example

```python
import pytest

@pytest.mark.integration
async def test_fetch_real_bitcoin_price():
    """Test fetching real Bitcoin price from CoinGecko."""
    client = CoinGeckoClient()

    prices = await client.fetch_prices(['bitcoin'])

    assert 'bitcoin' in prices
    assert prices['bitcoin']['usd'] > 0
```

### Using Fixtures

```python
@pytest.mark.unit
async def test_with_fixtures(test_db, sample_cryptocurrency, sample_alert):
    """Test using pytest fixtures."""
    # Fixtures are automatically injected
    crypto = await sample_cryptocurrency(symbol="BTC")
    alert = await sample_alert(crypto_id=crypto.crypto_id)

    # Test logic here
    assert alert.crypto_id == crypto.crypto_id
```

### Test Organization Best Practices

1. **One concept per test** - Each test should verify one specific behavior
2. **Clear test names** - Use descriptive names that explain what is being tested
3. **Arrange-Act-Assert** - Structure tests in three clear sections
4. **Use fixtures** - Avoid code duplication with pytest fixtures
5. **Mock external dependencies** - Use mocks in unit tests to isolate code
6. **Test edge cases** - Include tests for boundary conditions and error cases

## CI/CD Integration

### GitHub Actions

Tests run automatically on:
- Push to `main` or `develop` branches
- Pull requests to `main` or `develop`
- Manual workflow dispatch

### Workflow Jobs

1. **Unit Tests** - Run on Python 3.11 and 3.12
2. **Integration Tests** - Run after unit tests pass
3. **E2E Tests** - Run with PostgreSQL service
4. **Linting** - Code quality checks
5. **Security** - Security vulnerability scanning

### Running Locally Like CI

```bash
# Simulate CI environment
export TELEGRAM_BOT_TOKEN="123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11"
export SERVICE_AUTH_TOKEN="test-auth-token-12345"
export DATABASE_URL="sqlite+aiosqlite:///:memory:"

# Run tests
pytest -m unit -v
pytest -m integration -v
pytest -m e2e -v
```

## Load Testing

### Using Locust

```bash
# Install locust
pip install locust

# Run load test
cd /home/user/crypto-price-alert
locust -f tests/load/locustfile.py --host=http://localhost:52000

# Open browser to http://localhost:8089
# Configure users and spawn rate
```

### Load Test Scenarios

**Light Load** (Normal traffic)
```bash
locust -f tests/load/locustfile.py \
    --host=http://localhost:52000 \
    --users 50 \
    --spawn-rate 5 \
    --run-time 5m \
    --headless
```

**Stress Test** (Peak traffic)
```bash
locust -f tests/load/locustfile.py \
    --host=http://localhost:52000 \
    --users 200 \
    --spawn-rate 20 \
    --run-time 10m \
    --headless
```

**Spike Test** (Sudden traffic spike)
```bash
locust -f tests/load/locustfile.py \
    --host=http://localhost:52000 \
    --users 500 \
    --spawn-rate 100 \
    --run-time 2m \
    --headless
```

## Environment Variables

Required for different test types:

### Unit Tests
```bash
TELEGRAM_BOT_TOKEN="test-token"
SERVICE_AUTH_TOKEN="test-auth-token"
```

### Integration Tests
```bash
COINGECKO_API_KEY="your-api-key"  # Optional, for higher rate limits
```

### E2E Tests
```bash
DATABASE_URL="postgresql+asyncpg://user:pass@localhost:5432/testdb"
TELEGRAM_SERVICE_URL="http://localhost:51000"
```

## Coverage Goals

- **Overall Coverage**: > 80%
- **Critical Paths**: > 95% (alert_engine, rate_limiter, auth)
- **API Endpoints**: > 90%
- **Models/Schemas**: > 85%

### Viewing Coverage

```bash
# Generate HTML coverage report
pytest --cov=src --cov-report=html

# Open in browser
open htmlcov/index.html

# Terminal report with missing lines
pytest --cov=src --cov-report=term-missing
```

## Troubleshooting

### Common Issues

**Issue: "No module named 'crypto_service'"**
```bash
# Add src to PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:/home/user/crypto-price-alert/src"
```

**Issue: "Database connection errors"**
```bash
# Use in-memory database for tests
export DATABASE_URL="sqlite+aiosqlite:///:memory:"
```

**Issue: "Telegram API rate limiting"**
```bash
# Skip Telegram tests
pytest -m "not requires_telegram"
```

**Issue: "CoinGecko API rate limiting"**
```bash
# Skip API key required tests
pytest -m "not requires_api_key"

# Or add delays between tests
pytest --dist loadgroup
```

### Debug Mode

```bash
# Run with Python debugger
pytest --pdb

# Stop on first failure and debug
pytest -x --pdb

# Show print statements
pytest -s

# Very verbose output
pytest -vv
```

### Performance Issues

```bash
# Show slowest tests
pytest --durations=10

# Profile tests
pip install pytest-profiling
pytest --profile
```

## Best Practices

1. **Run unit tests frequently** during development
2. **Run integration tests** before committing
3. **Run full test suite** before creating pull requests
4. **Check coverage** for new code (should be > 80%)
5. **Update tests** when changing functionality
6. **Write tests first** (TDD) for bug fixes
7. **Keep tests fast** - mock external dependencies in unit tests
8. **Use descriptive assertions** - make failures clear
9. **Clean up test data** - use fixtures for setup/teardown
10. **Document complex tests** - add docstrings explaining what is tested

## Additional Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [Coverage.py Documentation](https://coverage.readthedocs.io/)
- [Locust Documentation](https://docs.locust.io/)
- [Testing Best Practices](https://docs.python-guide.org/writing/tests/)

## Getting Help

- Check test output for specific error messages
- Review this guide for common solutions
- Check CI logs for failures
- Ask team members for assistance
