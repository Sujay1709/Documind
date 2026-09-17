FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    HOME=/data \
    OLLAMA_MODELS=/data/ollama \
    OLLAMA_KEEP_ALIVE=-1 \
    DOCUMIND_PERSIST_DIR=/data/.documind/chroma \
    DOCUMIND_HISTORY_FILE=/data/.documind/history.json \
    DOCUMIND_SUMMARIES_FILE=/data/.documind/summaries.json \
    HF_HOME=/data/hf \
    PORT=7860

WORKDIR /app

# curl is used for the health checks; zstd is required by the Ollama installer.
RUN apt-get update && apt-get install -y --no-install-recommends curl ca-certificates zstd \
    && rm -rf /var/lib/apt/lists/*

RUN curl -fsSL https://ollama.com/install.sh | sh

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN pip install --no-cache-dir -e .

RUN mkdir -p /data/ollama /data/.documind /data/hf && chmod -R 777 /data

EXPOSE 7860
HEALTHCHECK CMD curl --fail http://localhost:${PORT}/healthz || exit 1

COPY deploy/hf-spaces/start.sh /start.sh
RUN chmod +x /start.sh

CMD ["/bin/bash", "/start.sh"]
