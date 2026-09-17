"""RAFT-style dataset construction for offline domain adaptation.

This module creates JSONL examples; it does not train or modify an Ollama model.
Training remains an explicit, reproducible offline step using a compatible
Transformers/PEFT/QLoRA environment.
"""

from __future__ import annotations

import json
import random
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass(frozen=True)
class RaftDocument:
    id: str
    text: str
    source: str
    page: int | None = None


@dataclass(frozen=True)
class RaftExample:
    question: str
    documents: list[dict[str, object]]
    answer: str
    quote: str
    reason: str
    citations: list[dict[str, object]]


def build_example(
    question: str,
    answer: str,
    golden: RaftDocument | None,
    distractors: list[RaftDocument],
    quote: str = "",
    reason: str = "",
) -> RaftExample:
    """Build one golden-plus-distractors or no-golden training example."""
    docs: list[dict[str, object]] = []
    if golden is not None:
        docs.append({**asdict(golden), "role": "gold"})
    docs.extend({**asdict(doc), "role": "distractor"} for doc in distractors)
    citations = (
        [{"source": golden.source, "page": golden.page}]
        if golden is not None
        else []
    )
    return RaftExample(
        question=question,
        documents=docs,
        answer=answer,
        quote=quote if golden is not None else "",
        reason=reason if golden is not None else "",
        citations=citations,
    )


def write_jsonl(examples: list[RaftExample], path: str | Path) -> None:
    """Write examples in a stable JSONL format for training tools."""
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        "\n".join(json.dumps(asdict(example), ensure_ascii=False) for example in examples)
        + ("\n" if examples else ""),
        encoding="utf-8",
    )


def build_distractor_examples(
    questions: list[dict[str, object]],
    documents: list[RaftDocument],
    *,
    distractors_per_example: int = 4,
    golden_probability: float = 0.8,
    seed: int = 0,
) -> list[RaftExample]:
    """Create RAFT examples from reviewed question records.

    Each question must contain ``answer`` and may contain ``golden_id``,
    ``quote``, and ``reason``. A missing golden id intentionally creates an
    abstention example.
    """
    if distractors_per_example < 0:
        raise ValueError("distractors_per_example must be non-negative")
    if not 0 <= golden_probability <= 1:
        raise ValueError("golden_probability must be between 0 and 1")

    by_id = {doc.id: doc for doc in documents}
    rng = random.Random(seed)
    examples: list[RaftExample] = []
    for item in questions:
        question = str(item["question"])
        answer = str(item.get("answer", "I don't know based on the provided documents."))
        golden_id = item.get("golden_id")
        golden = by_id.get(str(golden_id)) if golden_id is not None else None
        if golden is not None and rng.random() > golden_probability:
            golden = None
        pool = [doc for doc in documents if golden is None or doc.id != golden.id]
        rng.shuffle(pool)
        examples.append(
            build_example(
                question,
                answer if golden is not None else "I don't know based on the provided documents.",
                golden,
                pool[:distractors_per_example],
                quote=str(item.get("quote", "")),
                reason=str(item.get("reason", "")),
            )
        )
    return examples
