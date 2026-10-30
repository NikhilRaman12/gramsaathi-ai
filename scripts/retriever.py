"""Deterministic lexical retrieval over the repository's local source corpus."""

from __future__ import annotations

import math
import re
from collections import Counter
from dataclasses import replace
from pathlib import Path
from typing import Any

from scripts.chunk_pdfs import DATA_DIR, EvidenceChunk, load_evidence_chunks


_TOKEN = re.compile(r"[^\W_]+", re.UNICODE)
_STOP_WORDS = {
    "a", "about", "after", "all", "also", "am", "an", "and", "any", "are", "as", "at",
    "be", "because", "been", "before", "being", "but", "by", "can", "could", "did", "do",
    "does", "for", "from", "get", "have", "how", "i", "if", "in", "is", "it", "my", "of",
    "on", "or", "our", "please", "should", "so", "that", "the", "their", "them", "there",
    "this", "to", "was", "we", "what", "when", "where", "which", "who", "why", "with", "you",
}


def _tokens(text: str) -> list[str]:
    return [word.casefold() for word in _TOKEN.findall(text) if word.casefold() not in _STOP_WORDS]


class Retriever:
    """Search PDF/text chunks with BM25 and keep page-level source metadata.

    The built-in application path is local and lexical. An explicitly injected
    vector store can still be used by callers with a verified embedding setup.
    The checked-in FAISS pickle is unavailable in this checkout, and no fake
    embedding is used to claim semantic retrieval.
    """

    def __init__(
        self,
        chunks: list[EvidenceChunk] | None = None,
        *,
        data_dir: Path | str = DATA_DIR,
        vector_store: object | None = None,
    ) -> None:
        # vector_store remains accepted for callers that inject a legacy store;
        # the built-in application path always uses the deterministic corpus.
        self.vector_store = vector_store
        self.chunks = (
            list(chunks)
            if chunks is not None
            else ([] if vector_store is not None else load_evidence_chunks(data_dir))
        )
        self._doc_tokens = [_tokens(item.text) for item in self.chunks]
        self._doc_lengths = [len(tokens) for tokens in self._doc_tokens]
        self._average_length = (
            sum(self._doc_lengths) / len(self._doc_lengths) if self._doc_lengths else 0.0
        )
        self._document_frequency: Counter[str] = Counter(
            token for tokens in self._doc_tokens for token in set(tokens)
        )

    def search(self, question: str, k: int = 5) -> list[EvidenceChunk]:
        if k <= 0:
            return []
        if self.vector_store is not None:
            results = []
            for index, document in enumerate(self.vector_store.similarity_search(question, k=k), start=1):
                metadata = getattr(document, "metadata", {}) or {}
                source_file = str(metadata.get("source_file") or metadata.get("source") or "Legacy FAISS source")
                raw_urls: Any = metadata.get("source_urls", metadata.get("source_url", ()))
                urls = (raw_urls,) if isinstance(raw_urls, str) and raw_urls else tuple(raw_urls or ())
                page = metadata.get("page")
                try:
                    page = int(page) if page is not None else None
                except (TypeError, ValueError):
                    page = None
                results.append(
                    EvidenceChunk(
                        id=str(metadata.get("id") or f"legacy-faiss:{index}"),
                        text=str(getattr(document, "page_content", document)),
                        source_file=source_file,
                        source_title=str(metadata.get("source_title") or Path(source_file).stem),
                        page=page,
                        source_urls=tuple(str(url) for url in urls),
                        source_date=(str(metadata["source_date"]) if metadata.get("source_date") else None),
                    )
                )
            return results
        query_tokens = _tokens(question)
        if not query_tokens or not self.chunks or k <= 0:
            return []

        terms = Counter(query_tokens)
        total_docs = len(self.chunks)
        k1 = 1.5
        b = 0.75
        scored: list[tuple[float, int]] = []

        for index, tokens in enumerate(self._doc_tokens):
            if not tokens:
                continue
            frequencies = Counter(tokens)
            length = self._doc_lengths[index]
            score = 0.0
            matched_terms = 0
            for term, query_frequency in terms.items():
                frequency = frequencies.get(term, 0)
                if not frequency:
                    continue
                matched_terms += 1
                document_frequency = self._document_frequency[term]
                inverse_frequency = math.log(
                    1.0 + (total_docs - document_frequency + 0.5) / (document_frequency + 0.5)
                )
                denominator = frequency + k1 * (1.0 - b + b * length / max(self._average_length, 1.0))
                query_boost = 1.0 + math.log1p(query_frequency - 1.0) * 0.15
                score += inverse_frequency * frequency * (k1 + 1.0) / denominator * query_boost
            coverage = matched_terms / max(len(terms), 1)
            if score > 0.0 and coverage >= 0.5:
                scored.append((score, index))

        scored.sort(key=lambda item: (-item[0], self.chunks[item[1]].id))
        return [replace(self.chunks[index], score=score) for score, index in scored[:k]]

    def get_context(self, question: str, k: int = 3) -> str:
        """Backward-compatible context formatter for older callers."""
        return "\n\n".join(
            f"[{item.source_file}, page {item.page or 'text'}]\n{item.text}"
            for item in self.search(question, k=k)
        )
