#!/usr/bin/env python3
"""
测试单个文本文件的知识图谱构建
使用 LLM 进行关系抽取
"""

import os
import sys
import json

# 添加 kg_builder 到路径
sys.path.append('kg_builder')

def test_single_file(filename: str):
    """
    测试处理单个文本文件
    
    Args:
        filename: 文件名（相对于 texts/ 目录）
    """
    from text_preprocessing import preprocess_document
    from language_utils import detect_language
    from ner_chinese import extract_chinese_entities
    from candidate_filter import filter_candidate_sentences
    from llm_relation_extractor import extract_relations_with_llm
    from graph_builder import build_graph_from_triples
    
    import spacy
    try:
        nlp = spacy.load("en_core_web_sm")
    except:
        print("⚠️  spaCy 模型未安装，使用简单的句子分割")
        nlp = None
    
    print("="*70)
    print(f"测试文件: {filename}")
    print("="*70)
    
    # 读取文件
    file_path = os.path.join('texts', filename)
    if not os.path.exists(file_path):
        print(f"❌ 文件不存在: {file_path}")
        return
    
    with open(file_path, 'r', encoding='utf-8') as f:
        text = f.read()
    
    print(f"\n📄 文件信息:")
    print(f"  文件大小: {len(text)} 字符")
    print(f"  前 200 字符: {text[:200]}...")
    
    # Stage 1: 语言检测
    print(f"\n[1/6] 检测语言...")
    language = detect_language(text)
    print(f"  → 语言: {'中文' if language == 'zh' else '英文'}")
    
    # Stage 2: 文本预处理
    print(f"\n[2/6] 预处理文本...")
    cleaned_text = preprocess_document(text)
    print(f"  → 清理后: {len(cleaned_text)} 字符")
    
    # Stage 3: 句子分割
    print(f"\n[3/6] 分割句子...")
    if nlp:
        doc = nlp(cleaned_text[:1000000])  # 限制长度避免内存问题
        sentences = [sent.text.strip() for sent in doc.sents]
    else:
        # 简单的句子分割
        sentences = [s.strip() for s in cleaned_text.split('。') if s.strip()]
    
    sentences = [s for s in sentences if len(s) > 10]
    print(f"  → {len(sentences)} 个句子")
    
    # Stage 4: 候选句子过滤
    print(f"\n[4/6] 过滤候选句子...")
    candidates = filter_candidate_sentences(sentences, language)
    filter_rate = (1 - len(candidates)/len(sentences)) * 100 if sentences else 0
    print(f"  → {len(candidates)} 个候选句子 (过滤率: {filter_rate:.1f}%)")
    
    if candidates:
        print(f"\n  示例候选句子 (前3个):")
        for i, sent in enumerate(candidates[:3], 1):
            print(f"    {i}. {sent[:80]}...")
    
    # Stage 5: LLM 关系抽取
    print(f"\n[5/6] LLM 关系抽取...")
    
    # 限制候选句子数量以控制成本
    max_candidates = 20
    if len(candidates) > max_candidates:
        print(f"  ⚠️  候选句子过多，仅处理前 {max_candidates} 个")
        candidates = candidates[:max_candidates]
    
    all_triples = []
    batch_size = 5
    
    for i in range(0, len(candidates), batch_size):
        batch = candidates[i:i+batch_size]
        print(f"  → 处理批次 {i//batch_size + 1}/{(len(candidates)-1)//batch_size + 1} ({len(batch)} 句)...")
        
        # 合并批次
        combined_text = "\n\n".join(batch)
        
        # 提取关系
        triples = extract_relations_with_llm(combined_text, language=language)
        all_triples.extend(triples)
        
        print(f"    ✓ 提取 {len(triples)} 个关系")
    
    print(f"\n  总计: {len(all_triples)} 个关系三元组")
    
    # Stage 6: 构建知识图谱
    print(f"\n[6/6] 构建知识图谱...")
    
    # 提取实体
    entities = {}
    for sent in sentences[:100]:  # 限制处理的句子数
        ents = extract_chinese_entities(sent) if language == 'zh' else []
        for ent in ents:
            if ent['text'] not in entities:
                entities[ent['text']] = ent['type']
    
    print(f"  → 提取 {len(entities)} 个实体")
    
    # 构建图
    kg = build_graph_from_triples(all_triples, entities)
    
    # 显示统计
    stats = kg.get_statistics()
    print(f"\n📊 知识图谱统计:")
    print(f"  实体数: {stats['num_entities']}")
    print(f"  关系数: {stats['num_relations']}")
    print(f"  关系类型数: {stats['num_relation_types']}")
    print(f"  关系类型: {', '.join(stats['relation_types'][:10])}")
    
    # 显示示例关系
    if all_triples:
        print(f"\n📋 示例关系 (前10个):")
        for i, triple in enumerate(all_triples[:10], 1):
            print(f"  {i}. ({triple['subject']}) --[{triple['relation']}]--> ({triple['object']})")
    
    # 保存结果
    output_dir = 'output'
    os.makedirs(output_dir, exist_ok=True)
    
    # 安全的文件名
    safe_filename = filename.replace('/', '_').replace('\\', '_')
    output_path = os.path.join(output_dir, f"kg_{safe_filename}.json")
    
    kg.save(output_path)
    
    print(f"\n✅ 完成!")
    print(f"  结果已保存到: {output_path}")
    print("="*70)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python test_single_txt.py <文件名>")
        print("\n可用文件:")
        
        texts_dir = 'texts'
        if os.path.exists(texts_dir):
            files = [f for f in os.listdir(texts_dir) if f.endswith('.txt')]
            for i, f in enumerate(files[:5], 1):  # 只显示前5个
                print(f"  {i}. {f}")
            if len(files) > 5:
                print(f"  ... 还有 {len(files)-5} 个文件")
        
        print("\n示例:")
        print("  python test_single_txt.py '修改单-TCAMET 04010.1—2018《……互联互通系统规范 第1部分：系统总体要求》.txt'")
        sys.exit(1)
    
    filename = sys.argv[1]
    test_single_file(filename)
