# Multi-stage Dockerfile for banking-demo

# ─────────────────────────────────────────────────────────────────
# Stage 1: Builder — Install all dependencies
# ─────────────────────────────────────────────────────────────────
FROM python:3.12-slim AS builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc g++ && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt ./

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# ─────────────────────────────────────────────────────────────────
# Stage 2: Production — Lean runtime image
# ─────────────────────────────────────────────────────────────────
FROM python:3.12-slim

WORKDIR /app

# Copy Python packages from builder
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY . .

# Create data directories
RUN mkdir -p /data/chroma /data/sqlite

# Set environment defaults
ENV OLLAMA_MODEL=qwen3:0.6b
ENV COMBINED_OLLAMA_MODEL=
ENV OLLAMA_HOST=http://host.docker.internal:11434
ENV LOG_LEVEL=INFO

# Expose port
EXPOSE 8005

# Health check
HEALTHCHECK --interval=25s --timeout=10s --start-period=45s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8005/api/status')"

# Run application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8005"]
