# -*- coding: utf-8 -*-
"""
文本分块管理模块。
提供多种文本分块方式，支持 overlap 功能。
"""
import os
import hashlib
import re
from typing import Literal

from agentscope.rag import Document, DocMetadata
from agentscope.message import TextBlock
from agentscope.rag import TextReader


def split_text_with_overlap(
    text: str,
    chunk_size: int = 1024,
    overlap: int = 200,
    split_by: Literal["char", "sentence", "paragraph"] = "char"
) -> list[str]:
    """
    将文本分割成带有重叠的 chunks。
    
    Args:
        text: 输入文本
        chunk_size: 每个 chunk 的大小（字符数）
        overlap: 相邻 chunk 之间的重叠字符数
        split_by: 分割方式 ("char", "sentence", "paragraph")
    
    Returns:
        chunk 列表
        
    Raises:
        ValueError: 当 overlap >= chunk_size 时抛出
    """
    if overlap >= chunk_size:
        raise ValueError(f"overlap ({overlap}) 必须小于 chunk_size ({chunk_size})")
    
    # 第一步：按照指定方式初步分割
    if split_by == "char":
        # 按字符直接分割
        sentences = [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]
    
    elif split_by == "sentence":
        # 按句子分割
        try:
            import nltk
            nltk.download("punkt", quiet=True)
            nltk.download("punkt_tab", quiet=True)
            sentences = nltk.sent_tokenize(text)
        except ImportError:
            # 如果 nltk 不可用，使用简单的句号分割
            sentences = text.split("。")
    
    elif split_by == "paragraph":
        # 按段落分割
        sentences = [s.strip() for s in text.split("\n") if s.strip()]
    
    else:
        raise ValueError(f"不支持的 split_by: {split_by}")
    
    # 第二步：合并句子形成 chunks，并添加重叠
    chunks = []
    current_chunk = ""
    
    for sentence in sentences:
        # 如果加上这个句子会超过 chunk_size，则保存当前 chunk
        if len(current_chunk) + len(sentence) > chunk_size and current_chunk:
            chunks.append(current_chunk)
            
            # 创建重叠部分：从当前 chunk 的末尾取出最后 overlap 个字符
            overlap_text = current_chunk[-overlap:] if len(current_chunk) >= overlap else current_chunk
            current_chunk = overlap_text + sentence
        else:
            current_chunk += sentence
    
    # 添加最后一个 chunk
    if current_chunk:
        chunks.append(current_chunk)
    
    return [chunk.strip() for chunk in chunks if chunk.strip()]


def load_pre_chunked_documents(file_path: str) -> list[Document]:
    """
    从预先分块的 .txt 文件中加载并恢复 Document 对象列表。
    文件格式应为 '--- Document Chunk X ---'。
    
    Args:
        file_path: 预先分块的 txt 文件路径
    
    Returns:
        Document 对象列表
    """
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # 为整个文档生成一个唯一的 doc_id
    doc_id = hashlib.sha256(content.encode("utf-8")).hexdigest()

    # 按分隔符分割文本
    raw_chunks = re.split(r"--- Document Chunk \d+ ---", content)

    # 清理并创建 Document 对象
    documents = []
    # 过滤掉因分割产生的空字符串
    splits = [chunk.strip() for chunk in raw_chunks if chunk.strip()]
    total_chunks = len(splits)
    
    for idx, chunk_text in enumerate(splits):
        doc = Document(
            id=f"{doc_id}-{idx}",
            metadata=DocMetadata(
                content=TextBlock(type="text", text=chunk_text),
                doc_id=doc_id,
                chunk_id=idx,
                total_chunks=total_chunks,
            ),
        )
        documents.append(doc)

    return documents


