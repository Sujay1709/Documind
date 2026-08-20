#!/usr/bin/env bash
# Commit and push the DocuMind web-app rollout. Run this from the repo root
# in a non-sandboxed shell (your normal terminal).
#
# Usage:
#   bash /tmp/commit-documind.sh
#
# It will run five logical commits then push the current branch.
set -euo pipefail

cd "$(dirname "$(readlink -f "$0" 2>/dev/null || echo "$0")")/.." 2>/dev/null || true
# If the script was saved somewhere else, fall back to the current directory.
cd "${REPO_DIR:-$(pwd)}"

BRANCH="$(git rev-parse --abbrev-ref HEAD)"
echo "→ On branch: $BRANCH"
echo

git status --short
echo

# Sanity: the tests must still pass before we commit.
echo "→ Running pytest..."
pytest -q
echo

# Commit 1
echo "→ Commit 1/5: top_k_rerank default + new eval question"
git add src/documind/config.py eval/datasets/realistic.json
git commit -m "Tune re-rank default 8 -> 12; add 5th textbook multi-chunk eval question

The benchmark grid in eval/benchmark.md shows top_k_rerank=12 raises
faithfulness 0.62 -> 0.68 and keyword recall 0.75 -> 0.88 on the
realistic dataset (9 questions across 4 PDFs) versus the 8-chunk
baseline, at a small F1 cost. Docstring in config.py cites the data.

Added an eval question that requires the model to read several
chunks in document order, exercising the document-position re-sort
in pipeline.py:retrieve()."
echo

# Commit 2
echo "→ Commit 2/5: long-running web app"
git add src/documind/webapp.py src/documind/webapp/ tests/test_webapp.py pyproject.toml
git commit -m "Add documind-web: long-running Starlette + uvicorn service

Same documind.pipeline as the Streamlit UI; new transport so the
LLM, vector store, and cross-encoder stay resident between requests.
Single-page app at /, multipart PDF upload at /upload, SSE chat
stream at /chat, single-JSON at /api/chat, /healthz for liveness.

Hardening for a public demo:
  - per-visitor rate limit (DOCUMIND_RATE_LIMIT_PER_MIN)
  - optional shared-secret gate (DOCUMIND_API_TOKEN -> X-Documind-Token)
  - JSON-line audit log at .documind/audit.log
  - max_answer_tokens ceiling on streamed output
  - summarize_on_upload toggle (off by default in the public Space)

10 new tests in tests/test_webapp.py cover the SPA, SSE framing,
NDJSON fallback, multipart upload, rate-limit, and the token gate."
echo

# Commit 3
echo "→ Commit 3/5: deployment + docs"
git add Dockerfile docker-compose.yml .env.example .gitignore Makefile \
        deploy/hf-spaces/ start-web.sh README.md DEPLOY.md RESUME.md
git commit -m "Ship DocuMind as a long-running public web service

- Dockerfile defaults to ./start-web.sh (uvicorn on :8000);
  legacy streamlit run still works for the local UI.
- docker-compose.yml runs Ollama + the web app with healthchecks
  and a persistent /data volume.
- deploy/hf-spaces/ is a single-image HF Space (Python + Ollama
  on :7860) with persistent model storage at /data/ollama.
- start-web.sh boots Ollama, pulls the configured models, then
  runs uvicorn so a single command brings the whole stack up.
- README, DEPLOY, RESUME updated to lead with the web app and
  the 12-chunk re-rank default. New Handshake blurb included."
echo

# Commit 4
echo "→ Commit 4/5: admin path-upload + SPA admin panel"
git add src/documind/webapp.py src/documind/config.py \
        src/documind/webapp/static/ tests/test_webapp.py .env.example
git commit -m "Add admin /api/upload-by-path for server-side PDF indexing

Lets an admin drop a PDF into DOCUMIND_UPLOAD_DIR (default ./uploads) and
index it via JSON instead of multipart. Path is resolved and required to
live inside the upload dir, with '..' traversal rejected, so a leaked
admin token can't index arbitrary files.

Endpoint: POST /api/upload-by-path, body {\"path\": \"paper.pdf\"},
requires X-Documind-Token.

The SPA now has a small Admin sign-in button in the top bar; once a
token is stored, the path-upload box appears. Token is kept in
localStorage only - no server-side state.

Tests: 3 new cases in tests/test_webapp.py cover the 401 (no token),
403 (path outside upload dir), and the happy path."
echo

# Commit 5
echo "→ Commit 5/5: live HTTP smoke test in CI + docs"
git add scripts/smoke_webapp.py tests/test_smoke_script.py \
        .github/workflows/smoke.yml Makefile README.md DEPLOY.md RESUME.md
git commit -m "Add live HTTP smoke test in CI for the public web app

New scripts/smoke_webapp.py boots against a running uvicorn process
and asserts the shape of /healthz, /api/sources, /api/history, /chat,
/api/chat, and /. Tolerates /healthz returning 503 (Ollama not
reachable in CI), but fails the build on any other shape change so
'route signature drifted' regressions surface before deploy.

.github/workflows/smoke.yml runs the script on every PR touching
src/documind/webapp/, tests/test_webapp.py, scripts/smoke_webapp.py,
or this workflow file. Catches the 'did the import break?' and
'did a route change shape?' regressions that pure unit tests miss.

Tests: 2 new cases in tests/test_smoke_script.py stub urllib so the
script itself runs in CI.

DEPLOY.md gains a 'Server-side path uploads' section with the
copy-pasteable HF Space flow; RESUME.md gains a 7th bullet for the
admin endpoint and the smoke workflow."
echo

# Push
echo "→ Pushing $BRANCH to origin..."
git push origin "$BRANCH"

echo
echo "✓ Done. Five commits pushed to $BRANCH."
git log --oneline -7
