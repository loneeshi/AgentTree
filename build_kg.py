import os
import json
import spacy
from tqdm import tqdm

nlp = spacy.load("en_core_web_sm")

IGNORE_SUBJECTS = {"you", "it", "they", "this", "that", "he", "she", "we", "I", "which", "who"}
IGNORE_RELATIONS = {"be", "have", "do"}

def extract_triples_from_text(text):
    """更智能的基于依存关系的三元组抽取"""
    doc = nlp(text)
    triples = []
    for sent in doc.sents:
        subject, relation, obj = "", "", ""
        for token in sent:
            # 找主语
            if token.dep_ in ("nsubj", "nsubjpass") and token.text.lower() not in IGNORE_SUBJECTS:
                subject = " ".join([t.text for t in token.subtree])
            # 动词（关系）
            elif token.pos_ == "VERB" and token.lemma_ not in IGNORE_RELATIONS:
                relation = token.lemma_
            # 宾语
            elif token.dep_ in ("dobj", "pobj") and token.text.lower() not in IGNORE_SUBJECTS:
                obj = " ".join([t.text for t in token.subtree])
        if subject and obj and relation:
            triples.append({
                "subject": subject.strip(),
                "relation": relation.strip(),
                "object": obj.strip()
            })
    return triples

def build_knowledge_from_txt(txt_path):
    with open(txt_path, "r", encoding="utf-8") as f:
        text = f.read()
    return extract_triples_from_text(text)

def main():
    input_dir = "texts"
    output_dir = "output"
    os.makedirs(output_dir, exist_ok=True)

    all_data = {}
    for filename in tqdm(os.listdir(input_dir)):
        if filename.endswith(".txt"):
            path = os.path.join(input_dir, filename)
            triples = build_knowledge_from_txt(path)
            all_data[filename] = triples
            print(f"[+] {filename} -> {len(triples)} triples extracted.")

    output_path = os.path.join(output_dir, "knowledge.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(all_data, f, indent=2, ensure_ascii=False)
    print(f"[✅] Knowledge graph saved to {output_path}")

if __name__ == "__main__":
    main()
