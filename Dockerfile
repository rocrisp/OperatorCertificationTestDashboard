FROM python:3.11-slim

LABEL maintainer="CNF Certification Team"
LABEL description="Operator Certification Test Dashboard"
LABEL version="1.0"

# Install SSH client for remote connections
RUN apt-get update && apt-get install -y --no-install-recommends \
    openssh-client \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd -m -u 1000 dashboard

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY scripts/ ./scripts/

# Create logs directory
RUN mkdir -p /app/logs && chown -R dashboard:dashboard /app

# Create .ssh directory for SSH keys
RUN mkdir -p /home/dashboard/.ssh && \
    chown -R dashboard:dashboard /home/dashboard/.ssh && \
    chmod 700 /home/dashboard/.ssh

# Switch to non-root user
USER dashboard

# Environment variables with defaults
ENV REMOTE_HOST=rdu2 \
    REMOTE_BASE_DIR=/root/test-rose/certsuite \
    REPORT_DIR=/var/www/html \
    DASHBOARD_PORT=5001 \
    LOG_DIR=/app/logs \
    DEBUG=false \
    SSH_KEY_PATH="" \
    SSH_USER="" \
    REDHAT_CATALOG_INDEX=registry.redhat.io/redhat/redhat-operator-index:v4.20 \
    CERTIFIED_CATALOG_INDEX=registry.redhat.io/redhat/certified-operator-index:v4.20

# Expose the dashboard port
EXPOSE 5001

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:${DASHBOARD_PORT}/')" || exit 1

# Run the dashboard
CMD ["python", "scripts/web-dashboard.py"]
