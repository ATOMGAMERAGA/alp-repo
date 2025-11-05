# Multi-stage build for smaller image size
FROM python:3.11-alpine AS builder

# Install build dependencies
RUN apk add --no-cache \
    git \
    curl \
    bash

WORKDIR /app

# Copy only necessary files
COPY alp_manager.py /app/alp_manager.py

# Make executable
RUN chmod +x /app/alp_manager.py

# Final stage - minimal runtime
FROM python:3.11-alpine

LABEL maintainer="Alp Package Manager"
LABEL description="Advanced Linux Package Management System"
LABEL version="2.2"

# Install only runtime dependencies (smaller footprint)
RUN apk add --no-cache \
    git \
    curl \
    bash \
    ca-certificates \
    && rm -rf /var/cache/apk/*

# Create non-root user for security (optional)
# RUN adduser -D -h /home/alp alp

WORKDIR /app

# Copy from builder stage
COPY --from=builder /app/alp_manager.py /app/alp_manager.py

# Alp home directory with proper permissions
RUN mkdir -p /root/.alp/cache /root/.alp/logs /root/.alp/installed && \
    chmod -R 755 /root/.alp

# Environment optimization
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Create symlink for global access
RUN ln -sf /app/alp_manager.py /usr/local/bin/alp && \
    chmod +x /usr/local/bin/alp

# Default shell
SHELL ["/bin/bash", "-c"]

# Default command
CMD ["/bin/bash"]

# Optimized health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=2 \
    CMD python3 -c "import sys; sys.exit(0)" || exit 1
