FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc g++ && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy specific Python modules
COPY config.py llm.py mock.py tools.py agents.py data.py ui.py api.py harness.py main.py ./
COPY memory/ ./memory/

RUN mkdir -p /data/chroma /data/sqlite

ENV OLLAMA_MODEL=qwen3:0.6b
ENV OLLAMA_HOST=http://host.docker.internal:11434

EXPOSE 8007

HEALTHCHECK --interval=25s --timeout=10s --start-period=45s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8007/api/status')"

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8007"]
