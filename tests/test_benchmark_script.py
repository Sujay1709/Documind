"""Smoke test for the multi-config benchmark script.

We don't run the full pipeline (needs Ollama), but we do verify the script
imports cleanly and that ``to_markdown`` produces a table with one row per
configured run.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

_REPO = Path(__file__).resolve().parent.parent
_SCRIPT = _REPO / "scripts" / "benchmark.py"


def _load_benchmark_module():
    spec = importlib.util.spec_from_file_location("benchmark_under_test", _SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_to_markdown_has_one_row_per_run():
    mod = _load_benchmark_module()
    rows = [{"name": "r1", "aggregate": {k: 0.0 for k in [
        "retrieval_hit", "retrieval_recall", "mrr", "answer_f1",
        "keyword_recall", "faithfulness",
    ]}}]
    md = mod.to_markdown(rows)
    # Header row + separator + one data row = 3 lines (plus the leading title).
    assert md.count("| r1 |") == 1
    assert "retrieval_hit" in md and "faithfulness" in md
