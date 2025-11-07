"""
Telegram Alert Service - Main Application

FastAPI application for sending Telegram messages with:
- Bearer token authentication
- Rate limiting
- Message queuing
- Retry logic
- Health checks
- Prometheus metrics
"""

import time
import uuid
from collections import deque
from contextlib import asynccontextmanager
from typing import Deque

import structlog
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.responses import JSONResponse, PlainTextResponse
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from telegram.error import BadRequest, TelegramError

# Service metadata
__version__ = "1.0.0"
__service_name__ = "telegram-alert-service"

from auth import AuthToken
from config import settings
from health import perform_health_check
from metrics import (
    errors_total,
    message_delivery_seconds,
    messages_sent_total,
    queue_max_size_gauge,
    queue_size_gauge,
    rate_limit_hits_total,
    rate_limit_tokens_available,
    request_duration_seconds,
    requests_total,
    retry_attempts_total,
)
from models import AlertRequest, AlertResponse, ErrorResponse, HealthCheck
from rate_limiter import RateLimiter
from telegram_client import TelegramClient

# Configure structured logging
structlog.configure(
    processors=[
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer(),
    ],
    wrapper_class=structlog.make_filtering_bound_logger(
        getattr(structlog.stdlib, settings.log_level)
    ),
)

logger = structlog.get_logger(__name__)


