"""
Test utilities and helper functions.

Provides common testing utilities, data generators, and assertion helpers.
"""

import random
import string
from datetime import datetime, timedelta
from decimal import Decimal
from typing import List, Optional
from faker import Faker

fake = Faker()


class TestDataGenerator:
    """Generator for test data."""

    @staticmethod
    def random_string(length: int = 10) -> str:
        """Generate random string."""
        return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

    @staticmethod
    def random_user_id() -> str:
        """Generate random user ID."""
        return f"user_{TestDataGenerator.random_string(8)}"

    @staticmethod
    def random_alert_id() -> str:
        """Generate random alert ID."""
        return f"alert_{TestDataGenerator.random_string(8)}"

    @staticmethod
    def random_chat_id() -> str:
        """Generate random Telegram chat ID."""
        return str(random.randint(100000000, 999999999))

    @staticmethod
    def random_price(min_price: float = 100, max_price: float = 100000) -> Decimal:
        """Generate random cryptocurrency price."""
        price = random.uniform(min_price, max_price)
        return Decimal(f"{price:.2f}")

    @staticmethod
    def random_crypto_symbol() -> str:
        """Generate random cryptocurrency symbol."""
        return ''.join(random.choices(string.ascii_uppercase, k=3))

    @staticmethod
    def generate_price_series(
        base_price: Decimal,
        count: int = 10,
        volatility: float = 0.05
    ) -> List[Decimal]:
        """
        Generate a series of prices with simulated volatility.

        Args:
            base_price: Starting price
            count: Number of prices to generate
            volatility: Price change percentage (0.05 = 5%)

        Returns:
            List of prices
        """
        prices = [base_price]
        current_price = base_price

        for _ in range(count - 1):
            change = float(current_price) * volatility * random.uniform(-1, 1)
            current_price = Decimal(str(float(current_price) + change))
            prices.append(current_price)

        return prices

    @staticmethod
    def generate_timestamps(
        start: datetime,
        count: int = 10,
        interval_seconds: int = 60
    ) -> List[datetime]:
        """Generate series of timestamps."""
        timestamps = []
        current = start

        for _ in range(count):
            timestamps.append(current)
            current += timedelta(seconds=interval_seconds)

        return timestamps


class MockFactory:
    """Factory for creating mock objects."""

    @staticmethod
    def create_mock_cryptocurrency(
        crypto_id: str = "bitcoin",
        symbol: str = "BTC",
        name: str = "Bitcoin",
        current_price: Optional[Decimal] = None,
        is_active: bool = True
    ) -> dict:
        """Create mock cryptocurrency data."""
        return {
            "crypto_id": crypto_id,
            "symbol": symbol,
            "name": name,
            "current_price": current_price or Decimal("50000.00"),
            "market_cap": 1000000000,
            "volume_24h": 50000000,
            "price_change_24h": Decimal("500.00"),
            "is_active": is_active,
            "last_updated": datetime.utcnow(),
            "created_at": datetime.utcnow(),
        }

    @staticmethod
    def create_mock_alert(
        alert_id: Optional[str] = None,
        user_id: Optional[str] = None,
        crypto_id: str = "bitcoin",
        alert_type: str = "PRICE_ABOVE",
        threshold: Optional[Decimal] = None,
        enabled: bool = True
    ) -> dict:
        """Create mock alert data."""
        return {
            "alert_id": alert_id or TestDataGenerator.random_alert_id(),
            "user_id": user_id or TestDataGenerator.random_user_id(),
            "crypto_id": crypto_id,
            "alert_type": alert_type,
            "threshold": threshold or Decimal("60000.00"),
            "telegram_chat_id": TestDataGenerator.random_chat_id(),
            "enabled": enabled,
            "trigger_count": 0,
            "last_triggered_at": None,
            "last_triggered_price": None,
            "metadata": {},
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }

    @staticmethod
    def create_mock_user(
        user_id: Optional[str] = None,
        telegram_chat_id: Optional[str] = None
    ) -> dict:
        """Create mock user data."""
        return {
            "user_id": user_id or TestDataGenerator.random_user_id(),
            "telegram_chat_id": telegram_chat_id or TestDataGenerator.random_chat_id(),
            "telegram_username": fake.user_name(),
            "alert_count": 0,
            "watchlist_size": 0,
            "created_at": datetime.utcnow(),
        }

    @staticmethod
    def create_mock_coingecko_response(
        cryptos: List[str] = None
    ) -> dict:
        """Create mock CoinGecko API response."""
        if cryptos is None:
            cryptos = ["bitcoin", "ethereum"]

        response = {}
        for crypto in cryptos:
            response[crypto] = {
                "usd": random.uniform(100, 100000),
                "usd_market_cap": random.randint(1000000, 1000000000),
                "usd_24h_vol": random.randint(1000000, 100000000),
                "usd_24h_change": random.uniform(-10, 10),
                "last_updated_at": int(datetime.utcnow().timestamp()),
            }

        return response


