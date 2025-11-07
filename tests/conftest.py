"""
Pytest configuration and shared fixtures.
"""

import asyncio
import os
from datetime import datetime
from decimal import Decimal
from typing import AsyncGenerator, Generator
from unittest.mock import AsyncMock, MagicMock

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool

# Add src to path for imports
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from crypto_service.database import Base
from crypto_service.models import Cryptocurrency, Alert, User, PriceHistory, AlertLog


# ============================================================================
# Event Loop Configuration
# ============================================================================

@pytest.fixture(scope="session")
def event_loop_policy():
    """Set event loop policy for all async tests."""
    return asyncio.get_event_loop_policy()


# ============================================================================
# Database Fixtures
# ============================================================================

@pytest.fixture
async def test_db_engine():
    """Create a test database engine using in-memory SQLite."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False,
    )

    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    # Cleanup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.fixture
async def test_db(test_db_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create a test database session."""
    async_session = async_sessionmaker(
        test_db_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with async_session() as session:
        yield session
        await session.rollback()


# ============================================================================
# Model Factory Fixtures
# ============================================================================

@pytest.fixture
def sample_cryptocurrency(test_db):
    """Create a sample cryptocurrency for testing."""
    async def _create(
        crypto_id: str = "bitcoin",
        symbol: str = "BTC",
        name: str = "Bitcoin",
        current_price: Decimal = Decimal("50000.00"),
        is_active: bool = True,
    ) -> Cryptocurrency:
        crypto = Cryptocurrency(
            crypto_id=crypto_id,
            symbol=symbol,
            name=name,
            current_price=current_price,
            market_cap=1000000000,
            volume_24h=50000000,
            price_change_24h=Decimal("500.00"),
            is_active=is_active,
            last_updated=datetime.utcnow(),
        )
        test_db.add(crypto)
        await test_db.commit()
        await test_db.refresh(crypto)
        return crypto

    return _create


@pytest.fixture
def sample_user(test_db):
    """Create a sample user for testing."""
    async def _create(
        user_id: str = "user123",
        telegram_chat_id: str = "123456789",
        telegram_username: str = "testuser",
    ) -> User:
        user = User(
            user_id=user_id,
            telegram_chat_id=telegram_chat_id,
            telegram_username=telegram_username,
            alert_count=0,
            watchlist_size=0,
        )
        test_db.add(user)
        await test_db.commit()
        await test_db.refresh(user)
        return user

    return _create


@pytest.fixture
def sample_alert(test_db):
    """Create a sample alert for testing."""
    async def _create(
        alert_id: str = "alert123",
        user_id: str = "user123",
        crypto_id: str = "bitcoin",
        alert_type: str = "PRICE_ABOVE",
        threshold: Decimal = Decimal("60000.00"),
        telegram_chat_id: str = "123456789",
        enabled: bool = True,
    ) -> Alert:
        alert = Alert(
            alert_id=alert_id,
            user_id=user_id,
            crypto_id=crypto_id,
            alert_type=alert_type,
            threshold=threshold,
            telegram_chat_id=telegram_chat_id,
            enabled=enabled,
            trigger_count=0,
        )
        test_db.add(alert)
        await test_db.commit()
        await test_db.refresh(alert)
        return alert

    return _create


# ============================================================================
# Mock Service Fixtures
# ============================================================================

@pytest.fixture
def mock_telegram_bot():
    """Mock Telegram Bot API."""
    mock_bot = AsyncMock()

    # Mock get_me response
    mock_bot_info = MagicMock()
    mock_bot_info.id = 123456789
    mock_bot_info.username = "test_bot"
    mock_bot_info.first_name = "Test Bot"
    mock_bot_info.can_join_groups = True
    mock_bot_info.can_read_all_group_messages = True
    mock_bot.get_me.return_value = mock_bot_info

    # Mock send_message response
    mock_message = MagicMock()
    mock_message.message_id = 12345
    mock_message.date = datetime.utcnow()
    mock_message.chat.id = 123456789
    mock_bot.send_message.return_value = mock_message

    return mock_bot


@pytest.fixture
def mock_coingecko_response():
    """Mock CoinGecko API response."""
    return {
        "bitcoin": {
            "usd": 50000.00,
            "usd_market_cap": 1000000000,
            "usd_24h_vol": 50000000,
            "usd_24h_change": 2.5,
            "last_updated_at": 1234567890,
        },
        "ethereum": {
            "usd": 3000.00,
            "usd_market_cap": 350000000,
            "usd_24h_vol": 20000000,
            "usd_24h_change": -1.2,
            "last_updated_at": 1234567890,
        },
    }


@pytest.fixture
def mock_httpx_client(mock_coingecko_response):
    """Mock HTTPX async client for API calls."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = mock_coingecko_response
    mock_response.headers = {}

    mock_client = AsyncMock(spec=AsyncClient)
    mock_client.get.return_value = mock_response
    mock_client.post.return_value = mock_response
    mock_client.__aenter__.return_value = mock_client
    mock_client.__aexit__.return_value = None

    return mock_client


# ============================================================================
# Environment Configuration Fixtures
# ============================================================================

@pytest.fixture
def test_env_vars(monkeypatch):
    """Set test environment variables."""
    test_vars = {
        # Telegram Service
        "TELEGRAM_BOT_TOKEN": "123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11",
        "SERVICE_AUTH_TOKEN": "test-auth-token-12345",
        "TELEGRAM_RETRY_ATTEMPTS": "3",
        "TELEGRAM_RETRY_DELAY_SECONDS": "1",
        "TELEGRAM_API_TIMEOUT_SECONDS": "10",
        "RATE_LIMIT_MESSAGES_PER_SECOND": "25.0",
        "RATE_LIMIT_BURST_SIZE": "30",

        # Crypto Service
        "DATABASE_URL": "sqlite+aiosqlite:///:memory:",
        "COINGECKO_API_KEY": "test-coingecko-key",
        "TELEGRAM_SERVICE_URL": "http://localhost:51000",
        "PRICE_UPDATE_INTERVAL_SECONDS": "60",
        "ALERT_DEBOUNCE_SECONDS": "30",

        # General
        "LOG_LEVEL": "INFO",
        "SERVICE_NAME": "test-service",
        "SERVICE_VERSION": "test-1.0.0",
    }

    for key, value in test_vars.items():
        monkeypatch.setenv(key, value)

    return test_vars


# ============================================================================
# HTTP Client Fixtures
# ============================================================================

@pytest.fixture
async def telegram_service_client():
    """Create async HTTP client for Telegram service."""
    async with AsyncClient(base_url="http://localhost:51000") as client:
        yield client


@pytest.fixture
async def crypto_service_client():
    """Create async HTTP client for Crypto service."""
    async with AsyncClient(base_url="http://localhost:52000") as client:
        yield client


# ============================================================================
# Time Control Fixtures
# ============================================================================

@pytest.fixture
def freeze_time():
    """Fixture to freeze time for testing."""
    from datetime import datetime

    class FrozenTime:
        def __init__(self):
            self.frozen = datetime.utcnow()

        def set(self, dt: datetime):
            self.frozen = dt

        def get(self):
            return self.frozen

    return FrozenTime()


# ============================================================================
# Test Data Generators
# ============================================================================

@pytest.fixture
def generate_price_history():
    """Generate price history data for testing."""
    def _generate(crypto_id: str, count: int = 10, base_price: Decimal = Decimal("50000.00")):
        from datetime import timedelta

        history = []
        now = datetime.utcnow()

        for i in range(count):
            history.append(
                PriceHistory(
                    crypto_id=crypto_id,
                    price=base_price + Decimal(i * 100),
                    volume_24h=50000000 + (i * 1000000),
                    timestamp=now - timedelta(hours=count - i),
                    source="test",
                )
            )

        return history

    return _generate


# ============================================================================
# Cleanup Fixtures
# ============================================================================

@pytest.fixture(autouse=True)
async def cleanup_after_test():
    """Cleanup after each test."""
    yield
    # Any cleanup code here
    await asyncio.sleep(0)  # Allow pending tasks to complete
