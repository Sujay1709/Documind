import json

import pytest

from documind import evaluation as ev
from documind.evaluation import EvalSample
from documind.pipeline import RetrievalResult
from documind.reranker import RankedChunk


# --- pure metric functions -------------------------------------------------- #
def test_token_f1_identical_and_disjoint():
    assert ev.token_f1("paris is the capital", "paris is the capital") == 1.0
    assert ev.token_f1("paris", "tokyo") == 0.0
    assert ev.token_f1("", "anything") == 0.0


def test_token_f1_partial():
    score = ev.token_f1("the capital is paris", "paris")
    assert 0.0 < score < 1.0


def test_keyword_recall():
    assert ev.keyword_recall("Paris is lovely in 2014", ["Paris", "2014"]) == 1.0
    assert ev.keyword_recall("Paris only", ["Paris", "2014"]) == 0.5
    assert ev.keyword_recall("text", []) == 0.0


def test_faithfulness():
    # Every content word of the answer appears in the context -> fully grounded.
    assert ev.faithfulness("Paris capital", "Paris is the capital of France") == 1.0
    # Hallucinated content word absent from context lowers the score.
    assert ev.faithfulness("Berlin capital", "Paris is the capital") == 0.5
    assert ev.faithfulness("", "anything") == 0.0


def test_evidence_quote_support_and_abstention():
    answer = 'Evidence: "Paris is the capital of France." Answer: Paris.'
    assert ev.evidence_quote_support(answer, "Paris is the capital of France.") == 1.0
    assert ev.evidence_quote_support('Evidence: "Berlin."', "Paris is the capital.") == 0.0
    assert ev.abstention_accuracy("I don't know based on the provided documents.", "") == 1.0
    assert ev.abstention_accuracy("Paris.", "") == 0.0


def test_evaluation_gate_rejects_weak_or_failed_reports():
    report = ev.EvalReport(
        results=[],
        aggregate={"faithfulness": 0.9, "evidence_quote_support": 0.9, "evaluation_failure": 0.1},
    )
    with pytest.raises(ev.EvaluationGateError):
        ev.enforce_gate(report)


def test_evaluation_continues_after_sample_failure(monkeypatch):
    def failing_answer(question, history=None, source=None, settings=None):
        raise RuntimeError("ollama unavailable")

    monkeypatch.setattr(ev, "pipeline_answer", failing_answer)
    report = ev.evaluate_dataset([EvalSample(question="q?")])
    assert report.results[0].error == "ollama unavailable"
    assert report.aggregate["evaluation_failure"] == 1.0


def test_retrieval_metrics():
    assert ev.retrieval_hit(["a"], ["b", "a"]) == 1.0
    assert ev.retrieval_hit(["a"], ["b", "c"]) == 0.0
    assert ev.retrieval_recall(["a", "b"], ["a", "x"]) == 0.5
    assert ev.reciprocal_rank(["b"], ["a", "b", "c"]) == 0.5
    assert ev.reciprocal_rank(["z"], ["a", "b"]) == 0.0


# --- runner (pipeline mocked, no Ollama) ------------------------------------ #
def test_evaluate_dataset_with_mocked_pipeline(monkeypatch):
    chunks = [
        RankedChunk(text="Paris is the capital of France.",
                    metadata={"source": "geography_pdf", "page": 0}, score=9.0),
        RankedChunk(text="France is in Europe.",
                    metadata={"source": "geography_pdf", "page": 1}, score=4.0),
    ]

    def fake_answer(question, history=None, source=None, settings=None):
        retrieval = RetrievalResult(
            context="\n\n".join(c.text for c in chunks), chunks=chunks
        )
        return iter(["Paris ", "is ", "the ", "capital."]), retrieval

    monkeypatch.setattr(ev, "pipeline_answer", fake_answer)

    samples = [
        EvalSample(
            question="What is the capital of France?",
            ground_truth="Paris is the capital of France.",
            expected_sources=["geography_pdf"],
            expected_keywords=["Paris"],
        )
    ]
    report = ev.evaluate_dataset(samples)

    assert len(report.results) == 1
    m = report.results[0].metrics
    assert m["retrieval_hit"] == 1.0
    assert m["mrr"] == 1.0
    assert m["keyword_recall"] == 1.0
    assert 0.0 < m["answer_f1"] <= 1.0
    assert m["faithfulness"] == 1.0
    # aggregate present and well-formed
    assert "answer_f1" in report.aggregate
    assert report.config["source_scope"] == "all"


def test_report_markdown_renders(monkeypatch):
    def fake_answer(question, history=None, source=None, settings=None):
        return iter(["ok"]), RetrievalResult(context="ctx ok", chunks=[])

    monkeypatch.setattr(ev, "pipeline_answer", fake_answer)
    report = ev.evaluate_dataset([EvalSample(question="q?")])
    md = report.to_markdown()
    assert "RAG evaluation" in md and "Aggregate metrics" in md


# --- persistence / run history (no Ollama) ---------------------------------- #
def test_diff_aggregates_and_format():
    rows = ev.diff_aggregates(
        {"answer_f1": 0.8, "faithfulness": 0.7},
        {"answer_f1": 0.5, "mrr": 1.0},
    )
    by_metric = {r["metric"]: r for r in rows}
    assert by_metric["answer_f1"]["delta"] == 0.3
    assert by_metric["faithfulness"]["previous"] == 0.0
    assert by_metric["mrr"]["current"] == 0.0
    md = ev.format_aggregate_diff(rows)
    assert "Delta vs previous run" in md
    assert "answer_f1" in md and "+0.300" in md


def test_persist_report_writes_run_and_latest(tmp_path, monkeypatch):
    def fake_answer(question, history=None, source=None, settings=None):
        return iter(["Paris"]), RetrievalResult(context="Paris capital", chunks=[])

    monkeypatch.setattr(ev, "pipeline_answer", fake_answer)
    report = ev.evaluate_dataset(
        [EvalSample(question="q?", ground_truth="Paris", expected_keywords=["Paris"])]
    )

    runs_dir = tmp_path / "runs"
    latest_json = tmp_path / "report.json"
    latest_md = tmp_path / "report.md"

    first = ev.persist_report(
        report,
        runs_dir=runs_dir,
        latest_json=latest_json,
        latest_md=latest_md,
        run_id="20260101-000000",
    )
    assert first["previous"] is None
    assert first["diff"] == []
    assert (runs_dir / "20260101-000000" / "report.json").is_file()
    assert latest_json.is_file() and latest_md.is_file()

    # Bump a metric so the second run has a non-zero delta.
    report2 = ev.EvalReport(
        results=report.results,
        aggregate={**report.aggregate, "answer_f1": report.aggregate.get("answer_f1", 0) + 0.1},
        config=report.config,
    )
    second = ev.persist_report(
        report2,
        runs_dir=runs_dir,
        latest_json=latest_json,
        latest_md=latest_md,
        run_id="20260101-000001",
    )
    assert second["previous"] == "20260101-000000"
    assert any(r["metric"] == "answer_f1" and float(r["delta"]) == 0.1 for r in second["diff"])
    assert "Delta vs previous run" in (second["md_path"]).read_text(encoding="utf-8")
    assert json.loads(latest_json.read_text(encoding="utf-8"))["run_id"] == "20260101-000001"


def test_utc_run_id_format():
    from datetime import datetime, timezone

    rid = ev.utc_run_id(datetime(2026, 8, 13, 23, 14, 5, tzinfo=timezone.utc))
    assert rid == "20260813-231405"
