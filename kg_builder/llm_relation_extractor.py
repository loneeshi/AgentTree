"""
LLM-based relation extraction module.
Uses large language models to extract complex and implicit relations
that pattern-based methods might miss.
"""

import json
import os
from typing import List, Dict, Optional
from openai import OpenAI

# LLM 配置
# 支持 CoreGPU DeepSeek-R1 API, OpenAI API, 本地模型等
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "coregpu")  # coregpu, openai, ollama
LLM_MODEL = os.getenv("LLM_MODEL", "DeepSeek-R1")  # CoreGPU 使用 DeepSeek-R1
LLM_API_KEY = os.getenv("DPSK_API_KEY", "")
# 注意：base_url 不包含 /chat/completions，OpenAI SDK 会自动添加
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "https://ai.api.coregpu.cn/v1")

# 是否启用 LLM（默认关闭，需要 API Key 才开启）
ENABLE_LLM = bool(LLM_API_KEY) and os.getenv("ENABLE_LLM_EXTRACTION", "false").lower() == "true"

# 是否启用流式输出（用于调试）
ENABLE_STREAMING = os.getenv("ENABLE_LLM_STREAMING", "false").lower() == "true"


def get_llm_client():
    """
    获取 LLM 客户端。支持多种提供商。
    """
    if not ENABLE_LLM:
        return None

    if LLM_PROVIDER == "coregpu":
        return OpenAI(
            api_key=LLM_API_KEY,
            base_url=LLM_BASE_URL
        )

    elif LLM_PROVIDER == "openai":
        return OpenAI(
            api_key=LLM_API_KEY,
            base_url="https://api.openai.com/v1"
        )

    elif LLM_PROVIDER == "ollama":
        return OpenAI(
            api_key="ollama",
            base_url="http://localhost:11434/v1"
        )

    return None



# Prompt 模板
RELATION_EXTRACTION_PROMPT_ZH = """你是一个专业的知识图谱构建专家，擅长从中文技术文档中抽取实体关系。

【任务】
从以下文本中抽取所有有意义的实体关系三元组 (主语, 关系, 宾语)。

【要求】
1. 主语和宾语应该是具体的实体（人名、组织、系统、设备、标准等）
2. 关系应该是动词或动词短语，简洁明了
3. 优先抽取以下类型的关系：
   - 组成关系（包含、包括、由...组成）
   - 功能关系（用于、实现、负责、控制）
   - 连接关系（连接、接口、通信）
   - 依据关系（基于、依据、符合）
   - 缩写关系（...的缩写）
   - 传输关系（发送、接收、传输）
4. 忽略模糊的、不确定的关系
5. 每个三元组独立成行

【输出格式】
请以 JSON 数组格式返回，每个元素包含 subject, relation, object 三个字段。

【示例】
输入：城市轨道交通信号系统(CBTC)包括区域控制器(ZC)和列车自动监控系统(ATS)。
输出：
```json
[
  {{"subject": "城市轨道交通信号系统", "relation": "包括", "object": "区域控制器"}},
  {{"subject": "城市轨道交通信号系统", "relation": "包括", "object": "列车自动监控系统"}},
  {{"subject": "CBTC", "relation": "缩写", "object": "城市轨道交通信号系统"}},
  {{"subject": "ZC", "relation": "缩写", "object": "区域控制器"}},
  {{"subject": "ATS", "relation": "缩写", "object": "列车自动监控系统"}}
]
```

【文本】
{{text}}

【输出】请直接输出JSON数组，不要额外解释："""

RELATION_EXTRACTION_PROMPT_EN = """You are an expert in knowledge graph construction, skilled at extracting entity relations from technical documents.

【Task】
Extract all meaningful entity relation triples (subject, relation, object) from the following text.

【Requirements】
1. Subject and object should be concrete entities (people, organizations, systems, equipment, standards, etc.)
2. Relation should be a verb or verb phrase, concise and clear
3. Prioritize these relation types:
   - Composition (contains, includes, composed of)
   - Functional (used for, implements, responsible for, controls)
   - Connection (connects, interfaces with, communicates)
   - Based on (based on, according to, complies with)
   - Abbreviation (abbreviation of)
   - Transmission (sends, receives, transmits)
4. Ignore vague or uncertain relations
5. Each triple on a separate line

【Output Format】
Return as a JSON array, each element with subject, relation, object fields.

【Example】
Input: Apple, founded by Steve Jobs in 2003, is headquartered in California.
Output:
```json
[
  {{"subject": "Apple", "relation": "founded by", "object": "Steve Jobs"}},
  {{"subject": "Apple", "relation": "founded in", "object": "2003"}},
  {{"subject": "Apple", "relation": "headquartered in", "object": "California"}}
]
```

【Text】
{{text}}

【Output】Return JSON array only, no extra explanation:"""


