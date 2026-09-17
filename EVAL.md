# Evaluating DocuMind (RAG evaluation harness)

DocuMind ships with a small, dependency-free harness that measures both halves of
a RAG system: **did retrieval find the right passages**, and **is the generated
answer correct and grounded**. Generative answers (and the optional LLM judge)
use your **local Ollama** chat model — the same persistent backend as
`./start-web.sh`. No cloud API key paste is required.

## Metrics

**Retrieval** (need `expected_sources` in your dataset)
- `retrieval_hit` — 1 if any expected source was retrieved, else 0.
- `retrieval_recall` — fraction of expected sources retrieved.
- `mrr` — mean reciprocal rank of the first relevant source.

**Answer quality**
- `answer_f1` — token-level F1 vs. your reference answer (`ground_truth`).
- `keyword_recall` — fraction of `expected_keywords` present in the answer.
- `faithfulness` — share of the answer's content words found in the retrieved
  context (a free hallucination proxy; higher = better grounded).
- `evidence_quote_support` — fraction of `Evidence: "..."` quotes that appear
  verbatim in the retrieved context.
- `abstention_accuracy` — whether a no-context answer explicitly abstains
  instead of guessing.
- `evaluation_failure` — fraction of samples that failed due to infrastructure
  or model errors; a reliability gate requires this to be zero.
- `llm_judge` *(optional, `--judge`)* — the local chat model grades groundedness
  1–5, normalised to 0–1.

All retrieval/answer metric math is pure Python and unit-tested, so it runs in CI
without a model server. Generating answers (and the LLM judge) needs Ollama.

## Dataset format

A JSON array; every field except `question` is optional:

```json
[
  {
    "question": "What is the capital of France?",
    "ground_truth": "Paris is the capital of France.",
    "expected_sources": ["geography_pdf"],
    "expected_keywords": ["Paris"]
  }
]
```

`expected_sources` use the **normalised** indexed name (dots/dashes/spaces become
underscores), e.g. `geography.pdf` → `geography_pdf`. See the sidebar's
"Indexed documents" list for exact names.

## Running it

1. Index the documents your dataset asks about (upload them in the app, or via the
   ingestion API) and make sure Ollama is running.
2. Run the harness:

```bash
# all documents — persists under eval/runs/<UTC-timestamp>/
documind-eval --dataset eval/sample_dataset.json

# scope retrieval to a single document
documind-eval --dataset eval/sample_dataset.json --source geography_pdf

# also grade with the local LLM judge
documind-eval --dataset eval/sample_dataset.json --judge

# one-shot JSON only (skip run history)
documind-eval --dataset eval/sample_dataset.json --no-persist --out eval/oneshot.json

# enforce the grounding contract; exits 1 on regression or sample failure
documind-eval --dataset eval/sample_dataset.json --gate
```

The default gate requires faithfulness >= `0.75`, evidence quote support >=
`0.80`, and zero evaluation failures. Use `--min-faithfulness` and
`--min-evidence-quote-support` to calibrate thresholds for a reviewed corpus.
Missing metrics fail the gate instead of being treated as success.

### Persisted run history

Every default run writes:

| Path | Role |
| --- | --- |
| `eval/runs/<YYYYMMDD-HHMMSS>/report.json` | Full timestamped report |
| `eval/runs/<YYYYMMDD-HHMMSS>/report.md` | Markdown summary (+ delta table) |
| `eval/report.json` / `eval/report.md` | Always-updated “latest” mirror |

When a previous run exists, the CLI prints a short **delta vs previous run**
table (per-metric Δ). Run directories are gitignored; regenerate anytime with
`make eval`.

`make eval` runs the harness against `eval/datasets/realistic.json`.

## In CI / the cloud

The metric unit tests run automatically in GitHub Actions. A full generative eval
needs Ollama, so it isn't part of the default PR pipeline; a manual
**workflow_dispatch** job (`.github/workflows/eval.yml`) is provided to run it on
demand. You can also run `documind-eval` inside the deployed Hugging Face Space
(it already has Ollama and the models).

Evaluation failures are retained per question in the report so one broken model
request cannot hide failures in the rest of the dataset.
