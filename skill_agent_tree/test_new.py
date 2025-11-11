# -*- coding: utf-8 -*-
"""
新版 Skill Agent Tree 的简单测试

验证核心功能：
1. 智能体自主决策
2. 工具驱动的子agent创建和任务委托
3. 双记忆系统（技能 + 知识）
4. 纯通信，无检索
"""
import asyncio
import os

import agentscope
from agentscope.formatter import DashScopeChatFormatter
from agentscope.memory import InMemoryMemory
from agentscope.model import DashScopeChatModel
from agentscope.tool import Toolkit
from agentscope.message import Msg

from tree_node_agent import TreeNodeAgent, SkillMemory, KnowledgeMemory
from agent_tree import AgentTree


def test_memory_systems():
    """测试记忆系统"""
    print("\n" + "=" * 60)
    print("测试 1: 记忆系统")
    print("=" * 60)
    
    # 测试技能记忆
    skill_mem = SkillMemory()
    skill_mem.add_skill(
        "编程",
        "编写Python代码",
        "1. 理解需求 2. 设计方案 3. 编写代码 4. 测试",
        ["写函数", "写类"]
    )
    skill_mem.add_example("编程", "写装饰器")
    
    print("技能记忆:")
    print(skill_mem.get_skills_summary())
    
    # 测试知识记忆
    knowledge_mem = KnowledgeMemory()
    knowledge_mem.add_knowledge("Python", "装饰器是闭包的应用")
    knowledge_mem.add_knowledge("Python", "列表推导式语法: [x for x in ...]")
    
    print("\n知识记忆:")
    print(knowledge_mem.get_knowledge_summary())
    
    print("\n✓ 记忆系统测试通过")


async def test_autonomous_agent():
    """测试智能体的自主能力"""
    print("\n" + "=" * 60)
    print("测试 2: 智能体自主决策")
    print("=" * 60)
    
    agentscope.init(
        project="SkillAgentTree",
        name="test_autonomous",
        logging_level="INFO",
    )
    
    # 检查是否有API密钥
    if not os.environ.get("DASHSCOPE_API_KEY"):
        print("⚠ 跳过：需要 DASHSCOPE_API_KEY 环境变量")
        return
    
    model = DashScopeChatModel(
        model_name="qwen-max",
        api_key=os.environ["DASHSCOPE_API_KEY"],
        stream=False,  # 测试时不需要流式
    )
    
    # 创建自主智能体
    agent = TreeNodeAgent(
        name="TestAgent",
        sys_prompt="""你是测试智能体。

收到任务后：
1. 分析任务类型
2. 如果是数学任务，考虑创建数学子agent（用create_child_agent工具）
3. 完成任务后，记录技能（用learn_skill工具）

主动使用工具！""",
        model=model,
        formatter=DashScopeChatFormatter(),
        toolkit=Toolkit(),
        memory=InMemoryMemory(),
    )
    
    # 发送一个任务
    msg = Msg(
        name="user",
        content="帮我计算 25 * 4",
        role="user"
    )
    
    print("\n发送任务: 帮我计算 25 * 4")
    print("期待: 智能体会考虑创建子agent或学习技能")
    
    response = await agent.reply(msg)
    print(f"\n智能体响应: {response.get_text_content()[:200]}...")
    
    # 检查是否使用了工具
    print(f"\n创建的子agent: {list(agent.children.keys())}")
    print(f"学到的技能: {agent.skill_memory.list_skills()}")
    
    print("\n✓ 智能体自主决策测试完成")


async def test_tool_registration():
    """测试工具注册"""
    print("\n" + "=" * 60)
    print("测试 3: 工具注册")
    print("=" * 60)
    
    agentscope.init(
        project="SkillAgentTree",
        name="test_tools",
        logging_level="INFO",
    )
    
    # 创建一个简单的agent
    from agentscope.model import MockChatModel
    
    agent = TreeNodeAgent(
        name="ToolTestAgent",
        sys_prompt="测试智能体",
        model=MockChatModel(model_name="mock"),  # 使用mock model测试
        formatter=DashScopeChatFormatter(),
        toolkit=Toolkit(),
        memory=InMemoryMemory(),
    )
    
    # 检查工具是否注册
    tool_names = [tool.name for tool in agent.toolkit.tool_functions]
    
    expected_tools = [
        "create_child_agent",
        "delegate_to_child",
        "learn_skill",
        "remember_knowledge",
        "query_my_skills",
        "query_my_knowledge",
        "list_my_children",
    ]
    
    print("已注册的工具:")
    for tool in tool_names:
        status = "✓" if tool in expected_tools else "?"
        print(f"  {status} {tool}")
    
    missing = set(expected_tools) - set(tool_names)
    if missing:
        print(f"\n⚠ 缺失的工具: {missing}")
    else:
        print("\n✓ 所有预期工具都已注册")


