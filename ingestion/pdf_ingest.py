import os
import re
import uuid
from pathlib import Path
from typing import Dict, List, Tuple
import json
import pdfplumber
from AgentTree.config.settings import settings
from AgentTree.ingestion.text_normalize import normalize_text
from typing import Optional

"""PDF ingestion with optional garbled-page detection and OCR fallback.

Environment flags (all optional):
    ENABLE_ZH_SIMPLIFY=1            -> Traditional -> Simplified in normalize_text
    EXCLUDE_PATTERNS="pat1,pat2"    -> Regex patterns removed from text
    DETECT_GARBLED=1                -> Run heuristics on raw extracted text
    TRIGGER_OCR_ON_GARBLED=1        -> If garbled heuristics trigger, run OCR pipeline
    OCR_ENGINE=paddle|tesseract     -> Choose OCR backend (default tesseract)
    OCR_LANG=chi_sim+eng            -> Language(s) passed to OCR engine
    OCR_MIN_GAIN=50                 -> Minimum additional characters to accept OCR result
    OCR_DPI=200                     -> Rendering DPI for PDF page image

Heuristic signals include embedded font markers (cid:###), very short length, or low informative ratio.
OCR fallback uses pdfplumber page rendering -> PIL image -> backend OCR. Result replaces raw text only if
gain >= OCR_MIN_GAIN (difference in cleaned char length) OR raw was empty.
"""

PADDLE_AVAILABLE = False
TESSERACT_AVAILABLE = False
_paddle_ocr = None  # lazy holder

# PaddleOCR (optional, heavier GPU/CPU dependency)
try:  # pragma: no cover - optional import
    from paddleocr import PaddleOCR  # type: ignore
    PADDLE_AVAILABLE = True
except Exception:  # noqa: E722
    PADDLE_AVAILABLE = False

# pytesseract (lightweight wrapper; requires external tesseract binary installed via brew)
try:  # pragma: no cover - optional import
    import pytesseract  # type: ignore
    from PIL import Image, ImageOps, ImageFilter  # type: ignore
    TESSERACT_AVAILABLE = True
except Exception:  # noqa: E722
    TESSERACT_AVAILABLE = False

GARBLED_CID_PATTERN = re.compile(r"\(cid:\d+\)")

def clean_text(text: str) -> str:
    return normalize_text(text)

def _garbled_heuristics(text: str) -> Tuple[bool, str]:
    """Return (is_garbled, reason).
    Heuristics:
      - cid markers typical of failed embedded font extraction
      - very high ratio of punctuation/symbols vs CJK/latin
      - extremely short but non-empty (< 20 chars)
    """
    stripped = text.strip()
    if not stripped:
        return True, "empty"
    if GARBLED_CID_PATTERN.search(text):
        return True, "cid_markers"
    if len(stripped) < 20:
        return True, "too_short"
    # symbol ratio
    total = len(stripped)
    cjk = sum(1 for ch in stripped if '\u4e00' <= ch <= '\u9fff')
    latin = sum(1 for ch in stripped if ch.isalpha())
    digits = sum(1 for ch in stripped if ch.isdigit())
    informative = cjk + latin + digits
    if informative / max(total, 1) < 0.3:  # mostly symbols/spaces
        return True, "low_informative_ratio"
    return False, "ok"

def _ensure_paddle() -> Optional["PaddleOCR"]:
    global _paddle_ocr
    if _paddle_ocr is not None:
        return _paddle_ocr
    if not PADDLE_AVAILABLE:
        return None
    lang = os.getenv("OCR_LANG", "ch")  # PaddleOCR language code (e.g., 'ch', 'en')
    try:
        _paddle_ocr = PaddleOCR(use_angle_cls=True, lang=lang)  # type: ignore
    except Exception:
        _paddle_ocr = None
    return _paddle_ocr

def _run_ocr_paddle(image) -> str:
    ocr = _ensure_paddle()
    if not ocr:
        return ""
    try:
        result = ocr.ocr(image, cls=True)
        # result is list of [ [ [box], (text, prob) ], ... ]
        texts = []
        for line in result:
            for det in line:
                if isinstance(det, list) and len(det) == 2:
                    txt = det[1][0]
                else:
                    # paddleocr sometimes returns nested structures
                    try:
                        txt = det[1][0]
                    except Exception:
                        txt = ""
                if txt:
                    texts.append(txt)
        return "\n".join(texts)
    except Exception:
        return ""

