# Test Suite

Comprehensive test suite for the Crypto Price Alert system.

## Quick Start

```bash
# Install test dependencies
pip install -r requirements.txt

# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html
```

## Test Categories

### Unit Tests (`tests/unit/`)
Fast tests with mocked external dependencies.

```bash
pytest -m unit
```

**Coverage:**
- Rate limiter logic
- Authentication
- Alert evaluation logic
- Pydantic model validation
- Message formatting

### Integration Tests (`tests/integration/`)
Tests with real external API calls.

```bash
pytest -m integration
```

**Coverage:**
- CoinGecko API integration
- Database CRUD operations
- Service communication

### End-to-End Tests (`tests/e2e/`)
Complete system flow tests.

```bash
pytest -m e2e
```

**Coverage:**
- Complete alert flow (price fetch → evaluation → Telegram send)
- Multi-user scenarios
- Error handling flows

### Load Tests (`tests/load/`)
Performance and stress testing.

```bash
locust -f load/locustfile.py --host=http://localhost:52000
```

## Test Files

### Telegram Service Tests
- `unit/test_telegram_service/test_rate_limiter.py` - Token bucket rate limiting
- `unit/test_telegram_service/test_auth.py` - Bearer token authentication
- `unit/test_telegram_service/test_telegram_client.py` - Telegram Bot API client
- `unit/test_telegram_service/test_models.py` - Pydantic model validation

### Crypto Service Tests
- `unit/test_crypto_service/test_alert_engine.py` - Alert evaluation logic
- `unit/test_crypto_service/test_price_collector.py` - Price fetching and storage
- `unit/test_crypto_service/test_models.py` - Schema validation

### Integration Tests
- `integration/test_coingecko_api.py` - Real CoinGecko API calls
- `integration/test_database.py` - Database operations and constraints

### E2E Tests
- `e2e/test_full_alert_flow.py` - Complete alert system flows

## Test Markers

Use markers to run specific test categories:

```bash
# Fast unit tests only
pytest -m unit

# Integration tests without external dependencies
pytest -m "integration and not requires_telegram"

# All tests except slow ones
pytest -m "not slow"
```

**Available markers:**
- `unit` - Unit tests (fast, mocked)
- `integration` - Integration tests (real APIs)
- `e2e` - End-to-end tests
- `requires_telegram` - Needs Telegram bot token
- `requires_api_key` - Needs CoinGecko API key
- `requires_db` - Needs database connection
- `slow` - Slow running tests

## Fixtures

Common fixtures defined in `conftest.py`:

- `test_db` - In-memory SQLite database
- `sample_cryptocurrency` - Factory for creating test cryptocurrencies
- `sample_user` - Factory for creating test users
- `sample_alert` - Factory for creating test alerts
- `mock_telegram_bot` - Mocked Telegram bot client
- `mock_coingecko_response` - Mocked CoinGecko API response
- `test_env_vars` - Test environment variables

## Environment Variables

Set these for different test scenarios:

```bash
# Required for all tests
export TELEGRAM_BOT_TOKEN="test-token"
export SERVICE_AUTH_TOKEN="test-auth-token-12345"

# For integration tests (optional)
export COINGECKO_API_KEY="your-api-key"

# For E2E tests
export DATABASE_URL="postgresql+asyncpg://user:pass@localhost/testdb"
```

## Coverage

View coverage report:

```bash
# Generate HTML report
pytest --cov=src --cov-report=html

# Open in browser
open htmlcov/index.html
```

**Current Coverage Goals:**
- Overall: > 80%
- Critical paths: > 95%
- API endpoints: > 90%

## CI/CD

Tests run automatically on:
- Push to main/develop branches
- Pull requests
- Manual workflow dispatch

See `.github/workflows/tests.yml` for CI configuration.

## Writing New Tests

1. Choose appropriate test category (unit/integration/e2e)
2. Use existing fixtures from `conftest.py`
3. Add appropriate markers
4. Follow naming convention: `test_<what_is_being_tested>`
5. Include docstring explaining test purpose

Example:

```python
import pytest

@pytest.mark.unit
async def test_price_above_alert_triggers(test_db):
    """Test that PRICE_ABOVE alert triggers when price exceeds threshold."""
    # Arrange
    alert = create_alert(threshold=50000)
    crypto = create_crypto(price=51000)

    # Act
    should_trigger, message = evaluate_alert(alert, crypto)

    # Assert
    assert should_trigger is True
```

## Utilities

Helper functions in `utils/test_helpers.py`:

- `TestDataGenerator` - Generate random test data
- `MockFactory` - Create mock objects
- `AssertionHelpers` - Custom assertion helpers
- `TestScenarios` - Pre-built test scenarios

## Load Testing

Run load tests with Locust:

```bash
# Interactive mode
locust -f load/locustfile.py --host=http://localhost:52000

# Headless mode
locust -f load/locustfile.py \
    --host=http://localhost:52000 \
    --users 100 \
    --spawn-rate 10 \
    --run-time 5m \
    --headless
```

## Documentation

See `docs/testing/TESTING_GUIDE.md` for comprehensive testing documentation.

## Troubleshooting

**Tests failing with import errors?**
```bash
export PYTHONPATH="${PYTHONPATH}:/home/user/crypto-price-alert/src"
```

**Database errors?**
```bash
export DATABASE_URL="sqlite+aiosqlite:///:memory:"
```

**Rate limiting from APIs?**
```bash
pytest -m "not requires_api_key"
```

## Contact

For testing questions or issues, please refer to the testing guide or contact the development team.
