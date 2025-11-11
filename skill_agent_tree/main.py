# -*- coding: utf-8 -*-
"""技能学习树系统的主入口。

该模块使用根智能体初始化智能体树，智能体完全自主决策，
通过工具来创建子agent和委托任务，无需外部检索。
"""
import asyncio
import os
from typing import Optional

import agentscope
from agentscope.agent import UserAgent
from agentscope.formatter import DashScopeChatFormatter
from agentscope.memory import InMemoryMemory
from agentscope.model import DashScopeChatModel
from agentscope.tool import Toolkit
from agentscope.message import Msg

from tree_node_agent import TreeNodeAgent
from agent_tree import AgentTree


class SkillAgentTreeSystem:
    """管理技能学习树的主系统。
    
    系统特点：
    1. 智能体完全自主决策 - 通过 system prompt 引导
    2. 通过工具创建子agent和委托任务 - 而非外部控制
    3. 无检索过程 - 完全通过智能体通信
    4. 双记忆系统 - 技能记忆 + 知识记忆
    """

    def __init__(
        self,
        project_name: str = "SkillAgentTree",
        api_key: Optional[str] = None,
    ) -> None:
        """初始化技能学习树系统。

        参数:
            project_name (str): 项目名称
            api_key (Optional[str]): DashScope API 密钥
        """
        # 初始化 AgentScope
        agentscope.init(
            project=project_name,
            name="skill_learning_session",
            logging_level="INFO",
        )

        self.api_key = api_key or os.environ.get("DASHSCOPE_API_KEY")
        self.agent_tree: Optional[AgentTree] = None
        self.root_agent: Optional[TreeNodeAgent] = None

    async def initialize_root_agent(self) -> None:
        """初始化技能树的根智能体。"""
        # 为根智能体创建基础组件
        model = DashScopeChatModel(
            model_name="qwen-max",
            api_key=os.environ["DASHSCOPE_API_KEY"],
            stream=True,
        )
        formatter = DashScopeChatFormatter()
        toolkit = Toolkit()
        memory = InMemoryMemory()

        # 创建根智能体 - 完全自主的系统提示
        self.root_agent = TreeNodeAgent(
            name="RootAgent",
            sys_prompt=self._get_root_system_prompt(),
            model=model,
            formatter=formatter,
            toolkit=toolkit,
            memory=memory,
            skill_domain="通用协调",
        )

        # 初始化智能体树
        self.agent_tree = AgentTree("RootAgent")
        self.agent_tree.add_root_agent(self.root_agent, "RootAgent")
    
    def _get_root_system_prompt(self) -> str:
        """获取根智能体的系统提示 - 强调自主决策"""
        return """你是 RootAgent，一个具有完全自主决策能力的根智能体。

## 你的核心能力

你可以使用以下工具来管理你的工作：

1. **create_child_agent** - 创建专门的子智能体
   - 当某个领域的任务频繁出现时使用
   - 当某个任务需要专业知识时使用
   
2. **delegate_to_child** - 委托任务给子智能体
   - 当子智能体更适合处理某个任务时使用
   - 让专业的子智能体处理专业的事情

3. **learn_skill** - 学习和记录新技能
   - 当你成功完成某类任务后使用
   - 记录技能的方法论以便复用

4. **remember_knowledge** - 记住领域知识
   - 在交互中学到新知识时使用
   - 积累不同领域的知识库

5. **query_my_skills** - 查询你已掌握的技能
   - 需要了解自己能力时使用

6. **query_my_knowledge** - 查询你积累的知识
   - 需要回顾已学知识时使用

7. **list_my_children** - 列出你的子智能体
   - 需要知道可以委托给谁时使用

## 工作原则

**自主思考和决策：**
- 收到任务时，先思考：这是什么类型的任务？
- 判断：我能直接处理吗？还是需要专门的子智能体？
- 决定：如果有合适的子智能体，委托给它；如果没有但值得创建，就创建一个；否则自己处理

**技能学习：**
- 完成任务后，反思：这个任务是否值得记录为一个技能？
- 如果是重复出现的任务类型，使用 learn_skill 工具记录下来
- 记录方法论，以便未来遇到类似任务时可以复用

**知识积累：**
- 在帮助用户的过程中，注意积累各个领域的知识
- 使用 remember_knowledge 工具记住重要的知识点
- 建立你的知识库

**子智能体管理：**
- 根据需要创建子智能体，不要一开始就创建很多
- 每个子智能体应该有明确的技能领域
- 子智能体也可以创建自己的子智能体，形成层级结构

**通信而非检索：**
- 不要尝试检索信息，而是通过与子智能体通信来解决问题
- 父智能体知道子智能体的能力，根据这个来分配任务
- 子智能体专注于自己的领域

## 决策示例

用户："帮我解一道数学题"
- 思考：这是数学任务，我有数学专家子智能体吗？
- 如果有：使用 delegate_to_child 委托给数学专家
- 如果没有但数学任务很常见：使用 create_child_agent 创建数学专家，然后委托
- 如果是偶尔出现：自己处理，然后考虑是否 learn_skill

用户："教我写作技巧"
- 思考：这需要写作专业知识
- 判断：我有写作专家吗？查询 list_my_children
- 决策：创建一个写作专家子智能体来处理
- 学习：记住这是一个值得专业化的领域

记住：你是完全自主的，根据情况自己做决策，使用工具来实现你的决策。"""


    async def process_user_request(self, user_request: str) -> str:
        """通过智能体树处理用户请求。
        
        智能体会自主决定如何处理：直接回复、委托、创建子agent等

        参数:
            user_request (str): 用户请求

        返回:
            str: 智能体的响应
        """
        if not self.root_agent:
            raise RuntimeError("根智能体未初始化")

        # 创建用户消息
        msg = Msg(
            name="user",
            content=user_request,
            role="user",
        )

        # 让根智能体自主处理 - 它会根据情况使用工具
        response = await self.root_agent.reply(msg)
        return response.get_text_content() or str(response.content)

    async def run_interactive_session(self) -> None:
        """与智能体树运行交互式会话。"""
        print("\n" + "=" * 60)
        print("技能学习树系统 - 自主智能体交互会话")
        print("=" * 60)
        print("\n特点:")
        print("  - 智能体完全自主决策")
        print("  - 智能体自己决定是否创建子agent或委托任务")
        print("  - 通过工具实现智能体间通信")
        print("  - 积累技能记忆和知识记忆")
        print("\n命令:")
        print("  'exit' - 结束会话")
        print("  'info' - 显示根智能体信息")
        print("  'tree' - 显示当前树形结构")
        print("  或输入任何问题让智能体自主处理")
        print("=" * 60 + "\n")

        user_agent = UserAgent("用户")

        while True:
            try:
                # 获取用户输入
                user_input = await user_agent()

                if not user_input or not user_input.get_text_content():
                    continue

                user_text = user_input.get_text_content()

                if user_text.lower() == "exit":
                    print("\n结束会话...")
                    break

                elif user_text.lower() == "info":
                    if self.root_agent:
                        info = self.root_agent.get_agent_info()
                        print("\n根智能体信息:")
                        print(f"  名称: {info['name']}")
                        print(f"  领域: {info['domain']}")
                        print(f"  子智能体: {', '.join(info['children']) if info['children'] else '无'}")
                        print(f"  已学技能: {', '.join(info['skills']) if info['skills'] else '无'}")
                        print(f"  知识主题: {', '.join(info['knowledge_topics']) if info['knowledge_topics'] else '无'}")

                elif user_text.lower() == "tree":
                    if self.agent_tree:
                        print("\n当前智能体树结构:")
                        print(self.agent_tree.print_tree())
                        print("\n技能统计:")
                        skills_summary = self.agent_tree.get_skill_summary()
                        for agent, info in skills_summary.items():
                            print(
                                f"  {agent}: {info['skill_count']} 个技能"
                            )

                else:
                    # 让智能体自主处理用户请求
                    print("\n[智能体思考中...]")
                    response = await self.process_user_request(user_text)
                    print(f"\n{response}\n")

            except KeyboardInterrupt:
                print("\n\n会话被用户中断")
                break
            except Exception as e:
                print(f"\n错误: {str(e)}")
                import traceback
                traceback.print_exc()
                continue

    async def run(self) -> None:
        """运行完整系统。"""
        try:
            # 初始化根智能体
            print("正在初始化技能学习树系统...")
            await self.initialize_root_agent()
            print("✓ 根智能体已初始化并准备就绪")
            print("✓ 智能体可以自主决策、创建子agent、委托任务")

            # 运行交互式会话
            await self.run_interactive_session()

        except Exception as e:
            print(f"系统错误: {str(e)}")
            raise


async def main() -> None:
    """主入口。"""
    system = SkillAgentTreeSystem()
    await system.run()


if __name__ == "__main__":
    asyncio.run(main())

