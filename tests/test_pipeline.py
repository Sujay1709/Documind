"""Pipeline tests that stub out Ollama/Chroma so they run without a server."""

from documind import pipeline, vectorstore
from documind.config import get_settings
from documind.reranker import RankedChunk


def test_retrieve_handles_empty_store(monkeypatch):
    monkeypatch.setattr(
        vectorstore, "query", lambda *a, **k: {"documents": [[]], "metadatas": [[]]}
    )
    result = pipeline.retrieve("anything")
    assert result.is_empty
    assert result.context == ""


def test_retrieve_forwards_source_filter(monkeypatch):
    captured = {}

    def fake_query(prompt, n_results=None, source=None, settings=None):
        captured["source"] = source
        return {"documents": [[]], "metadatas": [[]]}

    monkeypatch.setattr(vectorstore, "query", fake_query)
    pipeline.retrieve("q", source="report_pdf")
    assert captured["source"] == "report_pdf"


def test_retrieve_reranks_and_builds_context(monkeypatch):
    fake = {
        "documents": [["alpha chunk", "beta chunk", "gamma chunk"]],
        "metadatas": [[{"source": "a"}, {"source": "b"}, {"source": "c"}]],
    }
    monkeypatch.setattr(vectorstore, "query", lambda *a, **k: fake)

    def fake_rerank(query, documents, metadatas=None, top_k=None):
        return [
            RankedChunk(text=documents[1], metadata=metadatas[1], score=0.9),
            RankedChunk(text=documents[0], metadata=metadatas[0], score=0.5),
        ]

    monkeypatch.setattr(pipeline, "rerank", fake_rerank)

    result = pipeline.retrieve("question", settings=get_settings())
    assert not result.is_empty
    assert len(result.chunks) == 2
    assert result.chunks[0].text == "beta chunk"
    assert "beta chunk" in result.context and "alpha chunk" in result.context


def test_hierarchy_groups_pages_before_document_order():
    chunks = [
        RankedChunk(
            "late", {"source": "a", "page": 2, "section_id": "s2", "chunk_index": 2}, 0.95
        ),
        RankedChunk(
            "early", {"source": "a", "page": 0, "section_id": "s0", "chunk_index": 0}, 0.80
        ),
        RankedChunk(
            "sibling", {"source": "a", "page": 2, "section_id": "s2", "chunk_index": 3}, 0.70
        ),
    ]
    selected = pipeline.group_and_rank_chunks(chunks, top_k=2)
    assert [chunk.text for chunk in selected] == ["late", "sibling"]
    ordered = sorted(selected, key=pipeline._document_order)
    assert [chunk.text for chunk in ordered] == ["late", "sibling"]


def test_hierarchy_falls_back_to_page_grouping():
    chunks = [
        RankedChunk("p1b", {"source": "a", "page": 1, "chunk_index": 2}, 0.8),
        RankedChunk("p1a", {"source": "a", "page": 1, "chunk_index": 1}, 0.7),
        RankedChunk("p0", {"source": "a", "page": 0, "chunk_index": 0}, 0.6),
    ]
    selected = pipeline.group_and_rank_chunks(chunks, top_k=2)
    assert {chunk.text for chunk in selected} == {"p1a", "p1b"}