async def load_documents_with_overlap(
    file_path: str,
    chunk_size: int = 1024,
    overlap: int = 200,
    split_by: Literal["char", "sentence", "paragraph"] = "char"
) -> list[Document]:
    """
    从文件加载文本并创建带有重叠的 Document 对象。
    
    Args:
        file_path: 文件路径
        chunk_size: 每个 chunk 的大小（字符数）
        overlap: 重叠大小（字符数）
        split_by: 分割方式 ("char", "sentence", "paragraph")
    
    Returns:
        Document 对象列表
    """
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    # 生成文档 ID
    doc_id = hashlib.sha256(content.encode("utf-8")).hexdigest()
    
    # 使用带重叠的分割方法
    splits = split_text_with_overlap(
        content,
        chunk_size=chunk_size,
        overlap=overlap,
        split_by=split_by
    )
    
    total_chunks = len(splits)
    documents = []
    
    for idx, chunk_text in enumerate(splits):
        doc = Document(
            id=f"{doc_id}-{idx}",
            metadata=DocMetadata(
                content=TextBlock(type="text", text=chunk_text),
                doc_id=doc_id,
                chunk_id=idx,
                total_chunks=total_chunks,
            ),
        )
        documents.append(doc)
    
    return documents


async def load_documents_direct(
    file_path: str,
    chunk_size: int = 1024,
    split_by: Literal["char", "sentence", "paragraph"] = "sentence"
) -> list[Document]:
    """
    使用 TextReader 直接加载文件（无重叠）。
    
    Args:
        file_path: 文件路径
        chunk_size: 每个 chunk 的大小（字符数）
        split_by: 分割方式
    
    Returns:
        Document 对象列表
    """
    reader = TextReader(chunk_size=chunk_size, split_by=split_by)
    
    with open(file_path, "r", encoding="utf-8") as f:
        text_content = f.read()
    
    documents = await reader(text=text_content)
    
    return documents


async def load_documents_from_directory(
    docs_directory: str,
    load_method: Literal["chunked", "direct", "overlap"] = "chunked",
    chunk_size: int = 1024,
    overlap: int = 200,
    split_by: Literal["char", "sentence", "paragraph"] = "char"
) -> list[Document]:
    """
    从目录中加载所有 .txt 文件。
    
    Args:
        docs_directory: 文档目录路径
        load_method: 加载方式 ("chunked" - 预分块, "direct" - 直接加载, "overlap" - 带重叠加载)
        chunk_size: 每个 chunk 的大小（字符数）
        overlap: 重叠大小（仅在 load_method="overlap" 时使用）
        split_by: 分割方式
    
    Returns:
        Document 对象列表
    """
    all_documents = []
    
    if not os.path.exists(docs_directory):
        raise FileNotFoundError(f"目录不存在: {docs_directory}")
    
    # 遍历目录中的所有 .txt 文件
    txt_files = [f for f in os.listdir(docs_directory) if f.endswith(".txt")]
    
    if not txt_files:
        print(f"警告: 目录中没有找到 .txt 文件: {docs_directory}")
        return all_documents
    
    print(f"找到 {len(txt_files)} 个 .txt 文件")
    
    for filename in txt_files:
        file_path = os.path.join(docs_directory, filename)
        print(f"  加载: {filename}")
        
        try:
            if load_method == "chunked":
                # 使用预分块的文档加载器
                documents = load_pre_chunked_documents(file_path)
            
            elif load_method == "overlap":
                # 使用带重叠的加载器
                documents = await load_documents_with_overlap(
                    file_path,
                    chunk_size=chunk_size,
                    overlap=overlap,
                    split_by=split_by
                )
            
            else:  # load_method == "direct"
                # 使用 TextReader 直接加载
                documents = await load_documents_direct(
                    file_path,
                    chunk_size=chunk_size,
                    split_by=split_by
                )
            
            all_documents.extend(documents)
            print(f"    ✓ 成功加载 {len(documents)} 个 chunks")
        
        except Exception as e:
            print(f"    ✗ 加载失败: {str(e)}")
            continue
    
    return all_documents