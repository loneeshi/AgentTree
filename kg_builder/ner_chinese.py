"""
Chinese NER module using SpaCy with Chinese language support.
For Chinese text, we use pattern-based extraction and SpaCy Chinese models.
"""

import re
import spacy

# Try to load Chinese model, fallback to pattern-based extraction
try:
    nlp_zh = spacy.load("zh_core_web_sm")
    HAS_CHINESE_MODEL = True
except:
    HAS_CHINESE_MODEL = False
    nlp_zh = None

def extract_chinese_entities(text: str) -> list[dict]:
    """
    Extract entities from Chinese text using multiple strategies.
    
    Args:
        text: Chinese text
        
    Returns:
        List of entity dictionaries
    """
    entities = []
    
    # Strategy 1: Technical abbreviations (e.g., CBTC, ATP, ATO, ZC, CI)
    # These are usually uppercase English letters
    tech_abbrev_pattern = r'\b([A-Z]{2,}(?:-[A-Z0-9]+)?)\b'
    for match in re.finditer(tech_abbrev_pattern, text):
        entities.append({
            'text': match.group(1),
            'type': 'TECH',  # Technical term
            'start': match.start(),
            'end': match.end()
        })
    
    # Strategy 2: Standards and specifications (e.g., TB/T 3528, IEC 62280)
    standard_pattern = r'(?:GB/?T?|TB/?T?|IEC|IEEE|EN)\s*[0-9]+(?:[.-][0-9]+)*(?:[-—][0-9]{4})?'
    for match in re.finditer(standard_pattern, text):
        entities.append({
            'text': match.group(0),
            'type': 'STANDARD',
            'start': match.start(),
            'end': match.end()
        })
    
    # Strategy 3: System names (Chinese + potential English)
    # e.g., 区域控制器, 列车自动监控系统
    # Improved pattern to capture complete system names
    system_keywords = [
        '系统', '设备', '装置', '控制器', '监控', '平台', '接口', 
        '协议', '模块', '单元', '终端', '服务器', '工作站', '子系统'
    ]
    
    for keyword in system_keywords:
        # Match 2-10 Chinese characters before the keyword
        pattern = f'([一-龥]{{2,10}}?{keyword})'
        for match in re.finditer(pattern, text):
            system_name = match.group(1).strip()
            
            # Avoid very long matches
            if len(system_name) <= 15:
                entities.append({
                    'text': system_name,
                    'type': 'SYSTEM',
                    'start': match.start(),
                    'end': match.end()
                })
    
    # Strategy 4: Use SpaCy if available
    if HAS_CHINESE_MODEL and nlp_zh:
        doc = nlp_zh(text)
        for ent in doc.ents:
            entities.append({
                'text': ent.text,
                'type': ent.label_,
                'start': ent.start_char,
                'end': ent.end_char
            })
    
    return entities

def extract_entities_multilang(text: str, language: str) -> list[dict]:
    """
    Extract entities based on detected language.
    
    Args:
        text: Input text
        language: 'zh' or 'en'
        
    Returns:
        List of entity dictionaries
    """
    if language == 'zh':
        return extract_chinese_entities(text)
    else:
        # Use the English NER from ner.py
        from ner import extract_entities as extract_english_entities
        return extract_english_entities(text)

if __name__ == '__main__':
    # Test with Chinese text
    test_text = "城市轨道交通信号系统(CBTC)互联互通系统规范，包括区域控制器(ZC)和列车自动监控系统(ATS)。参考标准GB/T 28807-2012和IEC 62290。"
    
    print("Testing Chinese NER:")
    print(f"Text: {test_text}\n")
    
    entities = extract_chinese_entities(test_text)
    
    print(f"Extracted {len(entities)} entities:")
    for ent in entities:
        print(f"  - {ent['text']:<30} [{ent['type']}]")
