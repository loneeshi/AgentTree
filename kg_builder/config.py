"""
Configuration file for knowledge graph construction.
Define standard relation schemas, filtering rules, and LLM settings.
"""

# ============================================================================
# LLM Configuration
# ============================================================================

# LLM provider selection: 'coregpu', 'openai', 'dashscope', or 'mock'
# Set via environment variables: COREGPU_API_KEY, OPENAI_API_KEY or DASHSCOPE_API_KEY
LLM_PROVIDER = 'auto'  # Auto-detect based on available API keys

# Model selection
LLM_MODELS = {
    'coregpu': 'DeepSeek-R1',     # CoreGPU API with DeepSeek-R1 model
    'openai': 'gpt-4o-mini',     # Cheaper model for extraction tasks
    'dashscope': 'qwen-plus',
}

# API endpoints
LLM_ENDPOINTS = {
    'coregpu': 'https://ai.api.coregpu.cn/v1',
    'openai': 'https://api.openai.com/v1',
    'dashscope': None,  # Uses default
}

# Batch processing settings
LLM_BATCH_SIZE = 10  # Number of sentences per API call
LLM_MAX_SENTENCES = 500  # Maximum sentences to process (cost control)

# Token budget (approximate)
LLM_TOKEN_BUDGET = 100000  # Stop if estimated tokens exceed this

# ============================================================================
# Filtering Configuration
# ============================================================================

# Candidate sentence filtering thresholds
MIN_SENTENCE_LENGTH = 10  # Characters
MAX_SENTENCE_LENGTH = 500  # Characters
MIN_ENTITIES_PER_SENTENCE = 2  # At least 2 entities for potential relations

# Relation keywords for candidate filtering (Chinese)
RELATION_KEYWORDS_ZH = [
    '包括', '包含', '含有', '由', '组成',  # Composition
    '用于', '应用于', '适用于', '服务于',  # Purpose
    '基于', '依据', '根据', '按照',  # Basis
    '连接', '接口', '通信', '传输',  # Connection
    '控制', '管理', '运行', '操作',  # Operation
    '实现', '提供', '支持',  # Implementation
    '发送', '接收', '传送',  # Transmission
    '规定', '要求', '明确', '说明',  # Specification
    '符合', '遵循', '满足',  # Compliance
    '是', '为', '属于', '隶属于',  # Identity
]

# Relation keywords for candidate filtering (English)
RELATION_KEYWORDS_EN = [
    'include', 'contain', 'comprise', 'consist',
    'use', 'apply', 'employ', 'serve',
    'base', 'derive', 'build', 'follow',
    'connect', 'link', 'interface', 'communicate',
    'control', 'manage', 'operate', 'run',
    'implement', 'provide', 'support',
    'send', 'receive', 'transmit',
    'specify', 'require', 'define',
    'comply', 'conform', 'satisfy',
    'is', 'are', 'belong',
]

# ============================================================================
# Standard Relations
# ============================================================================

# Standard relation types that we care about in the knowledge graph
STANDARD_RELATIONS = {
    # Taxonomic relations
    "is_a": ["instance of", "subclass of", "type of", "kind of", "是", "为"],
    "subclass_of": ["subclass of", "type of"],
    
    # Part-whole relations
    "part_of": ["part of", "component of", "member of", "belongs to", "属于", "隶属于"],
    "has_part": ["has part", "contains", "includes", "comprises", "包括", "包含", "含有", "涵盖"],
    
    # Functional relations
    "used_for": ["used for", "application", "function", "purpose", "用于", "应用于", "适用于"],
    "connects_with": ["connects with", "links to", "interfaces with", "连接", "接口", "通信"],
    "connects_to": ["connects to", "links to", "到"],
    "uses": ["uses", "utilizes", "employs", "通过", "使用"],
    
    # Comparison relations
    "different_from": ["different from", "distinct from", "not same as", "不同于"],
    "similar_to": ["similar to", "like", "resembles", "类似于"],
    
    # Temporal relations
    "followed_by": ["followed by", "succeeds", "comes after"],
    "follows": ["follows", "preceded by", "comes before"],
    
    # Attribution relations
    "based_on": ["based on", "derived from", "built on", "基于", "依据", "根据", "按照"],
    "operates": ["operates", "runs", "controls", "manages", "控制", "管理", "运行"],
    "abbreviation_of": ["abbreviation of", "short for", "缩写"],
    "implements": ["implements", "provides", "supports", "实现", "提供", "支持"],
    "transmits": ["transmits", "sends", "receives", "发送", "传输", "接收"],
    "specifies": ["specifies", "requires", "stipulates", "规定", "要求", "明确"],
    
    # Locative relations
    "located_in": ["located in", "situated in", "found in", "位于"],
    "headquartered_in": ["headquartered in", "based in"],
    
    # Technical relations
    "complies_with": ["complies with", "conforms to", "符合", "遵循"],
    
    # Other domain-specific relations
    "field_of_occupation": ["field of this occupation", "practiced by"],
    "publisher": ["publisher", "published by"],
}

# Inverted index for quick lookup
RELATION_MAPPING = {}
for standard_rel, variations in STANDARD_RELATIONS.items():
    for variation in variations:
        RELATION_MAPPING[variation.lower()] = standard_rel

# Entity types to keep (filter out noise)
VALID_ENTITY_TYPES = {"PER", "ORG", "LOC", "MISC", "TECH", "SYSTEM", "STANDARD"}

# Ignore patterns for entities (noise filtering)
IGNORE_ENTITY_PATTERNS = [
    r"^#+",  # Starts with ##
    r"^Document Chunk \d+$",  # Document Chunk references
    r"^Chunk \d+$",
    r"^Column$",
    r"^Document$",
    r"^\d+$",  # Pure numbers
    r"^[a-zA-Z]$",  # Single letters (but allow Chinese single chars)
    r"^of$|^the$|^a$|^an$",  # Common English words
    r"^修改单",  # Document structure words
    r"^团体标准",
    r"^第.*?页$",  # Page references
]

# Ignore patterns for relations (noise filtering)
IGNORE_RELATION_PATTERNS = [
    r"^Document Chunk",
    r"^Chunk",
    r"v\d+\.\d+",  # Version numbers
    r"^\d+\.\d+$",  # Numbers
]


# Minimum confidence threshold for entities (if available)
MIN_ENTITY_CONFIDENCE = 0.5

# Minimum length for valid entities
MIN_ENTITY_LENGTH = 2

# Maximum length for entities (to filter out sentences mistaken as entities)
MAX_ENTITY_LENGTH = 100
