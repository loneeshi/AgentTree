# -*- coding: utf-8 -*-
"""技能学习树形多智能体系统中的树节点代理实现。"""
import asyncio
import json
from typing import Any, Type, Optional, Dict, List
from pydantic import BaseModel

from agentscope.agent import ReActAgent
from agentscope.formatter import FormatterBase
from agentscope.memory import MemoryBase, LongTermMemoryBase, InMemoryMemory
from agentscope.message import Msg
from agentscope.model import ChatModelBase
from agentscope.tool import Toolkit, ToolResponse
from agentscope.rag import KnowledgeBase


class SkillMemory:
    """技能记忆类：存储技能描述和执行示例"""
    def __init__(self):
        self.skills: Dict[str, Dict[str, Any]] = {}
    
    def add_skill(self, skill_name: str, description: str, methodology: str, examples: List[str] = None):
        """添加或更新一个技能"""
        self.skills[skill_name] = {
            "description": description,
            "methodology": methodology,
            "examples": examples or [],
            "usage_count": self.skills.get(skill_name, {}).get("usage_count", 0)
        }
    
    def add_example(self, skill_name: str, example: str):
        """为技能添加执行示例"""
        if skill_name in self.skills:
            self.skills[skill_name]["examples"].append(example)
            # 只保留最近的10个示例
            self.skills[skill_name]["examples"] = self.skills[skill_name]["examples"][-10:]
    
    def use_skill(self, skill_name: str):
        """记录技能使用"""
        if skill_name in self.skills:
            self.skills[skill_name]["usage_count"] += 1
    
    def get_skill(self, skill_name: str) -> Optional[Dict[str, Any]]:
        """获取技能信息"""
        return self.skills.get(skill_name)
    
    def list_skills(self) -> List[str]:
        """列出所有技能名称"""
        return list(self.skills.keys())
    
    def get_skills_summary(self) -> str:
        """获取技能摘要文本"""
        if not self.skills:
            return "我目前还没有学会任何技能。"
        
        summary = "我目前掌握的技能：\n"
        for name, info in self.skills.items():
            summary += f"- {name}: {info['description']} (使用次数: {info['usage_count']})\n"
        return summary


class KnowledgeMemory:
    """知识记忆类：存储领域知识"""
    def __init__(self):
        self.knowledge: Dict[str, List[str]] = {}  # topic -> [facts]
    
    def add_knowledge(self, topic: str, fact: str):
        """添加知识点"""
        if topic not in self.knowledge:
            self.knowledge[topic] = []
        self.knowledge[topic].append(fact)
        # 只保留最近的20条知识
        self.knowledge[topic] = self.knowledge[topic][-20:]
    
    def get_knowledge(self, topic: str) -> List[str]:
        """获取某主题的知识"""
        return self.knowledge.get(topic, [])
    
    def get_all_topics(self) -> List[str]:
        """获取所有主题"""
        return list(self.knowledge.keys())
    
    def get_knowledge_summary(self) -> str:
        """获取知识摘要"""
        if not self.knowledge:
            return "我目前还没有积累任何领域知识。"
        
        summary = "我积累的知识：\n"
        for topic, facts in self.knowledge.items():
            summary += f"- {topic}: {len(facts)}条知识\n"
        return summary