def _run_ocr_tesseract(image) -> str:
    if not TESSERACT_AVAILABLE:
        return ""
    lang = os.getenv("OCR_LANG", "chi_sim+eng")
    try:
        # Allow custom binary path if not in PATH
        tess_cmd = os.getenv("TESSERACT_CMD")
        if tess_cmd:
            pytesseract.pytesseract.tesseract_cmd = tess_cmd  # type: ignore
        config = os.getenv("OCR_CONFIG", "")
        if config:
            return pytesseract.image_to_string(image, lang=lang, config=config)  # type: ignore
        return pytesseract.image_to_string(image, lang=lang)  # type: ignore
    except Exception:
        return ""

def _maybe_ocr(page, raw: str, reason: str, engine: str) -> Tuple[str, bool, str]:
    """Attempt OCR; return (text, used, ocr_engine).
    Acceptance logic (in order):
      1. If OCR produced no text -> reject.
      2. If ALWAYS_REPLACE_ON_CID=1 and reason == cid_markers -> accept.
      3. If raw is empty -> accept.
      4. If reason in {cid_markers, low_informative_ratio, too_short, empty} and OCR has >=1 CJK char -> accept.
      5. Else if length gain >= OCR_MIN_GAIN -> accept.
      6. Else reject.
    """
    dpi = int(os.getenv("OCR_DPI", "200"))
    debug = os.getenv("DEBUG_OCR", "0") == "1"
    try:
        page_render = page.to_image(resolution=dpi)
        if hasattr(page_render, "image") and page_render.image is not None:
            page_img = page_render.image  # pdfplumber <=0.9 legacy attr
        else:
            page_img = page_render.original  # pdfplumber 0.10+ attr
    except Exception as e:
        if debug:
            print(f"[ocr-debug] render_failed dpi={dpi} err={e}")
        return raw, False, "render_failed"
    # Optional pre-processing to combat watermark/low contrast text
    if os.getenv("OCR_PREPROCESS", "0") == "1":
        try:
            gray = ImageOps.grayscale(page_img)
            # light de-noise
            gray = gray.filter(ImageFilter.MedianFilter(size=3))
            # threshold
            thresh = int(os.getenv("OCR_THRESH", "170"))
            bw = gray.point(lambda x: 255 if x > thresh else 0, mode='1')
            page_img = bw
            if debug:
                print(f"[ocr-debug] preprocess applied: grayscale+median+threshold={thresh}")
        except Exception as pe:
            if debug:
                print(f"[ocr-debug] preprocess_failed err={pe}")
    if engine == "paddle":
        ocr_text = _run_ocr_paddle(page_img)
        ocr_engine_used = "paddle"
    else:
        ocr_text = _run_ocr_tesseract(page_img)
        ocr_engine_used = "tesseract"
    ocr_text = (ocr_text or "").strip()
    if not ocr_text:
        if debug:
            print(f"[ocr-debug] empty_ocr_result engine={ocr_engine_used}")
        return raw, False, ocr_engine_used
    # Stats
    raw_len = len(raw)
    ocr_len = len(ocr_text)
    cjk_count = sum(1 for ch in ocr_text if '\u4e00' <= ch <= '\u9fff')
    informative_raw = sum(1 for ch in raw if (ch.isdigit() or ch.isalpha() or ('\u4e00' <= ch <= '\u9fff')))
    informative_ratio_raw = informative_raw / max(len(raw.strip()) or 1, 1)
    gain_threshold = int(os.getenv("OCR_MIN_GAIN", "50"))
    always_replace_on_cid = os.getenv("ALWAYS_REPLACE_ON_CID", "0") == "1"
    accept = False
    if always_replace_on_cid and reason == "cid_markers":
        accept = True
    elif not raw.strip():  # original empty
        accept = True
    elif reason in {"cid_markers", "low_informative_ratio", "too_short", "empty"} and cjk_count >= 1:
        accept = True
    elif (ocr_len - raw_len) >= gain_threshold:
        accept = True
    if debug:
        print(
            f"[ocr-debug] decision engine={ocr_engine_used} reason={reason} raw_len={raw_len} ocr_len={ocr_len} cjk={cjk_count} inf_ratio_raw={informative_ratio_raw:.2f} gain={ocr_len - raw_len} threshold={gain_threshold} accept={accept}"
        )
    if accept:
        return ocr_text, True, ocr_engine_used
    return raw, False, ocr_engine_used

