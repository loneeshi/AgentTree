"""
Language detection and model selection utilities.
Automatically choose the right NER and RE models based on text language.
"""

import re

def detect_language(text: str) -> str:
    """
    Detect if the text is primarily Chinese or English.
    
    Args:
        text: Input text
        
    Returns:
        'zh' for Chinese, 'en' for English
    """
    # Count Chinese characters
    chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
    # Count English letters
    english_chars = len(re.findall(r'[a-zA-Z]', text))
    
    total_chars = chinese_chars + english_chars
    
    if total_chars == 0:
        return 'en'  # Default to English
    
    chinese_ratio = chinese_chars / total_chars
    
    # If more than 30% Chinese characters, treat as Chinese text
    return 'zh' if chinese_ratio > 0.3 else 'en'

def get_optimal_chunk_size(language: str) -> int:
    """
    Get optimal text chunk size based on language.
    Chinese texts can be processed in larger chunks.
    
    Args:
        language: 'zh' or 'en'
        
    Returns:
        Optimal chunk size in characters
    """
    return 200 if language == 'zh' else 500
