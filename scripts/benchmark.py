"""Run DocuMind's RAG evaluation across multiple configurations.

Compares chunking/retrieval settings against a fixed dataset and writes a
side-by-side Markdown + JSON report so we can see which knobs actually move
retrieval and answer-quality metrics.

Why this exists: the stock `make eval` only runs a single configuration. To
defend a claim like "bigger chunks improved hit@5 by 12%" we need *contrasts*.
This script loops over a small grid and reports aggregate metrics for each run.

Usage:
    python scripts/benchmark.py --dataset eval/datasets/realistic.json --out eval/benchmark.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Allow running as `python scripts/benchmark.py` from the repo root.
_REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO / "src"))

from documind.config import Settings  # noqa: E402
from documind.evaluation import evaluate_dataset, load_dataset  # noqa: E402

# A small, defensible grid. Each entry overrides Settings fields and re-evaluates
# the same dataset. The defaults ("baseline") reflect the values committed to
# config.py so we always have a known reference point.
GRID: list[dict] = [
    {
        "name": "baseline (chunk=1000, top_k=8, n_results=30)",
        "chunk_size": 1000,
        "chunk_overlap": 200,
        "n_results": 30,
        "top_k_rerank": 8,
    },
    {
        "name": "smaller chunks (chunk=400, top_k=8)",
        "chunk_size": 400,
        "chunk_overlap": 100,
        "n_results": 30,
        "top_k_rerank": 8,
    },
    {
        "name": "fewer final chunks (chunk=1000, top_k=3)",
        "chunk_size": 1000,
        "chunk_overlap": 200,
        "n_results": 30,
        "top_k_rerank": 3,
    },
    {
        "name": "wide recall (chunk=1000, top_k=12)",
        "chunk_size": 1000,
        "chunk_overlap": 200,
        "n_results": 30,
        "top_k_rerank": 12,
    },
]


def _run_one(name: str, overrides: dict, samples, base: Settings) -> dict:
    """Evaluate ``samples`` once with ``overrides`` applied to a fresh Settings."""
    # We build a fresh Settings per run so per-trial overrides don't leak via
    # the cached ``get_settings()`` singleton in production code paths.
    cfg = base.model_copy(update=overrides)
    report = evaluate_dataset(samples, settings=cfg)
    return {
        "name": name,
        "overrides": {k: v for k, v in overrides.items() if k != "name"},
        "aggregate": report.aggregate,
    }


def to_markdown(rows: list[dict]) -> str:
    """Pretty side-by-side table for the README / report."""
    keys = [
        "retrieval_hit",
        "retrieval_recall",
        "mrr",
        "answer_f1",
        "keyword_recall",
        "faithfulness",
    ]
    lines = [
        "# DocuMind benchmark",
        "",
        "| Config | " + " | ".join(keys) + " |",
        "| --- | " + " | ".join(["---"] * len(keys)) + " |",
    ]
    for r in rows:
        agg = r["aggregate"]
        cells = [f"{agg.get(k, 0):.3f}" for k in keys]
        lines.append(f"| {r['name']} | " + " | ".join(cells) + " |")
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Compare DocuMind RAG configs.")
    p.add_argument("--dataset", required=True, help="JSON eval dataset.")
    p.add_argument("--out", default="eval/benchmark.json", help="Where to write the JSON report.")
    p.add_argument(
        "--markdown",
        default=None,
        help="Optional path to also write a Markdown summary.",
    )
    args = p.parse_args(argv)

    samples = load_dataset(args.dataset)
    base = Settings()
    rows = [_run_one(name=g["name"], overrides=g, samples=samples, base=base) for g in GRID]

    out = {"dataset": args.dataset, "runs": rows}
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")

    md = to_markdown(rows)
    print(md)
    if args.markdown:
        Path(args.markdown).write_text(md, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
