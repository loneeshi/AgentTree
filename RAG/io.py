# -*- coding: utf-8 -*-
"""
Question-Answer I/O Handler

Handle reading questions from markdown files and writing answers to JSON files
in the specified format.
"""
import json
import re
from datetime import datetime
from typing import Dict, List, Any


def parse_questions_from_md(md_path: str) -> Dict[str, List[Dict[str, Any]]]:
    """
    从 Markdown 文件中解析问题。
    
    期望格式：
    ## 基础题（5 道）
    1. 问题 1？
    2. 问题 2？
    
    Args:
        md_path: Markdown 文件路径
        
    Returns:
        字典，key 为分类名称，value 为问题列表
        每个问题为 dict，包含 'id', 'category', 'text'
    """
    with open(md_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    questions_by_category = {}
    
    # 查找所有分类标题，如 "## 基础题（5 道）"
    category_pattern = r'## ([^（]+)（(\d+) 道）'
    categories = list(re.finditer(category_pattern, content))
    
    for idx, category_match in enumerate(categories):
        category_name = category_match.group(1)  # 例如 "基础题"
        category_start = category_match.end()
        
        # 查找该分类的结束位置（下一个分类或文件末尾）
        if idx + 1 < len(categories):
            category_end = categories[idx + 1].start()
        else:
            category_end = len(content)
        
        category_content = content[category_start:category_end]
        
        # 提取单个问题
        question_pattern = r'(\d+)\.\s+(.+?)(?=\n\d+\.|$)'
        questions = []
        for qmatch in re.finditer(question_pattern, category_content, re.DOTALL):
            q_num = int(qmatch.group(1))
            q_text = qmatch.group(2).strip()
            
            questions.append({
                'id': q_num,
                'category': category_name,
                'text': q_text
            })
        
        questions_by_category[category_name] = questions
    
    return questions_by_category


def save_answers_to_json(
    questions_dict: Dict[str, List[Dict[str, Any]]],
    answers_dict: Dict[str, Dict[int, str]],
    output_path: str = None,
    retrieve_results: Dict[str, Dict[int, List[Dict]]] = None
) -> str:
    """
    将问题和答案保存到 JSON 文件，按照示例模板格式。
    
    输出格式（三个分开的 JSON 对象）：
    {
      "query": "..."
    }
    
    {
      "result": [
        {"position": 1, "content": "..."},
        {"position": 2, "content": "..."}
      ]
    }
    
    {
      "answer": "..."
    }
    
    Args:
        questions_dict: 从 parse_questions_from_md 返回的问题字典
        answers_dict: 答案字典，结构为 {category: {q_id: answer_text}}
        output_path: 输出文件路径（不指定则自动生成）
        retrieve_results: 可选的检索结果字典，结构为 {category: {q_id: [result_objects]}}
            
    Returns:
        输出文件路径
    """
    if output_path is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = f"answers_{timestamp}.json"
    
    # 如果未提供检索结果，使用空列表
    if retrieve_results is None:
        retrieve_results = {}
    
    # 按顺序构建结果，按照示例模板格式写入
    with open(output_path, 'w', encoding='utf-8') as f:
        for category in sorted(questions_dict.keys()):
            question_list = questions_dict[category]
            
            for q in question_list:
                q_id = q['id']
                q_text = q['text']
                
                # 获取答案
                answer = answers_dict.get(category, {}).get(q_id, "未回答")
                
                # 获取检索结果
                retrieve_res = []
                if category in retrieve_results and q_id in retrieve_results[category]:
                    retrieve_res = retrieve_results[category][q_id]
                
                # 第一个对象：query
                query_obj = {"query": q_text}
                f.write(json.dumps(query_obj, ensure_ascii=False))
                f.write('\n\n')
                
                # 第二个对象：result
                result_obj = {"result": retrieve_res}
                f.write(json.dumps(result_obj, ensure_ascii=False))
                f.write('\n\n')
                
                # 第三个对象：answer
                answer_obj = {"answer": answer}
                f.write(json.dumps(answer_obj, ensure_ascii=False))
                f.write('\n\n')
    
    return output_path
