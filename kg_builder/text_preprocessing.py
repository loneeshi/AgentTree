"""
Text preprocessing utilities to clean and prepare text for knowledge extraction.
"""

import re

def clean_text(text: str) -> str:
    """
    Clean the input text by removing noise and formatting issues.
    
    Args:
        text: Raw text string
        
    Returns:
        Cleaned text string
    """
    # Remove multiple spaces
    text = re.sub(r'\s+', ' ', text)
    
    # Remove page numbers (common pattern: "Page 1", "- 1 -", etc.)
    text = re.sub(r'(?:Page|page)\s*\d+', '', text)
    text = re.sub(r'-\s*\d+\s*-', '', text)
    
    # Remove common header/footer markers
    text = re.sub(r'(?i)copyright.*?\d{4}', '', text)
    text = re.sub(r'(?i)all rights reserved', '', text)
    
    # Remove excessive punctuation
    text = re.sub(r'[.]{3,}', '...', text)
    text = re.sub(r'[-]{3,}', '---', text)
    
    # Remove URLs
    text = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', text)
    
    # Remove email addresses
    text = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '', text)
    
    return text.strip()

def is_meaningful_sentence(sentence: str) -> bool:
    """
    Determine if a sentence is meaningful for knowledge extraction.
    
    Args:
        sentence: A sentence string
        
    Returns:
        True if the sentence is meaningful, False otherwise
    """
    # Too short
    if len(sentence.split()) < 5:
        return False
    
    # Too long (likely a paragraph or malformed)
    if len(sentence.split()) > 100:
        return False
    
    # Mostly numbers or symbols
    alpha_count = sum(c.isalpha() for c in sentence)
    if alpha_count < len(sentence) * 0.5:
        return False
    
    # Common noise patterns
    noise_patterns = [
        r'^Table of Contents',
        r'^Index',
        r'^References',
        r'^Appendix',
        r'^Figure \d+',
        r'^Table \d+',
        r'^\d+\.\d+\s',  # Section numbers like "1.2 "
    ]
    
    for pattern in noise_patterns:
        if re.match(pattern, sentence, re.IGNORECASE):
            return False
    
    return True

def preprocess_document(text: str) -> str:
    """
    Complete preprocessing pipeline for a document.
    
    Args:
        text: Raw document text
        
    Returns:
        Preprocessed text ready for knowledge extraction
    """
    # First, clean the text
    text = clean_text(text)
    
    # Split into sentences and filter
    sentences = text.split('.')
    meaningful_sentences = [
        sent.strip() + '.'
        for sent in sentences
        if is_meaningful_sentence(sent.strip())
    ]
    
    return ' '.join(meaningful_sentences)
