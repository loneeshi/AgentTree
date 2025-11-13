# RAG Agent - 文档问答系统

这是一个基于 AgentScope 框架的检索增强生成（RAG）智能体系统，用于根据知识库文档回答用户问题。

## 功能特性

- **灵活的文档加载**：支持两种文档加载方式
  - `chunked`：适用于已预先分块的文档（使用 `--- Document Chunk X ---` 分隔符）
  - `direct`：直接读取原始文本并自动分割

- **可配置的向量存储**：支持两种存储方式
  - `memory`：内存存储（`:memory:`），适合测试和演示
  - `localhost`：远程 Qdrant 服务器（`http://localhost:6333`），适合生产环境

- **交互式对话界面**：支持与 AI 智能体的多轮对话

## 环境配置

### 必需的环境变量

在运行程序前，请设置以下环境变量：

```bash
# 阿里云灵积 API 密钥（用于文本嵌入）
export DASHSCOPE_API_KEY="your-dashscope-api-key"

# 自定义模型 API 密钥
export AI_STORE_API_KEY="your-ai-store-api-key"
```

### 依赖安装

```bash
pip install agentscope sentence-transformers
```

## 使用方法

### 基本用法

```bash
python agentic_usage.py --docs-dir <documents_directory>
```

### 完整参数说明

```bash
python agentic_usage.py \
  --docs-dir <directory_path> \
  --load-method <chunked|direct> \
  --db-location <memory|localhost>
```

### 参数详解

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `--docs-dir` | 字符串 | **必需** | 包含 `.txt` 文件的目录路径，或输入 `none` 跳过加载（使用现有数据库数据） |
| `--load-method` | 字符串 | `chunked` | 文档加载方式：`chunked` 或 `direct`（当 `--docs-dir` 为 `none` 时被忽略） |
| `--db-location` | 字符串 | `memory` | 向量数据库位置：`memory` 或 `localhost` |
| `--batch-size` | 整数 | `50` | 每批处理的文档数量（用于大规模文档加载） |

### 使用示例

#### 示例 1：使用预分块的文档，内存存储
```bash
python agentic_usage.py \
  --docs-dir /path/to/documents \
  --load-method chunked \
  --db-location memory
```

#### 示例 2：使用原始文本，远程 Qdrant 服务器
```bash
python agentic_usage.py \
  --docs-dir /path/to/documents \
  --load-method direct \
  --db-location localhost
```

#### 示例 3：快速开始（使用所有默认值）
```bash
python agentic_usage.py --docs-dir /Users/a86135/Desktop/Projects/skill_learning/AgentTree/AgentTree-kasike_ai_rail/Test/
```

#### 示例 4：使用 localhost Qdrant 中的现有数据（不加载新文档）
```bash
python agentic_usage.py \
  --docs-dir none \
  --db-location localhost
```

#### 示例 5：大规模文档加载（调整批处理大小）
```bash
python agentic_usage.py \
  --docs-dir /path/to/documents \
  --load-method chunked \
  --batch-size 30
```
使用较小的批处理大小（20-30）可以减少内存占用，但会增加加载时间。对于大规模文档库（1000+ 文件），推荐使用较小的批处理大小。

## 大规模文档加载优化

当处理包含大量文档的知识库时，程序会自动进行以下优化：

### 分批处理（Batching）

程序将文档分成多个小批次进行处理，而不是一次性加载所有文档。这有以下好处：

- **减少内存占用**：避免一次性在内存中存储所有文档
- **更好的响应性**：您可以实时看到处理进度
- **容错能力**：如果某一批出现问题，不会影响已处理的批次

### 进度条反馈

加载文档时，系统会显示实时进度条：

```
Adding 5000 documents to knowledge base...
Processing documents: 45%|████▌     | 2250/5000 [02:30<03:15, 14.3doc/s]
```

### 批处理大小建议

| 文档数量 | 推荐批处理大小 | 预期内存占用 |
|---------|--------------|-----------|
| < 100 | 50（默认） | < 1GB |
| 100-500 | 30-50 | 1-2GB |
| 500-2000 | 20-30 | 2-4GB |
| > 2000 | 10-20 | > 4GB |

### 使用建议

