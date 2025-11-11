# -*- coding: utf-8 -*-
"""智能体树通信和管理模块。

该模块处理技能学习树结构中 TreeNodeAgent 节点之间的通信逻辑。
注意：这个模块主要用于树形结构的可视化和管理，实际的任务委托
是由智能体自己通过工具完成的。
"""
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
import json

from agentscope.message import Msg


@dataclass
class AgentTreeNode:
    """表示智能体树结构中的一个节点。"""

    name: str
    agent: Any  # TreeNodeAgent 实例的引用
    parent: Optional["AgentTreeNode"] = None
    children: List["AgentTreeNode"] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """将节点转换为字典表示。"""
        skill_count = len(self.agent.skill_memory.skills) if hasattr(self.agent, 'skill_memory') else 0
        return {
            "name": self.name,
            "domain": self.agent.skill_domain if hasattr(self.agent, 'skill_domain') else "unknown",
            "skill_count": skill_count,
            "children": [child.to_dict() for child in self.children],
        }


class AgentTree:
    """管理智能体的树形结构。
    
    注意：这个类主要用于：
    1. 维护树形结构的元数据
    2. 提供树的可视化
    3. 收集统计信息
    
    实际的任务委托和子agent创建由智能体自主通过工具完成。
    """

    def __init__(self, root_agent_name: str) -> None:
        """初始化智能体树。

        参数:
            root_agent_name (str): 根智能体的名称
        """
        self.root_name = root_agent_name
        self.nodes: Dict[str, AgentTreeNode] = {}
        self.root: Optional[AgentTreeNode] = None

    def add_root_agent(self, agent: Any, agent_name: str) -> None:
        """向树中添加根智能体。

        参数:
            agent (TreeNodeAgent): 根智能体
            agent_name (str): 根智能体的名称
        """
        node = AgentTreeNode(name=agent_name, agent=agent)
        self.root = node
        self.nodes[agent_name] = node

    def add_child_agent(
        self,
        parent_name: str,
        child_agent: Any,
        child_name: str,
    ) -> AgentTreeNode:
        """在父智能体下向树中添加子智能体。
        
        注意：这个方法主要用于更新树的元数据。
        实际的子agent创建由智能体通过 create_child_agent 工具完成。

        参数:
            parent_name (str): 父智能体的名称
            child_agent (TreeNodeAgent): 子智能体实例
            child_name (str): 子智能体的名称

        返回:
            AgentTreeNode: 创建的子节点

        异常:
            ValueError: 如果未找到父智能体
        """
        if parent_name not in self.nodes:
            raise ValueError(f"父智能体 '{parent_name}' 未找到")

        parent_node = self.nodes[parent_name]
        child_node = AgentTreeNode(
            name=child_name,
            agent=child_agent,
            parent=parent_node,
        )

        parent_node.children.append(child_node)
        self.nodes[child_name] = child_node

        return child_node

    def get_node(self, agent_name: str) -> Optional[AgentTreeNode]:
        """按智能体名称获取节点。

        参数:
            agent_name (str): 智能体的名称

        返回:
            Optional[AgentTreeNode]: 如果找到，返回节点
        """
        return self.nodes.get(agent_name)

    def get_tree_structure(self) -> Dict[str, Any]:
        """获取完整的树形结构。

        返回:
            Dict[str, Any]: 树形结构字典
        """
        if self.root:
            return self.root.to_dict()
        return {}

    def print_tree(self, indent: int = 0) -> str:
        """生成树形结构的字符串表示。

        参数:
            indent (int): 格式化的缩进级别

        返回:
            str: 格式化的树形字符串
        """
        if not self.root:
            return "空树"

        def _print_node(node: AgentTreeNode, level: int = 0) -> str:
            skill_count = len(node.agent.skill_memory.skills) if hasattr(node.agent, 'skill_memory') else 0
            domain = node.agent.skill_domain if hasattr(node.agent, 'skill_domain') else "unknown"
            result = "  " * level + f"- {node.name} (领域: {domain}, 技能数: {skill_count})\n"
            for child in node.children:
                result += _print_node(child, level + 1)
            return result

        return _print_node(self.root)

    def get_skill_summary(self) -> Dict[str, Any]:
        """获取树中所有智能体学到的技能汇总。

        返回:
            Dict[str, Any]: 按智能体组织的技能汇总
        """
        summary = {}

        for agent_name, node in self.nodes.items():
            agent = node.agent
            if hasattr(agent, "skill_memory"):
                summary[agent_name] = {
                    "skill_count": len(agent.skill_memory.skills),
                    "skills": agent.skill_memory.list_skills(),
                    "knowledge_topics": agent.knowledge_memory.get_all_topics() if hasattr(agent, "knowledge_memory") else [],
                }
            else:
                summary[agent_name] = {
                    "skill_count": 0,
                    "skills": [],
                    "knowledge_topics": [],
                }

        return summary

    def export_tree_state(self) -> str:
        """将树的完整状态导出为JSON。

        返回:
            str: 树状态的JSON表示
        """
        state = {
            "tree_structure": self.get_tree_structure(),
            "skill_summary": self.get_skill_summary(),
        }
        return json.dumps(state, indent=2, ensure_ascii=False)
    
    def sync_from_agents(self) -> None:
        """从智能体同步树形结构。
        
        智能体可能通过工具创建了新的子agent，这个方法用于同步这些变化到 AgentTree。
        """
        if not self.root:
            return
        
        def _sync_node(node: AgentTreeNode):
            agent = node.agent
            if hasattr(agent, 'children'):
                # 检查是否有新的子agent
                for child_name, child_agent in agent.children.items():
                    if child_name not in self.nodes:
                        # 发现新的子agent，添加到树中
                        self.add_child_agent(node.name, child_agent, child_name)
                
                # 递归同步子节点
                for child_node in node.children:
                    _sync_node(child_node)
        
        _sync_node(self.root)

