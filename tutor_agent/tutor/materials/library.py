"""Local learning-material ingestion and retrieval.

* Text is extracted locally (PyMuPDF for PDF; .txt/.md read directly).
* Page numbers are preserved per chunk so citations can be checked.
* Extraction results are cached in SQLite keyed by SHA-256 (re-adding the
  same file is instant).
* Scanned PDFs use OCR only if Tesseract is installed; otherwise the user is told.
* Retrieval uses SQLite FTS5 (BM25) - small, fast, and fully offline.
* Document text is treated as untrusted data by the prompt layer.
"""

from __future__ import annotations

import hashlib
import logging
import re
import shutil
from dataclasses import dataclass
from pathlib import Path

from tutor.app_paths import unique_path
from tutor.domain import new_id
from tutor.storage.db import Database

log = logging.getLogger(__name__)

CHUNK_CHARS = 1200
MAX_FILE_MB = 100
SUPPORTED = {".pdf", ".txt", ".md"}
_STOP = set("""a an the and or of to in on for with is are was be by as at it this that from how what why which
can do does i you we me my explain understand please about into than then there their""".split())


@dataclass
class IngestResult:
    material_id: str
    filename: str
    pages: int
    chunks: int
    status: str        # ok | partial | failed | duplicate
    note: str


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def chunk_text(page_texts: list[tuple[int, str]], size: int = CHUNK_CHARS) -> list[tuple[int, str]]:
    chunks: list[tuple[int, str]] = []
    for page, text in page_texts:
        text = re.sub(r"[ \t]+", " ", text).strip()
        if not text:
            continue
        paras = re.split(r"\n\s*\n", text)
        buf = ""
        for p in paras:
            if len(buf) + len(p) > size and buf:
                chunks.append((page, buf.strip()))
                buf = ""
            while len(p) > size:
                chunks.append((page, p[:size]))
                p = p[size:]
            buf += p + "\n\n"
        if buf.strip():
            chunks.append((page, buf.strip()))
    return chunks


def ocr_available() -> bool:
    try:
        import pymupdf
        return bool(pymupdf.get_tessdata())
    except Exception:
        return False


def extract_pdf(path: Path) -> tuple[list[tuple[int, str]], int, str]:
    import pymupdf

    notes = []
    pages: list[tuple[int, str]] = []
    empty = 0
    with pymupdf.open(path) as doc:
        if doc.needs_pass:
            raise ValueError("The PDF is password-protected.")
        can_ocr = ocr_available()
        for i, page in enumerate(doc, start=1):
            text = page.get_text("text") or ""
            if len(text.strip()) < 20 and can_ocr:
                try:
                    tp = page.get_textpage_ocr(full=True)
                    text = page.get_text("text", textpage=tp)
                except Exception:
                    pass
            if len(text.strip()) < 20:
                empty += 1
            pages.append((i, text))
        n = len(doc)
    if empty:
        if can_ocr:
            notes.append(f"{empty} page(s) contained no readable text even after OCR.")
        else:
            notes.append(f"{empty} page(s) have no text layer (scanned?). Install Tesseract OCR to read them.")
    return pages, n, " ".join(notes)


class MaterialLibrary:
    def __init__(self, db: Database, folder: Path):
        self.db = db
        self.folder = Path(folder)
        self.folder.mkdir(parents=True, exist_ok=True)

    def ingest(self, source: Path, subject: str = "") -> IngestResult:
        source = Path(source)
        if source.suffix.lower() not in SUPPORTED:
            raise ValueError(f"Unsupported file type {source.suffix}. Supported: PDF, TXT, MD.")
        if source.stat().st_size > MAX_FILE_MB * 1024 * 1024:
            raise ValueError(f"File is larger than {MAX_FILE_MB} MB.")
        sha = _sha256(source)
        existing = self.db.material_by_hash(sha)
        if existing:
            return IngestResult(existing["id"], existing["filename"], existing["pages"], 0, "duplicate",
                                "This file was already added (cached extraction reused).")
        # Copy into the app folder so the original may move; never overwrite existing files.
        dest = unique_path(self.folder / source.name)
        shutil.copy2(source, dest)
        try:
            if source.suffix.lower() == ".pdf":
                page_texts, n_pages, note = extract_pdf(dest)
            else:
                page_texts, n_pages, note = [(1, dest.read_text(encoding="utf-8", errors="replace"))], 1, ""
        except Exception as exc:
            dest.unlink(missing_ok=True)
            raise ValueError(f"Could not read the file: {exc}") from exc
        chunks = chunk_text(page_texts)
        status = "ok" if chunks and not note else ("partial" if chunks else "failed")
        if not chunks:
            note = (note + " No text could be extracted.").strip()
        mid = new_id("mat_")
        self.db.add_material(mid, source.name, str(dest), sha, subject, n_pages, status, note, chunks)
        log.info("Ingested material: %d pages, %d chunks, status %s", n_pages, len(chunks), status)
        return IngestResult(mid, source.name, n_pages, len(chunks), status, note)

    def delete(self, material_id: str) -> None:
        row = self.db.delete_material(material_id)
        if row and row["path"]:
            p = Path(row["path"])
            if p.is_file() and self.folder in p.parents:
                p.unlink(missing_ok=True)

    def list(self):
        return self.db.list_materials()

    def search(self, query: str, subject: str | None = None, limit: int = 3, max_chars: int = 900) -> list[dict]:
        words = [w for w in re.findall(r"[A-Za-zÀ-ž0-9]{3,}", query.lower()) if w not in _STOP][:12]
        if not words:
            return []
        fts = " OR ".join(f'"{w}"' for w in words)
        rows = self.db.search_chunks(fts, subject, limit)
        return [{"filename": r["filename"], "page": r["page"], "text": r["text"][:max_chars]} for r in rows]
