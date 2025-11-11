import json
from pathlib import Path
from typing import List, Dict
from AgentTree.config.settings import settings

try:
    import camelot
    CAM_AVAILABLE = True
except ImportError:
    CAM_AVAILABLE = False

def extract_tables_from_pdf(pdf_path: str) -> List[Dict]:
    if not CAM_AVAILABLE:
        return []
    tables = camelot.read_pdf(pdf_path, pages="all")
    results = []
    for idx, t in enumerate(tables):
        df = t.df
        rows = df.values.tolist()
        results.append({
            "table_id": f"{Path(pdf_path).stem}_t{idx}",
            "header": rows[0],
            "rows": rows[1:]
        })
    return results

def run_table_pipeline(raw_dir=None, out_dir=None):
    raw_dir = raw_dir or settings.paths.RAW_DOC_DIR
    out_dir = out_dir or settings.paths.TABLE_DIR
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    all_tables = []
    for pdf in Path(raw_dir).glob("**/*.pdf"):
        tables = extract_tables_from_pdf(str(pdf))
        for tb in tables:
            tb["source_file"] = pdf.name
        all_tables.extend(tables)
    out = Path(out_dir) / "tables.json"
    with open(out, "w", encoding="utf-8") as f:
        json.dump(all_tables, f, ensure_ascii=False, indent=2)
    print(f"Extracted {len(all_tables)} tables -> {out}")

if __name__ == "__main__":
    run_table_pipeline()