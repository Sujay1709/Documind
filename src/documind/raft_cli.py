"""CLI for building RAFT-style JSONL examples from reviewed records."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .raft import RaftDocument, build_distractor_examples, write_jsonl


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="documind-raft")
    parser.add_argument("--questions", required=True, help="JSON array of reviewed questions.")
    parser.add_argument("--documents", required=True, help="JSON array of document records.")
    parser.add_argument("--out", required=True, help="Output JSONL path.")
    parser.add_argument("--distractors", type=int, default=4)
    parser.add_argument("--golden-probability", type=float, default=0.8)
    args = parser.parse_args(argv)

    questions = json.loads(Path(args.questions).read_text(encoding="utf-8"))
    documents = [
        RaftDocument(
            id=str(item["id"]),
            text=str(item["text"]),
            source=str(item["source"]),
            page=item.get("page"),
        )
        for item in json.loads(Path(args.documents).read_text(encoding="utf-8"))
    ]
    examples = build_distractor_examples(
        questions,
        documents,
        distractors_per_example=args.distractors,
        golden_probability=args.golden_probability,
    )
    write_jsonl(examples, args.out)
    print(f"Wrote {len(examples)} RAFT examples to {args.out}")
    return 0
