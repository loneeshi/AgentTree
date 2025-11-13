
# -*- coding: utf-8 -*-
"""The agentic usage example for RAG in AgentScope, where the agent is
equipped with RAG tools to answer questions based on a knowledge base.

The example is more challenging for the agent, requiring the agent to
adjust the retrieval parameters to get relevant results.
"""
import asyncio
import os
import argparse
from tqdm import tqdm

from agentscope.rag import SimpleKnowledge, QdrantStore
from agentscope import setup_logger
from agentscope.agent import ReActAgent, UserAgent
from agentscope.embedding import DashScopeTextEmbedding
from agentscope.formatter import OpenAIChatFormatter
from agentscope.message import Msg
from agentscope.model import OpenAIChatModel
from agentscope.tool import Toolkit

# 导入分块管理模块
from chunk_manager import load_documents_from_directory
# 导入Q&A读写处理模块
from qa_io_handler import QuestionReader, AnswerWriter, get_questions_summary


def create_knowledge_base(db_location: str) -> SimpleKnowledge:
    """
    Create a knowledge base instance with specified database location.
    
    Args:
        db_location: Either ":memory:" for in-memory storage or 
                     "http://localhost:6333" for remote Qdrant server
    
    Returns:
        SimpleKnowledge instance
    """
    return SimpleKnowledge(
        embedding_store=QdrantStore(
            location=db_location,
            collection_name="test_collection",
            dimensions=1024,
        ),
        embedding_model=DashScopeTextEmbedding(
            api_key=os.environ["DASHSCOPE_API_KEY"],
            model_name="text-embedding-v4",
        ),
    )


async def add_documents_with_progress(
    knowledge: SimpleKnowledge,
    documents: list,
    batch_size: int = 50
) -> None:
    """
    分批添加文档到知识库，并显示进度条。
    
    Args:
        knowledge: SimpleKnowledge 实例
        documents: 要添加的文档列表
        batch_size: 每批处理的文档数量（默认50个）
    """
    total_docs = len(documents)
    print(f"\nAdding {total_docs} documents to knowledge base...")
    
    # 分批处理文档
    with tqdm(total=total_docs, desc="Processing documents", unit="doc") as pbar:
        for i in range(0, total_docs, batch_size):
            batch = documents[i:i + batch_size]
            await knowledge.add_documents(batch)
            pbar.update(len(batch))
    
    print(f"✓ Successfully added {total_docs} documents to knowledge base\n")


setup_logger(level="ERROR")


async def answer_questions_batch(
    agent: ReActAgent,
    knowledge: SimpleKnowledge,
    questions_dict: dict,
    output_file: str = None,
) -> tuple:
    """
    Batch answer questions from markdown and save to JSON.
    
    Args:
        agent: ReActAgent instance
        knowledge: SimpleKnowledge instance
        questions_dict: Questions dictionary from QuestionReader.parse_markdown
        output_file: Output JSON file path (auto-generated if None)
        
    Returns:
        (answers_dict, output_file_path)
    """
    all_answers = {}
    retrieve_results = {}
    
    # Calculate total questions
    total_questions = sum(len(q_list) for q_list in questions_dict.values())
    
    print(f"\n{'='*70}")
    print(f"开始自动回答问题 (共 {total_questions} 道题)")
    print(f"{'='*70}\n")
    
    # Use progress bar for overall progress
    with tqdm(total=total_questions, desc="总体进度", unit="题") as overall_pbar:
        for category in sorted(questions_dict.keys()):
            print(f"\n{'='*70}")
            print(f"类别: {category}")
            print(f"{'='*70}")
            
            all_answers[category] = {}
            retrieve_results[category] = {}
            questions_list = questions_dict[category]
            
            for q in questions_list:
                q_id = q['id']
                q_text = q['text']
                
                # Display current question
                print(f"\n[{category} #{q_id}] {q_text[:100]}...")
                
                try:
                    # Submit question to agent
                    msg = Msg("user", q_text, "user")
                    response_msg = await agent(msg)
                    answer_text = response_msg.get_text_content()
                    
                    # Store answer
                    all_answers[category][q_id] = answer_text
                    retrieve_results[category][q_id] = []  # Retrieve results placeholder
                    
                    print(f"✓ 答案: {answer_text[:150]}...")
                    
                except Exception as e:
                    error_msg = f"Error: {str(e)}"
                    all_answers[category][q_id] = error_msg
                    retrieve_results[category][q_id] = []
                    print(f"✗ 出错: {error_msg}")
                
                overall_pbar.update(1)
    
    # Save answers to JSON
    output_path = AnswerWriter.write_answers(
        questions_dict,
        all_answers,
        output_file,
        retrieve_results
    )
    
    print(f"\n{'='*70}")
    print(f"✓ 所有答案已保存到: {output_path}")
    print(f"{'='*70}\n")
    
    return all_answers, output_path


