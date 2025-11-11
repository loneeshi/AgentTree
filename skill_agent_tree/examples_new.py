# -*- coding: utf-8 -*-
"""
新版技能学习树系统的使用示例。

展示智能体如何自主决策、创建子agent、委托任务和学习技能。
"""
import asyncio
import os

import agentscope
from agentscope.formatter import DashScopeChatFormatter
from agentscope.memory import InMemoryMemory
from agentscope.model import DashScopeChatModel
from agentscope.tool import Toolkit
from agentscope.message import Msg

from tree_node_agent import TreeNodeAgent
from agent_tree import AgentTree


# ============================================================================
# 示例 1: 智能体自主决策创建子agent
# ============================================================================

async def example_autonomous_child_creation() -> None:
    """演示智能体自主决定何时创建子agent"""
    print("\n" + "=" * 70)
    print("示例 1: 智能体自主决策创建子agent")
    print("=" * 70)
    
    agentscope.init(
        project="SkillAgentTree",
        name="example_autonomous",
        logging_level="INFO",
    )
    
    model = DashScopeChatModel(
        model_name="qwen-max",
        api_key=os.environ.get("DASHSCOPE_API_KEY"),
        stream=True,
    )
    formatter = DashScopeChatFormatter()
    
    # 创建根智能体 - 具有自主决策能力
    root_agent = TreeNodeAgent(
        name="RootAgent",
        sys_prompt="""你是一个自主决策的根智能体。

当收到任务时，你应该：
1. 思考：这是什么类型的任务？
2. 判断：我需要专门的子智能体吗？
3. 决策：如果需要，使用 create_child_agent 工具创建一个

你有以下工具可用：
- create_child_agent: 创建专门的子智能体
- delegate_to_child: 委托任务给子智能体
- learn_skill: 学习新技能
- remember_knowledge: 记住知识
- query_my_skills, query_my_knowledge, list_my_children: 查询工具

自主思考并使用工具！""",
        model=model,
        formatter=formatter,
        toolkit=Toolkit(),
        memory=InMemoryMemory(),
        skill_domain="通用",
    )
    
    # 给一个数学任务
    print("\n用户: 帮我解决一个数学问题：求解方程 x^2 + 5x + 6 = 0")
    msg = Msg(name="user", content="帮我解决一个数学问题：求解方程 x^2 + 5x + 6 = 0", role="user")
    
    response = await root_agent.reply(msg)
    print(f"\n智能体响应: {response.get_text_content()}")
    
    # 检查是否创建了子智能体
    print(f"\n子智能体列表: {list(root_agent.children.keys())}")
    print(f"技能列表: {root_agent.skill_memory.list_skills()}")


# ============================================================================
# 示例 2: 智能体自主学习和积累知识
# ============================================================================

async def example_autonomous_learning() -> None:
    """演示智能体自主学习技能和积累知识"""
    print("\n" + "=" * 70)
    print("示例 2: 智能体自主学习和积累知识")
    print("=" * 70)
    
    agentscope.init(
        project="SkillAgentTree",
        name="example_learning",
        logging_level="INFO",
    )
    
    model = DashScopeChatModel(
        model_name="qwen-max",
        api_key=os.environ.get("DASHSCOPE_API_KEY"),
        stream=True,
    )
    formatter = DashScopeChatFormatter()
    
    agent = TreeNodeAgent(
        name="LearningAgent",
        sys_prompt="""你是一个学习型智能体。

完成任务后，你应该：
1. 评估：这个任务值得记录为技能吗？
2. 如果是，使用 learn_skill 工具记录
3. 如果学到了知识，使用 remember_knowledge 记录

要自主思考并使用工具！""",
        model=model,
        formatter=formatter,
        toolkit=Toolkit(),
        memory=InMemoryMemory(),
        skill_domain="通用",
    )
    
    # 给几个类似的任务
    tasks = [
        "教我如何写一封正式的商务邮件",
        "帮我写一封求职邮件",
        "教我写感谢信的格式",
    ]
    
    for task in tasks:
        print(f"\n用户: {task}")
        msg = Msg(name="user", content=task, role="user")
        response = await agent.reply(msg)
        print(f"智能体: {response.get_text_content()[:200]}...")
    
    # 查看学到的技能和知识
    print("\n\n=== 学习成果 ===")
    print(agent.skill_memory.get_skills_summary())
    print(agent.knowledge_memory.get_knowledge_summary())


