# 快速开始指南 - 新版 Skill Agent Tree

## 🚀 5分钟上手

### 步骤 1: 安装依赖

```bash
cd skill_agent_tree
pip install agentscope pydantic shortuuid
```

### 步骤 2: 配置 API

```bash
export DASHSCOPE_API_KEY="your-api-key-here"
```

### 步骤 3: 创建你的第一个自主智能体

创建文件 `my_first_agent.py`：

```python
import asyncio
import os
import agentscope
from agentscope.model import DashScopeChatModel
from agentscope.formatter import DashScopeChatFormatter
from agentscope.tool import Toolkit
from agentscope.memory import InMemoryMemory
from agentscope.message import Msg

from tree_node_agent import TreeNodeAgent

async def main():
    # 1. 初始化 AgentScope
    agentscope.init(project="MyProject", name="session")
    
    # 2. 创建自主智能体
    agent = TreeNodeAgent(
        name="MyAgent",
        sys_prompt="""你是一个自主智能体。

当收到任务时：
1. 分析任务类型
2. 判断是否需要专门的子智能体
3. 使用工具：create_child_agent, delegate_to_child
4. 完成后学习：learn_skill, remember_knowledge

自主思考并使用工具！""",
        model=DashScopeChatModel(
            model_name="qwen-max",
            api_key=os.environ["DASHSCOPE_API_KEY"],
            stream=True
        ),
        formatter=DashScopeChatFormatter(),
        toolkit=Toolkit(),
        memory=InMemoryMemory(),
        skill_domain="通用"
    )
    
    # 3. 发送任务
    msg = Msg(
        name="user",
        content="帮我解决一个数学问题：2x + 5 = 11",
        role="user"
    )
    
    # 4. 智能体自主处理
    response = await agent.reply(msg)
    print(f"智能体响应: {response.get_text_content()}")
    
    # 5. 查看学习成果
    print(f"\n创建的子智能体: {list(agent.children.keys())}")
    print(f"学到的技能: {agent.skill_memory.list_skills()}")
    print(f"知识主题: {agent.knowledge_memory.get_all_topics()}")

if __name__ == "__main__":
    asyncio.run(main())
```

### 步骤 4: 运行

```bash
python my_first_agent.py
```

## 📖 核心概念

### 1. 自主决策

智能体会**自己思考**并决定：
- 是否需要创建子agent？
- 是否应该委托任务？
- 是否需要学习这个技能？

### 2. 工具驱动

智能体通过工具实现各种操作：

```python
# 智能体内部会调用这些工具（你不需要手动调用）
create_child_agent(name, domain, description)  # 创建子agent
delegate_to_child(child_name, task)            # 委托任务
learn_skill(name, description, methodology)     # 学习技能
remember_knowledge(topic, knowledge)            # 记住知识
```

### 3. 双记忆

智能体有两种记忆：

```python
# 技能记忆 - 如何做事
agent.skill_memory.add_skill(
    "编程",
    "编写代码",
    "1.理解需求 2.设计 3.编码"
)

# 知识记忆 - 知道什么
agent.knowledge_memory.add_knowledge(
    "Python",
    "装饰器用于修改函数行为"
)
```

## 🎯 常见场景

### 场景 1: 数学助手

```python
msg = Msg(name="user", content="帮我学习微积分", role="user")
response = await agent.reply(msg)

# 智能体可能会：
# 1. 创建 MathAgent
# 2. 将任务委托给 MathAgent
# 3. MathAgent 可能再创建 CalculusAgent
```

### 场景 2: 编程助手

```python
tasks = [
    "教我Python基础",
    "帮我写一个排序算法",
    "解释什么是装饰器"
]

for task in tasks:
    msg = Msg(name="user", content=task, role="user")
    response = await agent.reply(msg)
    # 智能体会逐步学习并积累编程技能
```

### 场景 3: 多领域助手

```python
# 第一个任务 - 数学
await agent.reply(Msg(name="user", content="解方程", role="user"))
# 可能创建 MathAgent

# 第二个任务 - 写作
await agent.reply(Msg(name="user", content="写一首诗", role="user"))
# 可能创建 WriterAgent

# 第三个任务 - 再次数学
await agent.reply(Msg(name="user", content="计算积分", role="user"))
# 会委托给已有的 MathAgent
```

## 🔍 调试技巧

### 查看智能体状态

```python
# 获取信息
info = agent.get_agent_info()
print(f"名称: {info['name']}")
print(f"子智能体: {info['children']}")
print(f"技能: {info['skills']}")

# 查看完整上下文
print(agent.get_full_context())
```

### 查看树结构

```python
from agent_tree import AgentTree

tree = AgentTree("RootAgent")
tree.add_root_agent(agent, "RootAgent")
tree.sync_from_agents()  # 同步智能体创建的子节点

print(tree.print_tree())
```

### 查看记忆

```python
# 技能摘要
print(agent.skill_memory.get_skills_summary())

# 知识摘要
print(agent.knowledge_memory.get_knowledge_summary())

# 具体技能
skill = agent.skill_memory.get_skill("编程")
print(skill['methodology'])
```

## ⚙️ 自定义配置

### 自定义 System Prompt

```python
my_prompt = """你是一个专注于数学的智能体。

规则：
1. 只处理数学相关任务
2. 遇到数学题时，优先自己解决
3. 只有在需要更细分领域（如微积分、代数）时才创建子agent
4. 记住所有数学知识和公式

使用你的工具！"""

agent = TreeNodeAgent(
    name="MathExpert",
    sys_prompt=my_prompt,
    ...
)
```

### 使用其他模型

```python
# 使用 OpenAI
from agentscope.model import OpenAIChatModel
from agentscope.formatter import OpenAIChatFormatter

model = OpenAIChatModel(
    model_name="gpt-4",
    api_key=os.environ["OPENAI_API_KEY"]
)
formatter = OpenAIChatFormatter()
```

## 📚 下一步

1. **查看完整文档**: `README_NEW.md`
2. **运行示例**: `python examples_new.py`
3. **运行测试**: `python test_new.py`
4. **启动交互式会话**: `python main.py`

## ❓ 常见问题

### Q: 智能体不创建子agent怎么办？

A: 检查 system prompt，确保明确指导何时创建子agent：

```python
sys_prompt = """...
当遇到专业领域任务时，你应该：
1. 评估：这个领域是否需要专门的子智能体？
2. 如果是，使用 create_child_agent 工具创建
3. 然后使用 delegate_to_child 委托任务
..."""
```

### Q: 如何让智能体更积极学习？

A: 在 prompt 中强调学习：

```python
sys_prompt = """...
完成每个任务后，你必须：
1. 评估：这是一个值得记录的技能吗？
2. 如果是，立即使用 learn_skill 工具
3. 如果学到知识，使用 remember_knowledge
..."""
```

### Q: 记忆会保存吗？

A: 当前是内存存储，重启后丢失。未来版本会支持持久化。

### Q: 可以使用多个根agent吗？

A: 可以！创建多个独立的 TreeNodeAgent 实例即可。

## 🎉 开始探索

现在你已经掌握了基础！尝试：

1. 创建自己的专业智能体
2. 设计有趣的 system prompt
3. 让智能体处理复杂任务
4. 观察智能体如何学习和成长

祝你玩得开心！🚀
