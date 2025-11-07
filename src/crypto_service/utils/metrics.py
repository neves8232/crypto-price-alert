"""
Prometheus metrics for monitoring service health and performance.
"""

from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from fastapi import Response

# API Request Metrics
api_requests_total = Counter(
    "crypto_api_requests_total",
    "Total API requests to crypto providers",
    ["provider", "status"],
)

api_latency_seconds = Histogram(
    "crypto_api_latency_seconds",
    "API request latency in seconds",
    ["provider"],
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0],
)

# Price Monitoring Metrics
price_updates_total = Counter(
    "price_updates_total",
    "Total price updates received",
    ["crypto"],
)

alerts_triggered_total = Counter(
    "alerts_triggered_total",
    "Total alerts triggered",
    ["crypto", "type"],
)

alerts_evaluated_total = Counter(
    "alerts_evaluated_total",
    "Total alert evaluations performed",
)

alert_evaluation_duration_seconds = Histogram(
    "alert_evaluation_duration_seconds",
    "Alert evaluation duration in seconds",
    buckets=[0.001, 0.005, 0.01, 0.05, 0.1, 0.5],
)

# Alert Dispatch Metrics
alert_dispatch_requests_total = Counter(
    "alert_dispatch_requests_total",
    "Total alert dispatch requests",
    ["status"],
)

alert_dispatch_latency_seconds = Histogram(
    "alert_dispatch_latency_seconds",
    "Alert dispatch latency in seconds",
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0],
)

# Database Metrics
database_queries_total = Counter(
    "database_queries_total",
    "Total database queries",
    ["operation"],
)

database_connection_pool_size = Gauge(
    "database_connection_pool_size",
    "Database connection pool size",
)

database_connection_pool_active = Gauge(
    "database_connection_pool_active",
    "Active database connections",
)

# System Metrics
active_alerts_gauge = Gauge(
    "active_alerts_gauge",
    "Number of active alerts",
)

active_crypto_monitors_gauge = Gauge(
    "active_crypto_monitors_gauge",
    "Number of active cryptocurrency monitors",
)

watchlist_total_size_gauge = Gauge(
    "watchlist_total_size_gauge",
    "Total watchlist size across all users",
)


def metrics_endpoint() -> Response:
    """
    Prometheus metrics endpoint handler.

    Returns:
        Response with Prometheus metrics in text format
    """
    metrics_data = generate_latest()
    return Response(
        content=metrics_data,
        media_type=CONTENT_TYPE_LATEST,
    )