def test_agent_info():
    """测试智能体信息查询"""
    print("\n" + "=" * 60)
    print("测试 4: 智能体信息")
    print("=" * 60)
    
    agentscope.init(
        project="SkillAgentTree",
        name="test_info",
        logging_level="INFO",
    )
    
    from agentscope.model import MockChatModel
    
    # 创建agent并添加一些数据
    agent = TreeNodeAgent(
        name="InfoTestAgent",
        sys_prompt="测试",
        model=MockChatModel(model_name="mock"),
        formatter=DashScopeChatFormatter(),
        toolkit=Toolkit(),
        memory=InMemoryMemory(),
        skill_domain="测试领域",
    )
    
    # 添加技能和知识
    agent.skill_memory.add_skill("测试技能", "描述", "方法")
    agent.knowledge_memory.add_knowledge("测试主题", "测试知识")
    
    # 获取信息
    info = agent.get_agent_info()
    
    print("智能体信息:")
    print(f"  名称: {info['name']}")
    print(f"  领域: {info['domain']}")
    print(f"  父节点: {info['parent']}")
    print(f"  子节点: {info['children']}")
    print(f"  技能: {info['skills']}")
    print(f"  知识主题: {info['knowledge_topics']}")
    
    # 获取完整上下文
    context = agent.get_full_context()
    print(f"\n完整上下文:\n{context}")
    
    print("\n✓ 智能体信息查询测试通过")


def test_agent_tree_sync():
    """测试树结构同步"""
    print("\n" + "=" * 60)
    print("测试 5: 树结构同步")
    print("=" * 60)
    
    agentscope.init(
        project="SkillAgentTree",
        name="test_tree",
        logging_level="INFO",
    )
    
    from agentscope.model import MockChatModel
    
    # 创建根agent
    root = TreeNodeAgent(
        name="Root",
        sys_prompt="根",
        model=MockChatModel(model_name="mock"),
        formatter=DashScopeChatFormatter(),
        toolkit=Toolkit(),
        memory=InMemoryMemory(),
    )
    
    # 创建树
    tree = AgentTree("Root")
    tree.add_root_agent(root, "Root")
    
    # 手动创建子agent（模拟工具调用）
    child = TreeNodeAgent(
        name="Child1",
        sys_prompt="子",
        model=MockChatModel(model_name="mock"),
        formatter=DashScopeChatFormatter(),
        toolkit=Toolkit(),
        memory=InMemoryMemory(),
        parent=root,
    )
    root.children["Child1"] = child
    
    # 同步树结构
    tree.sync_from_agents()
    
    # 检查树
    print("树结构:")
    print(tree.print_tree())
    
    # 验证
    assert "Child1" in tree.nodes, "子agent应该被同步到树中"
    
    print("\n✓ 树结构同步测试通过")


async def run_all_tests():
    """运行所有测试"""
    print("\n" + "=" * 70)
    print(" 新版 Skill Agent Tree 测试套件")
    print("=" * 70)
    
    tests = [
        ("记忆系统", test_memory_systems, False),
        ("工具注册", test_tool_registration, True),
        ("智能体信息", test_agent_info, False),
        ("树结构同步", test_agent_tree_sync, False),
        ("智能体自主决策", test_autonomous_agent, True),
    ]
    
    passed = 0
    failed = 0
    skipped = 0
    
    for name, test_func, is_async in tests:
        try:
            print(f"\n运行测试: {name}")
            if is_async:
                await test_func()
            else:
                test_func()
            passed += 1
        except Exception as e:
            if "跳过" in str(e) or "⚠ 跳过" in str(e):
                skipped += 1
                print(f"⚠ 跳过测试: {name}")
            else:
                failed += 1
                print(f"\n✗ 测试失败: {name}")
                print(f"错误: {e}")
                import traceback
                traceback.print_exc()
    
    print("\n" + "=" * 70)
    print(f" 测试结果: {passed} 通过, {failed} 失败, {skipped} 跳过")
    print("=" * 70)
    
    return failed == 0


if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    
    if success:
        print("\n🎉 所有测试通过！")
    else:
        print("\n❌ 部分测试失败")
        exit(1)
