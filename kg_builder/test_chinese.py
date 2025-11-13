"""
Quick test for Chinese knowledge extraction.
"""

from language_utils import detect_language
from ner_chinese import extract_chinese_entities
from relation_extraction_chinese import extract_chinese_relations_pattern
from entity_postprocessing import post_process_entities
from relation_postprocessing import post_process_relations

# Test text from your documents
TEST_TEXT = """
城市轨道交通信号系统(CBTC)互联互通系统规范包括区域控制器(ZC)、列车自动监控系统(ATS)和车载控制器(VOBC)。
ZC用于列车运行控制，ATS与ZC连接并进行信息交互。系统基于GB/T 28807-2012标准和TB/T 3528标准。
计算机联锁(CI)属于信号系统的重要组成部分。ATP用于列车自动防护。
ATS负责监控列车运行状态，通过RSSP协议实现安全通信。
车载设备向地面设备发送位置信息，地面控制中心管理所有列车的调度。
"""

def main():
    print("="*70)
    print("CHINESE KNOWLEDGE EXTRACTION TEST")
    print("="*70)
    
    print(f"\nTest Text:\n{TEST_TEXT}\n")
    
    # Test language detection
    lang = detect_language(TEST_TEXT)
    print(f"Detected Language: {'Chinese' if lang == 'zh' else 'English'}")
    print("-"*70)
    
    # Test entity extraction
    print("\n1. ENTITY EXTRACTION")
    print("-"*70)
    raw_entities = extract_chinese_entities(TEST_TEXT)
    print(f"Raw entities extracted: {len(raw_entities)}")
    for ent in raw_entities[:15]:  # Show first 15
        print(f"  - {ent['text']:<30} [{ent['type']}]")
    
    # Post-process entities
    processed_entities = post_process_entities(raw_entities)
    print(f"\nAfter post-processing: {len(processed_entities)} entities")
    for ent in processed_entities[:15]:
        print(f"  - {ent['text']:<30} [{ent['type']}]")
    
    # Test relation extraction
    print("\n2. RELATION EXTRACTION")
    print("-"*70)
    raw_relations = extract_chinese_relations_pattern(TEST_TEXT)
    print(f"Raw relations extracted: {len(raw_relations)}")
    for rel in raw_relations:
        print(f"  ({rel['subject']}) --[{rel['relation']}]--> ({rel['object']})")
    
    # Post-process relations
    processed_relations = post_process_relations(raw_relations)
    print(f"\nAfter post-processing: {len(processed_relations)} relations")
    for rel in processed_relations:
        print(f"  ({rel['subject']}) --[{rel['relation']}]--> ({rel['object']})")
    
    print("\n" + "="*70)
    print("TEST COMPLETE")
    print("="*70)
    print(f"\nSummary:")
    print(f"  - Entities: {len(raw_entities)} → {len(processed_entities)}")
    print(f"  - Relations: {len(raw_relations)} → {len(processed_relations)}")
    print(f"\nTo run on full dataset:")
    print(f"  python kg_builder/main.py")
    print()

if __name__ == '__main__':
    main()
