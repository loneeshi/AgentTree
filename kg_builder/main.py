"""
Knowledge Graph Construction Pipeline
Two-stage approach: Lightweight filtering → LLM extraction → Graph building
"""

import os
import json
import spacy
from tqdm import tqdm
from text_preprocessing import preprocess_document
from language_utils import detect_language
from ner_chinese import extract_chinese_entities
from candidate_filter import filter_candidate_sentences, get_extraction_priority
from llm_extractor import extract_relations_batch
from graph_builder import build_graph_from_triples

# Load spaCy for sentence segmentation
nlp = spacy.load("en_core_web_sm")

def process_document(text: str, use_llm: bool = True, llm_batch_size: int = 10) -> dict:
    """
    Process document to build knowledge graph using two-stage pipeline.
    
    Pipeline:
        1. Text preprocessing (noise removal)
        2. Sentence segmentation
        3. Candidate filtering (80%+ reduction)
        4. LLM extraction (high quality relations)
        5. Graph construction (deduplication, normalization)
    
    Args:
        text: Document text
        use_llm: Whether to use LLM extraction (if False, returns candidates only)
        llm_batch_size: Number of sentences per LLM API call
        
    Returns:
        Dictionary with entities, relations, and statistics
    """
    # Stage 0: Detect language
    language = detect_language(text)
    print(f"[0/5] Detected language: {'Chinese' if language == 'zh' else 'English'}")
    
    # Stage 1: Preprocessing
    print("[1/5] Preprocessing document...")
    cleaned_text = preprocess_document(text)
    
    # Stage 2: Sentence segmentation
    print("[2/5] Segmenting sentences...")
    doc = nlp(cleaned_text)
    sentences = [sent.text.strip() for sent in doc.sents]
    sentences = [s for s in sentences if s and len(s) > 10]
    print(f"  → {len(sentences)} sentences")
    
    # Stage 3: Candidate filtering (reduces ~80% sentences)
    print("[3/5] Filtering candidate sentences...")
    candidates = filter_candidate_sentences(sentences, language)
    print(f"  → {len(candidates)} candidates ({len(candidates)/len(sentences)*100:.1f}%)")
    
    # Prioritize candidates
    prioritized = sorted(
        [(s, get_extraction_priority(s, language)) for s in candidates],
        key=lambda x: x[1],
        reverse=True
    )
    candidate_sentences = [s for s, _ in prioritized]
    
    # Stage 4: LLM extraction
    all_triples = []
    extracted_entities = {}
    
    if use_llm and candidate_sentences:
        print(f"[4/5] Extracting relations via LLM (batch_size={llm_batch_size})...")
        all_triples = extract_relations_batch(
            candidate_sentences,
            language=language,
            batch_size=llm_batch_size
        )
        print(f"  → {len(all_triples)} relation triples extracted")
        
        # Extract entities from all sentences for better coverage
        print("  → Extracting entities...")
        for sent in tqdm(sentences[:500], desc="    Extracting entities"):  # Limit for performance
            entities = extract_chinese_entities(sent) if language == 'zh' else []
            for ent in entities:
                if ent['text'] not in extracted_entities:
                    extracted_entities[ent['text']] = ent['type']
    else:
        print("[4/5] Skipping LLM extraction (use_llm=False)")
    
    # Stage 5: Build knowledge graph
    print("[5/5] Building knowledge graph...")
    kg = build_graph_from_triples(all_triples, extracted_entities)
    
    return {
        "entities": [
            {
                "name": name,
                "type": data["type"],
                "frequency": data["frequency"]
            }
            for name, data in kg.entities.items()
        ],
        "relations": kg.relations,
        "metadata": {
            "language": language,
            "total_sentences": len(sentences),
            "candidate_sentences": len(candidate_sentences),
            "filter_rate": f"{(1 - len(candidate_sentences)/len(sentences))*100:.1f}%"
        },
        "statistics": kg.get_statistics()
    }


def main():
    """
    Main entry point for knowledge graph construction.
    Processes all text files in ../texts/ directory.
    """
    # Directories
    input_dir = os.path.join(os.path.dirname(__file__), '..', 'texts')
    output_dir = os.path.join(os.path.dirname(__file__), '..', 'output')
    os.makedirs(output_dir, exist_ok=True)

    # Configuration
    USE_LLM = True  # Set to False to skip LLM extraction (testing mode)
    LLM_BATCH_SIZE = 10  # Number of sentences per LLM call
    
    print(f"Configuration:")
    print(f"  Input directory: {input_dir}")
    print(f"  Output directory: {output_dir}")
    print(f"  Use LLM: {USE_LLM}")
    print(f"  LLM batch size: {LLM_BATCH_SIZE}")
    print()
    
    # Check if input directory exists
    if not os.path.exists(input_dir):
        print(f"⚠️  Input directory not found: {input_dir}")
        print(f"   Creating directory...")
        os.makedirs(input_dir, exist_ok=True)
        print(f"   Please add .txt files to {input_dir} and run again.")
        return
    
    # Process all text files
    text_files = [f for f in os.listdir(input_dir) if f.endswith('.txt')]
    
    if not text_files:
        print(f"⚠️  No .txt files found in {input_dir}")
        return
    
    print(f"Found {len(text_files)} text files to process\n")
    
    knowledge_graph = {}
    
    for filename in text_files:
        print(f"\n{'='*60}")
        print(f"Processing: {filename}")
        print('='*60)
        
        file_path = os.path.join(input_dir, filename)
        
        with open(file_path, "r", encoding="utf-8") as f:
            text = f.read()
        
        # Process document
        try:
            extracted_data = process_document(
                text,
                use_llm=USE_LLM,
                llm_batch_size=LLM_BATCH_SIZE
            )
            knowledge_graph[filename] = extracted_data
            
            print(f"\n✓ {filename} completed:")
            stats = extracted_data['statistics']
            print(f"  Entities: {stats['num_entities']}")
            print(f"  Relations: {stats['num_relations']}")
            print(f"  Relation types: {stats['num_relation_types']}")
            print(f"  Filter rate: {extracted_data['metadata']['filter_rate']}")
        
        except Exception as e:
            print(f"\n✗ Error processing {filename}: {e}")
            import traceback
            traceback.print_exc()

    # Save the knowledge graph
    output_path = os.path.join(output_dir, "knowledge_graph_llm.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(knowledge_graph, f, indent=2, ensure_ascii=False)
        
    print(f"\n{'='*60}")
    print(f"✅ Knowledge graph saved to:")
    print(f"   {output_path}")
    print('='*60)
    
    # Print overall statistics
    if knowledge_graph:
        total_entities = sum(kg['statistics']['num_entities'] for kg in knowledge_graph.values())
        total_relations = sum(kg['statistics']['num_relations'] for kg in knowledge_graph.values())
        
        print(f"\nOverall Statistics:")
        print(f"  Files processed: {len(knowledge_graph)}")
        print(f"  Total entities: {total_entities}")
        print(f"  Total relations: {total_relations}")
        print(f"  Avg entities/file: {total_entities / len(knowledge_graph):.1f}")
        print(f"  Avg relations/file: {total_relations / len(knowledge_graph):.1f}")
    
    print()

if __name__ == "__main__":
    main()