class AssertionHelpers:
    """Helper functions for test assertions."""

    @staticmethod
    def assert_price_within_range(
        actual: Decimal,
        expected: Decimal,
        tolerance_percent: float = 0.01
    ):
        """Assert that price is within tolerance range."""
        tolerance = abs(float(expected) * tolerance_percent)
        diff = abs(float(actual) - float(expected))

        assert diff <= tolerance, (
            f"Price {actual} not within {tolerance_percent*100}% of {expected}. "
            f"Difference: {diff}"
        )

    @staticmethod
    def assert_timestamp_recent(
        timestamp: datetime,
        max_age_seconds: int = 60
    ):
        """Assert that timestamp is recent."""
        age = (datetime.utcnow() - timestamp).total_seconds()

        assert age <= max_age_seconds, (
            f"Timestamp {timestamp} is too old. Age: {age}s, Max: {max_age_seconds}s"
        )

    @staticmethod
    def assert_dict_contains(actual: dict, expected: dict):
        """Assert that actual dict contains all key-value pairs from expected."""
        for key, value in expected.items():
            assert key in actual, f"Key '{key}' not found in actual dict"
            assert actual[key] == value, (
                f"Value mismatch for key '{key}': {actual[key]} != {value}"
            )


class TestScenarios:
    """Pre-built test scenarios."""

    @staticmethod
    def price_spike_scenario() -> dict:
        """Create scenario for sudden price spike."""
        base_price = Decimal("50000.00")
        spike_price = Decimal("55000.00")  # 10% spike

        return {
            "initial_price": base_price,
            "spike_price": spike_price,
            "change_percent": 10.0,
            "alert_threshold": Decimal("52000.00"),
            "should_trigger": True,
        }

    @staticmethod
    def price_drop_scenario() -> dict:
        """Create scenario for sudden price drop."""
        base_price = Decimal("50000.00")
        drop_price = Decimal("45000.00")  # 10% drop

        return {
            "initial_price": base_price,
            "drop_price": drop_price,
            "change_percent": -10.0,
            "alert_threshold": Decimal("48000.00"),
            "should_trigger": True,
        }

    @staticmethod
    def gradual_increase_scenario(steps: int = 5) -> dict:
        """Create scenario for gradual price increase."""
        base_price = Decimal("50000.00")
        increment = Decimal("500.00")

        prices = [base_price + (increment * i) for i in range(steps)]

        return {
            "prices": prices,
            "steps": steps,
            "total_change": float(increment * (steps - 1)),
        }


def wait_for_condition(
    condition_func,
    timeout_seconds: int = 10,
    check_interval: float = 0.1
):
    """
    Wait for a condition to become true.

    Args:
        condition_func: Function that returns True when condition is met
        timeout_seconds: Maximum time to wait
        check_interval: Time between checks

    Raises:
        TimeoutError: If condition not met within timeout
    """
    import time

    start_time = time.time()

    while time.time() - start_time < timeout_seconds:
        if condition_func():
            return True
        time.sleep(check_interval)

    raise TimeoutError(
        f"Condition not met within {timeout_seconds} seconds"
    )


def cleanup_test_data(db_session, model_class):
    """
    Helper to cleanup test data from database.

    Args:
        db_session: Database session
        model_class: SQLAlchemy model class to clean
    """
    # This would be used in test teardown
    # Implementation depends on async/sync session
    pass