# Global instances (initialized in lifespan)
telegram_client: TelegramClient
rate_limiter: RateLimiter
message_queue: Deque[dict]


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.

    Handles startup and shutdown events.
    """
    global telegram_client, rate_limiter, message_queue

    # Startup
    logger.info(
        "service_starting",
        service=__service_name__,
        version=__version__,
        environment=settings.app_env,
        port=settings.service_port,
    )

    # Initialize Telegram client
    telegram_client = TelegramClient()

    # Validate Telegram bot token on startup
    try:
        bot_info = await telegram_client.validate_token()
        logger.info(
            "telegram_bot_connected",
            bot_username=bot_info["username"],
            bot_id=bot_info["id"],
        )
    except TelegramError as e:
        logger.error(
            "telegram_bot_validation_failed",
            error=str(e),
            error_type=type(e).__name__,
        )
        raise RuntimeError(f"Failed to validate Telegram bot token: {e}")

    # Initialize rate limiter
    rate_limiter = RateLimiter(
        messages_per_second=settings.rate_limit_messages_per_second,
        burst_size=settings.rate_limit_burst_size,
    )

    # Initialize message queue
    message_queue = deque(maxlen=settings.queue_max_size)

    # Set queue max size metric
    queue_max_size_gauge.set(settings.queue_max_size)

    logger.info("service_started")

    yield

    # Shutdown
    logger.info("service_shutting_down")

    # Close Telegram client
    await telegram_client.close()

    logger.info("service_stopped")


# Create FastAPI app
app = FastAPI(
    title="Telegram Alert Service",
    description="Microservice for sending Telegram messages with rate limiting and queuing",
    version=__version__,
    lifespan=lifespan,
)


# Request ID middleware
@app.middleware("http")
async def add_request_id(request: Request, call_next):
    """Add request ID to all requests for tracking."""
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    request.state.request_id = request_id

    # Bind request ID to logger context
    structlog.contextvars.clear_contextvars()
    structlog.contextvars.bind_contextvars(request_id=request_id)

    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id

    return response


# Metrics middleware
@app.middleware("http")
async def track_metrics(request: Request, call_next):
    """Track request metrics."""
    start_time = time.time()

    response = await call_next(request)

    duration = time.time() - start_time

    # Track request metrics
    requests_total.labels(
        endpoint=request.url.path,
        method=request.method,
        status_code=response.status_code,
    ).inc()

    request_duration_seconds.labels(
        endpoint=request.url.path,
        method=request.method,
    ).observe(duration)

    return response


@app.post(
    "/api/v1/alerts/send",
    response_model=AlertResponse,
    status_code=status.HTTP_200_OK,
    responses={
        200: {"description": "Message sent successfully"},
        202: {"description": "Message queued for delivery"},
        400: {"description": "Bad request"},
        401: {"description": "Unauthorized"},
        429: {"description": "Rate limited"},
        500: {"description": "Internal server error"},
    },
)
async def send_alert(
    request: Request,
    alert: AlertRequest,
    auth_token: AuthToken,
) -> AlertResponse:
    """
    Send a Telegram alert message.

    Requires Bearer token authentication.

    The message will be sent immediately if rate limit allows,
    otherwise it will be queued for later delivery.

    Args:
        request: FastAPI request object
        alert: Alert request data
        auth_token: Validated auth token from dependency

    Returns:
        AlertResponse with delivery status

    Raises:
        HTTPException: For various error conditions
    """
    request_id = request.state.request_id
    start_time = time.time()

    logger.info(
        "alert_request_received",
        chat_id_prefix=alert.chat_id[:3] + "***" if len(alert.chat_id) > 6 else "***",
        message_length=len(alert.message),
        priority=alert.priority,
        parse_mode=alert.parse_mode,
    )

    try:
        # Check if we can send immediately (rate limit check)
        can_send = await rate_limiter.acquire()

        if not can_send:
            # Rate limited - queue the message
            rate_limit_hits_total.inc()

            # Add to queue
            if len(message_queue) >= settings.queue_max_size:
                logger.error("message_queue_full", queue_size=len(message_queue))
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Message queue is full. Please try again later.",
                )

            message_queue.append({
                "request_id": request_id,
                "alert": alert.model_dump(),
                "timestamp": time.time(),
            })

            queue_size_gauge.set(len(message_queue))

            logger.info(
                "message_queued",
                queue_position=len(message_queue),
                queue_size=len(message_queue),
            )

            return AlertResponse(
                status="queued",
                request_id=request_id,
                queue_position=len(message_queue),
                estimated_delay_seconds=int(len(message_queue) / settings.rate_limit_messages_per_second),
            )

        # Send message immediately
        try:
            result = await telegram_client.send_message(
                chat_id=alert.chat_id,
                text=alert.message,
                parse_mode=alert.parse_mode,
                request_id=request_id,
            )

            delivery_time_ms = int((time.time() - start_time) * 1000)

            # Track metrics
            messages_sent_total.labels(status="success").inc()
            message_delivery_seconds.observe(time.time() - start_time)

            logger.info(
                "message_sent_successfully",
                message_id=result["message_id"],
                delivery_time_ms=delivery_time_ms,
            )

            return AlertResponse(
                status="success",
                message_id=result["message_id"],
                telegram_response={"ok": True, "result": result},
                delivery_time_ms=delivery_time_ms,
                request_id=request_id,
            )

        except BadRequest as e:
            # Client error - invalid request
            messages_sent_total.labels(status="failed").inc()
            errors_total.labels(error_type="bad_request").inc()

            logger.error(
                "telegram_bad_request",
                error=str(e),
                error_type=type(e).__name__,
            )

            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid request: {str(e)}",
            )

        except TelegramError as e:
            # Telegram API error after retries
            messages_sent_total.labels(status="failed").inc()
            errors_total.labels(error_type="telegram_error").inc()

            logger.error(
                "telegram_api_error",
                error=str(e),
                error_type=type(e).__name__,
            )

            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to send message: {str(e)}",
            )

    except HTTPException:
        # Re-raise HTTP exceptions
        raise

    except Exception as e:
        # Unexpected error
        errors_total.labels(error_type="unexpected_error").inc()

        logger.exception(
            "unexpected_error",
            error=str(e),
            error_type=type(e).__name__,
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


@app.get(
    "/health",
    response_model=HealthCheck,
    responses={
        200: {"description": "Service is healthy"},
        503: {"description": "Service is unhealthy"},
    },
)
async def health_check() -> HealthCheck:
    """
    Health check endpoint.

    Checks:
    - Telegram API connectivity
    - Rate limiter status
    - Message queue status

    Returns:
        HealthCheck model with status and details
    """
    health = await perform_health_check(
        telegram_client=telegram_client,
        rate_limiter=rate_limiter,
        queue_size=len(message_queue),
    )

    # Update rate limit tokens gauge
    available_tokens = await rate_limiter.bucket.get_available_tokens()
    rate_limit_tokens_available.set(available_tokens)

    # Return 503 if unhealthy
    if health.status == "unhealthy":
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content=health.model_dump(),
        )

    return health


@app.get(
    "/metrics",
    response_class=PlainTextResponse,
    include_in_schema=False,
)
async def metrics():
    """
    Prometheus metrics endpoint.

    Returns metrics in Prometheus text format.
    """
    # Update queue size gauge before returning metrics
    queue_size_gauge.set(len(message_queue))

    # Update rate limit tokens gauge
    available_tokens = await rate_limiter.bucket.get_available_tokens()
    rate_limit_tokens_available.set(available_tokens)

    return PlainTextResponse(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST,
    )


@app.get(
    "/",
    include_in_schema=False,
)
async def root():
    """Root endpoint - service information."""
    return {
        "service": __service_name__,
        "version": __version__,
        "status": "running",
        "environment": settings.app_env,
    }


# Error handlers
@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    """Handle 404 errors."""
    return JSONResponse(
        status_code=404,
        content={
            "status": "error",
            "error_code": "NOT_FOUND",
            "message": "Endpoint not found",
            "request_id": getattr(request.state, "request_id", None),
        },
    )


@app.exception_handler(500)
async def internal_error_handler(request: Request, exc):
    """Handle 500 errors."""
    logger.exception("internal_server_error", error=str(exc))

    return JSONResponse(
        status_code=500,
        content={
            "status": "error",
            "error_code": "INTERNAL_SERVER_ERROR",
            "message": "Internal server error",
            "request_id": getattr(request.state, "request_id", None),
        },
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host=settings.host,
        port=settings.service_port,
        log_level=settings.log_level.lower(),
    )