# ============================================================================
# 示例 3: 层级任务委托
# ============================================================================

async def example_hierarchical_delegation() -> None:
    """演示智能体自主进行层级任务委托"""
    print("\n" + "=" * 70)
    print("示例 3: 层级任务委托")
    print("=" * 70)
    
    agentscope.init(
        project="SkillAgentTree",
        name="example_delegation",
        logging_level="INFO",
    )
    
    model = DashScopeChatModel(
        model_name="qwen-max",
        api_key=os.environ.get("DASHSCOPE_API_KEY"),
        stream=True,
    )
    formatter = DashScopeChatFormatter()
    
    # 创建根智能体
    root_agent = TreeNodeAgent(
        name="RootAgent",
        sys_prompt="""你是根智能体。

当收到任务时：
1. 先查看你的子智能体（list_my_children）
2. 如果有合适的子智能体，使用 delegate_to_child 委托
3. 如果没有但需要，使用 create_child_agent 创建
4. 完成任务后，考虑是否 learn_skill

自主决策！""",
        model=model,
        formatter=formatter,
        toolkit=Toolkit(),
        memory=InMemoryMemory(),
        skill_domain="通用",
    )
    
    # 创建树
    tree = AgentTree("RootAgent")
    tree.add_root_agent(root_agent, "RootAgent")
    
    # 给一系列不同领域的任务
    tasks = [
        "帮我计算 123 * 456",
        "帮我写一首关于秋天的诗",
        "解释一下量子纠缠",
        "再帮我计算 789 * 012",  # 第二次数学任务，应该委托
    ]
    
    for i, task in enumerate(tasks, 1):
        print(f"\n{'='*50}")
        print(f"任务 {i}: {task}")
        print('='*50)
        
        msg = Msg(name="user", content=task, role="user")
        response = await root_agent.reply(msg)
        print(f"\n响应: {response.get_text_content()[:300]}...")
        
        # 同步树结构
        tree.sync_from_agents()
        
        # 显示当前树结构
        print(f"\n当前树结构:")
        print(tree.print_tree())


# ============================================================================
# 示例 4: 完整的自主工作流
# ============================================================================

async def example_complete_autonomous_workflow() -> None:
    """演示完整的自主工作流：接收任务 → 思考 → 决策 → 执行 → 学习"""
    print("\n" + "=" * 70)
    print("示例 4: 完整的自主工作流")
    print("=" * 70)
    
    agentscope.init(
        project="SkillAgentTree",
        name="example_workflow",
        logging_level="INFO",
    )
    
    model = DashScopeChatModel(
        model_name="qwen-max",
        api_key=os.environ.get("DASHSCOPE_API_KEY"),
        stream=True,
    )
    formatter = DashScopeChatFormatter()
    
    # 创建具有完整自主能力的智能体
    agent = TreeNodeAgent(
        name="AutonomousAgent",
        sys_prompt="""你是一个完全自主的智能体。

## 工作流程

对于每个任务，你应该：

1. **分析任务**
   - 这是什么类型的任务？
   - 我以前处理过类似的吗？

2. **查询现状**（使用工具）
   - query_my_skills: 我掌握相关技能吗？
   - list_my_children: 我有可以委托的子智能体吗？

3. **做出决策**
   - 如果有相关技能且没有子智能体：自己处理
   - 如果有合适的子智能体：delegate_to_child 委托
   - 如果任务很专业且值得创建子智能体：create_child_agent

4. **执行任务**
   - 根据决策执行

5. **学习总结**
   - 任务完成后，如果学到了技能：learn_skill
   - 如果积累了知识：remember_knowledge

要展现你的思考过程！""",
        model=model,
        formatter=formatter,
        toolkit=Toolkit(),
        memory=InMemoryMemory(),
        skill_domain="通用",
    )
    
    # 模拟一系列真实的用户交互
    print("\n开始多轮交互...\n")
    
    interactions = [
        "教我Python中的列表推导式",
        "帮我写一个快速排序算法",
        "再给我解释一下Python的装饰器",
        "用JavaScript写一个防抖函数",
    ]
    
    for i, user_input in enumerate(interactions, 1):
        print(f"\n{'#'*70}")
        print(f"# 第 {i} 轮交互")
        print('#'*70)
        print(f"用户: {user_input}")
        print()
        
        msg = Msg(name="user", content=user_input, role="user")
        response = await agent.reply(msg)
        
        print(f"\n智能体响应:")
        print(response.get_text_content()[:500] + "..." if len(response.get_text_content()) > 500 else response.get_text_content())
        
        # 显示学习状态
        print(f"\n--- 当前状态 ---")
        print(f"掌握的技能: {agent.skill_memory.list_skills()}")
        print(f"知识主题: {agent.knowledge_memory.get_all_topics()}")
        print(f"子智能体: {list(agent.children.keys())}")
        print()


