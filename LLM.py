#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
@File    :   LLM.py
@Time    :   2025/11/10
@Ref   :   不要葱姜蒜
'''
import os
from typing import Dict, List, Optional, Tuple, Union
from openai import OpenAI
from langchain_openai import ChatOpenAI
from langchain_core.messages.human import HumanMessage
from langchain_core.callbacks import StdOutCallbackHandler
from dotenv import load_dotenv, find_dotenv
_ = load_dotenv(find_dotenv())

RAG_PROMPT_TEMPLATE="""
使用以上下文来回答用户的问题。如果你不知道答案，就说你不知道。总是使用中文回答。
问题: {question}
可参考的上下文：
···
{context}
···
如果给定的上下文无法让你做出回答，请回答数据库中没有这个内容，你不知道。
有用的回答:
"""


class BaseModel:
    def __init__(self, model) -> None:
        self.model = model

    def chat(self, prompt: str, history: List[dict], content: str) -> str:
        pass

    def load_model(self):
        pass

class OpenAIChat(BaseModel):
    def __init__(self, model: str = "deepseek") -> None:
        self.model = model

    def chat(self, prompt: str, history: List[dict], content: str) -> str:
        llm = ChatOpenAI(
            model_name= os.getenv("CLOUD_MODEL"),
            openai_api_key=os.getenv("CLOUD_API_KEY"),
            openai_api_base=os.getenv("CLOUD_BASE_URL"),
            callbacks=[StdOutCallbackHandler()],  # 实时打印生成内容
            temperature=0.7
        )
        # 创建一个聊天消息
        history.append({'role': 'user', 'content': RAG_PROMPT_TEMPLATE.format(question=prompt, context=content)})
        
        # 使用LangChain进行对话
        response = llm.invoke([HumanMessage(content=message['content']) for message in history])

        return response.content


if __name__ == "__main__":
    model = OpenAIChat()
    response = model.chat("中国的首都是哪里？", [], "中国的首都是北京。")
    print(response)
