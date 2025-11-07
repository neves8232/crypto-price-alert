"""
Load testing script using Locust.

Tests system performance under load.

Usage:
    locust -f tests/load/locustfile.py --host=http://localhost:52000
"""

import random
from decimal import Decimal
from locust import HttpUser, task, between, events
import json


class CryptoServiceUser(HttpUser):
    """Simulated user for crypto service load testing."""

    wait_time = between(1, 3)  # Wait 1-3 seconds between tasks

    def on_start(self):
        """Setup: Called when user starts."""
        self.auth_token = "test-auth-token-12345"  # Should match your test env
        self.headers = {
            "Authorization": f"Bearer {self.auth_token}",
            "Content-Type": "application/json",
        }

        # Create test cryptocurrencies
        self.cryptos = ["bitcoin", "ethereum", "solana"]
        self.user_id = f"load_test_user_{random.randint(1000, 9999)}"

    @task(3)
    def get_cryptocurrencies(self):
        """Get list of cryptocurrencies (most common operation)."""
        self.client.get("/api/cryptocurrencies", headers=self.headers)

    @task(2)
    def get_current_prices(self):
        """Get current prices."""
        self.client.get("/api/prices/current", headers=self.headers)

    @task(1)
    def create_alert(self):
        """Create a new alert (less common operation)."""
        crypto_id = random.choice(self.cryptos)
        alert_data = {
            "user_id": self.user_id,
            "crypto_id": crypto_id,
            "alert_type": random.choice([
                "PRICE_ABOVE",
                "PRICE_BELOW",
                "PRICE_CHANGE_PERCENT"
            ]),
            "threshold": float(Decimal(str(random.uniform(1000, 100000)))),
            "telegram_chat_id": f"{random.randint(100000000, 999999999)}",
            "enabled": True,
        }

        self.client.post(
            "/api/alerts",
            json=alert_data,
            headers=self.headers
        )

    @task(2)
    def get_alerts(self):
        """Get user's alerts."""
        self.client.get(
            f"/api/alerts?user_id={self.user_id}",
            headers=self.headers
        )

    @task(1)
    def get_price_history(self):
        """Get price history for a cryptocurrency."""
        crypto_id = random.choice(self.cryptos)
        self.client.get(
            f"/api/prices/history/{crypto_id}?interval=1h&limit=24",
            headers=self.headers
        )

    @task(4)
    def health_check(self):
        """Check service health (very common)."""
        self.client.get("/health")


class TelegramServiceUser(HttpUser):
    """Simulated user for Telegram service load testing."""

    wait_time = between(0.5, 2)

    def on_start(self):
        """Setup: Called when user starts."""
        self.auth_token = "test-auth-token-12345"
        self.headers = {
            "Authorization": f"Bearer {self.auth_token}",
            "Content-Type": "application/json",
        }

    @task(10)
    def send_alert(self):
        """Send alert message (primary operation)."""
        alert_data = {
            "chat_id": f"{random.randint(100000000, 999999999)}",
            "message": f"Test alert message {random.randint(1, 1000)}",
            "parse_mode": random.choice(["HTML", "Markdown", None]),
            "priority": random.choice(["low", "normal", "high"]),
            "metadata": {
                "test": True,
                "load_test_id": random.randint(1, 1000),
            }
        }

        self.client.post(
            "/api/v1/alerts/send",
            json=alert_data,
            headers=self.headers
        )

    @task(5)
    def health_check(self):
        """Check service health."""
        self.client.get("/health")

    @task(2)
    def get_metrics(self):
        """Get service metrics."""
        self.client.get("/metrics")


class BurstTrafficUser(HttpUser):
    """Simulated burst traffic scenario."""

    wait_time = between(0.1, 0.5)  # Very short wait times

    def on_start(self):
        self.auth_token = "test-auth-token-12345"
        self.headers = {
            "Authorization": f"Bearer {self.auth_token}",
            "Content-Type": "application/json",
        }

    @task
    def rapid_price_checks(self):
        """Rapid price check requests."""
        self.client.get("/api/prices/current", headers=self.headers)


# Custom events for additional metrics
@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Called when load test starts."""
    print("🚀 Load test starting...")


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Called when load test stops."""
    print("✅ Load test completed!")

    # Print summary statistics
    stats = environment.stats
    print(f"\n📊 Summary Statistics:")
    print(f"Total requests: {stats.total.num_requests}")
    print(f"Failed requests: {stats.total.num_failures}")
    print(f"Average response time: {stats.total.avg_response_time:.2f}ms")
    print(f"Max response time: {stats.total.max_response_time:.2f}ms")
    print(f"Requests/sec: {stats.total.total_rps:.2f}")


# Load test scenarios
class LightLoadUser(HttpUser):
    """Light load scenario - normal traffic."""

    wait_time = between(2, 5)
    weight = 3  # 3x more common than heavy load

    @task
    def normal_operations(self):
        """Normal user operations."""
        user = CryptoServiceUser(self.environment)
        user.get_cryptocurrencies()


class HeavyLoadUser(HttpUser):
    """Heavy load scenario - peak traffic."""

    wait_time = between(0.5, 1)
    weight = 1  # Less common

    @task
    def peak_operations(self):
        """Peak traffic operations."""
        user = BurstTrafficUser(self.environment)
        user.rapid_price_checks()


# Stress test configuration
"""
Run stress test with:

# Gradual ramp-up
locust -f tests/load/locustfile.py \
    --host=http://localhost:52000 \
    --users 100 \
    --spawn-rate 10 \
    --run-time 5m

# Spike test
locust -f tests/load/locustfile.py \
    --host=http://localhost:52000 \
    --users 500 \
    --spawn-rate 100 \
    --run-time 2m

# Endurance test
locust -f tests/load/locustfile.py \
    --host=http://localhost:52000 \
    --users 50 \
    --spawn-rate 5 \
    --run-time 30m
"""