# ============================================================================
# 示例 5: 简单演示 - 最小示例
# ============================================================================

async def example_minimal_demo() -> None:
    """最小演示：展示基本的自主能力"""
    print("\n" + "=" * 70)
    print("示例 5: 最小演示")
    print("=" * 70)
    
    agentscope.init(
        project="SkillAgentTree",
        name="minimal_demo",
        logging_level="INFO",
    )
    
    model = DashScopeChatModel(
        model_name="qwen-max",
        api_key=os.environ.get("DASHSCOPE_API_KEY"),
        stream=True,
    )
    
    agent = TreeNodeAgent(
        name="Agent",
        sys_prompt="你是一个自主智能体。可以使用工具来创建子agent、委托任务、学习技能和记住知识。",
        model=model,
        formatter=DashScopeChatFormatter(),
        toolkit=Toolkit(),
        memory=InMemoryMemory(),
    )
    
    # 简单的任务
    msg = Msg(name="user", content="帮我学习如何做数学题", role="user")
    response = await agent.reply(msg)
    
    print(f"响应: {response.get_text_content()}")
    print(f"\n创建的子智能体: {list(agent.children.keys())}")


# ============================================================================
# 主函数
# ============================================================================

async def main() -> None:
    """运行所有示例"""
    
    examples = [
        ("最小演示", example_minimal_demo),
        ("自主创建子agent", example_autonomous_child_creation),
        ("自主学习", example_autonomous_learning),
        ("层级委托", example_hierarchical_delegation),
        ("完整工作流", example_complete_autonomous_workflow),
    ]
    
    print("\n" + "=" * 70)
    print(" 新版技能学习树系统 - 示例演示")
    print("=" * 70)
    print("\n特性:")
    print("  ✓ 智能体完全自主决策")
    print("  ✓ 通过工具创建子agent和委托任务")
    print("  ✓ 双记忆系统：技能记忆 + 知识记忆")
    print("  ✓ 无需外部检索，纯智能体通信")
    print("=" * 70)
    
    # 让用户选择运行哪个示例
    print("\n可用示例:")
    for i, (name, _) in enumerate(examples, 1):
        print(f"  {i}. {name}")
    print(f"  {len(examples) + 1}. 运行所有示例")
    
    choice = input("\n请选择要运行的示例 (输入数字): ").strip()
    
    try:
        choice_num = int(choice)
        if 1 <= choice_num <= len(examples):
            name, func = examples[choice_num - 1]
            print(f"\n运行示例: {name}")
            await func()
        elif choice_num == len(examples) + 1:
            for name, func in examples:
                print(f"\n运行示例: {name}")
                try:
                    await func()
                except Exception as e:
                    print(f"错误: {e}")
                    import traceback
                    traceback.print_exc()
        else:
            print("无效的选择")
    except ValueError:
        print("无效的输入")
    
    print("\n" + "=" * 70)
    print(" 示例演示完成")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
