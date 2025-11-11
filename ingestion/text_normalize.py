import os
import re
import unicodedata
from typing import List

_DEFAULT_EXCLUDE_PATTERNS = [
    r"仅供.*内部使用",
    r"僅供.*內部使用",
    r"内部资料",
    r"內部資料",
    r"保密(文件|資料)?",
    r"Confidential",
    r"For Internal Use Only",
]

_compiled_patterns: List[re.Pattern] = []


def _compile_patterns() -> List[re.Pattern]:
    global _compiled_patterns
    if _compiled_patterns:
        return _compiled_patterns
    extra = os.getenv("EXCLUDE_PATTERNS", "").strip()
    patterns = list(_DEFAULT_EXCLUDE_PATTERNS)
    if extra:
        # comma-separated regexes
        patterns.extend([p.strip() for p in extra.split(",") if p.strip()])
    _compiled_patterns = [re.compile(p, re.IGNORECASE) for p in patterns]
    return _compiled_patterns


def _strip_controls(text: str) -> str:
    # remove BOM and control chars except \n
    text = text.replace("\ufeff", "")
    return "".join(ch for ch in text if (ch == "\n" or (ord(ch) >= 32 and ch != "\x7f")))


def _to_simplified(text: str) -> str:
    if os.getenv("ENABLE_ZH_SIMPLIFY", "0") not in ("1", "true", "TRUE", "yes", "Yes"):
        return text
    try:
        from opencc import OpenCC  # type: ignore
        cc = OpenCC("t2s")
        return cc.convert(text)
    except Exception:
        # OpenCC not available; return original text
        return text


def normalize_text(text: str) -> str:
    # Unicode normalize
    t = unicodedata.normalize("NFKC", text or "")
    t = _strip_controls(t)
    # Remove configured disclaimers / banners
    for pat in _compile_patterns():
        t = pat.sub(" ", t)
    # Convert Traditional -> Simplified if enabled
    t = _to_simplified(t)
    # Collapse excessive whitespace while preserving single newlines
    # First, normalize all whitespace to spaces/newlines
    t = re.sub(r"[\t\r\f]+", " ", t)
    # Collapse 3+ newlines to two
    t = re.sub(r"\n{3,}", "\n\n", t)
    # Within lines, collapse spaces
    t = "\n".join(re.sub(r"\s{2,}", " ", line).strip() for line in t.splitlines())
    # Final trim
    t = t.strip()
    return t
