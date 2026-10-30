"""Load source documents as page-aware, citation-ready evidence chunks."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlsplit

from PyPDF2 import PdfReader


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = REPOSITORY_ROOT / "data"
MANIFEST_PATH = DATA_DIR / "source_manifest.json"
CHUNK_SIZE = 1200
CHUNK_OVERLAP = 160


@dataclass(frozen=True)
class EvidenceChunk:
    """One searchable passage with enough metadata to cite its origin."""

    id: str
    text: str
    source_file: str
    source_title: str
    page: int | None
    source_urls: tuple[str, ...] = ()
    source_date: str | None = None
    score: float = 0.0

    def as_dict(self) -> dict[str, object]:
        return {
            "id": self.id,
            "text": self.text,
            "source_file": self.source_file,
            "source_title": self.source_title,
            "page": self.page,
            "source_urls": list(self.source_urls),
            "source_date": self.source_date,
            "score": self.score,
        }


def _read_manifest(path: Path) -> dict[str, dict[str, str | None]]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return value if isinstance(value, dict) else {}


def _safe_page_urls(page: object) -> tuple[str, ...]:
    urls: set[str] = set()
    for annotation in page.get("/Annots", []) or []:  # type: ignore[attr-defined]
        try:
            item = annotation.get_object()
            action = item.get("/A")
            url = action.get("/URI") if action else None
            parsed = urlsplit(url) if isinstance(url, str) else None
            if parsed and parsed.scheme in {"http", "https"} and parsed.netloc:
                urls.add(url)
        except (AttributeError, TypeError, ValueError):
            continue
    return tuple(sorted(urls))


def _split_text(text: str, size: int, overlap: int) -> list[str]:
    text = re.sub(r"\s+", " ", text).strip()
    if not text:
        return []
    chunks: list[str] = []
    start = 0
    while start < len(text):
        end = min(start + size, len(text))
        if end < len(text):
            boundary = text.rfind(" ", start + size // 2, end)
            if boundary > start:
                end = boundary
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end >= len(text):
            break
        start = max(start + 1, end - overlap)
    return chunks


def load_evidence_chunks(
    data_dir: Path | str = DATA_DIR,
    *,
    manifest_path: Path | str | None = None,
    chunk_size: int = CHUNK_SIZE,
    chunk_overlap: int = CHUNK_OVERLAP,
) -> list[EvidenceChunk]:
    """Extract PDF pages and text files without loading the LFS FAISS pickle."""
    root = Path(data_dir)
    manifest = _read_manifest(Path(manifest_path) if manifest_path else root / "source_manifest.json")
    results: list[EvidenceChunk] = []

    for path in sorted(root.iterdir()) if root.exists() else []:
        if not path.is_file() or path.name == "source_manifest.json":
            continue
        details = manifest.get(path.name, {})
        title = details.get("title") or path.stem.replace("_", " ")
        source_date = details.get("source_date")
        pages: list[tuple[int | None, str, tuple[str, ...]]] = []

        if path.suffix.lower() == ".pdf":
            try:
                reader = PdfReader(str(path))
                for page_number, page in enumerate(reader.pages, start=1):
                    pages.append((page_number, page.extract_text() or "", _safe_page_urls(page)))
            except Exception:
                # Keep a bad or scanned source from preventing the rest of the library loading.
                continue
        elif path.suffix.lower() in {".txt", ".md"}:
            try:
                content = path.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            # Ignore tiny placeholder files; they contain no useful evidence.
            if len(content.strip()) >= 80:
                pages.append((None, content, ()))
        else:
            continue

        for page_number, text, urls in pages:
            for chunk_number, chunk in enumerate(_split_text(text, chunk_size, chunk_overlap), start=1):
                page_suffix = f"p{page_number}" if page_number is not None else "text"
                chunk_id = f"{path.name}:{page_suffix}:c{chunk_number}"
                results.append(
                    EvidenceChunk(
                        id=chunk_id,
                        text=chunk,
                        source_file=f"data/{path.name}",
                        source_title=title,
                        page=page_number,
                        source_urls=urls,
                        source_date=source_date,
                    )
                )
    return results


def chunk_pdfs(data_dir: Path | str = DATA_DIR) -> list[str]:
    """Backward-compatible text-only helper used by the old FAISS builder."""
    return [item.text for item in load_evidence_chunks(data_dir)]


if __name__ == "__main__":
    chunks = load_evidence_chunks()
    print(f"Loaded {len(chunks)} evidence chunks from {DATA_DIR}.")
