# Multi-stage build for Crypto Price Alert Service

# Build stage
FROM python:3.11-slim as builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc && \
    rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt


# Runtime stage
FROM python:3.11-slim

# Create non-root user
RUN useradd -m -u 1000 cryptouser && \
    mkdir -p /app/data && \
    chown -R cryptouser:cryptouser /app

WORKDIR /app

# Install runtime dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends curl && \
    rm -rf /var/lib/apt/lists/*

# Copy Python dependencies from builder
COPY --from=builder /root/.local /home/cryptouser/.local

# Copy application code
COPY --chown=cryptouser:cryptouser . .

# Set Python path to include user packages
ENV PATH=/home/cryptouser/.local/bin:$PATH
ENV PYTHONPATH=/app

# Switch to non-root user
USER cryptouser

# Expose ports
EXPOSE 52000

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:52000/health || exit 1

# Run application
CMD ["python", "-m", "uvicorn", "crypto_service.main:app", "--host", "0.0.0.0", "--port", "52000"]
