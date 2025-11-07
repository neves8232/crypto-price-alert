"""
Main FastAPI application for the Crypto Price Alert Service.
"""

import uuid
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles

from crypto_service import __version__
from crypto_service.config import settings
from crypto_service.database import init_db, close_db
from crypto_service.utils.logging import configure_logging, get_logger
from crypto_service.services.scheduler import scheduler

# Import API routers
from crypto_service.api import health, cryptocurrencies, alerts, prices

# Configure logging
configure_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager for startup and shutdown events.
    """
    # Startup
    logger.info(
        "starting_application",
        version=__version__,
        environment=settings.app_env,
        port=settings.api_port,
    )

    # Initialize database
    try:
        await init_db()
        logger.info("database_initialized")
    except Exception as e:
        logger.error("database_initialization_failed", error=str(e), exc_info=True)
        raise

    # Start background scheduler
    try:
        await scheduler.start()
        logger.info("background_scheduler_started")
    except Exception as e:
        logger.error("scheduler_start_failed", error=str(e), exc_info=True)

    logger.info("application_started")

    yield

    # Shutdown
    logger.info("shutting_down_application")

    # Stop scheduler
    try:
        await scheduler.shutdown()
        logger.info("scheduler_stopped")
    except Exception as e:
        logger.error("scheduler_shutdown_failed", error=str(e), exc_info=True)

    # Close database
    try:
        await close_db()
        logger.info("database_closed")
    except Exception as e:
        logger.error("database_close_failed", error=str(e), exc_info=True)

    logger.info("application_shutdown_complete")


# Create FastAPI application
app = FastAPI(
    title="Crypto Price Alert Service",
    description="Real-time cryptocurrency price monitoring and alerting service",
    version=__version__,
    lifespan=lifespan,
    docs_url="/docs" if settings.is_development else None,
    redoc_url="/redoc" if settings.is_development else None,
)


# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request ID middleware
@app.middleware("http")
async def add_request_id(request: Request, call_next):
    """Add request ID to all requests for tracing."""
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    request.state.request_id = request_id

    # Bind request ID to logger context
    logger.bind(request_id=request_id)

    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id

    return response


# Exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Global exception handler for unhandled errors."""
    request_id = getattr(request.state, "request_id", "unknown")

    logger.error(
        "unhandled_exception",
        error=str(exc),
        path=request.url.path,
        method=request.method,
        request_id=request_id,
        exc_info=True,
    )

    return JSONResponse(
        status_code=500,
        content={
            "status": "error",
            "error_code": "INTERNAL_SERVER_ERROR",
            "message": "An internal error occurred",
            "request_id": request_id,
        },
    )


# Include routers
app.include_router(health.router)
app.include_router(cryptocurrencies.router)
app.include_router(alerts.router)
app.include_router(prices.router)

# Mount static files
STATIC_DIR = Path(__file__).parent / "static"
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
    logger.info("static_files_mounted", path=str(STATIC_DIR))
else:
    logger.warning("static_directory_not_found", path=str(STATIC_DIR))


# Root endpoint - serve the web UI
@app.get("/")
async def root():
    """Root endpoint - serves the web UI."""
    index_path = STATIC_DIR / "index.html"
    if index_path.exists():
        return FileResponse(index_path)
    else:
        # Fallback to API info if UI not available
        return {
            "service": "crypto-price-alert",
            "version": __version__,
            "status": "running",
            "docs": "/docs" if settings.is_development else "disabled",
            "ui": "not available - static files not found",
        }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.is_development,
        log_level=settings.log_level.lower(),
    )
