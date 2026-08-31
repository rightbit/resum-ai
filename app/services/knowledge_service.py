"""Knowledge-base loading and simple retrieval.

The professional knowledge base lives entirely in the /data directory as
plain Markdown files so the profile owner can edit their own experience
without touching application code.

This module implements a lightweight document-chunking + keyword scoring
retrieval strategy. It is intentionally simple: the interface
(`KnowledgeService.search`) is designed so a future version could swap in
an embeddings + vector database implementation (e.g. FAISS/pgvector)
without changing how callers use the service.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from app.config import settings


@dataclass
class Chunk:
    """A retrievable piece of the knowledge base."""

    source: str
    heading: str
    text: str

    @property
    def formatted(self) -> str:
        return f"### {self.source} — {self.heading}\n{self.text}".strip()


_WORD_RE = re.compile(r"[a-zA-Z0-9']+")


def _tokenize(text: str) -> list[str]:
    return [w.lower() for w in _WORD_RE.findall(text)]


def _split_into_chunks(source: str, markdown_text: str) -> list[Chunk]:
    """Split a Markdown document into chunks based on headings.

    Each `##`/`###` heading (or the whole document, if there are no
    headings) becomes one chunk. This is a simple stand-in for the more
    sophisticated chunking a RAG pipeline would use.
    """
    lines = markdown_text.splitlines()
    chunks: list[Chunk] = []
    current_heading = source
    current_lines: list[str] = []

    def flush():
        text = "\n".join(current_lines).strip()
        if text:
            chunks.append(Chunk(source=source, heading=current_heading, text=text))

    for line in lines:
        heading_match = re.match(r"^#{1,6}\s+(.*)", line)
        if heading_match:
            flush()
            current_heading = heading_match.group(1).strip()
            current_lines = []
        else:
            current_lines.append(line)
    flush()

    if not chunks:
        text = markdown_text.strip()
        if text:
            chunks.append(Chunk(source=source, heading=source, text=text))

    return chunks


class KnowledgeService:
    """Loads Markdown knowledge-base files and answers retrieval queries."""

    def __init__(self, data_dir: Path | None = None):
        self.data_dir = data_dir or settings.DATA_DIR
        self._chunks: list[Chunk] = []
        self._loaded = False

    def load(self, force: bool = False) -> None:
        """Load (or reload) all Markdown files from the data directory."""
        if self._loaded and not force:
            return
        chunks: list[Chunk] = []
        if self.data_dir.exists():
            for path in sorted(self.data_dir.glob("*.md")):
                text = path.read_text(encoding="utf-8")
                chunks.extend(_split_into_chunks(path.stem, text))
        self._chunks = chunks
        self._loaded = True

    @property
    def chunks(self) -> list[Chunk]:
        self.load()
        return self._chunks

    def all_text(self) -> str:
        """Return the full concatenated knowledge base (for small corpora)."""
        self.load()
        return "\n\n".join(chunk.formatted for chunk in self._chunks)

    def search(self, query: str, top_k: int = 6) -> list[Chunk]:
        """Return the most relevant chunks for a query using keyword overlap.

        This is a placeholder for a future embeddings-based similarity
        search. The public signature (query in, ranked Chunks out) is
        chosen so it can be swapped for a vector-search implementation
        later without touching callers.
        """
        self.load()
        query_tokens = set(_tokenize(query))
        if not query_tokens:
            return self._chunks[:top_k]

        scored: list[tuple[float, Chunk]] = []
        for chunk in self._chunks:
            chunk_tokens = _tokenize(f"{chunk.heading} {chunk.text}")
            if not chunk_tokens:
                continue
            overlap = sum(1 for t in chunk_tokens if t in query_tokens)
            if overlap:
                scored.append((overlap / (len(chunk_tokens) ** 0.5), chunk))

        scored.sort(key=lambda pair: pair[0], reverse=True)
        top = [chunk for _, chunk in scored[:top_k]]

        if not top:
            # Fall back to returning a broad sample so the AI still has
            # something to work with, rather than nothing at all.
            top = self._chunks[:top_k]
        return top

    def build_context(self, query: str, top_k: int = 6) -> str:
        """Build a context string for the AI prompt from relevant chunks."""
        relevant = self.search(query, top_k=top_k)
        return "\n\n".join(chunk.formatted for chunk in relevant)


# Module-level singleton used by the rest of the app.
knowledge_service = KnowledgeService()
