"""
LLM-based relation extractor - Stage 2 of the pipeline
Uses LLM API to extract high-quality entity relations from candidate sentences.
Supports batch processing to optimize token usage.
"""

import json
import os
from typing import Optional

def get_llm_client():
    """
    Initialize LLM client. Supports multiple providers.
    Set API key via environment variable COREGPU_API_KEY.
    
    Returns:
        LLM client instance
    """
    # Try CoreGPU API (DeepSeek-R1)
    try:
        from openai import OpenAI
        api_key = os.getenv('COREGPU_API_KEY')
        if api_key:
            client = OpenAI(
                api_key=api_key,
                base_url="https://ai.api.coregpu.cn/v1"
            )
            return ('coregpu', client)
    except ImportError:
        pass
    
    # Try OpenAI (original)
    try:
        from openai import OpenAI
        api_key = os.getenv('OPENAI_API_KEY')
        if api_key:
            client = OpenAI(api_key=api_key)
            return ('openai', client)
    except ImportError:
        pass
    
    # Try Dashscope (Alibaba)
    try:
        import dashscope
        api_key = os.getenv('DASHSCOPE_API_KEY')
        if api_key:
            dashscope.api_key = api_key
            return ('dashscope', dashscope)
    except ImportError:
        pass
    
    # Fallback: mock mode for testing
    print("⚠️  Warning: No LLM API key found. Running in MOCK mode.")
    print("   Set COREGPU_API_KEY, OPENAI_API_KEY or DASHSCOPE_API_KEY environment variable.")
    return ('mock', None)

def create_extraction_prompt(sentences: list[str], language: str = 'zh') -> str:
    """
    Create optimized prompt for relation extraction.
    
    Args:
        sentences: List of sentences to process
        language: 'zh' for Chinese, 'en' for English
        
    Returns:
        Prompt string
    """
    if language == 'zh':
        prompt = """你是一个知识图谱构建专家。请从以下句子中抽取所有的实体关系三元组。

要求：
1. 输出格式：JSON数组，每个元素是 {"subject": "主语实体", "relation": "关系", "object": "宾语实体"}
2. 关系类型应该是动词或动词短语，如："包括"、"用于"、"基于"、"连接"、"控制"等
3. 只抽取明确存在的关系，不要推理或猜测
4. 实体名称保持原文，包括缩写（如CBTC、ZC、ATS）
5. 如果某句子没有明确关系，该句返回空数组

句子列表：
"""
        for i, sent in enumerate(sentences, 1):
            prompt += f"{i}. {sent}\n"
        
        prompt += "\n请直接输出JSON数组，不要有其他解释文字："
    
    else:  # English
        prompt = """You are a knowledge graph expert. Extract all entity relation triples from the following sentences.

Requirements:
1. Output format: JSON array, each element is {"subject": "subject entity", "relation": "relation", "object": "object entity"}
2. Relations should be verbs or verb phrases
3. Only extract explicitly stated relations, do not infer
4. Keep entity names as they appear in text, including abbreviations
5. If a sentence has no clear relations, return empty array for that sentence

Sentences:
"""
        for i, sent in enumerate(sentences, 1):
            prompt += f"{i}. {sent}\n"
        
        prompt += "\nOutput JSON array only, no explanations:"
    
    return prompt

def call_llm_api(provider: str, client, prompt: str, model: str = None) -> str:
    """
    Call LLM API with the given prompt.
    
    Args:
        provider: 'coregpu', 'openai', 'dashscope', or 'mock'
        client: LLM client instance
        prompt: Prompt text
        model: Model name (optional, uses default if None)
        
    Returns:
        LLM response text
    """
    if provider == 'coregpu':
        model = model or 'DeepSeek-R1'
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are a knowledge graph extraction assistant. Output only valid JSON."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.1,  # Lower temperature for more consistent output
        )
        return response.choices[0].message.content
    
    elif provider == 'openai':
        model = model or 'gpt-4o-mini'  # Cheaper model for extraction
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are a knowledge graph extraction assistant. Output only valid JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,  # Lower temperature for more consistent output
        )
        return response.choices[0].message.content
    
    elif provider == 'dashscope':
        from dashscope import Generation
        model = model or 'qwen-plus'
        response = Generation.call(
            model=model,
            messages=[
                {"role": "system", "content": "You are a knowledge graph extraction assistant. Output only valid JSON."},
                {"role": "user", "content": prompt}
            ],
            result_format='message',
        )
        return response.output.choices[0].message.content
    
    elif provider == 'mock':
        # Mock mode for testing without API
        return '''[
            {"subject": "CBTC", "relation": "包括", "object": "ZC"},
            {"subject": "CBTC", "relation": "包括", "object": "ATS"},
            {"subject": "ZC", "relation": "用于", "object": "列车运行控制"}
        ]'''
    
    else:
        raise ValueError(f"Unknown provider: {provider}")

def parse_llm_response(response: str) -> list[dict]:
    """
    Parse LLM response into structured triples.
    
    Args:
        response: LLM response text
        
    Returns:
        List of relation triples
    """
    try:
        # Try to find JSON array in response
        start = response.find('[')
        end = response.rfind(']') + 1
        
        if start >= 0 and end > start:
            json_str = response[start:end]
            triples = json.loads(json_str)
            
            # Validate structure
            valid_triples = []
            for triple in triples:
                if isinstance(triple, dict) and all(k in triple for k in ['subject', 'relation', 'object']):
                    # Clean up
                    triple['subject'] = str(triple['subject']).strip()
                    triple['relation'] = str(triple['relation']).strip()
                    triple['object'] = str(triple['object']).strip()
                    
                    # Filter out empty or too short
                    if len(triple['subject']) > 1 and len(triple['object']) > 1 and triple['relation']:
                        valid_triples.append(triple)
            
            return valid_triples
    except Exception as e:
        print(f"⚠️  Failed to parse LLM response: {e}")
        print(f"   Response: {response[:200]}...")
    
    return []

def extract_relations_batch(sentences: list[str], language: str = 'zh', batch_size: int = 10) -> list[dict]:
    """
    Extract relations from multiple sentences using LLM in batches.
    
    Args:
        sentences: List of candidate sentences
        language: Language code
        batch_size: Number of sentences per API call (to optimize cost)
        
    Returns:
        List of extracted relation triples
    """
    provider, client = get_llm_client()
    all_triples = []
    
    # Process in batches
    for i in range(0, len(sentences), batch_size):
        batch = sentences[i:i+batch_size]
        
        print(f"  Processing batch {i//batch_size + 1}/{(len(sentences)-1)//batch_size + 1} ({len(batch)} sentences)...")
        
        # Create prompt
        prompt = create_extraction_prompt(batch, language)
        
        # Call LLM
        response = call_llm_api(provider, client, prompt)
        
        # Parse response
        triples = parse_llm_response(response)
        all_triples.extend(triples)
        
        print(f"    → Extracted {len(triples)} relations")
    
    return all_triples

if __name__ == '__main__':
    # Test
    test_sentences = [
        "城市轨道交通信号系统(CBTC)包括区域控制器(ZC)、列车自动监控系统(ATS)和车载控制器(VOBC)。",
        "ZC用于列车运行控制，ATS与ZC连接。",
        "系统基于GB/T 28807-2012标准。"
    ]
    
    print("Testing LLM Extractor:")
    print("="*60)
    
    triples = extract_relations_batch(test_sentences)
    
    print(f"\nExtracted {len(triples)} relations:")
    for triple in triples:
        print(f"  ({triple['subject']}) --[{triple['relation']}]--> ({triple['object']})")