def extract_pdf(path: str) -> List[Dict]:
    pages = []
    detect_garbled = os.getenv("DETECT_GARBLED", "0") == "1"
    trigger_ocr = os.getenv("TRIGGER_OCR_ON_GARBLED", "0") == "1"
    engine = os.getenv("OCR_ENGINE", "tesseract").lower()
    force_ocr = os.getenv("FORCE_OCR", "0") == "1"
    debug_ocr = os.getenv("DEBUG_OCR", "0") == "1"
    with pdfplumber.open(path) as pdf:
        for i, page in enumerate(pdf.pages):
            raw = page.extract_text() or ""
            cleaned = clean_text(raw)
            if detect_garbled:
                is_garbled, reason = _garbled_heuristics(cleaned)
            else:
                is_garbled, reason = False, "disabled"
            ocr_used = False
            ocr_engine_used = None
            final_text = cleaned
            should_try_ocr = (is_garbled and trigger_ocr) or force_ocr
            if debug_ocr:
                print(f"[ocr-debug] page={i+1} garbled={is_garbled} reason={reason} force={force_ocr} trigger={trigger_ocr} engine={engine}")
            if should_try_ocr:
                if engine == "paddle" and PADDLE_AVAILABLE:
                    ocr_result, ocr_used, ocr_engine_used = _maybe_ocr(page, raw, reason, "paddle")
                elif engine == "tesseract" and TESSERACT_AVAILABLE:
                    ocr_result, ocr_used, ocr_engine_used = _maybe_ocr(page, raw, reason, "tesseract")
                else:
                    if debug_ocr:
                        print(f"[ocr-debug] engine {engine} not available; paddle={PADDLE_AVAILABLE} tesseract={TESSERACT_AVAILABLE}")
                    ocr_result = final_text
                    ocr_used = False
                    ocr_engine_used = None
                if ocr_used:
                    cleaned = clean_text(ocr_result)
                    ocr_garbled, _ = _garbled_heuristics(cleaned)
                    if not ocr_garbled or reason == "empty":
                        final_text = cleaned
                    else:
                        if debug_ocr:
                            print(f"[ocr-debug] ocr_result_still_garbled keep_raw reason={reason}")
                else:
                    final_text = cleaned
            else:
                final_text = cleaned
            pages.append({
                "page_number": i + 1,
                "text": clean_text(final_text),
                "source_file": os.path.basename(path),
                "garbled": is_garbled,
                "garbled_reason": reason,
                "ocr_used": ocr_used,
                "ocr_engine": ocr_engine_used
            })
    return pages

def ingest_directory(input_dir: str = None, output_dir: str = None):
    input_dir = input_dir or settings.paths.RAW_DOC_DIR
    output_dir = output_dir or settings.paths.PARSED_DOC_DIR
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    parsed_manifest = []
    pdf_files = list(Path(input_dir).glob("**/*.pdf"))
    if not pdf_files:
        print(f"[warn] No PDF files found under '{input_dir}'. Manifest will be empty.")
    for file in pdf_files:
        pages = extract_pdf(str(file))
        doc_id = str(uuid.uuid4())
        out_file = Path(output_dir) / f"{doc_id}.json"
        with open(out_file, "w", encoding="utf-8") as f:
            json.dump({"doc_id": doc_id, "pages": pages}, f, ensure_ascii=False, indent=2)
        parsed_manifest.append({"doc_id": doc_id, "file": str(file), "pages": len(pages)})

    manifest_path = Path(output_dir) / "manifest.json"
    with open(manifest_path, "w", encoding="utf-8") as mf:
        json.dump(parsed_manifest, mf, ensure_ascii=False, indent=2)
    print(f"Ingested {len(parsed_manifest)} PDFs -> {manifest_path}")

def ingest_single_pdf(pdf_path: str, output_dir: str = None, preview_chars: int = 300):
    """Ingest only one PDF and print a concise preview for manual inspection.
    Adds garbled detection flags if DETECT_GARBLED=1.
    """
    output_dir = output_dir or settings.paths.PARSED_DOC_DIR
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    if not Path(pdf_path).is_file():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")
    pages = extract_pdf(pdf_path)
    doc_id = str(uuid.uuid4())
    out_file = Path(output_dir) / f"{doc_id}.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump({"doc_id": doc_id, "pages": pages}, f, ensure_ascii=False, indent=2)
    print(f"[single] Saved {out_file} with {len(pages)} pages.")
    for p in pages[:5]:  # limit preview to first 5 pages
        txt = p["text"][:preview_chars].replace("\n", " ")
        print(f"Page {p['page_number']} garbled={p['garbled']} reason={p['garbled_reason']} ocr={p['ocr_used']} | {txt[:preview_chars]}")
    return out_file

if __name__ == "__main__":
    target = os.getenv("SINGLE_PDF_PATH")
    if target:
        ingest_single_pdf(target, "/Users/dp/Agent_research/design/AgentTree/data/parsed")
    else:
        ingest_directory()