async def main(
    docs_directory: str,
    db_location: str,
    load_method: str,
    batch_size: int = 50,
    chunk_size: int = 1024,
    overlap: int = 200,
    markdown_file: str = None,
    output_file: str = None,
) -> None:
    """
    The main entry of the agent usage example for RAG in AgentScope.
    
    Args:
        docs_directory: Path to the directory containing .txt files, or "none" to skip loading
        db_location: Either ":memory:" for in-memory storage or 
                     "http://localhost:6333" for remote Qdrant server
        load_method: Either "chunked", "direct", or "overlap"
        batch_size: Number of documents to process in each batch
        chunk_size: Size of each chunk in characters
        overlap: Overlap size for "overlap" load method
        markdown_file: Path to markdown file with questions (for batch answering)
        output_file: Path to save answers JSON (auto-generated if None)
    """
    # Create knowledge base with specified location
    knowledge = create_knowledge_base(db_location)
    
    print(f"Using database location: {db_location}")
    
    # Load documents only if docs_directory is not "none"
    if docs_directory.lower() != "none":
        print(f"Using load method: {load_method}")
        print(f"Loading documents from: {docs_directory}")
        
        # Load documents from directory
        all_documents = await load_documents_from_directory(
            docs_directory,
            load_method=load_method,
            chunk_size=chunk_size,
            overlap=overlap,
            split_by="char"
        )

        if all_documents:
            print(f"Total documents loaded: {len(all_documents)}")
            # Add documents with progress bar and batching
            await add_documents_with_progress(knowledge, all_documents, batch_size=batch_size)
        else:
            print("No documents were loaded!")
    else:
        print("Skipping document loading (using existing knowledge base data)")

    # Create a toolkit and register the RAG tool function
    toolkit = Toolkit()
    toolkit.register_tool_function(
        knowledge.retrieve_knowledge,
        func_description=(
            "从知识库中检索行业标准、技术规范、研究报告和数据表等信息相关的文档。每次回答都要检索。注意，`query` "
            "参数对检索质量至关重要，你可以尝试不同的查询以获得最佳结果。"
            "调整 `limit` 和 `score_threshold` 参数可以获取更多或更少的结果。"
        ),
    )

    # Create an agent and a user
    agent = ReActAgent(
        name="Friday",
        sys_prompt=(
            "你是一个名为‘星期五’的乐于助人的助手。"
            "你配备了一个 'retrieve_knowledge' 工具，你可以从中获得行业标准、技术规范、研究报告和数据表等信息。"
            "你回答相关问题时可以用'retrieve_knowledge' 工具，检索信息。"
            "注意：当你无法获取相关结果时，请调整 `score_threshold` 参数。"
            "如果多次尝试（例如，通过更改查询或调整 `score_threshold`）后，'retrieve_knowledge' 工具仍然返回空结果或找不到相关信息，你应该礼貌地告知用户你没有找到相关信息，而不是继续无效的尝试。"
        ),
        toolkit=toolkit,
        model=OpenAIChatModel(
            api_key=os.environ["AI_STORE_API_KEY"],
            client_args={
                "base_url": "https://ai.api.coregpu.cn/v1/"
            },
            model_name="Qwen3-235B-A22B",
        ),
        formatter=OpenAIChatFormatter(),
    )
    user = UserAgent(name="User")
    
    # If markdown file is provided, do batch question answering
    if markdown_file:
        print(f"\n📄 读取题目文件: {markdown_file}")
        questions_dict = QuestionReader.parse_markdown(markdown_file)
        
        # Print summary
        print(get_questions_summary(questions_dict))
        
        # Batch answer questions
        await answer_questions_batch(
            agent=agent,
            knowledge=knowledge,
            questions_dict=questions_dict,
            output_file=output_file
        )
    else:
        # Interactive chat mode
        print("\n" + "="*50)
        print("RAG Agent Chat Interface")
        print("Type 'exit' to quit")
        print("="*50 + "\n")
        
        # Get the first message from the user
        user_input = input("User: ")
        
        while user_input.strip() != "exit":
            msg = Msg(
                "user",
                user_input,
                "user",
            )
            msg = await agent(msg)
            print(f"\nAgent: {msg.get_text_content()}\n")
            
            user_input = input("User: ")
        
        print("Goodbye!")


def main_entry():
    """Entry point with command-line argument parsing."""
    parser = argparse.ArgumentParser(
        description="RAG Agent with configurable document loading and question answering"
    )
    parser.add_argument(
        "--docs-dir",
        type=str,
        required=True,
        help="Directory containing .txt files to load into the knowledge base, or 'none' to skip loading and use existing data"
    )
    parser.add_argument(
        "--load-method",
        type=str,
        choices=["chunked", "direct", "overlap"],
        default="chunked",
        help="Method to load documents: 'chunked' for pre-chunked, 'direct' for raw text, 'overlap' for text with overlap"
    )
    parser.add_argument(
        "--db-location",
        type=str,
        choices=["memory", "localhost"],
        default="memory",
        help="Database location: 'memory' for in-memory, 'localhost' for http://localhost:6333"
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=100,
        help="Number of documents to process in each batch (default: 50)"
    )
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=1024,
        help="Size of each chunk in characters (default: 1024)"
    )
    parser.add_argument(
        "--overlap",
        type=int,
        default=200,
        help="Overlap size for chunks in 'overlap' mode (default: 200, ignored in other modes)"
    )
    parser.add_argument(
        "--md-file",
        type=str,
        default=None,
        help="Path to markdown file with questions for batch question answering (optional)"
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Output JSON file path for answers (auto-generated if not specified)"
    )
    
    args = parser.parse_args()
    
    # Convert db_location argument to actual location string
    db_location = ":memory:" if args.db_location == "memory" else "http://localhost:6333"
    
    # Run the async main function
    asyncio.run(main(
        args.docs_dir,
        db_location,
        args.load_method,
        args.batch_size,
        args.chunk_size,
        args.overlap,
        args.md_file,
        args.output
    ))


if __name__ == "__main__":
    main_entry()