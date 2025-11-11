"""Plain text / Markdown ingestion for AgentTree.

This ingestor scans a directory for .md and .txt files, converts each file
into a simple document JSON with a single page, and writes a manifest.json.

It mirrors the JSON structure produced by pdf_ingest.py so the downstream
chunking and indexing steps can be reused unchanged.
"""

import os
import re
import uuid
import json
from pathlib import Path
from typing import Dict, List, Iterable

from AgentTree.config.settings import settings
from AgentTree.ingestion.text_normalize import normalize_text


def clean_text(text: str) -> str:
    return normalize_text(text)


def iter_text_files(root: str, exts: Iterable[str] = (".md", ".txt")) -> Iterable[Path]:
    rootp = Path(root)
    for p in rootp.rglob("*"):
        if p.is_file() and p.suffix.lower() in exts:
            yield p


def read_file_utf8(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        # fallback with errors replaced
        return path.read_text(encoding="utf-8", errors="replace")


def ingest_text_directory(input_dir: str = None, output_dir: str = None):
    input_dir = input_dir or settings.paths.RAW_DOC_DIR
    output_dir = output_dir or settings.paths.PARSED_DOC_DIR
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    files = list(iter_text_files(input_dir))
    if not files:
        print(f"[warn] No .md/.txt files found under '{input_dir}'. Manifest will be empty.")

    parsed_manifest: List[Dict] = []
    for fp in files:
        raw = read_file_utf8(fp)
        text = clean_text(raw)
        pages = [
            {
                "page_number": 1,
                "text": text,
                "source_file": os.path.relpath(str(fp), start=input_dir),
            }
        ]
        doc_id = str(uuid.uuid4())
        out_file = Path(output_dir) / f"{doc_id}.json"
        with open(out_file, "w", encoding="utf-8") as f:
            json.dump({"doc_id": doc_id, "pages": pages}, f, ensure_ascii=False, indent=2)
        parsed_manifest.append({"doc_id": doc_id, "file": str(fp), "pages": len(pages)})

    manifest_path = Path(output_dir) / "manifest.json"
    with open(manifest_path, "w", encoding="utf-8") as mf:
        json.dump(parsed_manifest, mf, ensure_ascii=False, indent=2)
    print(f"Ingested {len(parsed_manifest)} text files -> {manifest_path}")


if __name__ == "__main__":
    ingest_text_directory()
