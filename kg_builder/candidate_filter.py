"""
Candidate sentence filtering - Stage 1 of the pipeline
Filters out sentences unlikely to contain relations, reducing LLM calls by 80%+
Uses lightweight NER and keyword matching.
"""

import re
from ner_chinese import extract_chinese_entities
from config import (
    MIN_SENTENCE_LENGTH,
    MAX_SENTENCE_LENGTH,
    MIN_ENTITIES_PER_SENTENCE,
    RELATION_KEYWORDS_ZH,
    RELATION_KEYWORDS_EN
)

import re
from ner_chinese import extract_chinese_entities

def has_multiple_entities(text: str) -> bool:
    """
    Check if text contains multiple entities (necessary for relations).
    
    Args:
        text: Input text
        
    Returns:
        True if text has 2+ entities
    """
    entities = extract_chinese_entities(text)
    # Need at least 2 entities to form a relation
    return len(entities) >= 2

def contains_relation_keywords(text: str, language: str = 'zh') -> bool:
    """
    Check if text contains keywords that often indicate relations.
    
    Args:
        text: Input text
        language: 'zh' for Chinese, 'en' for English
        
    Returns:
        True if relation keywords found
    """
    keywords = RELATION_KEYWORDS_ZH if language == 'zh' else RELATION_KEYWORDS_EN
    return any(keyword in text.lower() for keyword in keywords)

def is_candidate_sentence(text: str, language: str = 'zh') -> bool:
    """
    Determine if a sentence is a good candidate for LLM extraction.
    
    Args:
        text: Sentence text
        language: Language code
        
    Returns:
        True if sentence should be sent to LLM
    """
    # Length check
    if len(text) < MIN_SENTENCE_LENGTH or len(text) > MAX_SENTENCE_LENGTH:
        return False
    
    # Must have multiple entities
    if not has_multiple_entities(text):
        return False
    
    # Must contain relation keywords
    if not contains_relation_keywords(text, language):
        return False
    
    return True

def filter_candidate_sentences(sentences: list[str], language: str = 'zh') -> list[str]:
    """
    Filter sentences to get candidates for LLM extraction.
    
    Args:
        sentences: List of sentences
        language: Language code
        
    Returns:
        List of candidate sentences
    """
    return [s for s in sentences if is_candidate_sentence(s, language)]

def get_extraction_priority(text: str, language: str = 'zh') -> int:
    """
    Assign priority score (0-10) to candidate sentence.
    Higher priority = more likely to contain useful relations.
    
    Args:
        text: Sentence text
        language: Language code
        
    Returns:
        Priority score (0-10)
    """
    score = 5  # Base score
    
    # More entities = higher priority
    entities = extract_chinese_entities(text) if language == 'zh' else []
    if len(entities) >= 4:
        score += 3
    elif len(entities) >= 3:
        score += 2
    elif len(entities) >= 2:
        score += 1
    
    # Contains technical abbreviations (CBTC, ZC, etc.)
    if re.search(r'[A-Z]{2,}', text):
        score += 2
    
    # Contains standard references
    if re.search(r'GB/T|ISO|IEC|标准|规范', text):
        score += 1
    
    return min(score, 10)

if __name__ == '__main__':
    # Test
    test_sentences = [
        "城市轨道交通信号系统(CBTC)包括区域控制器(ZC)、列车自动监控系统(ATS)和车载控制器(VOBC)。",
        "今天天气很好。",  # Should be filtered out
        "ZC用于列车运行控制。",
        "系统基于GB/T 28807-2012标准。",
        "第三章",  # Should be filtered out
    ]
    
    print("Testing Candidate Filter:")
    print("="*60)
    
    candidates = filter_candidate_sentences(test_sentences)
    
    print(f"\nOriginal: {len(test_sentences)} sentences")
    print(f"Candidates: {len(candidates)} sentences")
    print(f"Reduction: {(1 - len(candidates)/len(test_sentences))*100:.1f}%\n")
    
    for sent in candidates:
        priority = get_extraction_priority(sent)
        print(f"[Priority {priority}] {sent[:60]}...")
