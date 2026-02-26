FROM python:3.11-slim as base

# Security: Run as non-root user
RUN useradd -m -u 1000 tileserver && \
    apt-get update && \
    apt-get install -y --no-install-recommends \
        curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy application
COPY --chown=tileserver:tileserver tile_server.py .

# Switch to non-root user
USER tileserver

# Health check endpoint
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

EXPOSE 8080

# Use exec form to ensure proper signal handling
ENTRYPOINT ["python3", "-u", "tile_server.py"]