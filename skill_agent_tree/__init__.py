# -*- coding: utf-8 -*-
"""Skill Agent Tree - A hierarchical multi-agent system for skill learning.

This package implements a tree-based architecture where:
1. Each node is an agent specialized in specific tasks
2. Agents can learn skills from interactions
3. Parent agents delegate tasks to child agents
4. The system builds a hierarchical skill tree over time
"""

from tree_node_agent import TreeNodeAgent
from agent_tree import AgentTree, AgentTreeNode

__version__ = "0.1.0"
__all__ = [
    "TreeNodeAgent",
    "AgentTree",
    "AgentTreeNode",
]
