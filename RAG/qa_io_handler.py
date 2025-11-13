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


class QuestionReader:
    """Read questions from markdown file."""
    
    @staticmethod
    def parse_markdown(md_path: str) -> Dict[str, List[Dict[str, Any]]]:
        """
        Parse questions from markdown file.
        
        Expected format:
        ## 基础题（5 道）
        1. Question 1?
        2. Question 2?
        ...
        
        Args:
            md_path: Path to markdown file
            
        Returns:
            Dictionary with category names as keys and question lists as values.
            Each question is a dict with 'id', 'category', 'text'
        """
        with open(md_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        questions_by_category = {}
        
        # Find all category headers like "## 基础题（5 道）"
        category_pattern = r'## ([^（]+)（(\d+) 道）'
        categories = list(re.finditer(category_pattern, content))
        
        for idx, category_match in enumerate(categories):
            category_name = category_match.group(1)  # e.g., "基础题"
            category_start = category_match.end()
            
            # Find the end of this category (next category or end of file)
            if idx + 1 < len(categories):
                category_end = categories[idx + 1].start()
            else:
                category_end = len(content)
            
            category_content = content[category_start:category_end]
            
            # Extract individual questions
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


class AnswerWriter:
    """Write answers to JSON file in the specified format."""
    
    @staticmethod
    def write_answers(
        questions_dict: Dict[str, List[Dict[str, Any]]],
        answers_dict: Dict[str, Dict[int, str]],
        output_path: str = None,
        retrieve_results: Dict[str, Dict[int, List[Dict]]] = None
    ) -> str:
        """
        Write questions and answers to JSON file in the specified format.
        
        Output format:
        {
          "query": "...",
          "result": [
            {"position": 1, "content": "..."},
            {"position": 2, "content": "..."}
          ],
          "answer": "..."
        }
        
        Args:
            questions_dict: Questions dictionary from parse_markdown
            answers_dict: Answers dictionary with structure {category: {q_id: answer_text}}
            output_path: Path to save JSON file (auto-generated if None)
            retrieve_results: Optional retrieval results dictionary
                             with structure {category: {q_id: [result_objects]}}
            
        Returns:
            Path to the output file
        """
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = f"answers_{timestamp}.json"
        
        # Initialize retrieve_results if not provided
        if retrieve_results is None:
            retrieve_results = {}
        
        # Build results array by iterating through all questions
        results = []
        
        for category in sorted(questions_dict.keys()):
            question_list = questions_dict[category]
            
            for q in question_list:
                q_id = q['id']
                q_text = q['text']
                
                # Get answer
                answer = answers_dict.get(category, {}).get(q_id, "未回答")
                
                # Get retrieval results
                retrieve_res = []
                if category in retrieve_results and q_id in retrieve_results[category]:
                    retrieve_res = retrieve_results[category][q_id]
                
                # Create result object
                result_obj = {
                    "query": q_text,
                    "result": retrieve_res,
                    "answer": answer
                }
                
                results.append(result_obj)
        
        # Write to JSON file
        with open(output_path, 'w', encoding='utf-8') as f:
            # Write as separate JSON objects (one per line as in the template)
            for result in results:
                json.dump(result, f, ensure_ascii=False)
                f.write('\n\n')
        
        return output_path


def get_questions_summary(questions_dict: Dict[str, List[Dict[str, Any]]]) -> str:
    """
    Get a summary of questions.
    
    Args:
        questions_dict: Questions dictionary from parse_markdown
        
    Returns:
        Summary string
    """
    total = sum(len(q_list) for q_list in questions_dict.values())
    summary = f"Found {total} questions in {len(questions_dict)} categories:\n"
    
    for category in sorted(questions_dict.keys()):
        summary += f"  - {category}: {len(questions_dict[category])} questions\n"
    
    return summary
