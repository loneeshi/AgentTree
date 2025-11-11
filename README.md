# AgentTree

## PDF Ingestion & OCR

The ingestion entry point is `AgentTree.ingestion.pdf_ingest`. When running from the
repository root (`/Users/dp/Agent_research/design`), you can enable the OCR fallback and
force Tesseract by export-style overrides:

```bash
OCR_ENGINE=tesseract FORCE_OCR=1 TRIGGER_OCR_ON_GARBLED=1 \
python -m AgentTree.ingestion.pdf_ingest
```

Key environment flags:

- `OCR_ENGINE` – choose the OCR backend (`tesseract` or `paddle`).
- `FORCE_OCR` – run OCR for every page (still subject to acceptance heuristics).
- `TRIGGER_OCR_ON_GARBLED` – automatically OCR pages flagged as garbled.
- `DEBUG_OCR=1` – print detailed per-page decision logs when debugging.

By default the module reads PDFs from `AgentTree/tests/AI_database` and writes parsed
artifacts to `AgentTree/data/parsed`, defined in `AgentTree/config/settings.py`. Adjust the
paths there or override via environment variables when needed.