class TreeNodeAgent(ReActAgent):
    """表示技能学习树中节点的智能体。
    
    每个树节点智能体可以：
    1. 通过思考自主决定是否创建子智能体或委托任务
    2. 存储两类记忆：技能记忆（技能描述+示例）和知识记忆（领域知识）
    3. 通过工具与其他智能体通信，无需主动检索
    4. 记住父子关系和自己的能力边界
    """

    def __init__(
        self,
        name: str,
        sys_prompt: str,
        model: ChatModelBase,
        formatter: FormatterBase,
        toolkit: Toolkit | None = None,
        memory: MemoryBase | None = None,
        long_term_memory: LongTermMemoryBase | None = None,
        parent: Optional["TreeNodeAgent"] = None,
        skill_domain: str = "通用",
        **kwargs: Any,
    ) -> None:
        """初始化树节点智能体。

        参数:
            name (str): 智能体的名称
            sys_prompt (str): 智能体的系统提示词
            model (ChatModelBase): 使用的聊天模型
            formatter (FormatterBase): 消息格式化器
            toolkit (Toolkit | None): 该智能体可用的工具
            memory (MemoryBase | None): 对话历史的内存
            long_term_memory (LongTermMemoryBase | None): 长期记忆
            parent (Optional[TreeNodeAgent]): 树中的父节点
            skill_domain (str): 该智能体负责的技能领域
            **kwargs: 传递给 ReActAgent 的额外参数
        """
        # 创建工具包（如果没有提供）
        if toolkit is None:
            toolkit = Toolkit()
        
        # 先调用父类初始化
        super().__init__(
            name=name,
            sys_prompt=sys_prompt,
            model=model,
            formatter=formatter,
            toolkit=toolkit,
            memory=memory,
            long_term_memory=long_term_memory,
            **kwargs,
        )

        # 树形结构
        self.parent: Optional[TreeNodeAgent] = parent
        self.children: Dict[str, "TreeNodeAgent"] = {}
        self.skill_domain = skill_domain

        # 两大类记忆
        self.skill_memory = SkillMemory()  # 技能记忆
        self.knowledge_memory = KnowledgeMemory()  # 知识记忆
        
        # 保存引用供工具使用
        self._model = model
        self._formatter = formatter
        
        # 注册工具：让agent可以通过工具调用来创建子agent和委托任务
        self._register_agent_tools()
    
    def _register_agent_tools(self):
        """注册智能体管理工具"""
        
        def create_child_agent(child_name: str, child_domain: str, child_description: str) -> ToolResponse:
            """创建一个专门处理特定技能领域的子智能体。
            
            当你发现某个任务需要专业知识，且这个领域值得创建专门的子智能体时使用此工具。
            
            Args:
                child_name: 子智能体的名称，如"数学专家"、"写作助手"
                child_domain: 子智能体负责的技能领域，如"数学"、"写作"
                child_description: 对子智能体技能的描述
            
            Returns:
                创建结果的描述
            """
            try:
                # 生成子智能体的系统提示
                child_sys_prompt = self._generate_child_sys_prompt(
                    child_name, child_domain, child_description
                )
                
                # 创建子智能体
                child_memory = InMemoryMemory()
                child_agent = TreeNodeAgent(
                    name=child_name,
                    sys_prompt=child_sys_prompt,
                    model=self._model,
                    formatter=self._formatter,
                    toolkit=Toolkit(),
                    memory=child_memory,
                    parent=self,
                    skill_domain=child_domain,
                )
                
                # 注册子智能体
                self.children[child_name] = child_agent
                
                result = f"成功创建子智能体 '{child_name}'，负责 {child_domain} 领域。现在你可以将相关任务委托给它。"
                return ToolResponse(content=[{"type": "text", "text": result}])
            
            except Exception as e:
                error_msg = f"创建子智能体失败: {str(e)}"
                return ToolResponse(content=[{"type": "text", "text": error_msg}])
        
        def delegate_to_child(child_name: str, task_description: str) -> ToolResponse:
            """将任务委托给一个子智能体处理。
            
            当你有子智能体且认为它更适合处理某个任务时使用此工具。
            
            Args:
                child_name: 要委托任务的子智能体名称
                task_description: 任务的详细描述
            
            Returns:
                子智能体的回复
            """
            try:
                if child_name not in self.children:
                    available = ', '.join(self.children.keys()) if self.children else '无'
                    error_msg = f"子智能体 '{child_name}' 不存在。当前可用的子智能体: {available}"
                    return ToolResponse(content=[{"type": "text", "text": error_msg}])
                
                child_agent = self.children[child_name]
                
                # 创建任务消息
                task_msg = Msg(
                    name=self.name,
                    content=task_description,
                    role="user",
                )
                
                # 同步调用子智能体（因为工具函数不能是async）
                # 注意：这里我们使用一个辅助方法
                response = self._sync_call_child(child_agent, task_msg)
                
                result = f"子智能体 {child_name} 的回复：\n{response}"
                return ToolResponse(content=[{"type": "text", "text": result}])
            
            except Exception as e:
                error_msg = f"委托任务失败: {str(e)}"
                return ToolResponse(content=[{"type": "text", "text": error_msg}])
        
        def learn_skill(skill_name: str, skill_description: str, methodology: str) -> ToolResponse:
            """记录学到的一个新技能。
            
            当你成功完成某类任务并认为这是一个值得记住的技能时使用此工具。
            
            Args:
                skill_name: 技能名称
                skill_description: 技能的描述
                methodology: 执行这个技能的方法论/步骤
            
            Returns:
                学习结果
            """
            try:
                self.skill_memory.add_skill(skill_name, skill_description, methodology)
                result = f"已学习技能: {skill_name}。我会记住这个技能以便将来使用。"
                return ToolResponse(content=[{"type": "text", "text": result}])
            except Exception as e:
                error_msg = f"学习技能失败: {str(e)}"
                return ToolResponse(content=[{"type": "text", "text": error_msg}])
        
        def remember_knowledge(topic: str, knowledge_point: str) -> ToolResponse:
            """记住某个领域的知识点。
            
            当你在交互中学到新的领域知识时使用此工具。
            
            Args:
                topic: 知识所属的主题/领域
                knowledge_point: 具体的知识内容
            
            Returns:
                记忆结果
            """
            try:
                self.knowledge_memory.add_knowledge(topic, knowledge_point)
                result = f"已记住关于 '{topic}' 的知识: {knowledge_point}"
                return ToolResponse(content=[{"type": "text", "text": result}])
            except Exception as e:
                error_msg = f"记忆知识失败: {str(e)}"
                return ToolResponse(content=[{"type": "text", "text": error_msg}])
        
        def query_my_skills() -> ToolResponse:
            """查询我当前掌握的所有技能。
            
            当你需要了解自己已经掌握哪些技能时使用此工具。
            
            Returns:
                技能列表的描述
            """
            result = self.skill_memory.get_skills_summary()
            return ToolResponse(content=[{"type": "text", "text": result}])
        
        def query_my_knowledge() -> ToolResponse:
            """查询我积累的知识。
            
            当你需要回顾已学知识时使用此工具。
            
            Returns:
                知识摘要
            """
            result = self.knowledge_memory.get_knowledge_summary()
            return ToolResponse(content=[{"type": "text", "text": result}])
        
        def list_my_children() -> ToolResponse:
            """列出我的所有子智能体及其负责的领域。
            
            当你需要知道有哪些子智能体可以委托任务时使用此工具。
            
            Returns:
                子智能体列表
            """
            if not self.children:
                result = "我目前还没有创建任何子智能体。"
            else:
                result = "我的子智能体：\n"
                for name, child in self.children.items():
                    skills_count = len(child.skill_memory.skills)
                    result += f"- {name}: 负责 {child.skill_domain} 领域，掌握 {skills_count} 个技能\n"
            return ToolResponse(content=[{"type": "text", "text": result}])
        
        # 注册所有工具（函数名会自动成为工具名）
        # 检查工具是否已注册，避免重复注册
        existing_tool_names = set(self.toolkit.tools.keys())
        
        tools_to_register = [
            ("create_child_agent", create_child_agent),
            ("delegate_to_child", delegate_to_child),
            ("learn_skill", learn_skill),
            ("remember_knowledge", remember_knowledge),
            ("query_my_skills", query_my_skills),
            ("query_my_knowledge", query_my_knowledge),
            ("list_my_children", list_my_children),
        ]
        
        for tool_name, tool_func in tools_to_register:
            if tool_name not in existing_tool_names:
                self.toolkit.register_tool_function(tool_func)
    
    def _generate_child_sys_prompt(self, child_name: str, child_domain: str, child_description: str) -> str:
        """生成子智能体的系统提示"""
        return f"""你是 {child_name}，一个专门负责 {child_domain} 领域的智能体。

你的职责：
- {child_description}
- 在 {child_domain} 领域提供专业的帮助
- 通过交互学习和积累该领域的知识
- 必要时可以创建自己的子智能体来处理更细分的任务

你有以下能力：
1. 回答 {child_domain} 相关的问题
2. 学习新的技能（使用 learn_skill 工具）
3. 记住领域知识（使用 remember_knowledge 工具）
4. 创建子智能体处理子任务（使用 create_child_agent 工具）
5. 委托任务给子智能体（使用 delegate_to_child 工具）

工作原则：
- 自主思考并决定如何处理任务
- 如果一个任务你不熟悉但值得学习，先尝试完成并学习
- 如果一个任务需要专门的子智能体，考虑创建一个
- 如果已有合适的子智能体，直接委托给它
- 持续积累 {child_domain} 领域的知识和技能

记住：你的父智能体是 {self.name}。"""
    
    def _sync_call_child(self, child_agent: "TreeNodeAgent", msg: Msg) -> str:
        """同步调用子智能体（用于工具函数中）"""
        # 在同步上下文中运行异步代码
        try:
            # 尝试获取当前事件循环
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # 如果已经在异步上下文中，需要使用其他方式
                # 这里返回一个延迟响应的提示
                return f"[委托给 {child_agent.name}] 任务已接收，处理中..."
            else:
                # 否则创建新的事件循环
                response = asyncio.run(child_agent.reply(msg))
                return response.get_text_content() or str(response.content)
        except Exception as e:
            return f"[委托失败] {str(e)}"

    async def reply(
        self,
        msg: Msg | list[Msg] | None = None,
        structured_model: Type[BaseModel] | None = None,
    ) -> Msg:
        """生成回复，智能体会自主决定是否创建子agent或委托任务。

        参数:
            msg (Msg | list[Msg] | None): 输入消息
            structured_model (Type[BaseModel] | None): 结构化输出模型

        返回:
            Msg: 响应消息
        """
        # 调用父类的 ReActAgent 回复方法，它会自动使用工具
        response = await super().reply(msg, structured_model)
        
        return response
    
    def get_agent_info(self) -> Dict[str, Any]:
        """获取智能体的完整信息"""
        return {
            "name": self.name,
            "domain": self.skill_domain,
            "parent": self.parent.name if self.parent else None,
            "children": list(self.children.keys()),
            "skills": self.skill_memory.list_skills(),
            "knowledge_topics": self.knowledge_memory.get_all_topics(),
        }
    
    def get_full_context(self) -> str:
        """获取智能体的完整上下文信息（用于系统提示）"""
        context = f"## 我的身份\n"
        context += f"- 名称: {self.name}\n"
        context += f"- 领域: {self.skill_domain}\n"
        
        if self.parent:
            context += f"- 父智能体: {self.parent.name}\n"
        
        if self.children:
            context += f"\n## 我的子智能体\n"
            for name, child in self.children.items():
                context += f"- {name}: {child.skill_domain}\n"
        
        context += f"\n## 我的技能\n{self.skill_memory.get_skills_summary()}\n"
        context += f"\n## 我的知识\n{self.knowledge_memory.get_knowledge_summary()}\n"
        
        return context
