import json

from documind.raft import RaftDocument, build_distractor_examples, write_jsonl


def test_builds_golden_and_distractor_examples():
    docs = [
        RaftDocument("gold", "Retention is seven years.", "policy_pdf", 2),
        RaftDocument("noise1", "Office hours are nine to five.", "policy_pdf", 1),
        RaftDocument("noise2", "The company was founded in 2010.", "about_pdf", 0),
    ]
    examples = build_distractor_examples(
        [{"question": "How long?", "answer": "Seven years.", "golden_id": "gold"}],
        docs,
        distractors_per_example=2,
        golden_probability=1,
    )
    item = examples[0]
    assert item.documents[0]["role"] == "gold"
    assert len(item.documents) == 3
    assert item.citations == [{"source": "policy_pdf", "page": 2}]


def test_can_create_no_golden_abstention_example(tmp_path):
    examples = build_distractor_examples(
        [{"question": "Missing?", "answer": "No answer", "golden_id": "missing"}],
        [RaftDocument("doc", "Unrelated.", "doc", 0)],
        distractors_per_example=1,
    )
    path = tmp_path / "raft.jsonl"
    write_jsonl(examples, path)
    row = json.loads(path.read_text(encoding="utf-8"))
    assert row["documents"][0]["role"] == "distractor"
    assert row["citations"] == []
    assert "don't know" in row["answer"]
