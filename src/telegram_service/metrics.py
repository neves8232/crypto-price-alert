"""
Prometheus Metrics

Exposes metrics for monitoring:
- Message delivery counts
- Delivery latency
- Queue size
- Rate limit hits
"""

from prometheus_client import Counter, Gauge, Histogram

# Message delivery metrics
messages_sent_total = Counter(
    "telegram_messages_sent_total",
    "Total number of messages sent via Telegram",
    ["status"]  # success, failed
)

message_delivery_seconds = Histogram(
    "telegram_message_delivery_seconds",
    "Time taken to deliver a message",
    buckets=[0.1, 0.25, 0.5, 1.0, 2.0, 5.0, 10.0]
)

# Rate limiting metrics
rate_limit_hits_total = Counter(
    "telegram_rate_limit_hits_total",
    "Total number of rate limit hits"
)

rate_limit_tokens_available = Gauge(
    "telegram_rate_limit_tokens_available",
    "Current number of available rate limit tokens"
)

# Queue metrics
queue_size_gauge = Gauge(
    "telegram_queue_size",
    "Current number of messages in queue"
)

queue_max_size_gauge = Gauge(
    "telegram_queue_max_size",
    "Maximum queue capacity"
)

# Retry metrics
retry_attempts_total = Counter(
    "telegram_retry_attempts_total",
    "Total number of retry attempts",
    ["attempt"]  # 1, 2, 3, etc.
)

# Error metrics
errors_total = Counter(
    "telegram_errors_total",
    "Total number of errors by type",
    ["error_type"]  # bad_request, network_error, timeout, etc.
)

# Request metrics
requests_total = Counter(
    "telegram_api_requests_total",
    "Total API requests received",
    ["endpoint", "method", "status_code"]
)

request_duration_seconds = Histogram(
    "telegram_api_request_duration_seconds",
    "API request duration",
    ["endpoint", "method"],
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0]
)
