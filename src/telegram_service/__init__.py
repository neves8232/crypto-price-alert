"""
Telegram Alert Service

A production-ready microservice for sending Telegram messages with:
- Rate limiting (30 msg/sec)
- Message queuing
- Retry logic with exponential backoff
- Prometheus metrics
- Health checks
- Bearer token authentication
"""

__version__ = "1.0.0"
__service_name__ = "telegram-alert-service"
