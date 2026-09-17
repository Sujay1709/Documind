#!/usr/bin/env bash
# Entrypoint for the Hugging Face Space: start Ollama, ensure models exist,
# then launch the long-running web app on the port Spaces expects (7860).
set -euo pipefail

CHAT_MODEL="${DOCUMIND_CHAT_MODEL:-llama3.2:3b}"
EMBED_MODEL="${DOCUMIND_EMBEDDING_MODEL:-nomic-embed-text}"
PORT="${PORT:-7860}"

OLLAMA_URL="${DOCUMIND_OLLAMA_BASE_URL:-http://localhost:11434}"
if [[ "$OLLAMA_URL" == "http://localhost:11434" || "$OLLAMA_URL" == "http://127.0.0.1:11434" ]]; then
  echo "▶ Starting bundled Ollama server…"
  ollama serve &

  echo "▶ Waiting for Ollama to be ready…"
  for _ in $(seq 1 60); do
    if curl -fsS "$OLLAMA_URL/api/tags" >/dev/null 2>&1; then
      echo "✓ Ollama is up."
      break
    fi
    sleep 2
  done

  echo "▶ Ensuring models are available (first boot can take a few minutes)…"
  ollama pull "$CHAT_MODEL"  || echo "⚠ could not pull $CHAT_MODEL"
  ollama pull "$EMBED_MODEL" || echo "⚠ could not pull $EMBED_MODEL"
else
  echo "▶ Using external Ollama-compatible endpoint: $OLLAMA_URL"
fi

echo "▶ Launching DocuMind web app on :$PORT…"
exec uvicorn documind.webapp:app \
  --host 0.0.0.0 \
  --port "$PORT" \
  --workers 1 \
  --log-level info
