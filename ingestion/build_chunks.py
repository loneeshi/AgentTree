import json
from pathlib import Path
from AgentTree.config.settings import settings

def chunk_pages(parsed_dir=None, out_dir=None, chunk_size=None, overlap=None):
    parsed_dir = parsed_dir or settings.paths.PARSED_DOC_DIR
    out_dir = out_dir or settings.paths.CHUNK_DIR
    chunk_size = chunk_size or settings.vector.chunk_size
    overlap = overlap or settings.vector.chunk_overlap
    Path(out_dir).mkdir(parents=True, exist_ok=True)

    manifest_path = Path(parsed_dir) / "manifest.json"
    manifest = json.loads(Path(manifest_path).read_text(encoding="utf-8"))

    chunk_records = []
    for doc_meta in manifest:
        doc_json = json.loads(Path(parsed_dir, f"{doc_meta['doc_id']}.json").read_text(encoding="utf-8"))
        joined = "\n".join([p["text"] for p in doc_json["pages"]])
        idx = 0
        while idx < len(joined):
            end = min(idx + chunk_size, len(joined))
            text_chunk = joined[idx:end]
            chunk_id = f"{doc_meta['doc_id']}_{idx}_{end}"
            chunk_records.append({
                "chunk_id": chunk_id,
                "doc_id": doc_meta['doc_id'],
                "text": text_chunk,
                "start": idx,
                "end": end
            })
            idx = end - overlap

    out_file = Path(out_dir) / "chunks.jsonl"
    with open(out_file, "w", encoding="utf-8") as f:
        for rec in chunk_records:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    print(f"Created {len(chunk_records)} chunks -> {out_file}")

if __name__ == "__main__":
    chunk_pages()