```bash
# 对于中等规模（100-500文档）
python agentic_usage.py --docs-dir /path/to/docs --batch-size 50

# 对于大规模（500-2000文档）
python agentic_usage.py --docs-dir /path/to/docs --batch-size 30

# 对于超大规模（2000+文档）
python agentic_usage.py --docs-dir /path/to/docs --batch-size 20

# 对于内存受限的环境
python agentic_usage.py --docs-dir /path/to/docs --batch-size 10
```

## 文档加载选项说明

### 加载新文档

如果您想加载新的 `.txt` 文件到知识库中：

```bash
python agentic_usage.py --docs-dir /path/to/documents --load-method chunked
```

### 使用现有数据库

如果您的 Qdrant 服务器中已经有数据，想直接使用现有数据而不加载新文档，只需设置 `--docs-dir none`：

```bash
python agentic_usage.py --docs-dir none --db-location localhost
```

在这种情况下，程序会：
- ✅ 连接到现有的 Qdrant 服务器（`http://localhost:6333`）
- ✅ **跳过文档加载** - 不会处理任何 `.txt` 文件
- ✅ 直接使用数据库中已存储的数据
- ✅ `--load-method` 和 `--batch-size` 参数被忽略（因为不需要加载文档）

## 文档格式

### 预分块格式（chunked）

如果您选择 `--load-method chunked`，文档应该使用以下格式：

```
--- Document Chunk 0 ---
[第一个分块的内容]

--- Document Chunk 1 ---
[第二个分块的内容]

--- Document Chunk 2 ---
[第三个分块的内容]
```

### 原始文本格式（direct）

如果您选择 `--load-method direct`，可以使用任何格式的纯文本文件。系统会自动按句子分割。

## 向量数据库配置

### 内存存储（默认）

适合开发和测试：
```bash
python agentic_usage.py --docs-dir /path/to/docs --db-location memory
```

### 远程 Qdrant 服务器

在使用远程服务器前，请确保 Qdrant 服务正在运行：

```bash
# 启动 Qdrant Docker 容器
docker run -p 6333:6333 qdrant/qdrant
```

然后运行程序：
```bash
python agentic_usage.py --docs-dir /path/to/docs --db-location localhost
```

## 交互流程

1. **程序启动**：加载文档到知识库，初始化 AI 智能体
2. **输入问题**：在 `User:` 提示符下输入您的问题
3. **智能体响应**：系统检索相关文档并生成答案
4. **继续对话**：输入下一个问题，或输入 `exit` 退出程序

## 常见问题

### Q: 如何选择加载方法？
A: 
- 如果您的文档已经预先分块（使用 `--- Document Chunk X ---` 格式），使用 `chunked`
- 如果您的文档是原始文本，使用 `direct`（系统会自动分割）

### Q: 内存存储和远程存储有什么区别？
A:
- **内存存储**：数据存在内存中，程序退出后丢失，适合测试
- **远程存储**：数据持久化存储在 Qdrant 服务器，适合生产环境

### Q: 如何处理 API 密钥配置？
A: 使用环境变量设置密钥：
```bash
export DASHSCOPE_API_KEY="your-key"
export AI_STORE_API_KEY="your-key"
python agentic_usage.py --docs-dir /path/to/docs
```

### Q: 如何改进检索结果质量？
A: 在对话中，AI 智能体会自动调整以下参数来优化检索：
- `query`：改进查询表述
- `limit`：检索文档数量
- `score_threshold`：相似度阈值

## 故障排除

| 问题 | 解决方案 |
|------|--------|
| `DASHSCOPE_API_KEY` 错误 | 检查环境变量是否正确设置 |
| 远程数据库连接失败 | 确保 Qdrant 服务在 `localhost:6333` 正常运行 |
| 检索结果不相关 | 尝试改进查询表述或调整 `score_threshold` |
| 文档未加载 | 检查文档目录路径和文件格式 |

## 技术栈

- **框架**：AgentScope
- **向量数据库**：Qdrant
- **嵌入模型**：DashScope text-embedding-v4
- **LLM 模型**：Qwen3-235B-A22B
- **Python 版本**：3.11+

## 许可证

MIT License

## 联系方式

如有问题或建议，请提出 Issue 或 Pull Request。
