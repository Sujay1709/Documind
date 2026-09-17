"""Command-line entry point for the RAG evaluation harness.

Examples:
    documind-eval --dataset eval/sample_dataset.json
    documind-eval --dataset eval/sample_dataset.json --source report_pdf --judge
    documind-eval --dataset eval/sample_dataset.json --no-persist --out eval/oneshot.json

By default every run is written to ``eval/runs/<UTC-timestamp>/`` and mirrored
to ``eval/report.{json,md}``. A delta table vs the previous run is printed when
prior history exists. Generative answers require a running Ollama server.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .evaluation import (
    DEFAULT_LATEST_JSON,
    DEFAULT_LATEST_MD,
    DEFAULT_RUNS_DIR,
    EvalReport,
    EvaluationGateError,
    enforce_gate,
    evaluate_dataset,
    format_aggregate_diff,
    load_dataset,
    persist_report,
)


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(prog="documind-eval", description="Evaluate DocuMind RAG quality.")
    p.add_argument("--dataset", required=True, help="Path to a JSON eval dataset.")
    p.add_argument("--source", default=None, help="Scope retrieval to this indexed document.")
    p.add_argument("--judge", action="store_true", help="Also score with the LLM judge.")
    p.add_argument(
        "--gate",
        action="store_true",
        help="Fail if grounding metrics regress below the reliability contract.",
    )
    p.add_argument("--min-faithfulness", type=float, default=0.75)
    p.add_argument("--min-evidence-quote-support", type=float, default=0.80)
    p.add_argument(
        "--out",
        default=None,
        help="Optional extra path for the JSON report (in addition to the run history).",
    )
    p.add_argument(
        "--runs-dir",
        default=str(DEFAULT_RUNS_DIR),
        help=f"Directory for timestamped runs (default: {DEFAULT_RUNS_DIR}).",
    )
    p.add_argument(
        "--no-persist",
        action="store_true",
        help="Skip eval/runs/ history and only write --out if provided.",
    )
    return p.parse_args(argv)


def run(argv: list[str] | None = None) -> EvalReport:
    args = _parse_args(argv)
    samples = load_dataset(args.dataset)
    report = evaluate_dataset(samples, source=args.source, use_llm_judge=args.judge)

    print(report.to_markdown())

    if not args.no_persist:
        saved = persist_report(
            report,
            runs_dir=args.runs_dir,
            latest_json=DEFAULT_LATEST_JSON,
            latest_md=DEFAULT_LATEST_MD,
        )
        print(f"\nPersisted run {saved['run_id']} → {saved['run_dir']}")
        print(f"Latest mirror → {saved['latest_json']}")
        if saved["previous"] and saved["diff"]:
            print(f"Compared to previous run {saved['previous']}")
            print()
            print(format_aggregate_diff(saved["diff"]))
        elif not saved["previous"]:
            print("(No previous run to compare against.)")

    if args.out:
        out = Path(args.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(report.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"\nFull report written to {out}")
    if args.gate:
        enforce_gate(
            report,
            min_faithfulness=args.min_faithfulness,
            min_evidence_quote_support=args.min_evidence_quote_support,
        )
        print("\nEvaluation gate: PASS")
    return report


def main(argv: list[str] | None = None) -> int:
    try:
        run(argv)
    except FileNotFoundError as exc:
        print(f"Dataset not found: {exc}", file=sys.stderr)
        return 2
    except EvaluationGateError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
