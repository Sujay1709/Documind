"""High-level RAG orchestration tying retrieval, re-ranking and generation together."""

from __future__ import annotations

import logging
from collections import defaultdict
from collections.abc import Iterator
from dataclasses import dataclass, field

from . import vectorstore
from .config import Settings, get_settings
from .reranker import RankedChunk, rerank

logger = logging.getLogger(__name__)


@dataclass
class RetrievalResult:
    """The context assembled for a question, plus the chunks it came from."""

    context: str
    chunks: list[RankedChunk] = field(default_factory=list)

    @property
    def is_empty(self) -> bool:
        return not self.chunks


def retrieve(
    question: str,
    source: str | None = None,
    settings: Settings | None = None,
) -> RetrievalResult:
    """Retrieve candidate chunks for ``question`` and re-rank them.

    Returns the concatenated context string (fed to the LLM) and the ranked
    chunks (used for citations in the UI). When ``source`` is set, retrieval is
    restricted to that document.
    """
    settings = settings or get_settings()
    results = vectorstore.query(
        question, n_results=settings.n_results, source=source, settings=settings
    )

    documents = (results.get("documents") or [[]])[0]
    metadatas = (results.get("metadatas") or [[]])[0]
    if not documents:
        return RetrievalResult(context="", chunks=[])

    ranked = rerank(
        question,
        documents=documents,
        metadatas=metadatas,
        # Rank the complete candidate pool before the hierarchy chooses the
        # best pages/sections. Otherwise a relevant sibling chunk can be
        # discarded before its page has a chance to compete.
        top_k=len(documents),
    )
    selected = group_and_rank_chunks(ranked, top_k=settings.top_k_rerank)
    # Selection is relevance- and hierarchy-based; presentation is always
    # document order so adjacent passages read naturally to the model.
    ordered = sorted(selected, key=_document_order)
    context = "\n\n".join(chunk.text for chunk in ordered)
    return RetrievalResult(context=context, chunks=ordered)


def group_and_rank_chunks(
    chunks: list[RankedChunk],
    top_k: int,
) -> list[RankedChunk]:
    """Select relevant chunks by page/section, with stable document ordering.

    Chroma returns independent chunks.  This small PageIndex-style second
    stage lets a page or section compete as a unit (using its best chunk
    score), then fills the context from the strongest groups.  Existing
    metadata remains authoritative; missing hierarchy fields safely fall back
    to page and chunk position.
    """
    if not chunks or top_k <= 0:
        return []

    groups: dict[tuple, list[RankedChunk]] = defaultdict(list)
    for chunk in chunks:
        metadata = chunk.metadata or {}
        groups[_hierarchy_key(metadata)].append(chunk)

    ranked_groups = sorted(
        groups.values(),
        key=lambda group: (
            -max(item.score for item in group),
            _document_order(min(group, key=_document_order)),
        ),
    )
    selected: list[RankedChunk] = []
    for group in ranked_groups:
        selected.extend(sorted(group, key=lambda item: (-item.score, _document_order(item))))
        if len(selected) >= top_k:
            break
    return selected[:top_k]


def _hierarchy_key(metadata: dict) -> tuple:
    """Return a document/source-aware page/section grouping key."""
    page = metadata.get("page")
    page_key = page if isinstance(page, int) else 0
    section = metadata.get("section_id") or metadata.get("section") or metadata.get(
        "section_title"
    )
    return (metadata.get("source", "unknown"), page_key, section or f"page-{page_key}")


def _document_order(chunk: RankedChunk) -> tuple[str, int, int, int]:
    """Sort key placing a chunk at its natural position in the source document."""
    meta = chunk.metadata or {}
    page = meta.get("page")
    section_index = meta.get("section_index")
    index = meta.get("chunk_index")
    # Source names are useful for separating complete indexed documents, but
    # should not impose an order on lightweight/test metadata that has no
    # positional fields.
    source_value = meta.get("source")
    source = source_value if isinstance(source_value, str) and (
        isinstance(page, int) or isinstance(index, int)
    ) else ""
    return (
        source if isinstance(source, str) else "",
        page if isinstance(page, int) else 0,
        section_index if isinstance(section_index, int) else 0,
        index if isinstance(index, int) else 0,
    )


def answer(
    question: str,
    history: list[dict] | None = None,
    source: str | None = None,
    settings: Settings | None = None,
) -> tuple[Iterator[str], RetrievalResult]:
    """Run the full RAG pipeline.

    Returns a streaming token iterator and the retrieval result so the caller
    can display both the answer and its sources. When ``source`` is set, the
    answer is grounded only in that document.
    """
    from .llm import stream_answer  # local import keeps ollama optional for tests

    retrieval = retrieve(question, source=source, settings=settings)
    stream = stream_answer(retrieval.context, question, history=history)
    return stream, retrieval
