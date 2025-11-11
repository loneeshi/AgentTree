import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import List

BASE_DIR = Path(__file__).resolve().parent.parent
ROOT = Path(__file__).resolve().parent.parent.parent

@dataclass
class Paths:
    RAW_DOC_DIR: str = str(ROOT / "tests/AI_database")
    PARSED_DOC_DIR: str = str(BASE_DIR / "data/parsed")
    CHUNK_DIR: str = str(BASE_DIR / "data/chunks")
    TABLE_DIR: str = str(BASE_DIR / "data/tables")
    KG_DIR: str = str(BASE_DIR / "data/kg")
    INDEX_DIR: str = str(BASE_DIR / "data/index")
    CACHE_DIR: str = str(BASE_DIR / "data/cache")

@dataclass
class VectorIndexCfg:
    host: str = os.getenv("QDRANT_HOST", "localhost")
    port: int = int(os.getenv("QDRANT_PORT", "6333"))
    collection: str = "rail_docs"
    embedding_model: str = "BAAI/bge-m3"
    embedding_dim: int = 1024  # bge-m3 dim
    chunk_size: int = 1500
    chunk_overlap: int = 150

@dataclass
class KeywordIndexCfg:
    host: str = os.getenv("OPENSEARCH_HOST", "localhost")
    port: int = int(os.getenv("OPENSEARCH_PORT", "9200"))
    index_name: str = "rail_docs_keyword"
    shards: int = 1
    replicas: int = 0

@dataclass
class GraphCfg:
    uri: str = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    user: str = os.getenv("NEO4J_USER", "neo4j")
    password: str = os.getenv("NEO4J_PASSWORD", "password")
    batch_size: int = 500

@dataclass
class LLMServingCfg:
    # For cloud providers (e.g., Tianyi AI Store), set endpoint to base URL without trailing /v1
    # Example: https://ai.api.coregpu.cn
    endpoint: str = os.getenv("VLLM_ENDPOINT", os.getenv("LLM_ENDPOINT", "http://localhost:8000"))
    model: str = os.getenv("LLM_MODEL", "Qwen2.5-14B-Instruct")
    # API key for provider (AI Store / OpenAI-compatible). Prefer LLM_API_KEY then AI_STORE_API_KEY then OPENAI_API_KEY.
    api_key: str = os.getenv("LLM_API_KEY", os.getenv("AI_STORE_API_KEY", os.getenv("OPENAI_API_KEY", "")))
    max_output_tokens: int = 512
    temperature: float = 0.2
    top_p: float = 0.9

@dataclass
class RerankerCfg:
    model: str = "BAAI/bge-reranker-v2-m3"
    top_k: int = 8

@dataclass
class RetrievalCfg:
    hybrid_alpha: float = 0.55  # weight for dense vs keyword
    max_candidates: int = 40
    final_context_k: int = 8
    diversity_lambda: float = 0.3  # MMR diversity

@dataclass
class TokenBudgetCfg:
    max_context_tokens: int = 3000
    hard_cap_tokens: int = 3500
    reserve_answer_tokens: int = 600

@dataclass
class ProjectSettings:
    paths: Paths = Paths()
    vector: VectorIndexCfg = VectorIndexCfg()
    keyword: KeywordIndexCfg = KeywordIndexCfg()
    graph: GraphCfg = GraphCfg()
    serving: LLMServingCfg = LLMServingCfg()
    reranker: RerankerCfg = RerankerCfg()
    retrieval: RetrievalCfg = RetrievalCfg()
    token_budget: TokenBudgetCfg = TokenBudgetCfg()
    allowed_question_types: List[str] = field(default_factory=lambda: [
        "definition", "compliance", "version_diff", "table_lookup", "parameter_calc"
    ])

settings = ProjectSettings()