def extract_relations_with_llm(
    text: str,
    language: str = "zh",
    max_tokens: int = 2000,
    temperature: float = 0.1
) -> List[Dict[str, str]]:
    """
    使用 LLM 从文本中抽取关系三元组。
    
    Args:
        text: 输入文本
        language: 语言 ('zh' 或 'en')
        max_tokens: 最大生成 token 数
        temperature: 生成温度（越低越确定）
    
    Returns:
        关系三元组列表
    """
    if not ENABLE_LLM:
        return []
    
    client = get_llm_client()
    if not client:
        return []
    
    # 调试信息：显示实际配置
    print(f"🔧 Debug Info:")
    print(f"   Provider: {LLM_PROVIDER}")
    print(f"   Model: {LLM_MODEL}")
    print(f"   Base URL: {LLM_BASE_URL}")
    print(f"   API Key: {LLM_API_KEY[:10]}..." if LLM_API_KEY else "   API Key: Not set")
    print()
    
    # 选择合适的 Prompt
    prompt_template = RELATION_EXTRACTION_PROMPT_ZH if language == "zh" else RELATION_EXTRACTION_PROMPT_EN
    prompt = prompt_template.format(text=text)
    
    try:
        # 调用 LLM（支持流式和非流式）
        if ENABLE_STREAMING:
            # 流式输出（用于调试）
            print("🔄 开始流式输出...\n")
            response_stream = client.chat.completions.create(
                model=LLM_MODEL,
                messages=[
                    {"role": "system", "content": "You are a professional knowledge graph construction assistant. Always respond with valid JSON format."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=max_tokens,
                temperature=temperature,
                stream=True,
                response_format={"type": "json_object"}  # 强制 JSON 输出
            )
            
            # 收集流式响应
            full_content = ""
            reasoning_content = ""
            
            for chunk in response_stream:
                if not chunk.choices:
                    continue
                
                delta = chunk.choices[0].delta
                
                # 收集思考过程（DeepSeek-R1 特有）
                if hasattr(delta, 'reasoning_content') and delta.reasoning_content:
                    reasoning_content += delta.reasoning_content
                    print(delta.reasoning_content, end="", flush=True)
                
                # 收集实际内容
                if delta.content:
                    full_content += delta.content
            
            if reasoning_content:
                print("\n" + "="*50)
            
            content = full_content.strip()
        
        else:
            # 非流式输出（正常模式）
            response = client.chat.completions.create(
                model=LLM_MODEL,
                messages=[
                    {"role": "system", "content": "You are a professional knowledge graph construction assistant. Always respond with valid JSON format."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=max_tokens,
                temperature=temperature,
                response_format={"type": "json_object"}  # 强制 JSON 输出
            )
            
            content = response.choices[0].message.content.strip()
        
        # 解析响应
        
        # 尝试提取 JSON（处理可能的 markdown 代码块）
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()
        
        # 解析 JSON
        relations = json.loads(content)
        
        # 验证格式
        if isinstance(relations, dict) and "relations" in relations:
            relations = relations["relations"]
        
        if not isinstance(relations, list):
            print(f"⚠️  LLM returned non-list format: {type(relations)}")
            return []
        
        # 标准化字段名
        standardized = []
        for rel in relations:
            if isinstance(rel, dict):
                standardized.append({
                    "subject": rel.get("subject", rel.get("主语", "")),
                    "relation": rel.get("relation", rel.get("关系", "")),
                    "object": rel.get("object", rel.get("宾语", ""))
                })
        
        return standardized
    
    except json.JSONDecodeError as e:
        print(f"⚠️  Failed to parse LLM response as JSON: {e}")
        print(f"    Response: {content[:200]}...")
        return []
    
    except Exception as e:
        print(f"⚠️  LLM extraction error: {e}")
        print(f"    Error type: {type(e).__name__}")
        
        # 检查是否是 HTTP 错误
        if hasattr(e, 'response'):
            print(f"    Status code: {e.response.status_code if hasattr(e.response, 'status_code') else 'unknown'}")
            print(f"    Response: {e.response.text[:200] if hasattr(e.response, 'text') else 'no response text'}...")
        
        # 检查是否是 OpenAI API 错误
        if hasattr(e, 'body'):
            print(f"    Error body: {e.body}")
        
        import traceback
        print(f"    Traceback:")
        traceback.print_exc()
        
        return []


def extract_relations_batch_with_llm(
    texts: List[str],
    language: str = "zh",
    batch_size: int = 5
) -> List[List[Dict[str, str]]]:
    """
    批量处理多个文本。
    
    Args:
        texts: 文本列表
        language: 语言
        batch_size: 批次大小（一次处理几个句子）
    
    Returns:
        每个文本对应的关系列表
    """
    if not ENABLE_LLM:
        return [[] for _ in texts]
    
    results = []
    
    # 分批处理
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
        
        # 合并文本
        combined_text = "\n\n".join([f"[段落{j+1}] {t}" for j, t in enumerate(batch)])
        
        # 提取关系
        relations = extract_relations_with_llm(combined_text, language)
        
        # TODO: 更智能的分配关系到对应句子
        # 现在简单地把所有关系都分配给第一个文本
        results.append(relations)
        for _ in range(len(batch) - 1):
            results.append([])
    
    return results


if __name__ == "__main__":
    # 测试
    print("="*70)
    print("LLM Relation Extraction Test")
    print("="*70)
    
    if not ENABLE_LLM:
        print("\n⚠️  LLM extraction is DISABLED.")
        print("To enable:")
        print("  1. Set environment variable: export DPSK_API_KEY='your-deepseek-key'")
        print("  2. Set environment variable: export ENABLE_LLM_EXTRACTION='true'")
        print("  3. (Optional) Set LLM_MODEL, LLM_PROVIDER, LLM_BASE_URL")
        print("\n💡 Quick setup:")
        print("  python setup_deepseek.py")
    else:
        print(f"\n✓ LLM enabled: {LLM_PROVIDER} / {LLM_MODEL}")
        print(f"✓ Base URL: {LLM_BASE_URL}")
        
        test_text = """
        城市轨道交通信号系统(CBTC)包括区域控制器(ZC)、列车自动监控系统(ATS)和车载控制器(VOBC)。
        ZC负责列车运行控制，通过RSSP协议与ATS进行安全通信。
        系统符合GB/T 28807-2012标准。
        """
        
        print(f"\nTest Text:\n{test_text}\n")
        
        relations = extract_relations_with_llm(test_text, language="zh")
        
        print(f"Extracted {len(relations)} relations:")
        for rel in relations:
            print(f"  ({rel['subject']}) --[{rel['relation']}]--> ({rel['object']})")
