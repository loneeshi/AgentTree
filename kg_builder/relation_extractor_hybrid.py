"""
Hybrid relation extraction combining pattern-based and LLM-based methods.
"""

from typing import List, Dict
from relation_extraction_chinese import extract_chinese_relations_pattern
from relation_extraction import extract_relations as extract_english_relations
from llm_relation_extractor import extract_relations_with_llm, ENABLE_LLM


def extract_relations_hybrid(
    text: str,
    language: str = "zh",
    use_llm: bool = True,
    llm_weight: float = 1.0
) -> List[Dict[str, str]]:
    """
    混合关系抽取：规则 + LLM。
    
    Args:
        text: 输入文本
        language: 语言 ('zh' 或 'en')
        use_llm: 是否使用 LLM（如果环境未配置，自动跳过）
        llm_weight: LLM 结果的权重（用于后续排序/过滤）
    
    Returns:
        关系三元组列表
    """
    relations = []
    
    # 1. 规则抽取（始终执行）
    if language == "zh":
        pattern_relations = extract_chinese_relations_pattern(text)
    else:
        pattern_relations = extract_english_relations()
    
    # 为规则抽取的关系添加来源标记
    for rel in pattern_relations:
        rel['source'] = 'pattern'
        rel['confidence'] = 0.8  # 规则抽取的置信度
    
    relations.extend(pattern_relations)
    
    # 2. LLM 抽取（如果启用）
    if use_llm and ENABLE_LLM:
        llm_relations = extract_relations_with_llm(text, language)
        
        # 为 LLM 抽取的关系添加来源标记
        for rel in llm_relations:
            rel['source'] = 'llm'
            rel['confidence'] = 0.9 * llm_weight  # LLM 通常更准确
        
        relations.extend(llm_relations)
    
    return relations


def merge_and_deduplicate_relations(relations: List[Dict[str, str]]) -> List[Dict[str, str]]:
    """
    合并和去重关系。
    
    策略：
    1. 相同的 (subject, relation, object) → 保留置信度高的
    2. 相似的关系（如"包括"vs"包含"）→ 标准化后去重
    3. 保留 LLM 发现的新关系
    
    Args:
        relations: 关系列表
    
    Returns:
        去重后的关系列表
    """
    # 标准化关系名称的映射
    relation_normalization = {
        "包括": "has_part",
        "包含": "has_part",
        "含有": "has_part",
        "用于": "used_for",
        "应用于": "used_for",
        "连接": "connects_with",
        "通信": "connects_with",
        "基于": "based_on",
        "依据": "based_on",
        "控制": "operates",
        "管理": "operates",
        "缩写": "abbreviation_of",
    }
    
    seen = {}
    merged = []
    
    for rel in relations:
        # 标准化关系
        relation_normalized = relation_normalization.get(
            rel['relation'],
            rel['relation']
        )
        
        # 创建唯一键
        key = (
            rel['subject'].lower().strip(),
            relation_normalized.lower(),
            rel['object'].lower().strip()
        )
        
        # 去重逻辑
        if key in seen:
            # 如果已存在，保留置信度更高的
            existing = seen[key]
            if rel.get('confidence', 0) > existing.get('confidence', 0):
                seen[key] = rel
        else:
            seen[key] = rel
    
    # 返回去重后的关系
    merged = list(seen.values())
    
    return merged


if __name__ == "__main__":
    # 测试混合抽取
    test_text = """
    城市轨道交通信号系统(CBTC)包括区域控制器(ZC)、列车自动监控系统(ATS)和车载控制器(VOBC)。
    ZC负责列车运行控制，通过RSSP协议与ATS进行安全通信。
    """
    
    print("="*70)
    print("HYBRID RELATION EXTRACTION TEST")
    print("="*70)
    
    print(f"\nTest Text:\n{test_text}\n")
    
    # 提取关系
    relations = extract_relations_hybrid(test_text, language="zh", use_llm=True)
    
    print(f"\nExtracted {len(relations)} relations (before deduplication):")
    for rel in relations:
        source = rel.get('source', 'unknown')
        conf = rel.get('confidence', 0)
        print(f"  [{source:7s}] ({rel['subject']}) --[{rel['relation']}]--> ({rel['object']}) [{conf:.2f}]")
    
    # 去重
    merged = merge_and_deduplicate_relations(relations)
    
    print(f"\nAfter deduplication: {len(merged)} relations:")
    for rel in merged:
        source = rel.get('source', 'unknown')
        conf = rel.get('confidence', 0)
        print(f"  [{source:7s}] ({rel['subject']}) --[{rel['relation']}]--> ({rel['object']}) [{conf:.2f}]")
