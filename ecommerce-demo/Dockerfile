FROM python:3.12-slim
WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends gcc g++ && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY main.py .
COPY transaction_summary.py .
COPY llm/ ./llm/
COPY memory/ ./memory/
COPY agents/ ./agents/
COPY tools/ ./tools/
COPY data/ ./data/
COPY harness/ ./harness/

# Create data directories
RUN mkdir -p /data/chroma /data/sqlite

# Environment variables
ENV OLLAMA_MODEL=qwen3:0.6b
ENV ECOMMERCE_OLLAMA_MODEL=
ENV OLLAMA_HOST=http://host.docker.internal:11434
ENV DATA_DIR=/data

# Expose port
EXPOSE 8007

# Health check
HEALTHCHECK --interval=25s --timeout=10s --start-period=45s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8007/api/status')"

# Start application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8007"]
