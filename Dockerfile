# =============================================================
#  TaskApp - Production Dockerfile
# =============================================================
FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# System deps for mysqlclient + curl for healthcheck
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        default-libmysqlclient-dev \
        pkg-config \
        curl \
        ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Layer caching: install deps before copying source
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install -r requirements.txt && \
    pip install gunicorn==22.0.0 prometheus-flask-exporter==0.23.1

# Copy source
COPY . .

# Non-root user
RUN useradd -m -u 1000 appuser && \
    mkdir -p /app/static/uploads && \
    chown -R appuser:appuser /app
USER appuser

EXPOSE 5000

HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:5000/healthz || exit 1

CMD ["gunicorn", \
     "--workers=2", \
     "--threads=2", \
     "--bind=0.0.0.0:5000", \
     "--access-logfile=-", \
     "--error-logfile=-", \
     "--log-level=info", \
     "--timeout=60", \
     "run:app"]
